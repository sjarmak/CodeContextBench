#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT_DEFAULT="runs/staging/ccb_build_haiku_20260227_025524/baseline-local-direct"
TASK_DEFAULT="servo-scrollend-event-feat-001"

RUN_ROOT="${RUN_ROOT:-$RUN_ROOT_DEFAULT}"
TASK_ID="${TASK_ID:-$TASK_DEFAULT}"

usage() {
  cat <<'EOF'
Usage:
  scripts/handoff_monitor_scrollend.sh status
  scripts/handoff_monitor_scrollend.sh watch [SECONDS]
  scripts/handoff_monitor_scrollend.sh investigate

Environment overrides:
  RUN_ROOT   Run root (default: runs/staging/ccb_build_haiku_20260227_025524/baseline-local-direct)
  TASK_ID    Task id for investigation (default: servo-scrollend-event-feat-001)
EOF
}

latest_trial_dir() {
  local task_glob
  task_glob="${RUN_ROOT}"/*/"${TASK_ID}"__*
  ls -td ${task_glob} 2>/dev/null | head -n1 || true
}

print_summary_table() {
  if [[ ! -d "${RUN_ROOT}" ]]; then
    echo "Run root not found: ${RUN_ROOT}"
    return 1
  fi

  printf "%-40s %-10s %-8s %s\n" "task" "status" "reward" "trial_dir"
  printf "%-40s %-10s %-8s %s\n" "----------------------------------------" "----------" "--------" "---------"

  local stamp task_dir task_base task_name result_file status reward
  for stamp in "${RUN_ROOT}"/*; do
    [[ -d "${stamp}" ]] || continue
    task_dir="$(find "${stamp}" -mindepth 1 -maxdepth 1 -type d | head -n1 || true)"
    [[ -n "${task_dir}" ]] || continue
    task_base="$(basename "${task_dir}")"
    task_name="${task_base%%__*}"
    result_file="${task_dir}/result.json"

    if [[ -f "${result_file}" ]]; then
      status="$(jq -r '.status // "done"' "${result_file}" 2>/dev/null || echo "done")"
      reward="$(jq -r '.reward // .verifier_result.rewards.reward // "n/a"' "${result_file}" 2>/dev/null || echo "n/a")"
    else
      status="running"
      reward="n/a"
    fi

    printf "%-40s %-10s %-8s %s\n" "${task_name}" "${status}" "${reward}" "${task_dir}"
  done | sort
}

status_cmd() {
  echo "Run root: ${RUN_ROOT}"
  echo "Task id : ${TASK_ID}"
  echo
  echo "Active harbor processes:"
  ps -ef | rg "harbor run --path .*/benchmarks/ccb_build|run_selected_tasks.sh" | rg -v rg || echo "(none)"
  echo
  print_summary_table
}

investigate_cmd() {
  local trial result_file verifier_file reward_file trajectory
  trial="$(latest_trial_dir)"

  if [[ -z "${trial}" ]]; then
    echo "No trial directory found for task ${TASK_ID} under ${RUN_ROOT}"
    return 1
  fi

  result_file="${trial}/result.json"
  verifier_file="${trial}/verifier/test-stdout.txt"
  reward_file="${trial}/verifier/reward.txt"
  trajectory="${trial}/agent/trajectory.json"

  echo "Trial: ${trial}"
  echo
  echo "Artifact presence:"
  [[ -f "${result_file}" ]] && echo "  - result.json: yes" || echo "  - result.json: no"
  [[ -f "${verifier_file}" ]] && echo "  - verifier/test-stdout.txt: yes" || echo "  - verifier/test-stdout.txt: no"
  [[ -f "${reward_file}" ]] && echo "  - verifier/reward.txt: yes" || echo "  - verifier/reward.txt: no"
  [[ -f "${trial}/agent/claude-code.txt" ]] && echo "  - agent/claude-code.txt: yes" || echo "  - agent/claude-code.txt: no"
  [[ -f "${trajectory}" ]] && echo "  - agent/trajectory.json: yes" || echo "  - agent/trajectory.json: no"

  if [[ -f "${result_file}" ]]; then
    echo
    echo "result.json summary:"
    jq '{status,reward,exception_info,verifier_reward:(.verifier_result.rewards.reward // null)}' "${result_file}" || true
  fi

  if [[ -f "${verifier_file}" ]]; then
    echo
    echo "Verifier tail:"
    tail -n 60 "${verifier_file}" || true
  fi

  echo
  echo "Command return codes:"
  find "${trial}/agent" -maxdepth 2 -name return_code.txt -print -exec cat {} \; 2>/dev/null || echo "(none)"

  echo
  echo "Agent command stderr tails:"
  find "${trial}/agent" -maxdepth 2 -name stderr.txt -print | while read -r stderr_file; do
    echo "--- ${stderr_file}"
    tail -n 20 "${stderr_file}" || true
  done
}

watch_cmd() {
  local interval="${1:-30}"
  while true; do
    clear || true
    date
    echo
    status_cmd
    echo
    echo "Refreshing in ${interval}s (Ctrl+C to stop)"
    sleep "${interval}"
  done
}

main() {
  local cmd="${1:-}"
  case "${cmd}" in
    status)
      status_cmd
      ;;
    investigate)
      investigate_cmd
      ;;
    watch)
      watch_cmd "${2:-30}"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "${@}"
