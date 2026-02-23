#!/usr/bin/env bash
# Migrate sg-evals repos used by CodeContextBench to sg-evals org.
# Uses bare clone + mirror push to preserve all branches (incl. scip-enabled).
set -euo pipefail

WORKDIR="/tmp/sg-evals-migration"
LOGFILE="$WORKDIR/migration.log"
PARALLEL=3

mkdir -p "$WORKDIR"
echo "Migration started at $(date -u)" | tee "$LOGFILE"

# Full list of sg-evals repos to migrate
REPOS=(
  CodeCoverageSummary--dibench
  DotNetKoans--dibench
  Ghost--b43bfc85
  IAMActionHunter--dibench
  OpenHands--latest
  ansible--379058e1
  ansible--4c5ce5a1
  ansible--811093f0
  ansible--e40889e7
  ansible--eea46a0d
  aspnetcore--87525573
  bustub--d5f79431
  cal.com--4b99072b
  cgen--dibench
  containerd--317286ac
  django--674eda1c
  dotenv-expand--dibench
  element-web--cf3c899d
  element-web--f14374a5
  envoy--50ea83e6
  envoy--7b8baff1
  etcd--d89978e8
  etcd-io-etcd
  expressjs-express
  flask--798e006f
  flipt--3d5a345f
  flipt--9f8127f2
  flipt--b433bd05
  flipt--c188284f
  grafana
  grafana-loki
  grafana-mimir
  grpc--957dba5e
  kubernetes--stripped
  kubernetes-api
  kubernetes-client-go
  kubernetes-kubernetes
  linux--07c4ee00
  linux--07cc49f6
  linux--11a48a5a
  linux--55b2af1c
  linux--fa5941f4
  llama.cpp--56399714
  lodash
  markdown--dibench
  navidrome--9c3b4561
  navidrome--d0dceae0
  nodebb--76c6e302
  nodebb--f1a80d48
  nodejs-node
  numpy
  numpy--a639fbf5
  openlibrary--7f6b722a
  openlibrary--92db3454
  openlibrary--c506c1b0
  openlibrary--d109cc7e
  pandas
  pandas--41968da5
  pcap-parser--dibench
  prisma-prisma
  qutebrowser--233cb1cc
  qutebrowser--394bfaed
  qutebrowser--3fd8e129
  qutebrowser--e5340c44
  requests--421b8733
  scikit-learn
  scikit-learn--cb7e82dd
  scipy
  similar-asserts--dibench
  teleport--3587cca7
  teleport--7744f72c
  teleport--8302d467
  teleport--c1b1c6a1
  terraform--24236f4f
  terraform--7637a921
  tutanota--f3ffe17a
  vuls--1832b4ee
  vuls--4c04acbd
  vuls--d18e7a75
  webclients--369fd37d
  webclients--8be4f6cb
  webclients--c6f65d20
  webclients--caf10ba9
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

  # Check if source repo exists on GitHub
  if ! gh api "/repos/$src" --silent 2>/dev/null; then
    echo "[$idx/$TOTAL] SKIP (source not found): $name" | tee -a "$LOGFILE"
    echo "SKIP_SOURCE_NOT_FOUND" > "$status_file"
    return 0
  fi

  # Check if target already exists
  if gh api "/repos/$dst" --silent 2>/dev/null; then
    echo "[$idx/$TOTAL] SKIP (already exists): $name" | tee -a "$LOGFILE"
    echo "SKIP_ALREADY_EXISTS" > "$status_file"
    return 0
  fi

  # Get source description
  local desc
  desc=$(gh api "/repos/$src" --jq '.description // ""' 2>/dev/null || echo "")

  # Create target repo (public)
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

  # Bare clone from source
  rm -rf "$clone_dir"
  if ! git clone --bare "https://github.com/$src.git" "$clone_dir" 2>>"$LOGFILE"; then
    echo "[$idx/$TOTAL] FAIL (clone): $name" | tee -a "$LOGFILE"
    echo "FAIL_CLONE" > "$status_file"
    rm -rf "$clone_dir"
    return 0
  fi

  # Mirror push to target
  if ! git -C "$clone_dir" push --mirror "https://github.com/$dst.git" 2>>"$LOGFILE"; then
    echo "[$idx/$TOTAL] FAIL (push): $name" | tee -a "$LOGFILE"
    echo "FAIL_PUSH" > "$status_file"
    rm -rf "$clone_dir"
    return 0
  fi

  # Cleanup clone
  rm -rf "$clone_dir"

  echo "[$idx/$TOTAL] OK: $name" | tee -a "$LOGFILE"
  echo "OK" > "$status_file"
}

# Run with limited parallelism
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

# Summary
echo "" | tee -a "$LOGFILE"
echo "=== MIGRATION SUMMARY ===" | tee -a "$LOGFILE"
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
echo "Migration finished at $(date -u)" | tee -a "$LOGFILE"
