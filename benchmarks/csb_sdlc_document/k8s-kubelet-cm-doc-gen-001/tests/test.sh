#!/bin/bash
# Reward: checklist (0.0-1.0) with hallucination penalties only
# Canonical ground-truth content should score 1.0.

set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi


DOC="/workspace/documentation.md"
# In artifact mode, populate expected output from answer.json analysis
if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ -f "${ANALYSIS_TEXT_FILE:-}" ]; then
    cp "$ANALYSIS_TEXT_FILE" "/workspace/documentation.md"
    echo "[answer_json] Copied analysis text to /workspace/documentation.md"
fi
GROUND_TRUTH="/tests/ground_truth.json"
REWARD_FILE="/logs/verifier/reward.txt"

TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

mkdir -p /logs/verifier

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


if [ ! -f "$GROUND_TRUTH" ]; then
    echo "ERROR: ground_truth.json not found at $GROUND_TRUTH"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

if [ ! -f "$DOC" ]; then
    echo "No documentation found at $DOC"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

python3 << 'PYEOF'
import hashlib
import json
import re
from pathlib import Path

DOC_PATH = Path('/workspace/documentation.md')
GT_PATH = Path('/tests/ground_truth.json')
REWARD_PATH = Path('/logs/verifier/reward.txt')

text = DOC_PATH.read_text(errors='ignore')
gt = json.loads(GT_PATH.read_text())

# Canonical human-authored source should always score 1.0 when provided verbatim.
doc_sha = hashlib.sha256(text.encode("utf-8")).hexdigest().lower()
canonical_sha = ((((gt.get("ground_truth_provenance") or {}).get("canonical_source") or {}).get("sha256") or "").lower())
if canonical_sha and doc_sha == canonical_sha:
    print("Canonical source SHA match: awarding 1.0")
    REWARD_PATH.write_text("1.00\n")
    raise SystemExit(0)


def check_any(patterns, body):
    for p in patterns:
        try:
            if re.search(p, body, re.IGNORECASE | re.DOTALL):
                return True
        except re.error:
            if p.lower() in body.lower():
                return True
    return False


def check_all(patterns, body):
    for p in patterns:
        try:
            if not re.search(p, body, re.IGNORECASE | re.DOTALL):
                return False
        except re.error:
            if p.lower() not in body.lower():
                return False
    return True


def ratio(items, all_patterns=False):
    score = 0.0
    total = 0.0
    for it in items:
        w = float(it.get('weight', 0.0))
        total += w
        ok = check_all(it.get('patterns', []), text) if all_patterns else check_any(it.get('patterns', []), text)
        if ok:
            score += w
    return (score / total) if total > 0 else 0.0

# Base checklist score (content-grounded only)
r_topics = ratio(gt.get('required_topics', []))
r_refs = ratio(gt.get('file_references', []))
r_flow = ratio(gt.get('data_flow', []), all_patterns=True)
r_ext = ratio(gt.get('extension_points', []))

w = gt.get('weights', {})
base = (
    r_topics * float(w.get('required_topics', 0.4)) +
    r_refs * float(w.get('file_references', 0.25)) +
    r_flow * float(w.get('data_flow', 0.2)) +
    r_ext * float(w.get('extension_points', 0.15))
)

# Hallucination penalty: invalid path mentions only.
penalty = 0.0
path_candidates = set(re.findall(r"(?:staging/src|pkg|cmd|api)/[A-Za-z0-9_./-]+\.go", text))
invalid = 0
for p in path_candidates:
    if not Path('/workspace', p).exists():
        invalid += 1
if path_candidates:
    invalid_ratio = invalid / len(path_candidates)
    penalty += min(0.35, invalid_ratio * 0.5)

final = max(0.0, min(1.0, base - penalty))

print('=== Score Breakdown ===')
print(f'base: {base:.3f}')
print(f'  topics={r_topics:.3f} refs={r_refs:.3f} flow={r_flow:.3f} ext={r_ext:.3f}')
print('=== Hallucination Check ===')
print(f'path_candidates={len(path_candidates)} invalid_paths={invalid} penalty={penalty:.3f}')
print(f'FINAL={final:.3f}')

REWARD_PATH.write_text(f"{final:.2f}\n")
PYEOF
