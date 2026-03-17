#!/usr/bin/env bash
# Migrate remaining sg-evals repos to sg-evals org (batch 2).
# Same approach: bare clone + mirror push to preserve all branches.
set -euo pipefail

WORKDIR="/tmp/sg-evals-migration-b2"
LOGFILE="$WORKDIR/migration.log"
PARALLEL=3

mkdir -p "$WORKDIR"
echo "Migration batch 2 started at $(date -u)" | tee "$LOGFILE"

REPOS=(
  NodeBB--8fd8079a
  QuantLib--dbdcc14e
  Strata--66225ca9
  TensorRT-LLM--b98f3fca
  ansible--b2a289dc
  api--f32ed1d6
  api--v0.32.0
  apimachinery--b2e9f88f
  argo-cd--206a6eec
  argo-cd--v2.13.2
  autoscaler--0ccfef95
  camel--1006f047
  cilium--a2f97aa8
  cilium--ad6b298d
  cilium--v1.16.5
  client-go--v0.32.0
  curl--09e25b9d
  data-plane-api--84e84367
  django--6b995cff
  django--9e7cc2b6
  django--e295033
  emissary--3bbdbe0f
  envoy--1d0ba73a
  envoy--25f893b4
  envoy--d7809ba2
  envoy--v1.31.1
  envoy--v1.31.2
  envoy--v1.32.1
  envoy--v1.33.0
  express--4.21.1
  flink--0cc95fcc
  go-control-plane--71637ad6
  grafana--26d36ec
  grafana--v11.4.0
  grpc-go--3be7e2d0
  grpc-go--v1.56.2
  grpcurl--25c896aa
  istio--2300e245
  istio--44d0e58e
  istio--4c1f845d
  istio--f8af3cae
  istio--f8c9b973
  kafka--0753c489
  kafka--0cd95bc2
  kafka--3.8.0
  kafka--3.9.0
  kafka--be816b82
  kafka--e678b4b
  kubernetes--2e534d6
  kubernetes--31bf3ed4
  kubernetes--8c9c67c0
  kubernetes--v1.30.0
  kubernetes--v1.32.0
  loki--v3.3.4
  net--88194ad8
  node--v22.13.0
  numpy--v2.2.2
  pandas--v2.2.3
  postgres--5a461dc4
  prometheus
  prometheus--ba14bc4
  prometheus--v2.52.0
  prometheus--v3.2.1
  pytorch--5811a8d7
  pytorch--863edc78
  pytorch--ca246612
  pytorch--cbe1a35d
  pytorch--d18007a1
  qutebrowser--50efac08
  qutebrowser--6b320dc1
  qutebrowser--6dd402c0
  qutebrowser--deeb15d6
  rust--01f6ddf7
  scikit-learn--1.6.1
  scipy--v1.15.1
  servo--be6a2f99
  ssh--v0.3.4
  teleport--0415e422
  terraform--9658f9df
  terraform--a3dc5711
  terraform--f65c52c8
  terraform--v1.10.3
  terraform--v1.9.0
  terraform-provider-aws--e9b4629e
  tutanota--f373ac38
  vscode--1.96.0
  vscode--138f619c
  vscode--17baf841
  vscode--69d110f2
  vuls--139f3a81
  webclients--369fd37d
  webclients--8be4f6cb
  webclients--c6f65d20
  wish--v0.5.0
)

TOTAL=${#REPOS[@]}
echo "Total repos to migrate: $TOTAL" | tee -a "$LOGFILE"

migrate_one() {
  local name="$1"
  local idx="$2"
  local src="sg-evals/$name"
  local dst="sg-evals/$name"
  local clone_dir="$WORKDIR/$name.git"
  local status_file="$WORKDIR/${name}.status"

  echo "[$idx/$TOTAL] Starting: $name" | tee -a "$LOGFILE"

  if ! gh api "/repos/$src" --silent 2>/dev/null; then
    echo "[$idx/$TOTAL] SKIP (source not found): $name" | tee -a "$LOGFILE"
    echo "SKIP_SOURCE_NOT_FOUND" > "$status_file"
    return 0
  fi

  if gh api "/repos/$dst" --silent 2>/dev/null; then
    echo "[$idx/$TOTAL] SKIP (already exists): $name" | tee -a "$LOGFILE"
    echo "SKIP_ALREADY_EXISTS" > "$status_file"
    return 0
  fi

  local desc
  desc=$(gh api "/repos/$src" --jq '.description // ""' 2>/dev/null || echo "")

  if ! gh api /orgs/sg-evals/repos \
    --method POST \
    -f "name=$name" \
    -f "description=$desc" \
    -f "visibility=public" \
    --silent 2>>"$LOGFILE"; then
    echo "[$idx/$TOTAL] FAIL (create): $name" | tee -a "$LOGFILE"
    echo "FAIL_CREATE" > "$status_file"
    return 0
  fi

  rm -rf "$clone_dir"
  if ! git clone --bare "https://github.com/$src.git" "$clone_dir" 2>>"$LOGFILE"; then
    echo "[$idx/$TOTAL] FAIL (clone): $name" | tee -a "$LOGFILE"
    echo "FAIL_CLONE" > "$status_file"
    rm -rf "$clone_dir"
    return 0
  fi

  if ! git -C "$clone_dir" push --mirror "https://github.com/$dst.git" 2>>"$LOGFILE"; then
    echo "[$idx/$TOTAL] FAIL (push): $name" | tee -a "$LOGFILE"
    echo "FAIL_PUSH" > "$status_file"
    rm -rf "$clone_dir"
    return 0
  fi

  rm -rf "$clone_dir"
  echo "[$idx/$TOTAL] OK: $name" | tee -a "$LOGFILE"
  echo "OK" > "$status_file"
}

running=0
idx=0
for name in "${REPOS[@]}"; do
  idx=$((idx + 1))
  migrate_one "$name" "$idx" &
  running=$((running + 1))
  if [ "$running" -ge "$PARALLEL" ]; then
    wait -n 2>/dev/null || true
    running=$((running - 1))
  fi
done
wait

echo "" | tee -a "$LOGFILE"
echo "=== MIGRATION BATCH 2 SUMMARY ===" | tee -a "$LOGFILE"
ok=0; skip_src=0; skip_exist=0; fail_create=0; fail_clone=0; fail_push=0; unknown=0
for name in "${REPOS[@]}"; do
  sf="$WORKDIR/${name}.status"
  if [ -f "$sf" ]; then
    s=$(cat "$sf")
    case "$s" in
      OK) ok=$((ok+1)) ;;
      SKIP_SOURCE_NOT_FOUND) skip_src=$((skip_src+1)); echo "  SOURCE_NOT_FOUND: $name" | tee -a "$LOGFILE" ;;
      SKIP_ALREADY_EXISTS) skip_exist=$((skip_exist+1)) ;;
      FAIL_CREATE) fail_create=$((fail_create+1)); echo "  FAIL_CREATE: $name" | tee -a "$LOGFILE" ;;
      FAIL_CLONE) fail_clone=$((fail_clone+1)); echo "  FAIL_CLONE: $name" | tee -a "$LOGFILE" ;;
      FAIL_PUSH) fail_push=$((fail_push+1)); echo "  FAIL_PUSH: $name" | tee -a "$LOGFILE" ;;
      *) unknown=$((unknown+1)); echo "  UNKNOWN($s): $name" | tee -a "$LOGFILE" ;;
    esac
  else
    unknown=$((unknown+1))
    echo "  NO_STATUS: $name" | tee -a "$LOGFILE"
  fi
done

echo "" | tee -a "$LOGFILE"
echo "OK:                 $ok" | tee -a "$LOGFILE"
echo "Skip (exists):      $skip_exist" | tee -a "$LOGFILE"
echo "Skip (src missing): $skip_src" | tee -a "$LOGFILE"
echo "Fail (create):      $fail_create" | tee -a "$LOGFILE"
echo "Fail (clone):       $fail_clone" | tee -a "$LOGFILE"
echo "Fail (push):        $fail_push" | tee -a "$LOGFILE"
echo "Unknown:            $unknown" | tee -a "$LOGFILE"
echo "Migration batch 2 finished at $(date -u)" | tee -a "$LOGFILE"
