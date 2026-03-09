#!/usr/bin/env python3
"""Migrate pending verifier test.sh scripts to emit validation_result.json sidecar.

For each pending task (structured_output_mode=none, migration_class=emit_validation_result_sidecar),
this script patches the test.sh to emit /logs/verifier/validation_result.json alongside reward.txt.

Families handled:
  - checklist (16 tasks) — heterogeneous scoring, each has unique checks
  - ir_checklist (17 tasks) — uses verifier_lib.sh composite scoring
  - f1 (2 tasks) — pure F1 scorer template
  - f1_hybrid (7 tasks) — detection F1 + fix score blend
  - continuous (5 tasks) — weighted category checklist
  - test_ratio (3 tasks) — SWE-bench test pass ratio

Usage:
  python3 scripts/migrate_validation_result_sidecar.py [--dry-run] [--family FAMILY]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

BENCHMARKS_ROOT = Path(__file__).resolve().parent.parent / "benchmarks"
AUDIT_PATH = Path(__file__).resolve().parent.parent / "configs" / "canonical_evaluation_audit.json"

# ── Family-specific sidecar emitter blocks ──────────────────────────────────

# These are appended/injected into each test.sh to emit validation_result.json.
# Each block is a bash function that reads the reward.txt (already written) and
# emits the sidecar.

CHECKLIST_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result() {
    local reward="$1"
    local sub_scores_json="${2:-{\}}"
    local details_json="${3:-null}"
    local status="${4:-scored}"
    local failure_json="${5:-null}"
    python3 - "$reward" "$sub_scores_json" "$details_json" "$status" "$failure_json" <<'VR_PYEOF'
import json, sys

reward_str, sub_scores_raw, details_raw, status, failure_raw = sys.argv[1:6]
try:
    reward = float(reward_str)
except (TypeError, ValueError):
    reward = 0.0
try:
    sub_scores = json.loads(sub_scores_raw)
except Exception:
    sub_scores = {}
try:
    details = json.loads(details_raw) if details_raw != "null" else None
except Exception:
    details = None
try:
    failure = json.loads(failure_raw) if failure_raw != "null" else None
except Exception:
    failure = None

if status != "scored":
    failure = failure or {
        "code": "missing_required_output",
        "message": "Agent did not produce required output",
        "stage": "output_validation",
    }

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": status,
    "scorable": status == "scored",
    "scorer_family": "checklist",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": status == "scored" and reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": sub_scores,
    "failure": failure,
}
if details:
    payload["details"] = details

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''

IR_CHECKLIST_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result() {
    local reward="$1"
    python3 - "$reward" "$TASK_QUALITY" "$IR_RECALL" "$IR_PRECISION" "$DEP_ACCURACY" <<'VR_PYEOF'
import json, sys

reward_str = sys.argv[1]
task_quality = sys.argv[2] if len(sys.argv) > 2 else "0"
ir_recall = sys.argv[3] if len(sys.argv) > 3 else "0"
ir_precision = sys.argv[4] if len(sys.argv) > 4 else "0"
dep_accuracy = sys.argv[5] if len(sys.argv) > 5 else "0"

def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

reward = safe_float(reward_str)

sub_scores = {
    "task_quality": safe_float(task_quality),
    "file_recall": safe_float(ir_recall),
    "file_precision": safe_float(ir_precision),
    "dep_accuracy": safe_float(dep_accuracy),
}

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "ir_checklist",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": sub_scores,
    "failure": None,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}

write_invalid_output_vr() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" <<'VR_PYEOF'
import json, sys
code, message = sys.argv[1:3]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "ir_checklist",
    "reward": 0.0,
    "pass_threshold": 0.5,
    "passed": False,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {},
    "failure": {"code": code, "message": message, "stage": "output_validation"},
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''

F1_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result_f1() {
    REWARD_FILE="/logs/verifier/reward.txt" OUTPUT_PATH="$OUTPUT_PATH" GROUND_TRUTH="$GROUND_TRUTH" \
    python3 <<'VR_PYEOF'
import json, os, re, sys

reward_path = os.environ.get("REWARD_FILE", "/logs/verifier/reward.txt")
output_path = os.environ.get("OUTPUT_PATH", "/workspace/implementors.json")
gt_path = os.environ.get("GROUND_TRUTH", "/tests/ground_truth.json")

try:
    with open(reward_path) as f:
        reward = float(f.read().strip())
except Exception:
    reward = 0.0

status = "scored"
sub_scores = {}
failure = None

# Re-derive precision/recall from the same logic
try:
    with open(gt_path) as f:
        gt = json.load(f)
    key_fields = gt.get("key_fields", [])
    expected = gt.get("entries", [])

    def normalize_repo(name):
        n = name.strip()
        for prefix in ("github.com/", "https://github.com/"):
            if n.startswith(prefix):
                n = n[len(prefix):]
        if n.startswith("sg-evals/"):
            n = n[len("sg-evals/"):]
        n = re.sub(r'--[0-9a-f]{7,}$', '', n)
        if "/" in n:
            n = n.rsplit("/", 1)[-1]
        return n

    def make_key(entry, fields):
        parts = []
        for f_name in fields:
            val = str(entry.get(f_name, "")).strip()
            if f_name == "repo":
                val = normalize_repo(val)
            parts.append(val)
        return tuple(parts)

    reported = []
    if os.path.isfile(output_path):
        try:
            with open(output_path) as f:
                raw = f.read()
            m = re.search(r'```(?:json)?\s*\n(.*?)```', raw, re.DOTALL)
            raw = m.group(1).strip() if m else raw.strip()
            reported = json.loads(raw)
            if not isinstance(reported, list):
                reported = []
        except Exception:
            reported = []

    expected_keys = [make_key(e, key_fields) for e in expected]
    reported_keys = [make_key(r, key_fields) for r in reported]
    matched = set()
    tp = 0
    for r_key in reported_keys:
        for e_idx, e_key in enumerate(expected_keys):
            if e_idx in matched:
                continue
            if r_key == e_key:
                matched.add(e_idx)
                tp += 1
                break
    prec = tp / len(reported) if reported else 0.0
    rec = tp / len(expected) if expected else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    sub_scores = {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4)}
except Exception as exc:
    status = "verifier_error"
    failure = {"code": "verifier_exception", "message": str(exc), "stage": "scoring"}

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": status,
    "scorable": status == "scored",
    "scorer_family": "f1",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": status == "scored" and reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": output_path,
        "required_artifact": False,
    },
    "sub_scores": sub_scores,
    "failure": failure,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''

F1_HYBRID_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result_f1_hybrid() {
    local reward="$1"
    python3 - "$reward" <<'VR_PYEOF'
import json, sys

try:
    reward = float(sys.argv[1])
except (TypeError, ValueError):
    reward = 0.0

# The f1_hybrid family blends detection F1 (50%) and fix score (50%).
# Sub-scores are not re-derived here since they're printed to stderr during scoring.
# The reward is the authoritative composite.

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "f1_hybrid",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {},
    "failure": None,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}

write_invalid_output_f1_hybrid() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" <<'VR_PYEOF'
import json, sys
code, message = sys.argv[1:3]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "f1_hybrid",
    "reward": 0.0,
    "pass_threshold": 0.5,
    "passed": False,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {},
    "failure": {"code": code, "message": message, "stage": "output_validation"},
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''

CONTINUOUS_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result_continuous() {
    local reward="$1"
    python3 - "$reward" <<'VR_PYEOF'
import json, sys

try:
    reward = float(sys.argv[1])
except (TypeError, ValueError):
    reward = 0.0

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "continuous",
    "reward": reward,
    "pass_threshold": 0.5,
    "passed": reward >= 0.5,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {"continuous_score": reward},
    "failure": None,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}

write_invalid_output_continuous() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" <<'VR_PYEOF'
import json, sys
code, message = sys.argv[1:3]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "continuous",
    "reward": 0.0,
    "pass_threshold": 0.5,
    "passed": False,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {},
    "failure": {"code": code, "message": message, "stage": "output_validation"},
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''

TEST_RATIO_SIDECAR = r'''
# ── validation_result sidecar ───────────────────────────────────────────────
write_validation_result_test_ratio() {
    local reward="$1"
    python3 - "$reward" <<'VR_PYEOF'
import json, sys

try:
    reward = float(sys.argv[1])
except (TypeError, ValueError):
    reward = 0.0

payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "test_ratio",
    "reward": reward,
    "pass_threshold": 1.0,
    "passed": reward >= 1.0,
    "output_contract": {
        "mode": "unspecified",
        "primary_path": None,
        "required_artifact": False,
    },
    "sub_scores": {"tests_passed_ratio": reward},
    "failure": None,
}

with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
VR_PYEOF
}
'''


def get_pending_tasks(family_filter=None):
    """Return list of pending tasks from the audit."""
    with open(AUDIT_PATH) as f:
        audit = json.load(f)

    pending = []
    for task in audit["tasks"]:
        if task.get("excluded"):
            continue
        mc = task.get("validation_result_plan", {}).get("migration_class", "")
        if mc != "emit_validation_result_sidecar":
            continue
        family = task["evaluator"]["family"]
        if family_filter and family != family_filter:
            continue
        pending.append({
            "task_id": task["task_id"],
            "family": family,
            "task_dir": task["task_dir"],
            "test_sh": BENCHMARKS_ROOT / task["task_dir"] / "tests" / "test.sh",
        })
    return pending


def migrate_checklist(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate a checklist-family test.sh to emit validation_result.json."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert the sidecar function before the first scoring section
    # Then add a call at each exit point where reward.txt is written

    # Strategy: insert the function definition early, then wrap each
    # `echo "X.X" > /logs/verifier/reward.txt` pattern with a VR call.

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_pattern = r'(mkdir -p /logs/verifier\n)'
    if re.search(mkdir_pattern, content):
        content = re.sub(mkdir_pattern, r'\1' + CHECKLIST_SIDECAR + '\n', content, count=1)
    else:
        # Insert after set -e line
        content = re.sub(r'(set -e\n)', r'\1' + CHECKLIST_SIDECAR + '\n', content, count=1)

    # Find all patterns where reward.txt is written with 0.0 (guard failures)
    # Pattern: echo "0.0" > /logs/verifier/reward.txt followed by exit 0
    content = re.sub(
        r'(echo "0\.0" > /logs/verifier/reward\.txt\n)(.*?)(exit 0)',
        r'\1write_validation_result "0.0" "{}" "null" "invalid_output"\n\3',
        content,
        flags=re.DOTALL,
    )

    # Find the final reward.txt write (the success path)
    # Pattern: echo "$FINAL_SCORE" > /logs/verifier/reward.txt
    # or: echo "$SCORE" > /logs/verifier/reward.txt
    final_write_pattern = r'(echo "\$(?:FINAL_SCORE|SCORE)" > /logs/verifier/reward\.txt\n)'
    if re.search(final_write_pattern, content):
        # Add VR call after the final reward.txt write
        content = re.sub(
            final_write_pattern,
            r'\1write_validation_result "$FINAL_SCORE" "{}" "null" "scored"\n',
            content,
        )
        # Fix: if the variable is $SCORE not $FINAL_SCORE in the VR call
        # We need to be smarter - check which var was used
        # Actually, let's just handle both names
        content = content.replace(
            'write_validation_result "$FINAL_SCORE"',
            'write_validation_result "${FINAL_SCORE:-$SCORE}"',
        )

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


def migrate_ir_checklist(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate an ir_checklist-family test.sh."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_match = content.find("mkdir -p /logs/verifier\n")
    if mkdir_match >= 0:
        insert_pos = content.index('\n', mkdir_match) + 1
        content = content[:insert_pos] + IR_CHECKLIST_SIDECAR + '\n' + content[insert_pos:]
    else:
        # Insert after source /tests/verifier_lib.sh
        lib_match = content.find("source /tests/verifier_lib.sh\n")
        if lib_match >= 0:
            insert_pos = content.index('\n', lib_match) + 1
            content = content[:insert_pos] + IR_CHECKLIST_SIDECAR + '\n' + content[insert_pos:]

    # Wrap guard failures (echo "0.0" > reward.txt + exit 0)
    content = re.sub(
        r'(echo "0\.0" > /logs/verifier/reward\.txt\n)(.*?)(exit 0)',
        r'\1write_invalid_output_vr "missing_required_output" "Agent did not produce required output"\n\3',
        content,
        flags=re.DOTALL,
    )

    # Add VR call after the final composite score write
    final_pattern = r'(echo "\$SCORE" > /logs/verifier/reward\.txt\n)'
    if re.search(final_pattern, content):
        content = re.sub(
            final_pattern,
            r'\1write_validation_result "$SCORE"\n',
            content,
        )

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


def migrate_f1(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate an f1-family test.sh."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_match = content.find("mkdir -p /logs/verifier\n")
    if mkdir_match >= 0:
        insert_pos = content.index('\n', mkdir_match) + 1
        content = content[:insert_pos] + F1_SIDECAR + '\n' + content[insert_pos:]

    # Add VR call after the PYEOF that ends the scoring block
    # The f1 template ends with `PYEOF` and that's it
    # We need to add a call at the very end
    content = content.rstrip() + '\nwrite_validation_result_f1\n'

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


def migrate_f1_hybrid(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate an f1_hybrid-family test.sh."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_match = content.find("mkdir -p /logs/verifier\n")
    if mkdir_match >= 0:
        insert_pos = content.index('\n', mkdir_match) + 1
        content = content[:insert_pos] + F1_HYBRID_SIDECAR + '\n' + content[insert_pos:]

    # Wrap guard failures — these write "0.0" to reward.txt and exit 0
    content = re.sub(
        r'(echo "0\.0" > /logs/verifier/reward\.txt\n)(.*?)(exit 0)',
        r'\1write_invalid_output_f1_hybrid "missing_required_output" "Agent did not produce required output"\n\3',
        content,
        flags=re.DOTALL,
    )

    # Add VR call after the final reward.txt write
    final_pattern = r'(echo "\$FINAL_SCORE" > /logs/verifier/reward\.txt\n)'
    if re.search(final_pattern, content):
        content = re.sub(
            final_pattern,
            r'\1write_validation_result_f1_hybrid "$FINAL_SCORE"\n',
            content,
        )

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


def migrate_continuous(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate a continuous-family test.sh."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_match = content.find("mkdir -p /logs/verifier\n")
    if mkdir_match >= 0:
        insert_pos = content.index('\n', mkdir_match) + 1
        content = content[:insert_pos] + CONTINUOUS_SIDECAR + '\n' + content[insert_pos:]

    # Wrap guard failures
    content = re.sub(
        r'(echo "0\.0" > ["$]REWARD_FILE["]?\n)',
        r'\1write_invalid_output_continuous "missing_required_output" "Agent did not produce required output"\n',
        content,
    )
    # Also handle: echo "0.0" > "$REWARD_FILE"
    # (already covered by the pattern above with optional quotes)

    # The continuous verifier's Python block calls write_reward() which writes to $REWARD_FILE.
    # We need to add VR emission after the Python block finishes.
    # The Python block ends with PYTHON_SCRIPT or PYEOF — add VR call after
    if "PYTHON_SCRIPT" in content:
        content = content.rstrip()
        content += '\n\n# Emit validation_result sidecar from reward.txt\n'
        content += 'REWARD_VAL=$(cat /logs/verifier/reward.txt 2>/dev/null | tr -d "\\n" || echo "0.0")\n'
        content += 'write_validation_result_continuous "$REWARD_VAL"\n'

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


def migrate_test_ratio(test_sh_path: Path, dry_run: bool) -> bool:
    """Migrate a test_ratio-family test.sh."""
    content = test_sh_path.read_text()

    if "validation_result.json" in content:
        print(f"  SKIP (already has validation_result.json)")
        return False

    # Insert function after `mkdir -p /logs/verifier`
    mkdir_match = content.find("mkdir -p /logs/verifier\n")
    if mkdir_match >= 0:
        insert_pos = content.index('\n', mkdir_match) + 1
        content = content[:insert_pos] + TEST_RATIO_SIDECAR + '\n' + content[insert_pos:]

    # Replace the trap to also emit VR on exit
    old_trap = "trap 'if [ ! -f /logs/verifier/reward.txt ]; then echo \"0.0\" > /logs/verifier/reward.txt; fi' EXIT"
    new_trap = (
        "trap 'if [ ! -f /logs/verifier/reward.txt ]; then echo \"0.0\" > /logs/verifier/reward.txt; fi; "
        "REWARD_VAL=$(cat /logs/verifier/reward.txt 2>/dev/null | tr -d \"\\n\" || echo \"0.0\"); "
        "write_validation_result_test_ratio \"$REWARD_VAL\"' EXIT"
    )
    content = content.replace(old_trap, new_trap)

    if dry_run:
        print(f"  DRY-RUN: would write {test_sh_path}")
        return True

    test_sh_path.write_text(content)
    return True


FAMILY_MIGRATORS = {
    "checklist": migrate_checklist,
    "ir_checklist": migrate_ir_checklist,
    "f1": migrate_f1,
    "f1_hybrid": migrate_f1_hybrid,
    "continuous": migrate_continuous,
    "test_ratio": migrate_test_ratio,
}


def main():
    parser = argparse.ArgumentParser(description="Migrate verifiers to emit validation_result.json")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without writing")
    parser.add_argument("--family", help="Only migrate tasks in this verifier family")
    args = parser.parse_args()

    tasks = get_pending_tasks(family_filter=args.family)
    print(f"Found {len(tasks)} pending tasks")

    migrated = 0
    skipped = 0
    errors = 0

    for task in tasks:
        family = task["family"]
        test_sh = task["test_sh"]
        print(f"\n{task['task_id']} ({family}):")

        if not test_sh.is_file():
            print(f"  ERROR: {test_sh} not found")
            errors += 1
            continue

        migrator = FAMILY_MIGRATORS.get(family)
        if not migrator:
            print(f"  ERROR: no migrator for family '{family}'")
            errors += 1
            continue

        try:
            if migrator(test_sh, dry_run=args.dry_run):
                migrated += 1
            else:
                skipped += 1
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors += 1

    print(f"\n{'DRY-RUN ' if args.dry_run else ''}Summary: {migrated} migrated, {skipped} skipped, {errors} errors")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
