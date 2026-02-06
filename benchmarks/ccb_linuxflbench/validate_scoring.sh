#!/bin/bash
# Validate test.sh scoring logic for all ccb_linuxflbench tasks.
# Creates mock fault_localization_result.json files and runs each
# test.sh in a temp environment to verify correct/partial/wrong scoring.
#
# Usage:  ./benchmarks/ccb_linuxflbench/validate_scoring.sh

set -e

BENCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMPBASE=$(mktemp -d /tmp/lfl-validate.XXXXXX)
trap "rm -rf $TMPBASE" EXIT

PASS=0
FAIL=0

# Ground truth for each task
declare -A GT_FILES=(
    ["lfl-acpi-207835"]="drivers/acpi/video_detect.c"
    ["lfl-wifi-206661"]="drivers/net/wireless/intel/iwlwifi/pcie/drv.c"
    ["lfl-nfs-117651"]="net/sunrpc/xprtsock.c"
    ["lfl-sata-203475"]="drivers/ata/libata-core.c"
    ["lfl-sound-53441"]="sound/pci/hda/hda_intel.c"
)

declare -A GT_METHODS=(
    ["lfl-acpi-207835"]="video_detect_dmi_table"
    ["lfl-wifi-206661"]="iwl_dev_info_table"
    ["lfl-nfs-117651"]="xs_sock_set_reuseport"
    ["lfl-sata-203475"]="ata_device_blacklist"
    ["lfl-sound-53441"]="DEFINE_PCI_DEVICE_TABLE"
)

# Run a single test scenario.
#   run_scenario <task_id> <scenario_name> <json_content> <expected_score>
run_scenario() {
    local task_id=$1
    local scenario=$2
    local json_content=$3
    local expected=$4

    local workdir="$TMPBASE/${task_id}/${scenario}"
    mkdir -p "$workdir/tests" "$workdir/logs-verifier"

    # Copy test.sh and patch absolute paths to use our temp dirs
    sed \
        -e "s|cd /workspace|cd $workdir|g" \
        -e "s|/workspace/fault_localization_result.json|$workdir/fault_localization_result.json|g" \
        -e "s|/logs/verifier|$workdir/logs-verifier|g" \
        "$BENCH_DIR/$task_id/tests/test.sh" > "$workdir/tests/test.sh"
    chmod +x "$workdir/tests/test.sh"

    # Write mock result (empty string means no file)
    if [ -n "$json_content" ]; then
        echo "$json_content" > "$workdir/fault_localization_result.json"
    fi

    # Run
    local reward
    if bash "$workdir/tests/test.sh" > "$workdir/stdout.txt" 2>&1; then
        reward=$(cat "$workdir/logs-verifier/reward.txt" 2>/dev/null || echo "MISSING")
    else
        reward=$(cat "$workdir/logs-verifier/reward.txt" 2>/dev/null || echo "ERROR")
    fi

    if [ "$reward" = "$expected" ]; then
        echo "  PASS  $task_id / $scenario  →  $reward (expected $expected)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $task_id / $scenario  →  $reward (expected $expected)"
        echo "        stdout: $(tail -3 "$workdir/stdout.txt" | tr '\n' ' ')"
        FAIL=$((FAIL + 1))
    fi
}

echo "=============================================="
echo "Validating ccb_linuxflbench test.sh scoring"
echo "=============================================="
echo ""

for task_id in "${!GT_FILES[@]}"; do
    gt_file="${GT_FILES[$task_id]}"
    gt_method="${GT_METHODS[$task_id]}"

    echo "── $task_id ──"

    # Scenario 1: No result file → 0.0
    run_scenario "$task_id" "no-result" "" "0.0"

    # Scenario 2: Invalid JSON → 0.0
    run_scenario "$task_id" "bad-json" "not json{{{" "0.0"

    # Scenario 3: Perfect result → 1.0
    # Fields(1) + file_exact(4) + method(3) + reasoning(1) + confidence(1) = 10/10
    run_scenario "$task_id" "perfect" \
        "{\"buggy_files\":[\"$gt_file\"],\"buggy_functions\":[\"$gt_method\"],\"confidence\":0.9,\"reasoning\":\"The bug is clearly in this function based on the report.\"}" \
        "1.0"

    # Scenario 4: Right file, wrong method → 0.7
    # Fields(1) + file_exact(4) + reasoning(1) + confidence(1) = 7/10
    run_scenario "$task_id" "file-only" \
        "{\"buggy_files\":[\"$gt_file\"],\"buggy_functions\":[\"wrong_function\"],\"confidence\":0.5,\"reasoning\":\"Found the file but guessed wrong on function.\"}" \
        "0.7"

    # Scenario 5: Wrong file, right method → 0.6
    # Fields(1) + method(3) + reasoning(1) + confidence(1) = 6/10
    run_scenario "$task_id" "method-only" \
        "{\"buggy_files\":[\"wrong/path.c\"],\"buggy_functions\":[\"$gt_method\"],\"confidence\":0.5,\"reasoning\":\"Found the function name but wrong file.\"}" \
        "0.6"

    # Scenario 6: Correct file in top-5 but not first → 0.7
    # Fields(1) + top5(1) + method(3) + reasoning(1) + confidence(1) = 7/10
    run_scenario "$task_id" "file-in-top5" \
        "{\"buggy_files\":[\"wrong/a.c\",\"wrong/b.c\",\"$gt_file\"],\"buggy_functions\":[\"$gt_method\"],\"confidence\":0.7,\"reasoning\":\"Listed multiple candidates, correct one is third.\"}" \
        "0.7"

    # Scenario 7: Everything wrong → 0.3
    # Fields(1) + reasoning(1) + confidence(1) = 3/10
    run_scenario "$task_id" "all-wrong" \
        "{\"buggy_files\":[\"wrong/file.c\"],\"buggy_functions\":[\"wrong_fn\"],\"confidence\":0.1,\"reasoning\":\"Total guess that turned out wrong.\"}" \
        "0.3"

    # Scenario 8: Missing fields → 0.0
    run_scenario "$task_id" "no-fields" \
        "{\"files\":[\"$gt_file\"],\"funcs\":[\"$gt_method\"]}" \
        "0.0"

    echo ""
done

echo "=============================================="
echo "Results: $PASS passed, $FAIL failed"
echo "=============================================="
if [ "$FAIL" -gt 0 ]; then
    echo "FIX the failing scenarios before running benchmarks."
    exit 1
else
    echo "All scoring scenarios validated."
fi
