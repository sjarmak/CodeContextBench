#!/bin/bash
# Reward: semantic_similarity (0.0-1.0) — content, file references, and pattern matching
# Harbor test script for api_upgrade_01 — patch validation with fallback diff collection
#
# Primary (a): Check for explicit /logs/agent/patch.diff
# Fallback (b): Auto-generate diff from workspace changes in /ccb_crossrepo/src/

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

set -x

# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi

# NOTE: set -e intentionally NOT used — fallback logic requires graceful failure handling

# --- Timeout guard: re-exec under timeout if not already guarded ---
if [ -z "$__TIMEOUT_GUARD" ]; then
    export __TIMEOUT_GUARD=1
    timeout 600 bash "$0" "$@" || {
        rc=$?
        if [ $rc -eq 124 ]; then
            mkdir -p /logs/verifier
            echo "0.0" > /logs/verifier/reward.txt
            echo "Verification timed out after 600s" >&2
        fi
        exit 0
    }
    exit 0
fi

PATCH_FILE="/logs/agent/patch.diff"
EXPECTED_CHANGES="/tests/expected_changes.json"
CORPUS_ROOT="/ccb_crossrepo"
VALIDATOR="/tests/validate_patch_inline.py"
REWARD_FILE="/logs/verifier/reward.txt"
VALIDATION_RESULT="/logs/verifier/validation_result.json"

echo "=== api_upgrade_01 Patch Validation ===" >&2
echo "" >&2

# ============================================
# Step 1: Locate or generate the patch
# ============================================
EFFECTIVE_PATCH="$PATCH_FILE"

if [ -f "$PATCH_FILE" ] && [ -s "$PATCH_FILE" ]; then
    echo "Found explicit patch at $PATCH_FILE ($(wc -l < "$PATCH_FILE") lines)" >&2
else
    echo "No patch at $PATCH_FILE — trying fallback diff collection..." >&2

    # Fallback: generate diff from git changes in the source repos
    FALLBACK_PATCH=$(mktemp /logs/verifier/fallback_XXXXXX.diff)
    > "$FALLBACK_PATCH"

    for repo_dir in "$CORPUS_ROOT"/src/*/; do
        if [ -d "$repo_dir/.git" ]; then
            repo_name=$(basename "$repo_dir")
            echo "  Checking $repo_name for changes..." >&2
            cd "$repo_dir"
            # Capture both staged and unstaged changes
            git diff HEAD -- . >> "$FALLBACK_PATCH" 2>/dev/null || true
            # Also capture untracked files as diffs (only if they match expected file paths)
            EXPECTED_FILE_LIST=$(python3 -c "import json; [print(p) for p in json.load(open('$EXPECTED_CHANGES')).get('expected_files',[])]" 2>/dev/null || true)
            git ls-files --others --exclude-standard | while read -r f; do
                # Only include untracked files that match an expected file path
                is_expected=false
                for ef in $EXPECTED_FILE_LIST; do
                    case "$ef" in *"$f"*) is_expected=true; break;; esac
                    case "$f" in *"$ef"*) is_expected=true; break;; esac
                done
                if [ "$is_expected" = true ] && [ -f "$f" ]; then
                    echo "diff --git a/$f b/$f" >> "$FALLBACK_PATCH"
                    echo "new file mode 100644" >> "$FALLBACK_PATCH"
                    echo "--- /dev/null" >> "$FALLBACK_PATCH"
                    echo "+++ b/$f" >> "$FALLBACK_PATCH"
                    wc_lines=$(wc -l < "$f")
                    echo "@@ -0,0 +1,$wc_lines @@" >> "$FALLBACK_PATCH"
                    sed 's/^/+/' "$f" >> "$FALLBACK_PATCH"
                fi
            done
        fi
    done

    # Fallback: also scan /workspace/ for files matching expected paths
    # OpenHands agents write to /workspace/ instead of /ccb_crossrepo/src/
    if [ -d "/workspace" ] && [ ! -s "$FALLBACK_PATCH" ]; then
        echo "  Scanning /workspace/ for expected file matches..." >&2
        EXPECTED_FILE_LIST=$(python3 -c "import json; [print(p) for p in json.load(open('$EXPECTED_CHANGES')).get('expected_files',[])]" 2>/dev/null || true)

        # Check git repos under /workspace for staged/unstaged changes
        for ws_git_dir in $(find /workspace -name .git -type d -maxdepth 4 2>/dev/null); do
            ws_repo_dir=$(dirname "$ws_git_dir")
            echo "  Checking workspace repo $ws_repo_dir for changes..." >&2
            cd "$ws_repo_dir"
            git diff HEAD -- . >> "$FALLBACK_PATCH" 2>/dev/null || true
            git ls-files --others --exclude-standard | while read -r f; do
                is_expected=false
                for ef in $EXPECTED_FILE_LIST; do
                    case "$ef" in *"$f"*) is_expected=true; break;; esac
                    case "$f" in *"$ef"*) is_expected=true; break;; esac
                done
                if [ "$is_expected" = true ] && [ -f "$f" ]; then
                    echo "diff --git a/$f b/$f" >> "$FALLBACK_PATCH"
                    echo "new file mode 100644" >> "$FALLBACK_PATCH"
                    echo "--- /dev/null" >> "$FALLBACK_PATCH"
                    echo "+++ b/$f" >> "$FALLBACK_PATCH"
                    wc_lines=$(wc -l < "$f")
                    echo "@@ -0,0 +1,$wc_lines @@" >> "$FALLBACK_PATCH"
                    sed 's/^/+/' "$f" >> "$FALLBACK_PATCH"
                fi
            done
        done

        # Also scan for non-git files in /workspace that match expected paths
        if [ ! -s "$FALLBACK_PATCH" ]; then
            for ef in $EXPECTED_FILE_LIST; do
                # Try direct path under /workspace
                candidate="/workspace/$ef"
                if [ -f "$candidate" ]; then
                    echo "  Found expected file at $candidate" >&2
                    echo "diff --git a/$ef b/$ef" >> "$FALLBACK_PATCH"
                    echo "new file mode 100644" >> "$FALLBACK_PATCH"
                    echo "--- /dev/null" >> "$FALLBACK_PATCH"
                    echo "+++ b/$ef" >> "$FALLBACK_PATCH"
                    wc_lines=$(wc -l < "$candidate")
                    echo "@@ -0,0 +1,$wc_lines @@" >> "$FALLBACK_PATCH"
                    sed 's/^/+/' "$candidate" >> "$FALLBACK_PATCH"
                fi
                # Also try finding the basename anywhere under /workspace
                ef_basename=$(basename "$ef")
                find /workspace -name "$ef_basename" -type f 2>/dev/null | while read -r found_file; do
                    # Verify the suffix of the path matches
                    case "$found_file" in *"$ef"*)
                        if [ -f "$found_file" ]; then
                            echo "  Found expected file at $found_file" >&2
                            echo "diff --git a/$ef b/$ef" >> "$FALLBACK_PATCH"
                            echo "new file mode 100644" >> "$FALLBACK_PATCH"
                            echo "--- /dev/null" >> "$FALLBACK_PATCH"
                            echo "+++ b/$ef" >> "$FALLBACK_PATCH"
                            wc_lines=$(wc -l < "$found_file")
                            echo "@@ -0,0 +1,$wc_lines @@" >> "$FALLBACK_PATCH"
                            sed 's/^/+/' "$found_file" >> "$FALLBACK_PATCH"
                        fi
                    ;; esac
                done
            done
        fi
    fi

    if [ -s "$FALLBACK_PATCH" ]; then
        echo "Fallback diff collected: $(wc -l < "$FALLBACK_PATCH") lines" >&2
        EFFECTIVE_PATCH="$FALLBACK_PATCH"
        # Also save it for inspection
        cp "$FALLBACK_PATCH" "/logs/agent/patch.diff" 2>/dev/null || true
    else
        echo "ERROR: No changes found in any source repository" >&2
        echo "0.0" > "$REWARD_FILE"
        exit 0
    fi
fi

# ============================================
# Step 2: Validate the patch
# ============================================
echo "" >&2
echo "Validating patch against expected changes..." >&2

# Inline validation — self-contained, no external dependencies
echo "Using inline validation..." >&2
python3 - "$EFFECTIVE_PATCH" "$EXPECTED_CHANGES" "$VALIDATION_RESULT" << 'PYEOF'
import json, re, sys
from pathlib import Path

patch_path, expected_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

with open(patch_path) as f:
    patch_text = f.read()
with open(expected_path) as f:
    expected = json.load(f)

# Parse unified diff
files = {}
current = None
for line in patch_text.splitlines():
    if line.startswith("diff --git "):
        parts = line.split(" b/", 1)
        if len(parts) == 2:
            current = parts[1]
            files[current] = {"added": [], "removed": []}
    elif current:
        if line.startswith("+") and not line.startswith("+++"):
            files[current]["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            files[current]["removed"].append(line[1:])

if not files:
    result = {"overall_score": 0.0, "error": "No files in patch"}
else:
    # File coverage
    exp_files = expected.get("expected_files", [])
    matched = []
    for ef in exp_files:
        for pf in files:
            if pf == ef or pf.endswith(ef) or ef.endswith(pf):
                matched.append(ef)
                break
    file_cov = len(matched) / len(exp_files) if exp_files else 1.0

    # Pattern matching
    all_added = "\n".join(l for f in files.values() for l in f["added"])
    all_removed = "\n".join(l for f in files.values() for l in f["removed"])
    pat_scores = []
    pat_results = {"removed": {}, "added": {}}
    for p in expected.get("expected_patterns", {}).get("removed", []):
        try: found = bool(re.search(p, all_removed))
        except: found = p in all_removed
        pat_results["removed"][p] = found
        pat_scores.append(1.0 if found else 0.0)
    for p in expected.get("expected_patterns", {}).get("added", []):
        try: found = bool(re.search(p, all_added))
        except: found = p in all_added
        pat_results["added"][p] = found
        pat_scores.append(1.0 if found else 0.0)
    pat_score = sum(pat_scores) / len(pat_scores) if pat_scores else 1.0

    result = {
        "overall_score": round(0.4 * file_cov + 0.6 * pat_score, 4),
        "file_coverage": round(file_cov, 4),
        "pattern_score": round(pat_score, 4),
        "files_in_patch": list(files.keys()),
        "files_matched": matched,
        "pattern_results": pat_results,
    }

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2), file=sys.stderr)
print(result["overall_score"])
PYEOF

if [ -f "$VALIDATION_RESULT" ]; then
    REWARD=$(python3 -c "import json; print(json.load(open('$VALIDATION_RESULT'))['overall_score'])" 2>/dev/null)
    if [ -n "$REWARD" ]; then
        echo "$REWARD" > "$REWARD_FILE"
        echo "Validation complete — Reward: $REWARD" >&2
    else
        echo "0.0" > "$REWARD_FILE"
        echo "WARNING: Could not parse validation result, defaulting to 0.0" >&2
    fi
else
    echo "0.0" > "$REWARD_FILE"
    echo "WARNING: No validation result file generated, defaulting to 0.0" >&2
fi

# Dual-score: independently score both direct edits and answer.json
[ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
