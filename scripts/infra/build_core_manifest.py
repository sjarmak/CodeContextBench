#!/usr/bin/env python3
"""Build the canonical 220-task core benchmark manifest.

Selects tasks from the eligible pool using the allocation targets in
CORE_RETRIEVAL_BENCHMARK_SPEC.md, prioritizing core_ready over conditional,
and maximizing LOC band and n_repos diversity within each suite.

Output: configs/core_benchmark_manifest.json
"""

import json
import random
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TASKS_FILE = ROOT / "configs" / "selected_benchmark_tasks.json"
LABELS_FILE = ROOT / "configs" / "verifier_quality_labels.json"
OUTPUT_FILE = ROOT / "configs" / "core_benchmark_manifest.json"

# Target allocation from the spec
SUITE_TARGETS = {
    "csb_org_security": 28,
    "csb_org_incident": 20,
    "csb_org_migration": 22,
    "csb_org_crossrepo_tracing": 18,
    "csb_org_onboarding": 16,
    "csb_org_compliance": 12,
    "csb_org_crossorg": 10,
    "csb_org_domain": 10,
    "csb_org_org": 10,
    "csb_org_crossrepo": 8,
    "csb_org_platform": 6,
    "csb_sdlc_fix": 18,
    "csb_sdlc_understand": 8,
    "csb_sdlc_secure": 6,
    "csb_sdlc_test": 6,
    "csb_sdlc_feature": 6,
    "csb_sdlc_debug": 4,
    "csb_sdlc_design": 4,
    "csb_sdlc_document": 4,
    "csb_sdlc_refactor": 4,
}

TARGET_TOTAL = sum(SUITE_TARGETS.values())  # 220


def loc_band(loc):
    if loc is None:
        return "unknown"
    if loc < 400_000:
        return "<400K"
    if loc < 2_000_000:
        return "400K-2M"
    if loc < 8_000_000:
        return "2M-8M"
    if loc < 40_000_000:
        return "8M-40M"
    return ">40M"


def get_paired_tasks():
    from scripts.extract_v2_report_data import scan_all_tasks

    records = scan_all_tasks()
    by_task = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_task[r["task_name"]][r["config_type"]].append(r["reward"])
    return {task for task, cfg in by_task.items() if "baseline" in cfg and "mcp" in cfg}


def select_from_suite(candidates, target_n):
    """Select target_n tasks from candidates, maximizing diversity."""
    if len(candidates) <= target_n:
        return candidates

    # Prioritize core_ready over conditional
    core_ready = [t for t in candidates if t["_vq"] == "core_ready"]
    conditional = [t for t in candidates if t["_vq"] == "conditional"]

    selected = []

    # First pass: ensure LOC band diversity
    by_band = defaultdict(list)
    for t in candidates:
        by_band[loc_band(t.get("repo_approx_loc"))].append(t)

    # Pick one from each represented band (preferring core_ready)
    for band in ["<400K", "400K-2M", "2M-8M", "8M-40M", ">40M"]:
        band_tasks = by_band.get(band, [])
        if band_tasks and len(selected) < target_n:
            cr = [t for t in band_tasks if t["_vq"] == "core_ready"]
            pick = cr[0] if cr else band_tasks[0]
            selected.append(pick)

    # Ensure multi-repo diversity
    multi_repo = [t for t in candidates if t.get("n_repos", 1) > 1 and t not in selected]
    if multi_repo and len(selected) < target_n:
        cr = [t for t in multi_repo if t["_vq"] == "core_ready"]
        pick = cr[0] if cr else multi_repo[0]
        if pick not in selected:
            selected.append(pick)

    # Fill remaining from core_ready first, then conditional
    remaining_cr = [t for t in core_ready if t not in selected]
    remaining_cond = [t for t in conditional if t not in selected]

    for t in remaining_cr:
        if len(selected) >= target_n:
            break
        selected.append(t)

    for t in remaining_cond:
        if len(selected) >= target_n:
            break
        selected.append(t)

    return selected[:target_n]


def main():
    tasks = json.loads(TASKS_FILE.read_text())["tasks"]
    labels = json.loads(LABELS_FILE.read_text())["labels"]
    paired = get_paired_tasks()

    # Annotate and filter eligible
    by_suite = defaultdict(list)
    for t in tasks:
        tid = t["task_id"]
        vq = labels.get(tid, {}).get("label", "unknown")
        is_paired = tid.lower() in paired
        loc = t.get("repo_approx_loc")
        t["_vq"] = vq
        t["_paired"] = is_paired

        if is_paired and vq in ("core_ready", "conditional") and loc:
            by_suite[t["benchmark"]].append(t)

    # Select per suite
    manifest_tasks = []
    suite_actual = {}
    for suite, target in SUITE_TARGETS.items():
        candidates = by_suite.get(suite, [])
        selected = select_from_suite(candidates, target)
        suite_actual[suite] = len(selected)
        manifest_tasks.extend(selected)

        if len(selected) < target:
            print(f"  WARN: {suite} has {len(selected)}/{target} (pool: {len(candidates)})")

    actual_total = len(manifest_tasks)
    print(f"\nManifest: {actual_total}/{TARGET_TOTAL} tasks")

    # Build clean output (strip internal fields)
    manifest_entries = []
    for t in manifest_tasks:
        manifest_entries.append({
            "task_id": t["task_id"],
            "benchmark": t["benchmark"],
            "repo_approx_loc": t.get("repo_approx_loc"),
            "n_repos": t.get("n_repos", 1),
            "verifier_quality": t["_vq"],
            "loc_band": loc_band(t.get("repo_approx_loc")),
        })

    output = {
        "schema_version": "1.0",
        "description": "Canonical 220-task core benchmark for retrieval impact measurement.",
        "target_total": TARGET_TOTAL,
        "actual_total": actual_total,
        "suite_allocation": {s: {"target": SUITE_TARGETS[s], "actual": suite_actual[s]} for s in SUITE_TARGETS},
        "tasks": manifest_entries,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Written to {OUTPUT_FILE}")

    # Distribution summary
    print(f"\nLOC bands: {Counter(t['loc_band'] for t in manifest_entries)}")
    print(f"n_repos: {Counter(t['n_repos'] for t in manifest_entries)}")
    print(f"VQ: {Counter(t['verifier_quality'] for t in manifest_entries)}")


if __name__ == "__main__":
    main()
