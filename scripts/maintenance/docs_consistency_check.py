#!/usr/bin/env python3
"""Check that core documentation references existing files and valid config keys."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DOCS = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/START_HERE_BY_TASK.md",
    "docs/ops/README.md",
    "docs/ops/ROOT_AGENT_GUIDE.md",
    "docs/ops/WORKFLOWS.md",
    "docs/ops/TROUBLESHOOTING.md",
    "docs/ops/SCRIPT_INDEX.md",
    "docs/CONFIGS.md",
    "docs/QA_PROCESS.md",
    "docs/EXTENSIBILITY.md",
    "docs/REPO_HEALTH.md",
    "docs/reference/README.md",
    "docs/reference/CONFIGS.md",
    "docs/explanations/README.md",
]

REF_PATTERNS = [
    re.compile(r"(scripts/[A-Za-z0-9_./-]+\.py)"),
    re.compile(r"(configs/[A-Za-z0-9_./-]+\.sh)"),
    re.compile(r"(docs/[A-Za-z0-9_./-]+\.md)"),
]

ROOT_AGENT_SOFT_MAX = 8 * 1024
ROOT_AGENT_HARD_MAX = 12 * 1024
LOCAL_AGENT_SOFT_MAX = 6 * 1024
LOCAL_AGENT_TARGET_DIRS = ["scripts", "configs", "docs"]


def _load_matrix() -> dict:
    path = ROOT / "configs" / "eval_matrix.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def _extract_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for pat in REF_PATTERNS:
        refs.update(pat.findall(text))
    return refs


def _check_agent_guides(errors: list[str], warnings: list[str]) -> None:
    root_agents = ROOT / "AGENTS.md"
    root_claude = ROOT / "CLAUDE.md"
    if root_agents.is_file() and root_claude.is_file():
        a_text = root_agents.read_text(errors="replace")
        c_text = root_claude.read_text(errors="replace")
        if a_text != c_text:
            errors.append("agent_guides_drift:AGENTS.md!=CLAUDE.md")
        a_size = root_agents.stat().st_size
        if a_size > ROOT_AGENT_HARD_MAX:
            errors.append(f"agent_guide_root_too_large:{a_size}>{ROOT_AGENT_HARD_MAX}")
        elif a_size > ROOT_AGENT_SOFT_MAX:
            warnings.append(f"agent_guide_root_over_budget:{a_size}>{ROOT_AGENT_SOFT_MAX}")

    for rel_dir in LOCAL_AGENT_TARGET_DIRS:
        d = ROOT / rel_dir
        a = d / "AGENTS.md"
        c = d / "CLAUDE.md"
        if not a.is_file() or not c.is_file():
            errors.append(f"agent_guide_local_missing:{rel_dir}")
            continue
        a_text = a.read_text(errors="replace")
        c_text = c.read_text(errors="replace")
        if a_text != c_text:
            errors.append(f"agent_guide_local_drift:{rel_dir}")
        size = a.stat().st_size
        if size > LOCAL_AGENT_SOFT_MAX:
            warnings.append(f"agent_guide_local_over_budget:{rel_dir}:{size}>{LOCAL_AGENT_SOFT_MAX}")


def _check_script_registry(errors: list[str], warnings: list[str]) -> None:
    registry_path = ROOT / "scripts" / "registry.json"
    index_path = ROOT / "docs" / "ops" / "SCRIPT_INDEX.md"
    if not registry_path.is_file():
        errors.append("script_registry_missing:scripts/registry.json")
        return
    try:
        payload = json.loads(registry_path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"script_registry_invalid_json:{exc}")
        return

    registry_scripts = payload.get("scripts")
    if not isinstance(registry_scripts, list):
        errors.append("script_registry_missing_scripts_list")
        return

    listed = set()
    for item in registry_scripts:
        if not isinstance(item, dict):
            errors.append("script_registry_invalid_entry_type")
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path.startswith("scripts/"):
            errors.append(f"script_registry_invalid_path:{path!r}")
            continue
        listed.add(path.split("/", 1)[1])

    actual = {
        p.relative_to(ROOT / "scripts").as_posix()
        for p in (ROOT / "scripts").rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".sh"}
        and p.name != "registry.json"
        and not p.name.endswith(".pyc")
    }
    missing = sorted(actual - listed)
    extra = sorted(listed - actual)
    if missing:
        errors.append(f"script_registry_missing_entries:{','.join(missing[:10])}")
    if extra:
        errors.append(f"script_registry_extra_entries:{','.join(extra[:10])}")

    if not index_path.is_file():
        errors.append("script_index_missing:docs/ops/SCRIPT_INDEX.md")
        return
    index_text = index_path.read_text(errors="replace")
    if "Generated from `scripts/registry.json`" not in index_text:
        errors.append("script_index_missing_generated_marker")
    # Spot-check that the generated index references the current registry size.
    if len(registry_scripts) > 0 and "`scripts/" not in index_text:
        warnings.append("script_index_suspicious_no_script_entries")


def _check_generated_agent_nav(errors: list[str]) -> None:
    cmd = [sys.executable, str(ROOT / "scripts" / "maintenance" / "refresh_agent_navigation.py"), "--check"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        return
    errors.append("generated_agent_navigation_stale")
    for line in (result.stdout or "").strip().splitlines()[:6]:
        if line:
            errors.append(f"generated_agent_navigation_detail:{line}")


def _scan_all_docs_refs(errors: list[str], warnings: list[str]) -> None:
    seen: set[tuple[str, str]] = set()
    for p in sorted((ROOT / "docs").rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        refs = _extract_refs(p.read_text(errors="replace"))
        for ref in sorted(refs):
            key = (rel, ref)
            if key in seen:
                continue
            seen.add(key)
            if (ROOT / ref).exists():
                continue
            # Archive docs are scanned to detect drift but only warn to avoid
            # blocking merges on historical materials.
            if rel.startswith("docs/archive/"):
                warnings.append(f"missing_ref_archive:{rel}:{ref}")
            else:
                errors.append(f"missing_ref_all_docs:{rel}:{ref}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs",
        nargs="*",
        default=DEFAULT_DOCS,
        help="Docs to scan (default: core docs)",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    for rel in args.docs:
        p = ROOT / rel
        if not p.is_file():
            errors.append(f"doc_missing:{rel}")
            continue
        refs = _extract_refs(p.read_text(errors="replace"))
        for ref in sorted(refs):
            if not (ROOT / ref).exists():
                errors.append(f"missing_ref:{rel}:{ref}")

    matrix = _load_matrix()
    if matrix:
        supported = matrix.get("supported_configs") or []
        defaults = matrix.get("official_default_configs") or []
        if not isinstance(supported, list) or not all(isinstance(x, str) for x in supported):
            errors.append("eval_matrix_invalid_supported_configs")
        if not isinstance(defaults, list) or not all(isinstance(x, str) for x in defaults):
            errors.append("eval_matrix_invalid_official_default_configs")
        if isinstance(supported, list) and isinstance(defaults, list):
            missing = [x for x in defaults if x not in supported]
            if missing:
                errors.append(f"eval_matrix_defaults_not_supported:{','.join(missing)}")
        defs = matrix.get("config_definitions") or {}
        if not isinstance(defs, dict):
            errors.append("eval_matrix_invalid_config_definitions")
        else:
            for cfg in supported:
                if cfg not in defs:
                    warnings.append(f"eval_matrix_missing_definition:{cfg}")

    _check_agent_guides(errors, warnings)
    _check_script_registry(errors, warnings)
    _check_generated_agent_nav(errors)
    _scan_all_docs_refs(errors, warnings)

    if errors:
        print("Docs consistency: FAILED")
        for err in errors:
            print(f"  - {err}")
    else:
        print("Docs consistency: OK")
    if warnings:
        print("Warnings:")
        for warn in warnings:
            print(f"  - {warn}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
