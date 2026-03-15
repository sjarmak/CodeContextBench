#!/usr/bin/env python3
"""Add compile-gate checks to implementation task verifiers.

Scans feature/fix/refactor/test/debug tasks for structural-only verifiers
and inserts a language-appropriate compile check before the final score line.

Usage:
  python3 scripts/add_compile_gates.py --dry-run     # Preview changes
  python3 scripts/add_compile_gates.py --execute      # Apply changes
  python3 scripts/add_compile_gates.py --execute --lang python  # Only Python tasks
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks" / "csb"

# Implementation task directories
IMPL_DIRS = ["feature", "fix", "refactor", "test", "debug"]

# Skip analysis/investigation tasks (they produce docs, not code)
ANALYSIS_TASK_PATTERNS = [
    r"ccx-",           # Cross-codebase analysis
    r"-investigate-",  # Bug investigation
    r"-analysis-",     # Analysis tasks
    r"-review-",       # Code review tasks
]

# Functional check patterns (if any present, task already has compile gate)
FUNCTIONAL_PATTERNS = [
    r"\bgo\s+build\b", r"\bgo\s+vet\b", r"\bgo\s+test\b",
    r"\bnpm\s+test\b", r"\bnpx\s+jest\b", r"\byarn\s+test\b",
    r"\bnpx\s+tsc\b",
    r"\bpytest\b", r"\bpython.*-m\s+pytest\b", r"\bunittest\b",
    r"\bpy_compile\b",
    r"\bmake\s+test\b", r"\bmake\s+check\b", r"\bcargo\s+test\b",
    r"\bmvn\s+(test|compile)\b", r"\bgradle\s+test\b", r"\bgradlew\b",
    r"\bgcc\b", r"\bg\+\+\b", r"\bcmake\b",
    r"\btsc\b", r"\bjavac\b",
]

# Language-to-compile-gate mapping
# Each entry: (check_command, echo_pass, echo_fail, needs_tool_check, tool_name)
COMPILE_GATES = {
    "python": {
        "snippet": '''\
# Check {n}: Python syntax validation
PYFILES_OK=true
for pyf in $(git diff --name-only HEAD 2>/dev/null | grep '\\.py$' || find "$WORKSPACE" -name '*.py' -newer "$WORKSPACE/.git" -maxdepth 4 2>/dev/null | head -20); do
    if [ -f "$WORKSPACE/$pyf" ] 2>/dev/null || [ -f "$pyf" ]; then
        target="$pyf"
        [ ! -f "$target" ] && target="$WORKSPACE/$pyf"
        if ! python3 -m py_compile "$target" 2>/dev/null; then
            PYFILES_OK=false
            break
        fi
    fi
done
if [ "$PYFILES_OK" = true ]; then
    SCORE=$((SCORE + 1))
    echo "PASS: Python syntax validation"
else
    echo "FAIL: Python syntax validation (py_compile error)"
fi''',
        "tool_check": None,  # python3 always available
    },
    "go": {
        "snippet": '''\
# Check {n}: Go compilation
if command -v go >/dev/null 2>&1; then
    cd "$WORKSPACE"
    if go vet ./... 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Go vet passes"
    else
        echo "FAIL: Go vet fails"
    fi
    cd - >/dev/null
else
    echo "SKIP: Go toolchain not available"
fi''',
        "tool_check": "go",
    },
    "c": {
        "snippet": '''\
# Check {n}: C syntax validation
if command -v gcc >/dev/null 2>&1; then
    C_SYNTAX_OK=true
    for cf in $(git diff --name-only HEAD 2>/dev/null | grep '\\.[ch]$' | head -10); do
        if [ -f "$WORKSPACE/$cf" ]; then
            if ! gcc -fsyntax-only -I "$WORKSPACE/include" "$WORKSPACE/$cf" 2>/dev/null; then
                C_SYNTAX_OK=false
                break
            fi
        fi
    done
    if [ "$C_SYNTAX_OK" = true ]; then
        SCORE=$((SCORE + 1))
        echo "PASS: C syntax validation"
    else
        echo "FAIL: C syntax validation (gcc -fsyntax-only error)"
    fi
else
    echo "SKIP: gcc not available"
fi''',
        "tool_check": "gcc",
    },
    "c++": {
        "snippet": '''\
# Check {n}: C++ syntax validation
if command -v g++ >/dev/null 2>&1; then
    CPP_SYNTAX_OK=true
    for cf in $(git diff --name-only HEAD 2>/dev/null | grep '\\.(cpp|cc|cxx|h|hpp)$' | head -10); do
        if [ -f "$WORKSPACE/$cf" ]; then
            if ! g++ -fsyntax-only -std=c++17 "$WORKSPACE/$cf" 2>/dev/null; then
                CPP_SYNTAX_OK=false
                break
            fi
        fi
    done
    if [ "$CPP_SYNTAX_OK" = true ]; then
        SCORE=$((SCORE + 1))
        echo "PASS: C++ syntax validation"
    else
        echo "FAIL: C++ syntax validation"
    fi
else
    echo "SKIP: g++ not available"
fi''',
        "tool_check": "g++",
    },
    "typescript": {
        "snippet": '''\
# Check {n}: TypeScript compilation
if command -v npx >/dev/null 2>&1; then
    cd "$WORKSPACE"
    if npx tsc --noEmit 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: TypeScript compilation"
    else
        echo "FAIL: TypeScript compilation fails"
    fi
    cd - >/dev/null
else
    echo "SKIP: npx/tsc not available"
fi''',
        "tool_check": "npx",
    },
    "javascript": {
        "snippet": '''\
# Check {n}: JavaScript syntax validation
if command -v node >/dev/null 2>&1; then
    JS_SYNTAX_OK=true
    for jsf in $(git diff --name-only HEAD 2>/dev/null | grep '\\.js$' | head -10); do
        if [ -f "$WORKSPACE/$jsf" ]; then
            if ! node --check "$WORKSPACE/$jsf" 2>/dev/null; then
                JS_SYNTAX_OK=false
                break
            fi
        fi
    done
    if [ "$JS_SYNTAX_OK" = true ]; then
        SCORE=$((SCORE + 1))
        echo "PASS: JavaScript syntax validation"
    else
        echo "FAIL: JavaScript syntax validation"
    fi
else
    echo "SKIP: node not available"
fi''',
        "tool_check": "node",
    },
    "java": {
        "snippet": '''\
# Check {n}: Java compilation
if [ -f "$WORKSPACE/gradlew" ]; then
    cd "$WORKSPACE"
    if timeout 120 ./gradlew compileJava -q 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Java compilation (Gradle)"
    else
        echo "FAIL: Java compilation fails"
    fi
    cd - >/dev/null
elif command -v mvn >/dev/null 2>&1; then
    cd "$WORKSPACE"
    if timeout 120 mvn compile -q 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Java compilation (Maven)"
    else
        echo "FAIL: Java compilation fails"
    fi
    cd - >/dev/null
else
    echo "SKIP: Java build tools not available"
fi''',
        "tool_check": None,
    },
    "rust": {
        "snippet": '''\
# Check {n}: Rust compilation
if command -v cargo >/dev/null 2>&1; then
    cd "$WORKSPACE"
    if timeout 120 cargo check 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: Rust compilation (cargo check)"
    else
        echo "FAIL: Rust compilation fails"
    fi
    cd - >/dev/null
else
    echo "SKIP: cargo not available"
fi''',
        "tool_check": "cargo",
    },
    "c#": {
        "snippet": '''\
# Check {n}: C# compilation
if command -v dotnet >/dev/null 2>&1; then
    cd "$WORKSPACE"
    if timeout 120 dotnet build --no-restore -q 2>/dev/null; then
        SCORE=$((SCORE + 1))
        echo "PASS: C# compilation (dotnet build)"
    else
        echo "FAIL: C# compilation fails"
    fi
    cd - >/dev/null
else
    echo "SKIP: dotnet not available"
fi''',
        "tool_check": "dotnet",
    },
}


def _parse_toml_simple(path: Path) -> dict:
    """Minimal TOML parser."""
    result = {}
    section = ""
    if not path.is_file():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            section = line.strip("[]").strip()
            continue
        if "=" in line:
            if '"""' in line:
                break
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            full_key = f"{section}.{key}" if section else key
            result[full_key] = val
    return result


def _is_analysis_task(task_name: str) -> bool:
    """Check if task is an analysis/investigation task (no code changes expected)."""
    return any(re.search(pat, task_name) for pat in ANALYSIS_TASK_PATTERNS)


def _has_functional_checks(content: str) -> bool:
    """Check if verifier already has functional verification."""
    return any(re.search(pat, content) for pat in FUNCTIONAL_PATTERNS)


def _find_insertion_point(content: str) -> tuple[int, int]:
    """Find where to insert the compile gate and the current TOTAL value.

    Returns (line_index_for_insertion, current_total).
    """
    lines = content.split("\n")

    # Find TOTAL=N line
    total = 0
    for line in lines:
        m = re.match(r'^TOTAL=(\d+)', line)
        if m:
            total = int(m.group(1))
            break

    # Find insertion point: before "echo" line showing score
    for i, line in enumerate(lines):
        if re.search(r'echo.*"Score:.*\$SCORE.*\$TOTAL"', line):
            return i, total
        if re.search(r'echo.*Score:.*SCORE.*TOTAL', line):
            return i, total

    # Fallback: before write_scored_result
    for i, line in enumerate(lines):
        if "write_scored_result" in line:
            return i, total

    # Fallback: before dual_score_lib
    for i, line in enumerate(lines):
        if "dual_score_lib" in line:
            return i, total

    return len(lines) - 1, total


def process_task(task_dir: Path, dry_run: bool = True) -> dict:
    """Process a single task. Returns status dict."""
    task_name = task_dir.name
    result = {"task": task_name, "action": "skip", "reason": ""}

    if _is_analysis_task(task_name):
        result["reason"] = "analysis/investigation task"
        return result

    toml = _parse_toml_simple(task_dir / "task.toml")
    lang = (toml.get("task.language") or toml.get("metadata.language") or "").lower()

    if not lang:
        result["reason"] = "no language in task.toml"
        return result

    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.is_file():
        result["reason"] = "no test.sh"
        return result

    content = test_sh.read_text()

    if _has_functional_checks(content):
        result["reason"] = "already has functional checks"
        return result

    # Check if this is a SCORE/TOTAL checklist pattern
    if "SCORE=" not in content or "TOTAL=" not in content:
        result["reason"] = "non-checklist verifier pattern"
        return result

    # Normalize language aliases
    lang_key = {"cpp": "c++", "csharp": "c#"}.get(lang, lang)
    gate = COMPILE_GATES.get(lang_key)
    if not gate:
        result["action"] = "no_gate"
        result["reason"] = f"no compile gate defined for {lang}"
        return result

    insertion_idx, current_total = _find_insertion_point(content)
    if insertion_idx <= 0:
        result["reason"] = "could not find insertion point"
        return result

    new_total = current_total + 1
    check_num = current_total + 1
    snippet = gate["snippet"].format(n=check_num)

    lines = content.split("\n")

    # Update TOTAL
    new_lines = []
    for line in lines:
        if re.match(r'^TOTAL=\d+', line):
            new_lines.append(f"TOTAL={new_total}")
        else:
            new_lines.append(line)

    # Insert snippet before the insertion point
    new_lines.insert(insertion_idx, "")
    new_lines.insert(insertion_idx + 1, snippet)

    new_content = "\n".join(new_lines)

    result["action"] = "update"
    result["lang"] = lang
    result["old_total"] = current_total
    result["new_total"] = new_total
    result["tool_check"] = gate.get("tool_check")

    if not dry_run:
        test_sh.write_text(new_content)
        result["written"] = True
    else:
        result["written"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="Add compile gates to implementation task verifiers")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    mode.add_argument("--execute", action="store_true", help="Apply changes")
    parser.add_argument("--lang", help="Only process tasks with this language")
    args = parser.parse_args()

    dry_run = args.dry_run

    updates = []
    skips = []
    no_gates = []

    for impl_dir_name in IMPL_DIRS:
        impl_dir = BENCHMARKS_DIR / impl_dir_name
        if not impl_dir.is_dir():
            continue

        for task_dir in sorted(impl_dir.iterdir()):
            if not task_dir.is_dir() or task_dir.name.startswith((".", "_")):
                continue

            if args.lang:
                toml = _parse_toml_simple(task_dir / "task.toml")
                task_lang = (toml.get("task.language") or toml.get("metadata.language") or "").lower()
                if task_lang != args.lang.lower():
                    continue

            result = process_task(task_dir, dry_run=dry_run)

            if result["action"] == "update":
                updates.append(result)
            elif result["action"] == "no_gate":
                no_gates.append(result)
            else:
                skips.append(result)

    # Report
    print(f"\n{'DRY RUN' if dry_run else 'EXECUTED'}: Compile gate additions\n")

    if updates:
        print(f"Updated ({len(updates)} tasks):")
        for r in updates:
            tool_note = f" [needs {r['tool_check']}]" if r.get("tool_check") else ""
            print(f"  {r['task']}: {r['lang']}, TOTAL {r['old_total']}→{r['new_total']}{tool_note}")

    if no_gates:
        print(f"\nNo gate defined ({len(no_gates)} tasks):")
        for r in no_gates:
            print(f"  {r['task']}: {r['reason']}")

    if skips:
        skip_reasons = {}
        for r in skips:
            reason = r["reason"]
            skip_reasons.setdefault(reason, []).append(r["task"])
        print(f"\nSkipped ({len(skips)} tasks):")
        for reason, tasks in sorted(skip_reasons.items()):
            print(f"  {reason} ({len(tasks)}): {', '.join(tasks[:5])}")
            if len(tasks) > 5:
                print(f"    ... and {len(tasks) - 5} more")

    print(f"\nTotal: {len(updates)} updated, {len(no_gates)} no gate, {len(skips)} skipped")


if __name__ == "__main__":
    main()
