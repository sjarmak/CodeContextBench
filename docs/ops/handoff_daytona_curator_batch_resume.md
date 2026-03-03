# Handoff: Resume Daytona Curator Batch — 24 Remaining SDLC Tasks

## Goal
Complete ground truth generation for the remaining 24 SDLC tasks, then commit and push all ground_truth.json files.

## Current Status
- **32/56 tasks completed** in the first Daytona parallel run (session killed by VM spindown)
- **24 tasks still missing** ground_truth.json
- **136 total SDLC ground_truth.json files** exist (104 pre-existing + 32 new)
- Code changes to `scripts/daytona_curator_runner.py` and `scripts/context_retrieval_agent.py` are **complete and tested** — NOT committed yet
- The second retry run (`run2`) was killed by the VM spindown before making progress

### Breakdown of 24 remaining tasks
```
 8 csb_sdlc_test    (code reviews: aspnetcore, calcom, curl, envoy, ghost, terraform, vscode; coverage-gap-001; unitgen-go)
 5 csb_sdlc_debug   (ansible, 3x qutebrowser, tutanota, vuls)
 3 csb_sdlc_secure  (django: audit-trail, legacy-dep, sensitive-file)
 2 csb_sdlc_fix     (pytorch: relu-gelu-fusion, tracer-graph-cleanup)
 1 csb_sdlc_feature (bustub-hyperloglog-impl)
 1 csb_sdlc_design  (etcd-grpc-api-upgrade)
 1 csb_sdlc_refactor (python-http-class-naming)
 1 csb_sdlc_understand (django-template-inherit-recall)
```

### Why 24 failed in batch 1
- **6 tasks returned 0 files** (curator ran but JSON extraction failed or agent output had no files list):
  - pytorch-relu-gelu-fusion-fix-001, django-legacy-dep-vuln-001, etcd-grpc-api-upgrade-001, django-audit-trail-implement-001, python-http-class-naming-refac-001, test-coverage-gap-001
- **18 tasks timed out or sandbox hung** — the `as_completed(timeout=1080)` expired and `ThreadPoolExecutor.__exit__` blocked waiting for sandbox cleanup. These were mostly large-repo tasks (pytorch, ansible, teleport) or tasks that started late in the queue.

### Known bug: `as_completed` timeout causes process hang
The `for future in as_completed(futures, timeout=...)` pattern raises `TimeoutError` when the timeout expires, which isn't caught outside the loop. The `ThreadPoolExecutor.__exit__` then blocks waiting for all futures. Fix: wrap the `for` loop in `try/except TimeoutError` and cancel remaining futures.

## Files Changed (not yet committed)

### `scripts/daytona_curator_runner.py` (major refactor, +560/-85 lines)
- Added SDLC mode: `--sdlc-all`, `--mcp-all`, `--suite`, `--task-dir`, `--missing-only` flags
- `_extract_repo_info_for_sandbox()`: 4-strategy repo URL extraction:
  1. Dockerfile `git clone` URLs (sg-evals mirrors)
  2. `# Repo:` comment (SWEAP images, e.g. element-hq/element-web)
  3. `# Source: org/repo (commit)` (SWEAP debug, e.g. flipt-io/flipt)
  3b. SWEAP FROM tag parsing (tutanota — instance ID format)
  4. `TAC_REPO_MAP` for bustub (cmu-db/bustub) and openhands (All-Hands-AI/OpenHands)
- `setup_curator_sandbox()`: now accepts `repos: List[Dict]` for multi-repo cloning
- `run_curator_in_sandbox()`: added `user_msg` and `workdir` params for SDLC mode
- `process_sdlc_task()`: new function — parses task locally, builds user message with `build_user_message()`, runs curator in sandbox, writes ground truth with `write_curator_outputs()`
- `_run_sdlc_mode()` / `_run_contextbench_mode()`: split main() into dual-mode dispatch
- Existing ContextBench mode preserved via `process_task()` (updated for new `repos` list signature)

### `scripts/context_retrieval_agent.py` (+51 lines)
- `_resolve_repos()`: Added Strategy 4 (`# Source: org/repo (commit)` parsing), Strategy 4b (SWEAP FROM tag parsing), Strategy 5 (TAC_REPO_MAP)

## Commands to Resume

```bash
# 1. Source environment
source .env.local

# 2. Verify dry run shows 24 tasks
python3 scripts/daytona_curator_runner.py --sdlc-all --missing-only --dry-run

# 3. Run the remaining 24 tasks (note: may need the as_completed fix first)
python3 scripts/daytona_curator_runner.py --sdlc-all --missing-only --parallel 20

# 4. Verify 0 remaining
python3 scripts/daytona_curator_runner.py --sdlc-all --missing-only --dry-run
# Should show: Total: 0 tasks

# 5. Spot-check outputs
python3 -m json.tool benchmarks/csb_sdlc_debug/flipt-auth-cookie-regression-prove-001/tests/ground_truth.json | head -20

# 6. Commit everything
git add scripts/context_retrieval_agent.py scripts/daytona_curator_runner.py
git add benchmarks/csb_sdlc_*/*/tests/ground_truth.json benchmarks/csb_sdlc_*/*/tests/ground_truth_meta.json
git commit -m "feat: add SDLC mode to Daytona curator runner + batch ground truth generation

Refactor daytona_curator_runner.py to support CodeScaleBench SDLC tasks
alongside existing ContextBench calibration mode. Adds multi-strategy repo
resolution (git clone URLs, # Repo:, # Source:, SWEAP FROM tags, TAC map),
multi-repo sandbox cloning, and ground_truth.json output via
write_curator_outputs().

Also adds Strategies 4/4b/5 to _resolve_repos() in
context_retrieval_agent.py for # Source: parsing, SWEAP FROM tag parsing,
and TAC image repo mapping.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

git push
```

## Open Risks / Unknowns
1. **`as_completed` hang bug**: The `_run_sdlc_mode` function's `for future in as_completed(...)` can hang the process if the timeout fires. Fix by adding `try/except TimeoutError` around the for loop.
2. **6 "no files" tasks**: These ran successfully but the curator agent didn't produce parseable JSON with a `files` list. May need prompt tweaks or manual inspection of what the curator actually returned. Consider adding `--verbose` for these specific tasks to capture the raw output.
3. **Large repo timeouts**: pytorch, ansible, teleport take 5-10 min just to clone. The 900s sandbox timeout may be tight. Consider `--depth 1` for shallow clones where commit isn't needed.
4. **`.` target dir edge case**: Some sg-evals Dockerfiles clone to `.` (e.g., vscode, postgres, flipt). This produces `name="."` and `workdir="/workspace/."`. It works but is ugly — consider normalizing to the slug's repo name.

## Next Best Command
```bash
# Fix the as_completed hang, then rerun:
source .env.local && python3 scripts/daytona_curator_runner.py --sdlc-all --missing-only --parallel 20 2>&1 | tee /tmp/daytona_sdlc_run3.log
```
