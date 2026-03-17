#!/usr/bin/env python3
"""Generate task_spec.json from ground_truth.json for tasks that lack one.

Reads ground_truth.json (various schemas) and produces task_spec.json in the
format that oracle_checks.py + dual_score_lib.sh expect:

  {
    "id": "<task_id>",
    "artifacts": {
      "oracle": {
        "required_files": [{"repo": "...", "path": "..."}],
        "required_symbols": [{"symbol": "...", "file": "..."}],
        "required_references": [],
        "dependency_chains": [{"steps": [...]}]
      }
    },
    "evaluation": {
      "checks": [
        {"type": "file_set_match", "params": {}},
        {"type": "keyword_presence", "params": {"required_keywords": [...]}}
      ]
    }
  }

Handles 23+ ground_truth.json schemas found across SDLC tasks.

Usage:
    python3 scripts/generate_task_specs_from_gt.py [--dry-run]
    python3 scripts/generate_task_specs_from_gt.py --suite feature
    python3 scripts/generate_task_specs_from_gt.py --task-id django-rate-limit-middleware-feat-001
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARKS_DIR = os.path.join(PROJECT_ROOT, "benchmarks", "csb")


def _normalize_file_entry(entry) -> Dict[str, str]:
    """Convert a file entry to {"repo": ..., "path": ...} dict format."""
    if isinstance(entry, dict):
        # Already has repo/path structure
        if "repo" in entry and "path" in entry:
            return {"repo": entry["repo"], "path": entry["path"]}
        # Has just "file" key
        if "file" in entry:
            return {"repo": "", "path": entry["file"]}
        return {"repo": "", "path": str(entry)}
    if isinstance(entry, str):
        s = entry
        if s.startswith("github.com/"):
            s = s[len("github.com/"):]
        parts = s.split("/", 2)
        # Only split into repo/path if it looks like an org/repo prefix
        # (contains -- hash suffix typical of sg-evals mirrors)
        if len(parts) >= 3 and "--" in parts[1]:
            return {"repo": f"{parts[0]}/{parts[1]}", "path": parts[2]}
        # Otherwise treat as a workspace-relative path (SDLC tasks)
        return {"repo": "", "path": s}
    return {"repo": "", "path": str(entry)}


def _normalize_symbol_entry(entry) -> Dict[str, str]:
    """Convert a symbol entry to {"symbol": ..., "file": ...} dict format."""
    if isinstance(entry, dict):
        return {
            "symbol": entry.get("symbol", entry.get("name", entry.get("canonical_name", ""))),
            "file": entry.get("file", entry.get("path", entry.get("canonical_path", ""))),
        }
    if isinstance(entry, str):
        return {"symbol": entry, "file": ""}
    return {"symbol": str(entry), "file": ""}


def extract_files(gt: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract file list from any GT schema."""
    files = []

    # Direct file lists
    for key in ("files", "expected_files", "buggy_files", "root_cause_files",
                "expected_edit_files", "file_references"):
        raw = gt.get(key, [])
        if isinstance(raw, list):
            for entry in raw:
                normalized = _normalize_file_entry(entry)
                if normalized["path"] and normalized not in files:
                    files.append(normalized)

    # onboard-search tasks: canonical_path
    if "canonical_path" in gt:
        entry = {"repo": "", "path": gt["canonical_path"]}
        if entry not in files:
            files.append(entry)

    # entries list (envoy-grpc style)
    for entry in gt.get("entries", []):
        if isinstance(entry, dict) and entry.get("file"):
            normalized = _normalize_file_entry(entry["file"])
            if normalized not in files:
                files.append(normalized)

    # Dependency chain steps may contain file paths
    for step in gt.get("dependency_chain", []):
        if isinstance(step, dict) and step.get("path"):
            normalized = _normalize_file_entry(step)
            if normalized not in files:
                files.append(normalized)

    # data_flow entries
    for entry in gt.get("data_flow", []):
        if isinstance(entry, dict) and entry.get("file"):
            normalized = _normalize_file_entry(entry["file"])
            if normalized not in files:
                files.append(normalized)

    # entry_points
    for entry in gt.get("entry_points", []):
        if isinstance(entry, dict) and entry.get("file"):
            normalized = _normalize_file_entry(entry["file"])
            if normalized not in files:
                files.append(normalized)

    return files


def extract_symbols(gt: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract symbol list from any GT schema."""
    symbols = []

    # Direct symbols list
    for entry in gt.get("symbols", []):
        normalized = _normalize_symbol_entry(entry)
        if normalized["symbol"] and normalized not in symbols:
            symbols.append(normalized)

    # buggy_functions
    for entry in gt.get("buggy_functions", []):
        normalized = _normalize_symbol_entry(entry)
        if normalized["symbol"] and normalized not in symbols:
            symbols.append(normalized)

    # onboard-search: canonical_name
    if "canonical_name" in gt:
        entry = {"symbol": gt["canonical_name"], "file": gt.get("canonical_path", "")}
        if entry not in symbols:
            symbols.append(entry)

    # old_symbol/new_symbol (refactor tasks)
    for key in ("old_symbol", "new_symbol"):
        if gt.get(key):
            entry = {"symbol": gt[key], "file": ""}
            if entry not in symbols:
                symbols.append(entry)

    # entries with key_fields
    for entry in gt.get("entries", []):
        if isinstance(entry, dict):
            for kf in gt.get("key_fields", []):
                val = entry.get(kf)
                if val and isinstance(val, str):
                    sym = {"symbol": val, "file": entry.get("file", "")}
                    if sym not in symbols:
                        symbols.append(sym)

    return symbols


def extract_keywords(gt: Dict[str, Any], symbols: List[Dict[str, str]]) -> List[str]:
    """Extract keyword list from any GT schema."""
    keywords = []

    # expected_keywords
    for kw in gt.get("expected_keywords", []):
        if isinstance(kw, str) and kw not in keywords:
            keywords.append(kw)

    # required_topics (document tasks) — may have "topic", "description", or "patterns"
    for topic in gt.get("required_topics", []):
        if isinstance(topic, dict):
            kw = topic.get("topic") or topic.get("description", "")
            if kw and kw not in keywords:
                keywords.append(kw)
            # Also extract patterns as keywords
            for pat in topic.get("patterns", []):
                if isinstance(pat, str) and pat not in keywords:
                    keywords.append(pat)
        elif isinstance(topic, str) and topic not in keywords:
            keywords.append(topic)

    # required_findings (understand tasks) — may have "finding" or "description"
    for finding in gt.get("required_findings", []):
        if isinstance(finding, dict):
            kw = finding.get("finding") or finding.get("description", "")
            if kw and kw not in keywords:
                keywords.append(kw)
        elif isinstance(finding, str) and finding not in keywords:
            keywords.append(finding)

    # thread_safety, performance_notes, cross_references, extension_points (doc tasks)
    for key in ("thread_safety", "performance_notes", "cross_references", "extension_points"):
        for item in gt.get(key, []):
            if isinstance(item, str) and item not in keywords:
                keywords.append(item)
            elif isinstance(item, dict):
                kw = item.get("description") or item.get("name", "")
                if kw and kw not in keywords:
                    keywords.append(kw)

    # Symbol names as keywords
    for sym in symbols:
        name = sym.get("symbol", "")
        if name and name not in keywords:
            keywords.append(name)

    # text field — extract key sentences (short ones only)
    text = gt.get("text", "")
    if isinstance(text, str) and text:
        # Don't add full text as keyword, but add short phrases if reasonable
        pass

    # scoring_categories keys (document tasks)
    for cat_name in gt.get("scoring_categories", {}).keys():
        if isinstance(cat_name, str) and cat_name not in keywords:
            keywords.append(cat_name)

    return keywords


def extract_chains(gt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract dependency chains from any GT schema."""
    chains = []

    raw_chain = gt.get("dependency_chain", [])
    if raw_chain:
        chains.append({"steps": raw_chain})

    # causal_chain (understand tasks)
    raw_causal = gt.get("causal_chain", [])
    if raw_causal:
        chains.append({"steps": raw_causal})

    # data_flow as a chain
    raw_flow = gt.get("data_flow", [])
    if raw_flow:
        chains.append({"steps": raw_flow})

    return chains


def generate_task_spec(task_id: str, gt: Dict[str, Any]) -> Dict[str, Any]:
    """Generate task_spec.json content from ground_truth.json data."""
    files = extract_files(gt)
    symbols = extract_symbols(gt)
    keywords = extract_keywords(gt, symbols)
    chains = extract_chains(gt)

    # Build evaluation checks based on available data
    checks = []
    if files:
        checks.append({"type": "file_set_match", "params": {}})
    if symbols:
        checks.append({"type": "symbol_resolution", "params": {}})
    if chains:
        checks.append({"type": "dependency_chain", "params": {}})
    if keywords:
        checks.append({
            "type": "keyword_presence",
            "params": {"required_keywords": keywords},
        })

    spec = {
        "id": task_id,
        "artifacts": {
            "oracle": {
                "required_files": files,
                "required_symbols": symbols,
                "required_references": [],
                "dependency_chains": chains,
            }
        },
        "evaluation": {
            "checks": checks,
        },
    }

    return spec


def process_task(suite: str, task_name: str, dry_run: bool) -> str:
    """Process one task. Returns status string."""
    task_dir = os.path.join(BENCHMARKS_DIR, suite, task_name)
    tests_dir = os.path.join(task_dir, "tests")
    spec_path = os.path.join(tests_dir, "task_spec.json")
    gt_path = os.path.join(tests_dir, "ground_truth.json")

    if os.path.isfile(spec_path):
        return f"SKIP (exists) {suite}/{task_name}"

    if not os.path.isfile(gt_path):
        return f"SKIP (no GT) {suite}/{task_name}"

    with open(gt_path) as f:
        gt = json.load(f)

    # Read task_id from task.toml or ground_truth
    task_id = gt.get("task_id", task_name)

    spec = generate_task_spec(task_id, gt)
    files = spec["artifacts"]["oracle"]["required_files"]
    symbols = spec["artifacts"]["oracle"]["required_symbols"]
    chains = spec["artifacts"]["oracle"]["dependency_chains"]
    checks = spec["evaluation"]["checks"]
    kw_count = 0
    for c in checks:
        if c["type"] == "keyword_presence":
            kw_count = len(c["params"].get("required_keywords", []))

    summary_parts = []
    if files:
        summary_parts.append(f"{len(files)}F")
    if symbols:
        summary_parts.append(f"{len(symbols)}S")
    if chains:
        summary_parts.append(f"{len(chains)}C")
    if kw_count:
        summary_parts.append(f"{kw_count}K")
    summary_parts.append(f"{len(checks)}chk")
    summary = " ".join(summary_parts)

    if dry_run:
        return f"DRY-RUN {suite}/{task_name}: {summary}"

    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")

    return f"OK {suite}/{task_name}: {summary}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate task_spec.json from ground_truth.json for tasks missing one"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--suite", help="Only process this suite")
    parser.add_argument("--task-id", help="Only process this specific task")
    args = parser.parse_args()

    suites = sorted(d for d in os.listdir(BENCHMARKS_DIR)
                    if os.path.isdir(os.path.join(BENCHMARKS_DIR, d)))

    if args.suite:
        suites = [s for s in suites if s == args.suite]
        if not suites:
            print(f"ERROR: suite '{args.suite}' not found")
            return 1

    ok = 0
    skip_exists = 0
    skip_no_gt = 0
    generated = 0

    for suite in suites:
        suite_dir = os.path.join(BENCHMARKS_DIR, suite)
        tasks = sorted(d for d in os.listdir(suite_dir)
                       if os.path.isdir(os.path.join(suite_dir, d)))

        if args.task_id:
            tasks = [t for t in tasks if t == args.task_id]

        for task_name in tasks:
            status = process_task(suite, task_name, args.dry_run)
            if status.startswith("SKIP (exists)"):
                skip_exists += 1
            elif status.startswith("SKIP (no GT)"):
                skip_no_gt += 1
                print(f"  {status}")
            elif status.startswith("OK") or status.startswith("DRY-RUN"):
                generated += 1
                print(f"  {status}")

    print(f"\nDone: {generated} generated, {skip_exists} already exist, {skip_no_gt} no GT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
