#!/usr/bin/env python3
"""Backfill size metadata in selected_benchmark_tasks.json.

Populates per-task:
  - context_length
  - files_count
  - context_length_source
  - files_count_source

Extraction order:
1) task.toml metadata (exact)
2) git tree scan at pinned repo revision (exact files, byte-based token estimate)
3) environment/repo scan (approximate, where available)
4) MCP-breakdown proxy (estimated)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import shlex
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def _read_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _run(
    cmd: list[str], cwd: Path | None = None, timeout_sec: int | None = None
) -> subprocess.CompletedProcess[str]:
    cwd_s = str(cwd) if cwd else None
    if timeout_sec is None:
        return subprocess.run(
            cmd,
            cwd=cwd_s,
            text=True,
            capture_output=True,
            check=False,
        )
    proc = subprocess.Popen(
        cmd,
        cwd=cwd_s,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    try:
        out, err = proc.communicate(timeout=timeout_sec)
        return subprocess.CompletedProcess(cmd, proc.returncode, out, err)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, 15)
        except OSError:
            pass
        try:
            out, err = proc.communicate(timeout=2)
        except Exception:
            out, err = "", "timeout"
        return subprocess.CompletedProcess(cmd, returncode=124, stdout=out or "", stderr=err or "timeout")


def _safe_slug(repo: str) -> str:
    return repo.replace("/", "__")


def _parse_repo_and_rev(task_dir: Path) -> tuple[str | None, str | None]:
    """Extract (owner/repo, rev) from task.toml / repo_path / Dockerfile hints."""
    toml_path = task_dir / "task.toml"
    repo: str | None = None
    rev: str | None = None

    if toml_path.is_file():
        try:
            d = _read_toml(toml_path)
        except Exception:
            d = {}
        task = d.get("task", {}) or {}
        repo_raw = task.get("repo")
        rev_raw = task.get("pre_fix_rev")
        if isinstance(repo_raw, str) and repo_raw.strip():
            repo = repo_raw.strip()
        if isinstance(rev_raw, str) and rev_raw.strip():
            rev = rev_raw.strip()

    repo_path_file = task_dir / "repo_path"
    if repo_path_file.is_file() and (not repo or "/" not in repo):
        try:
            rp = repo_path_file.read_text(errors="ignore").strip()
        except OSError:
            rp = ""
        if "/" in rp:
            repo = rp

    # Fallback: parse clone URL in environment/Dockerfile.
    dockerfile = task_dir / "environment" / "Dockerfile"
    if dockerfile.is_file() and (not repo or not rev):
        try:
            txt = dockerfile.read_text(errors="ignore")
        except OSError:
            txt = ""
        if not repo:
            m_repo = re.search(r"https://github.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\\.git)?(?:\\s|$)", txt)
            if m_repo:
                repo = m_repo.group(1)
        if not rev:
            m_rev = re.search(r"git checkout\\s+([0-9a-fA-F]{7,40}|v[0-9][A-Za-z0-9._-]*)", txt)
            if m_rev:
                rev = m_rev.group(1)

    if repo and "/" not in repo:
        repo = None
    return repo, rev


def _git_tree_metrics(repo: str, rev: str, cache_dir: Path, git_timeout_sec: int) -> tuple[int | None, int | None]:
    """Return (approx_context_tokens_from_blob_bytes, files_count) for repo@rev."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    local = cache_dir / _safe_slug(repo)
    remote = f"https://github.com/{repo}.git"

    if not local.exists():
        cp = _run(
            ["git", "-c", "gc.auto=0", "clone", "--filter=blob:none", "--no-checkout", remote, str(local)],
            timeout_sec=git_timeout_sec,
        )
        if cp.returncode != 0:
            return None, None
        _run(["git", "-C", str(local), "config", "gc.auto", "0"], timeout_sec=git_timeout_sec)

    # Resolve revision to commit.
    cp = _run(
        ["git", "-c", "gc.auto=0", "-C", str(local), "rev-parse", "--verify", f"{rev}^{{commit}}"],
        timeout_sec=git_timeout_sec,
    )
    if cp.returncode != 0:
        cp_fetch = _run(
            ["git", "-c", "gc.auto=0", "-C", str(local), "fetch", "--quiet", "origin", rev, "--depth", "1"],
            timeout_sec=git_timeout_sec,
        )
        if cp_fetch.returncode != 0:
            return None, None
        cp = _run(
            ["git", "-c", "gc.auto=0", "-C", str(local), "rev-parse", "--verify", f"{rev}^{{commit}}"],
            timeout_sec=git_timeout_sec,
        )
        if cp.returncode != 0:
            return None, None

    commit = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else None
    if not commit:
        return None, None

    # Parse tracked blobs and sum exact blob sizes from tree entries.
    local_q = shlex.quote(str(local))
    commit_q = shlex.quote(commit)
    shell_cmd = (
        f"git -c gc.auto=0 -C {local_q} ls-tree -r -l {commit_q} | "
        "awk '$2==\"blob\"{c+=1;s+=$4} END{print c, s}'"
    )
    cp_tree = _run(["bash", "-lc", shell_cmd], timeout_sec=git_timeout_sec)
    if cp_tree.returncode != 0:
        return None, None
    out = (cp_tree.stdout or "").strip()
    if not out:
        return None, None
    parts = out.split()
    if len(parts) < 2:
        return None, None
    try:
        files_count = int(parts[0])
        total_bytes = int(parts[1])
    except ValueError:
        return None, None

    if files_count <= 0 or total_bytes <= 0:
        return None, None

    approx_tokens = max(1, total_bytes // 4)
    return approx_tokens, files_count


def _scan_env_repo(repo_dir: Path) -> tuple[int | None, int | None]:
    """Return (approx_context_tokens, files_count) from environment/repo."""
    if not repo_dir.is_dir():
        return None, None

    files_count = 0
    approx_tokens = 0

    for p in repo_dir.rglob("*"):
        if not p.is_file():
            continue
        files_count += 1
        try:
            # Fast approximate token count from UTF-8 text length.
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text:
            continue
        approx_tokens += max(1, len(text) // 4)

    return approx_tokens if approx_tokens > 0 else None, files_count if files_count > 0 else None


def _proxy_context_length(task: dict) -> int | None:
    mb = task.get("mcp_breakdown") or {}
    cc = mb.get("context_complexity") if isinstance(mb, dict) else None
    try:
        cc = float(cc) if cc is not None else None
    except (TypeError, ValueError):
        cc = None
    if cc is None:
        return None
    return int(round(cc * 1_000_000))


def _proxy_files_count(task: dict) -> int | None:
    mb = task.get("mcp_breakdown") or {}
    cfd = mb.get("cross_file_deps") if isinstance(mb, dict) else None
    try:
        cfd = float(cfd) if cfd is not None else None
    except (TypeError, ValueError):
        cfd = None
    if cfd is None:
        return None
    # ccb_k8sdocs uses a larger package-size scale in scoring heuristics.
    scale = 450 if task.get("benchmark") == "ccb_k8sdocs" else 20
    return max(1, int(round(cfd * scale)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill size metadata in selected_benchmark_tasks.json")
    parser.add_argument(
        "--selected-tasks",
        type=Path,
        default=Path("configs/selected_benchmark_tasks.json"),
        help="Path to selected_benchmark_tasks.json",
    )
    parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=Path("benchmarks"),
        help="Path to benchmarks/ root",
    )
    parser.add_argument(
        "--git-cache-dir",
        type=Path,
        default=Path(".cache/repo_size"),
        help="Cache directory for blobless git clones used for size extraction",
    )
    parser.add_argument(
        "--disable-git-tree",
        action="store_true",
        help="Disable git tree exact extraction pass",
    )
    parser.add_argument(
        "--git-timeout-sec",
        type=int,
        default=90,
        help="Timeout per git operation/revision extraction in seconds",
    )
    parser.add_argument(
        "--task-ids-file",
        type=Path,
        help="Optional newline-delimited list of task_id values to limit processing",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes back to selected tasks file",
    )
    args = parser.parse_args()

    data = json.loads(args.selected_tasks.read_text())
    tasks = data.get("tasks", data) if isinstance(data, dict) else data
    task_id_filter: set[str] | None = None
    if args.task_ids_file:
        try:
            lines = [line.strip() for line in args.task_ids_file.read_text().splitlines() if line.strip()]
        except OSError:
            lines = []
        if lines:
            task_id_filter = set(lines)
            print(f"Filtering to {len(task_id_filter)} specified task_ids")

    n_total = 0
    n_ctx = 0
    n_files = 0
    n_ctx_exact = 0
    n_ctx_repo = 0
    n_ctx_proxy = 0
    n_ctx_git = 0
    n_files_exact = 0
    n_files_repo = 0
    n_files_proxy = 0
    n_files_git = 0
    git_cache: dict[tuple[str, str], tuple[int | None, int | None]] = {}

    processed_ids: set[str] = set()
    for t in tasks:
        task_id = t.get("task_id")
        if task_id_filter is not None and task_id not in task_id_filter:
            continue
        if task_id:
            processed_ids.add(task_id)
        n_total += 1
        if n_total % 25 == 0:
            print(f"... processed {n_total}/{len(tasks)} tasks")
        task_dir = args.benchmarks_dir / t.get("task_dir", "")
        toml_path = task_dir / "task.toml"
        repo_dir = task_dir / "environment" / "repo"

        context_length = t.get("context_length")
        files_count = t.get("files_count")
        context_src = t.get("context_length_source")
        files_src = t.get("files_count_source")

        # Proxy values are placeholders; prefer replacing them with stronger sources.
        ctx_is_proxy = context_src == "mcp_breakdown_proxy"
        files_is_proxy = files_src == "mcp_breakdown_proxy"

        # 1) task.toml metadata (exact)
        if toml_path.is_file():
            try:
                d = _read_toml(toml_path)
                meta = d.get("metadata", {}) or {}
            except Exception:
                meta = {}
            ctx_meta = meta.get("context_length")
            files_meta = meta.get("files_count")
            try:
                if ctx_meta is not None and int(ctx_meta) > 0:
                    context_length = int(ctx_meta)
                    context_src = "task_toml_metadata"
            except (TypeError, ValueError):
                pass
            try:
                if files_meta is not None and int(files_meta) > 0:
                    files_count = int(files_meta)
                    files_src = "task_toml_metadata"
            except (TypeError, ValueError):
                pass

        # 2) git tree scan at pinned revision (exact files + byte-based token estimate)
        need_ctx = (not context_length or context_length <= 0 or ctx_is_proxy)
        need_files = (not files_count or files_count <= 0 or files_is_proxy)
        if (need_ctx or need_files) and not args.disable_git_tree:
            repo_ref, rev_ref = _parse_repo_and_rev(task_dir)
            if repo_ref and rev_ref:
                key = (repo_ref, rev_ref)
                if key not in git_cache:
                    git_cache[key] = _git_tree_metrics(repo_ref, rev_ref, args.git_cache_dir, args.git_timeout_sec)
                ctx_git, files_git = git_cache[key]
                if need_ctx and ctx_git is not None:
                    context_length = int(ctx_git)
                    context_src = "git_tree_blob_bytes_div4"
                if need_files and files_git is not None:
                    files_count = int(files_git)
                    files_src = "git_tree_blob_count"

        # 3) environment/repo scan (approximate)
        if (not context_length or context_length <= 0) or (not files_count or files_count <= 0):
            ctx_repo, files_repo = _scan_env_repo(repo_dir)
            if (not context_length or context_length <= 0) and ctx_repo is not None:
                context_length = int(ctx_repo)
                context_src = "env_repo_scan_approx"
            if (not files_count or files_count <= 0) and files_repo is not None:
                files_count = int(files_repo)
                files_src = "env_repo_scan"

        # 4) MCP proxy (estimated)
        if not context_length or context_length <= 0:
            ctx_proxy = _proxy_context_length(t)
            if ctx_proxy is not None:
                context_length = ctx_proxy
                context_src = "mcp_breakdown_proxy"
        if not files_count or files_count <= 0:
            files_proxy = _proxy_files_count(t)
            if files_proxy is not None:
                files_count = files_proxy
                files_src = "mcp_breakdown_proxy"

        if context_length and context_length > 0:
            t["context_length"] = int(context_length)
            t["context_length_source"] = context_src
            n_ctx += 1
            if context_src == "task_toml_metadata":
                n_ctx_exact += 1
            elif context_src == "git_tree_blob_bytes_div4":
                n_ctx_git += 1
            elif context_src == "env_repo_scan_approx":
                n_ctx_repo += 1
            elif context_src == "mcp_breakdown_proxy":
                n_ctx_proxy += 1
        else:
            t["context_length"] = None
            t["context_length_source"] = "unknown"

        if files_count and files_count > 0:
            t["files_count"] = int(files_count)
            t["files_count_source"] = files_src
            n_files += 1
            if files_src == "task_toml_metadata":
                n_files_exact += 1
            elif files_src == "git_tree_blob_count":
                n_files_git += 1
            elif files_src == "env_repo_scan":
                n_files_repo += 1
            elif files_src == "mcp_breakdown_proxy":
                n_files_proxy += 1
        else:
            t["files_count"] = None
            t["files_count_source"] = "unknown"

    print(f"Tasks: {n_total}")
    if task_id_filter is not None:
        missing = task_id_filter - processed_ids
        print(f"Processed {len(processed_ids)} of {len(task_id_filter)} requested task_ids")
        if missing:
            print(f"Missing task_ids: {sorted(missing)}")
    print(
        "context_length populated: "
        f"{n_ctx} (task_toml={n_ctx_exact}, git_tree={n_ctx_git}, repo_scan={n_ctx_repo}, proxy={n_ctx_proxy})"
    )
    print(
        "files_count populated:   "
        f"{n_files} (task_toml={n_files_exact}, git_tree={n_files_git}, repo_scan={n_files_repo}, proxy={n_files_proxy})"
    )

    if args.write:
        if isinstance(data, dict) and "tasks" in data:
            data["tasks"] = tasks
        else:
            data = tasks
        args.selected_tasks.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Wrote {args.selected_tasks}")


if __name__ == "__main__":
    main()
