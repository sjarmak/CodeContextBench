#!/usr/bin/env python3
"""Redact real secrets from text (trajectories, HTML reports, transcripts).

This module is used in two contexts:
  1. As a library — called by export_official_results.py before writing HTML.
  2. As a CLI — to batch-sanitize files already on disk.

Design:
  - Patterns target provider-specific prefixes (sk-ant-, sgp_, ghp_, etc.).
  - An allowlist exempts known fake/test credentials used in benchmark tasks.
  - HTML-entity-encoded variants are handled (e.g. &quot;sk-ant-...&quot;).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Secret patterns — each tuple is (compiled_regex, human_label).
# Patterns are intentionally conservative: they require provider-specific
# prefixes so we don't over-redact random base64 strings.
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Anthropic API keys (sk-ant-api03-..., sk-ant-...)
    (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}"), "ANTHROPIC_KEY"),
    # OpenAI API keys (sk-proj-..., sk-...)  — but NOT "sk_test_" or "sk_live_"
    # which are Stripe keys handled separately below.
    (re.compile(r"sk-proj-[a-zA-Z0-9_\-]{20,}"), "OPENAI_KEY"),
    # Sourcegraph tokens (sgp_<hex>_<hex>)
    (re.compile(r"sgp_[a-f0-9]{10,}_[a-f0-9]{20,}"), "SOURCEGRAPH_TOKEN"),
    # GitHub PATs (ghp_*, gho_*, ghs_*, ghu_*, github_pat_*)
    (re.compile(r"(?:ghp|gho|ghs|ghu)_[a-zA-Z0-9]{30,}"), "GITHUB_TOKEN"),
    (re.compile(r"github_pat_[a-zA-Z0-9_]{30,}"), "GITHUB_TOKEN"),
    # Daytona API keys
    (re.compile(r"dtn_[a-f0-9]{40,}"), "DAYTONA_KEY"),
    # Google API keys (AIzaSy...)
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{30,}"), "GOOGLE_API_KEY"),
    # Sourcegraph OAuth client secrets (sgo_cs_...)
    (re.compile(r"sgo_cs_[a-f0-9]{40,}"), "SG_OAUTH_SECRET"),
    # Grafana service account tokens (glsa_...)
    (re.compile(r"glsa_[a-zA-Z0-9]{20,}_[a-f0-9]{8}"), "GRAFANA_TOKEN"),
]

# ---------------------------------------------------------------------------
# Allowlist — known fake / test credentials embedded in benchmark tasks.
# These are intentional fixtures (e.g. security awareness tasks, locobench
# dummy Stripe keys). Values are substring prefixes that, when matched,
# suppress redaction.
# ---------------------------------------------------------------------------

FAKE_KEY_ALLOWLIST: set[str] = {
    # Locobench dummy Stripe keys (placeholder patterns, not real)
    "sk_test_XXXXXXXXXXXXXXXXXXXXXXXX",
    "sk_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ12345",
    "sk_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ",
    "sk_live_a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    "whsec_XXXXXXXXXXXXXXXXXXXXXXXX",
    # TAC (The Agent Company) internal service tokens — not real external creds
    "root-token",
    "plane_api_83f868352c6f490aba59b869ffdae1cf",
}

# Substrings that, if present anywhere in a matched secret, mark it as
# clearly fake/placeholder regardless of provider prefix.
_FAKE_INDICATORS = ("XXXX", "aBcDeF", "a1b2c3d4", "example", "test_key", "dummy")


def _is_allowlisted(match_text: str) -> bool:
    """Return True if the matched secret is a known fake."""
    if match_text in FAKE_KEY_ALLOWLIST:
        return True
    for indicator in _FAKE_INDICATORS:
        if indicator in match_text:
            return True
    return False


def redact_secrets(text: str) -> str:
    """Replace real secrets in *text* with [REDACTED:<label>] placeholders.

    Safe to call on raw text, HTML source, or JSON strings.
    HTML-entity-encoded quotes (&quot;) adjacent to secrets do not interfere
    because our patterns match only the key characters [a-zA-Z0-9_-].
    """
    for pattern, label in _SECRET_PATTERNS:
        text = pattern.sub(
            lambda m: m.group(0) if _is_allowlisted(m.group(0)) else f"[REDACTED:{label}]",
            text,
        )
    return text


# ---------------------------------------------------------------------------
# CLI: batch-sanitize files on disk
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Redact real secrets from files (HTML reports, trajectories, transcripts).",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to sanitize (directories are walked recursively for .html/.json/.jsonl).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be redacted without modifying files.",
    )
    parser.add_argument(
        "--extensions",
        default=".html,.json,.jsonl,.txt,.md",
        help="Comma-separated file extensions to process (default: .html,.json,.jsonl,.txt,.md).",
    )
    args = parser.parse_args()

    extensions = set(args.extensions.split(","))
    targets: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            for ext in extensions:
                targets.extend(p.rglob(f"*{ext}"))
        else:
            print(f"Warning: {p} not found, skipping", file=sys.stderr)

    total_redactions = 0
    files_modified = 0

    for fpath in sorted(set(targets)):
        try:
            original = fpath.read_text(errors="replace")
        except Exception as e:
            print(f"Warning: cannot read {fpath}: {e}", file=sys.stderr)
            continue

        sanitized = redact_secrets(original)
        if sanitized == original:
            continue

        # Count redactions
        count = sanitized.count("[REDACTED:")
        total_redactions += count
        files_modified += 1

        if args.dry_run:
            print(f"  {fpath}: {count} redaction(s)")
        else:
            fpath.write_text(sanitized)
            print(f"  {fpath}: {count} redaction(s) applied")

    summary = f"\n{'Would redact' if args.dry_run else 'Redacted'} {total_redactions} secret(s) across {files_modified} file(s)."
    print(summary)
    if args.dry_run and total_redactions > 0:
        print("Re-run without --dry-run to apply.")


if __name__ == "__main__":
    _cli()
