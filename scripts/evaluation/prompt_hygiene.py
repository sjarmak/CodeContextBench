#!/usr/bin/env python3
"""Audit and scrub instruction prompts for location and solution leakage."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SELECTED_TASKS_PATH = REPO_ROOT / "configs" / "selected_benchmark_tasks.json"

ALLOWED_TOKENS = {
    "/workspace",
    "/workspace/",
    "/workspace/answer.json",
    "/workspace/review.json",
    "/workspace/regression_test.py",
    "/logs/agent/onboarding.md",
    "/logs/agent/solution.md",
    "TASK_OUTPUT",
    "TASK_WORKDIR=/workspace",
    "TASK_REPO_ROOT=/workspace",
    "TASK_OUTPUT=/workspace/answer.json",
    "answer.json",
    "review.json",
    "regression_test.py",
    "--- a/",
    "+++ b/",
}
ALLOWED_PREFIXES = ("/workspace/", "/logs/agent/", "TASK_WORKDIR=", "TASK_REPO_ROOT=", "TASK_OUTPUT=")
PATH_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt", ".rb", ".rs",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".scala",
    ".sh", ".yaml", ".yml", ".json", ".toml", ".sql", ".proto", ".xml",
    ".html", ".css", ".md",
)
SECTION_TITLES_TO_DROP = (
    "## Key Components",
    "## Key Reference Files",
    "## What to Find",
    "## Evaluation",
    "## Testing",
)
SOLUTION_LINE_PATTERNS = [
    re.compile(r"\bBefore calling `[^`]+`, use `[^`]+`", re.I),
    re.compile(r"\bReplace the brute-force\b", re.I),
    re.compile(r"\bAdd a new `[^`]+` method\b", re.I),
    re.compile(r"\bThe check uses `[^`]+`", re.I),
    re.compile(r"\binstead of reconstructing from a flattened string\b", re.I),
    re.compile(r"\breject images exceeding \d+\s*megapixels\b", re.I),
    re.compile(r"\bImages exceeding \d+\s*MP\b", re.I),
]
SCORING_LINE_PATTERNS = [
    re.compile(r"\bground-truth diff\b", re.I),
    re.compile(r"\bclosed-world oracle\b", re.I),
    re.compile(r"\bAll \d+ modified files updated correctly\b", re.I),
    re.compile(r"\bThe verifier will compare\b", re.I),
    re.compile(r"\bScore\s*=", re.I),
    re.compile(r"\bmatch the expected fix\b", re.I),
]
BACKTICK_TOKEN_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^##\s+", re.M)
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FILE_TOKEN_RE = re.compile(r"(^|/)[^/`\n]+\.[A-Za-z0-9]+$")
DIR_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.()\-]+(?:/[A-Za-z0-9_.()\-]+)+/?$")
MODULE_TOKEN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}$")


@dataclass
class Finding:
    file: str
    issue_type: str
    line: int
    value: str


def _load_selected_task_instruction_paths(include_mcp: bool) -> list[Path]:
    data = json.loads(SELECTED_TASKS_PATH.read_text())
    paths: list[Path] = []
    for task in data["tasks"]:
        task_dir = REPO_ROOT / "benchmarks" / task["task_dir"]
        paths.append(task_dir / "instruction.md")
        if include_mcp:
            mcp_path = task_dir / "instruction_mcp.md"
            if mcp_path.exists():
                paths.append(mcp_path)
    return paths


def _scan_instruction_paths(root: Path, include_mcp: bool) -> list[Path]:
    names = {"instruction.md"}
    if include_mcp:
        names.add("instruction_mcp.md")
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name in names)


def _load_git_modified_instruction_paths(include_mcp: bool) -> list[Path]:
    names = {"instruction.md"}
    if include_mcp:
        names.add("instruction_mcp.md")

    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if len(raw_line) < 4:
            continue
        raw_path = raw_line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        path = (REPO_ROOT / raw_path).resolve()
        if path.name in names and path.is_file():
            paths.append(path)
    return sorted(dict.fromkeys(paths))


def _is_allowed_token(token: str) -> bool:
    return token in ALLOWED_TOKENS or token.startswith(ALLOWED_PREFIXES)


def _is_path_like_token(token: str) -> bool:
    if _is_allowed_token(token):
        return False
    if token.startswith("http://") or token.startswith("https://"):
        return False
    if FILE_TOKEN_RE.search(token) and token.endswith(PATH_EXTENSIONS):
        return True
    if DIR_TOKEN_RE.match(token):
        return True
    if MODULE_TOKEN_RE.match(token):
        return True
    return False


def _replacement_for_token(token: str) -> str:
    if REPO_RE.match(token):
        return "the repository"
    if MODULE_TOKEN_RE.match(token):
        return "the relevant module"
    if FILE_TOKEN_RE.search(token) and token.endswith(PATH_EXTENSIONS):
        return "the relevant file"
    return "the relevant code area"


def find_prompt_findings(text: str, file_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in BACKTICK_TOKEN_RE.finditer(line):
            token = match.group(1).strip()
            if _is_path_like_token(token):
                findings.append(Finding(str(file_path), "code_location_hint", line_no, token))
        for pattern in SOLUTION_LINE_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(str(file_path), "solution_leakage", line_no, line.strip()))
                break
        for pattern in SCORING_LINE_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(str(file_path), "scoring_leakage", line_no, line.strip()))
                break
    return findings


def _drop_sections(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        if line.strip() in SECTION_TITLES_TO_DROP:
            skip = True
            continue
        if skip and line.startswith("## "):
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _sanitize_line(line: str) -> str:
    line = _rewrite_leaky_line(line)
    if line == "":
        return ""
    if any(pattern.search(line) for pattern in SCORING_LINE_PATTERNS):
        return ""
    if line.strip() == "Changes:":
        return ""
    if re.match(r"^\s*-\s+\d+\s+files modified", line):
        return ""
    line = re.sub(r"\s*\((?:look|search|check|find)\s+in\s+`[^`]+`\)", "", line, flags=re.I)
    line = re.sub(r"\s*\((?:under|in|within)\s+`[^`]+`\)", "", line, flags=re.I)
    line = re.sub(r"\s+(?:under|inside|within|in|from)\s+`([^`]+)`", lambda m: "" if _is_path_like_token(m.group(1)) else m.group(0), line)
    line = re.sub(r"`([^`\n]+)`", lambda m: _replacement_for_token(m.group(1)) if _is_path_like_token(m.group(1)) else m.group(0), line)
    indent_match = re.match(r"^(\s*)(.*)$", line)
    indent = indent_match.group(1)
    body = indent_match.group(2)
    body = re.sub(r"\s{2,}", " ", body).rstrip()
    body = body.replace(" ()", "")
    body = body.replace(" : ", ": ")
    return indent + body


def _rewrite_leaky_line(line: str) -> str:
    prefix_match = re.match(r"^(\s*(?:\d+\.\s+|-\s+))", line)
    prefix = prefix_match.group(1) if prefix_match else ""
    body = line[len(prefix):] if prefix else line
    replacements = [
        (re.compile(r"Before calling `[^`]+`, use `[^`]+` to read the image dimensions without decompressing", re.I),
         "Add a lightweight guard before full decode so oversized images are rejected safely."),
        (re.compile(r"Calculate the total pixel count .* reject images exceeding \d+\s*megapixels", re.I),
         "Enforce a reasonable upper bound on decoded image size."),
        (re.compile(r"Images exceeding \d+\s*MP.*", re.I),
         "Oversized images are rejected before full decode."),
        (re.compile(r"The check uses `[^`]+`.*", re.I),
         "The protection is implemented in the normal image-processing flow."),
        (re.compile(r"Replace the brute-force .*", re.I),
         "Replace the current approach with one that avoids the rate-limiting failure mode."),
        (re.compile(r"Add a new `[^`]+` method .*", re.I),
         "Introduce any supporting helper needed for the new membership-check flow."),
        (re.compile(r"Update the session handler to use the new method.*", re.I),
         "Update the calling path to use the new flow."),
        (re.compile(r"A new `[^`]+` method exists.*", re.I),
         "Supporting client functionality exists for the new membership-check flow."),
        (re.compile(r"instead of reconstructing from a flattened string", re.I),
         "using editor-native position handling rather than reconstructed offsets"),
    ]
    for pattern, replacement in replacements:
        if pattern.search(body):
            return prefix + pattern.sub(replacement, body)
    return line


def _renumber_ordered_lists(lines: list[str]) -> list[str]:
    out: list[str] = []
    counter = 0
    in_list = False
    for line in lines:
        match = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if match:
            counter = counter + 1 if in_list else 1
            in_list = True
            out.append(f"{match.group(1)}{counter}. {match.group(3)}")
            continue
        if line.strip():
            in_list = False
            counter = 0
        out.append(line)
    return out


def _format_json_fence(fence: str, lines: list[str]) -> list[str]:
    if "json" not in fence.lower():
        return [fence, *lines, "```"]
    try:
        payload = "\n".join(lines).strip()
        parsed = json.loads(payload)
        formatted = json.dumps(parsed, indent=2).splitlines()
        return [fence, *formatted, "```"]
    except json.JSONDecodeError:
        return [fence, *lines, "```"]


def sanitize_instruction_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = _drop_sections(text)
    cleaned_lines: list[str] = []
    previous_blank = False
    in_fence = False
    fence_header = ""
    fence_lines: list[str] = []
    for raw_line in text.splitlines():
        if raw_line.startswith("```"):
            if in_fence:
                cleaned_lines.extend(_format_json_fence(fence_header, fence_lines))
                in_fence = False
                fence_header = ""
                fence_lines = []
            else:
                in_fence = True
                fence_header = raw_line
            previous_blank = False
            continue
        if in_fence:
            fence_lines.append(raw_line)
            continue
        line = _sanitize_line(raw_line)
        if not line.strip():
            if previous_blank:
                continue
            cleaned_lines.append("")
            previous_blank = True
            continue
        cleaned_lines.append(line)
        previous_blank = False
    if in_fence:
        cleaned_lines.extend(_format_json_fence(fence_header, fence_lines))
    cleaned_lines = _renumber_ordered_lists(cleaned_lines)
    cleaned = "\n".join(cleaned_lines).strip() + "\n"
    cleaned = re.sub(r"\n## Success Criteria\n\n(?:- Code changes match.*\n)+", "\n## Success Criteria\n\n", cleaned)
    cleaned = re.sub(r"\n\*\*Time Limit:\*\*.*\n", "\n", cleaned)
    return cleaned


def audit_paths(paths: Iterable[Path]) -> dict[str, object]:
    paths = list(paths)
    findings: list[Finding] = []
    by_file: dict[str, list[Finding]] = defaultdict(list)
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(errors="ignore")
        file_findings = find_prompt_findings(text, path)
        findings.extend(file_findings)
        if file_findings:
            by_file[str(path)].extend(file_findings)

    issue_counts = Counter(f.issue_type for f in findings)
    files_with_issue = defaultdict(set)
    for finding in findings:
        files_with_issue[finding.issue_type].add(finding.file)
    return {
        "totals": {
            "files_scanned": len(paths),
            "files_flagged": len(by_file),
            "files_with_location_hints": len(files_with_issue.get("code_location_hint", set())),
            "files_with_solution_leakage": len(files_with_issue.get("solution_leakage", set())),
            "files_with_scoring_leakage": len(files_with_issue.get("scoring_leakage", set())),
            "code_location_hints": issue_counts.get("code_location_hint", 0),
            "solution_leakage": issue_counts.get("solution_leakage", 0),
            "scoring_leakage": issue_counts.get("scoring_leakage", 0),
        },
        "files": [
            {
                "file": file_path,
                "issues": [
                    {"type": f.issue_type, "line": f.line, "value": f.value}
                    for f in sorted(file_findings, key=lambda item: (item.line, item.issue_type, item.value))
                ],
            }
            for file_path, file_findings in sorted(by_file.items())
        ],
    }


def write_markdown_report(report: dict[str, object], out_path: Path, title: str) -> None:
    totals = report["totals"]
    lines = [
        f"# {title}",
        "",
        f"- Files scanned: {totals['files_scanned']}",
        f"- Files flagged: {totals['files_flagged']}",
        f"- Files with location hints: {totals['files_with_location_hints']}",
        f"- Files with solution leakage: {totals['files_with_solution_leakage']}",
        f"- Files with scoring leakage: {totals['files_with_scoring_leakage']}",
        f"- Code-location hints: {totals['code_location_hints']}",
        f"- Solution leakage findings: {totals['solution_leakage']}",
        f"- Scoring leakage findings: {totals['scoring_leakage']}",
        "",
    ]
    for file_entry in report["files"]:
        lines.append(f"## {file_entry['file']}")
        lines.append("")
        for issue in file_entry["issues"]:
            lines.append(f"- `{issue['type']}` line {issue['line']}: {issue['value']}")
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-selected", action="store_true", help="Audit selected canonical tasks.")
    parser.add_argument(
        "--git-modified",
        action="store_true",
        help="Audit only instruction files currently modified or untracked in this git worktree.",
    )
    parser.add_argument("--scan-root", action="append", default=[], help="Additional root to scan for instruction files.")
    parser.add_argument("--include-mcp", action="store_true", help="Also include instruction_mcp.md files.")
    parser.add_argument("--apply", action="store_true", help="Rewrite scanned files in place.")
    parser.add_argument("--report-json", type=Path, help="Write JSON report to this path.")
    parser.add_argument("--report-md", type=Path, help="Write Markdown report to this path.")
    parser.add_argument("--title", default="Prompt Hygiene Audit", help="Markdown report title.")
    parser.add_argument("--fail-on-findings", action="store_true", help="Exit non-zero when findings remain.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    paths: list[Path] = []
    if args.canonical_selected:
        paths.extend(_load_selected_task_instruction_paths(args.include_mcp))
    if args.git_modified:
        paths.extend(_load_git_modified_instruction_paths(args.include_mcp))
    for root in args.scan_root:
        paths.extend(_scan_instruction_paths(Path(root).expanduser(), args.include_mcp))
    deduped_paths = sorted(dict.fromkeys(path for path in paths if path.exists()))

    if args.apply:
        for path in deduped_paths:
            original = path.read_text(errors="ignore")
            cleaned = sanitize_instruction_text(original)
            if cleaned != original:
                path.write_text(cleaned)

    report = audit_paths(deduped_paths)
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2) + "\n")
    if args.report_md:
        write_markdown_report(report, args.report_md, args.title)

    totals = report["totals"]
    print(json.dumps(totals, indent=2))
    if args.fail_on_findings and totals["files_flagged"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
