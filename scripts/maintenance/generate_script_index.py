#!/usr/bin/env python3
"""Generate docs/ops/SCRIPT_INDEX.md from scripts/registry.json."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT / "scripts" / "registry.json"
OUT_PATH = ROOT / "docs" / "ops" / "SCRIPT_INDEX.md"

CATEGORY_TITLES = {
    "core_operations": "Core Operations",
    "analysis_comparison": "Analysis & Comparison",
    "qa_quality": "QA & Quality",
    "data_management": "Data Management",
    "submission_reporting": "Submission & Reporting",
    "task_creation_selection": "Task Creation & Selection",
    "infra_mirrors": "Infra & Mirrors",
    "library_helpers": "Library / Helpers",
    "validation": "Validation",
    "generation": "Generation",
    "migration": "Migration",
    "misc": "Misc",
}

CATEGORY_ORDER = [
    "core_operations",
    "analysis_comparison",
    "qa_quality",
    "data_management",
    "submission_reporting",
    "task_creation_selection",
    "infra_mirrors",
    "library_helpers",
    "validation",
    "generation",
    "migration",
    "misc",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if docs/ops/SCRIPT_INDEX.md is stale")
    args = parser.parse_args()

    if not REGISTRY_PATH.is_file():
        raise SystemExit(f"missing registry: {REGISTRY_PATH}")
    payload = json.loads(REGISTRY_PATH.read_text())
    scripts = payload.get("scripts") or []

    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in scripts:
        grouped[entry.get("category", "misc")].append(entry)

    lines: list[str] = []
    lines.append("# Script Index")
    lines.append("")
    lines.append("Generated from `scripts/registry.json` by `scripts/maintenance/generate_script_index.py`.")
    lines.append("")
    lines.append("## When To Read This")
    lines.append("- You need to find the right script without opening many files.")
    lines.append("- You need to identify maintained vs one-off scripts.")
    lines.append("")
    lines.append("## Do Not Read First If")
    lines.append("- You already know the workflow: use `docs/START_HERE_BY_TASK.md` first.")
    lines.append("- You are working in a single script and only need that file.")
    lines.append("")
    lines.append("## Usage")
    lines.append("- Filter by category first, then open the specific script.")
    lines.append("- Treat `one_off` scripts as historical unless explicitly needed.")
    lines.append("")
    for category in CATEGORY_ORDER:
        entries = sorted(grouped.get(category, []), key=lambda e: e["name"])
        if not entries:
            continue
        title = CATEGORY_TITLES.get(category, category.replace("_", " ").title())
        lines.append(f"## {title}")
        lines.append("")
        for entry in entries:
            status = entry.get("status", "maintained")
            suffix = " [one_off]" if status == "one_off" else ""
            lines.append(f"- `{entry['path']}`{suffix} - {entry.get('summary', '')}")
        lines.append("")

    lines.append("## Regeneration")
    lines.append("```bash")
    lines.append("python3 scripts/maintenance/generate_script_registry.py")
    lines.append("python3 scripts/maintenance/generate_script_index.py")
    lines.append("```")
    lines.append("")

    rendered = "\n".join(lines)
    if args.check:
        if not OUT_PATH.is_file() or OUT_PATH.read_text() != rendered:
            print("Script index: STALE")
            print("  - run: python3 scripts/maintenance/generate_script_index.py")
            return 1
        print("Script index: OK")
        return 0

    OUT_PATH.write_text(rendered)
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
