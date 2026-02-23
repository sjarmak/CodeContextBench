#!/usr/bin/env python3
"""Register 20 new MCP-unique tasks in both selection files."""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_USE_CASE_IDS = [2, 3, 12, 13, 22, 26, 32, 33, 43, 44, 52, 53, 62, 71, 72, 73, 74, 81, 82, 83]

# Language map from repo_set_id
LANG_MAP = {
    "apache-kafka-ecosystem": "java",
    "envoy-service-mesh": "cpp",
    "rust-systems": "rust",
    "kubernetes-ecosystem": "go",
}

# Primary repo for each repo set (used as "repo" field in selection files)
PRIMARY_REPO = {
    "apache-kafka-ecosystem": "apache/kafka",
    "envoy-service-mesh": "envoyproxy/envoy",
    "rust-systems": "rust-lang/rust",
    "kubernetes-ecosystem": "kubernetes/kubernetes",
}


def load_registry():
    path = os.path.join(PROJECT_ROOT, "configs/use_case_registry.json")
    with open(path) as f:
        return json.load(f)


def find_task_dir_and_id(uc_id, uc_entry):
    """Find task directory and task_id from disk."""
    suite = uc_entry["mcp_suite"]
    suite_dir = os.path.join(PROJECT_ROOT, "benchmarks", suite)
    if not os.path.isdir(suite_dir):
        return None, None

    for entry in os.listdir(suite_dir):
        toml_path = os.path.join(suite_dir, entry, "task.toml")
        if os.path.isfile(toml_path):
            with open(toml_path) as f:
                content = f.read()
            if f"use_case_id = {uc_id}" in content:
                # Extract task ID from toml
                for line in content.splitlines():
                    if line.strip().startswith("id = "):
                        tid = line.split('"')[1]
                        return f"{suite}/{entry}", tid
                return f"{suite}/{entry}", entry.upper()
    return None, None


def main():
    registry = load_registry()
    uc_map = {uc["use_case_id"]: uc for uc in registry["use_cases"]}

    # ---- Update selected_mcp_unique_tasks.json ----
    mcp_path = os.path.join(PROJECT_ROOT, "configs/selected_mcp_unique_tasks.json")
    with open(mcp_path) as f:
        mcp_data = json.load(f)

    existing_uc_ids = {t["use_case_id"] for t in mcp_data["tasks"]}
    new_mcp_entries = []

    for uc_id in NEW_USE_CASE_IDS:
        if uc_id in existing_uc_ids:
            print(f"  UC {uc_id}: already in selected_mcp_unique_tasks.json, skipping")
            continue

        uc = uc_map[uc_id]
        repo_set = uc["repo_set_id"]
        task_dir, task_id = find_task_dir_and_id(uc_id, uc)
        if not task_dir:
            print(f"  UC {uc_id}: ERROR - task directory not found")
            continue

        entry = {
            "task_id": task_id,
            "mcp_suite": uc["mcp_suite"],
            "use_case_category": uc["category"],
            "use_case_id": uc_id,
            "language": LANG_MAP.get(repo_set, "mixed"),
            "difficulty": uc["difficulty"],
            "repo": PRIMARY_REPO.get(repo_set, "unknown"),
            "mcp_benefit_score": 0.85,
            "task_dir": task_dir,
            "deepsearch_relevant": "deepsearch" in uc.get("mcp_capabilities_required", []),
            "oracle_check_types": uc["oracle_check_types"],
            "repo_set_id": repo_set,
        }
        new_mcp_entries.append(entry)
        print(f"  UC {uc_id}: {task_id} -> {task_dir}")

    mcp_data["tasks"].extend(new_mcp_entries)
    with open(mcp_path, "w") as f:
        json.dump(mcp_data, f, indent=2)
        f.write("\n")
    print(f"\nselected_mcp_unique_tasks.json: {len(mcp_data['tasks'])} total tasks")

    # ---- Update selected_benchmark_tasks.json ----
    bench_path = os.path.join(PROJECT_ROOT, "configs/selected_benchmark_tasks.json")
    with open(bench_path) as f:
        bench_data = json.load(f)

    existing_bench_ids = set()
    for t in bench_data["tasks"]:
        if t.get("mcp_unique"):
            existing_bench_ids.add(t.get("task_id", ""))

    new_bench_entries = []
    for uc_id in NEW_USE_CASE_IDS:
        uc = uc_map[uc_id]
        repo_set = uc["repo_set_id"]
        task_dir, task_id = find_task_dir_and_id(uc_id, uc)
        if not task_dir:
            continue

        if task_id in existing_bench_ids:
            print(f"  {task_id}: already in selected_benchmark_tasks.json, skipping")
            continue

        entry = {
            "task_id": task_id,
            "benchmark": uc["mcp_suite"],
            "task_dir": task_dir,
            "mcp_unique": True,
            "mcp_suite": uc["mcp_suite"],
            "mcp_benefit_score": 1.0,
            "context_length": 0,
            "context_length_source": "mcp_unique_artifact",
        }
        new_bench_entries.append(entry)

    bench_data["tasks"].extend(new_bench_entries)

    # Update metadata
    total = len(bench_data["tasks"])
    bench_data["metadata"]["total_selected"] = total
    bench_data["metadata"]["target_total"] = total
    bench_data["metadata"]["last_updated"] = "2026-02-23"
    bench_data["metadata"]["target_note"] = (
        f"All SDLC suites at target + 40 MCP-unique tasks across 10 ccb_mcp_* suites."
    )
    bench_data["metadata"]["note"] = (
        "Added 20 new MCP-unique tasks (categories H: domain, I: agentic). "
        "Expanded from 190 to 210 total. New repo sets: apache-kafka-ecosystem, "
        "envoy-service-mesh, rust-systems."
    )

    # Update mcp_unique_suites list
    bench_data["methodology"]["mcp_unique_suites"] = sorted(set(
        bench_data["methodology"].get("mcp_unique_suites", [])
        + ["ccb_mcp_domain", "ccb_mcp_org"]
    ))

    # Update statistics
    stats = {}
    for t in bench_data["tasks"]:
        bm = t.get("benchmark", "")
        stats[bm] = stats.get(bm, 0) + 1
    bench_data["statistics"]["tasks_per_benchmark"] = dict(sorted(stats.items()))

    with open(bench_path, "w") as f:
        json.dump(bench_data, f, indent=2)
        f.write("\n")
    print(f"selected_benchmark_tasks.json: {total} total tasks")

    return 0


if __name__ == "__main__":
    sys.exit(main())
