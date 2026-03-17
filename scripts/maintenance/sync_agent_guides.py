#!/usr/bin/env python3
"""Generate root and local AGENTS.md/CLAUDE.md mirrors from canonical sources."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

ROOT_SOURCE = ROOT / "docs" / "ops" / "ROOT_AGENT_GUIDE.md"
LOCAL_SOURCES = {
    ROOT / "scripts": ROOT / "docs" / "ops" / "local_guides" / "scripts.md",
    ROOT / "configs": ROOT / "docs" / "ops" / "local_guides" / "configs.md",
    ROOT / "docs": ROOT / "docs" / "ops" / "local_guides" / "docs.md",
}


def _write_pair(target_dir: Path, content: str) -> None:
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = target_dir / name
        path.write_text(content)


def _check_pair(target_dir: Path, content: str, stale: list[str]) -> None:
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = target_dir / name
        if not path.is_file():
            stale.append(f"missing:{path.relative_to(ROOT)}")
            continue
        if path.read_text() != content:
            stale.append(f"stale:{path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated guides are stale")
    args = parser.parse_args()

    if not ROOT_SOURCE.is_file():
        raise SystemExit(f"missing source: {ROOT_SOURCE}")

    root_content = ROOT_SOURCE.read_text()
    stale: list[str] = []
    if args.check:
        _check_pair(ROOT, root_content, stale)
    else:
        _write_pair(ROOT, root_content)

    for target_dir, source in LOCAL_SOURCES.items():
        if not source.is_file():
            raise SystemExit(f"missing local source: {source}")
        if not target_dir.is_dir():
            # Skip directories that don't exist (e.g. tasks/ was removed)
            continue
        content = source.read_text()
        if args.check:
            _check_pair(target_dir, content, stale)
        else:
            _write_pair(target_dir, content)

    if args.check:
        if stale:
            print("Agent guides: STALE")
            for item in stale:
                print(f"  - {item}")
            return 1
        print("Agent guides: OK")
        return 0

    print("Synced root and local AGENTS.md/CLAUDE.md guides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
