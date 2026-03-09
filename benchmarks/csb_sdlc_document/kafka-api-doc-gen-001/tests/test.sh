#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen API reference tasks: scores /workspace/documentation.md
# against ground-truth API methods, behavioral notes, usage examples, and structure.
#
# Scoring weights (from ground_truth.json):
#   api_methods:              0.40
#   behavioral_notes:         0.30
#   usage_examples:           0.20
#   documentation_structure:  0.10
#
set -e
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


# ── Check prerequisites ────────────────────────────────────────────────
if [ ! -f "$GROUND_TRUTH" ]; then
    echo "ERROR: ground_truth.json not found at $GROUND_TRUTH"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

if [ ! -f "$DOC" ]; then
    echo "No documentation found at $DOC"
    echo "Agent did not produce the required output."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

DOC_SIZE=$(wc -c < "$DOC")
if [ "$DOC_SIZE" -lt 500 ]; then
    echo "Documentation is too short (${DOC_SIZE} bytes). Likely incomplete."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

echo "Scoring API reference documentation ($DOC_SIZE bytes)..."
echo "Ground truth: $GROUND_TRUTH"
echo ""

# ── Delegate scoring to Python ────────────────────────────────────────
python3 << 'PYEOF'
import json, re, sys

DOC_PATH = "/workspace/documentation.md"
GT_PATH = "/tests/ground_truth.json"
REWARD_PATH = "/logs/verifier/reward.txt"

with open(DOC_PATH) as f:
    doc = f.read()
with open(GT_PATH) as f:
    gt = json.load(f)

def check_patterns(patterns, text):
    """Return True if at least one pattern matches (case-insensitive)."""
    for p in patterns:
        try:
            if re.search(p, text, re.IGNORECASE | re.DOTALL):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False

sc = gt["scoring_categories"]

# ── Score api_methods ──────────────────────────────────────────────────
print("=== API Methods ===")
m_score, m_total = 0.0, 0.0
for item in sc["api_methods"]["items"]:
    m_total += item["weight"]
    if check_patterns(item["patterns"], doc):
        m_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']:.3f})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']:.3f})")
m_ratio = m_score / m_total if m_total > 0 else 0
print(f"  API methods score: {m_score:.3f} / {m_total:.3f} = {m_ratio:.2f}")
print()

# ── Score behavioral_notes ─────────────────────────────────────────────
print("=== Behavioral Notes ===")
b_score, b_total = 0.0, 0.0
for item in sc["behavioral_notes"]["items"]:
    b_total += item["weight"]
    if check_patterns(item["patterns"], doc):
        b_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']:.3f})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']:.3f})")
b_ratio = b_score / b_total if b_total > 0 else 0
print(f"  Behavioral notes score: {b_score:.3f} / {b_total:.3f} = {b_ratio:.2f}")
print()

# ── Score usage_examples ───────────────────────────────────────────────
print("=== Usage Examples ===")
u_score, u_total = 0.0, 0.0
for item in sc["usage_examples"]["items"]:
    u_total += item["weight"]
    if check_patterns(item["patterns"], doc):
        u_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']:.3f})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']:.3f})")
u_ratio = u_score / u_total if u_total > 0 else 0
print(f"  Usage examples score: {u_score:.3f} / {u_total:.3f} = {u_ratio:.2f}")
print()

# ── Score documentation_structure ──────────────────────────────────────
print("=== Documentation Structure ===")
s_score, s_total = 0.0, 0.0
for item in sc["documentation_structure"]["items"]:
    s_total += item["weight"]
    if check_patterns(item["patterns"], doc):
        s_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']:.3f})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']:.3f})")
s_ratio = s_score / s_total if s_total > 0 else 0
print(f"  Structure score: {s_score:.3f} / {s_total:.3f} = {s_ratio:.2f}")
print()

# ── Compute weighted total ─────────────────────────────────────────────
w_methods = sc["api_methods"]["weight"]
w_behavioral = sc["behavioral_notes"]["weight"]
w_examples = sc["usage_examples"]["weight"]
w_structure = sc["documentation_structure"]["weight"]

total = (m_ratio * w_methods +
         b_ratio * w_behavioral +
         u_ratio * w_examples +
         s_ratio * w_structure)

print("=== Final Score ===")
print(f"  API methods:  {m_ratio:.2f} * {w_methods} = {m_ratio * w_methods:.3f}")
print(f"  Behavioral:   {b_ratio:.2f} * {w_behavioral} = {b_ratio * w_behavioral:.3f}")
print(f"  Examples:     {u_ratio:.2f} * {w_examples} = {u_ratio * w_examples:.3f}")
print(f"  Structure:    {s_ratio:.2f} * {w_structure} = {s_ratio * w_structure:.3f}")
print(f"  TOTAL:        {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
