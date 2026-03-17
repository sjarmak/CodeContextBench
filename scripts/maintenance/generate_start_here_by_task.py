#!/usr/bin/env python3
"""Generate docs/START_HERE_BY_TASK.md from docs/ops/task_routes.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ROUTES_PATH = ROOT / "docs" / "ops" / "task_routes.json"
OUT_PATH = ROOT / "docs" / "START_HERE_BY_TASK.md"


def render(payload: dict) -> str:
    title = payload.get("title", "Start Here By Task")
    intro = payload.get("intro", "Use this page first for operational work.")
    routes = payload.get("routes") or []
    if not isinstance(routes, list):
        raise SystemExit("docs/ops/task_routes.json: 'routes' must be a list")

    lines: list[str] = [f"# {title}", "", intro, ""]

    for route in routes:
        if not isinstance(route, dict):
            raise SystemExit("docs/ops/task_routes.json: route entries must be objects")
        name = route.get("name")
        when = route.get("when")
        read_order = route.get("read_order") or []
        commands = route.get("commands") or []
        if not isinstance(name, str) or not isinstance(when, str):
            raise SystemExit("docs/ops/task_routes.json: route must include string 'name' and 'when'")
        if not all(isinstance(x, str) for x in read_order):
            raise SystemExit(f"route '{name}': read_order must be strings")
        if not all(isinstance(x, str) for x in commands):
            raise SystemExit(f"route '{name}': commands must be strings")

        lines.append(f"## {name}")
        lines.append("### When To Read This")
        lines.append(f"- {when}")
        lines.append("")
        lines.append("### Read Order")
        for i, doc in enumerate(read_order, start=1):
            lines.append(f"{i}. `{doc}`")
        lines.append("")
        if commands:
            lines.append("### Key Commands")
            lines.append("```bash")
            lines.extend(commands)
            lines.append("```")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if docs/START_HERE_BY_TASK.md is stale")
    args = parser.parse_args()

    if not ROUTES_PATH.is_file():
        raise SystemExit(f"missing routes manifest: {ROUTES_PATH}")
    payload = json.loads(ROUTES_PATH.read_text())
    rendered = render(payload)

    if args.check:
        if not OUT_PATH.is_file() or OUT_PATH.read_text() != rendered:
            print("Start-here routes doc: STALE")
            print("  - run: python3 scripts/generate_start_here_by_task.py")
            return 1
        print("Start-here routes doc: OK")
        return 0

    OUT_PATH.write_text(rendered)
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
