ABC Audit Report: ccb_codereview
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 17  Fail: 0  Warn: 4  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    WARN   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_crossrepo
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 18  Fail: 0  Warn: 3  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_dependeval
Grade: A  |  Overall: PASS

  Criteria: 29  Pass: 14  Fail: 0  Warn: 5  Skip: 10
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    WARN   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_dibench
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 16  Fail: 0  Warn: 5  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    WARN   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_investigation
Grade: A  |  Overall: PASS

  Criteria: 29  Pass: 16  Fail: 0  Warn: 3  Skip: 10
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_k8sdocs
Grade: A  |  Overall: PASS

  Criteria: 29  Pass: 17  Fail: 0  Warn: 2  Skip: 10
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_largerepo
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 18  Fail: 0  Warn: 3  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_linuxflbench
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 17  Fail: 0  Warn: 4  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_locobench
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 19  Fail: 0  Warn: 2  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    PASS   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_pytorch
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 17  Fail: 0  Warn: 4  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    WARN   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_repoqa
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 18  Fail: 0  Warn: 3  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    PASS   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    WARN   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_swebenchpro
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 19  Fail: 0  Warn: 2  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    PASS   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    WARN   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_sweperf
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 20  Fail: 0  Warn: 1  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    PASS   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    PASS   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

ABC Audit Report: ccb_tac
Grade: A  |  Overall: PASS

  Criteria: 32  Pass: 18  Fail: 0  Warn: 3  Skip: 11
  Critical failures: 0  Important pass rate: 1.0

  ID     Status Sev          Title                                             
  ────── ────── ──────────── ──────────────────────────────────────────────────
  T.1    PASS   CRITICAL     Dockerfile pins versions (no :latest, pinned apt)
  T.2    SKIP   IMPORTANT    No unreachable external URLs in instruction.md
  T.3    PASS   IMPORTANT    No shared API keys in task.toml/Dockerfile
  T.4    PASS   CRITICAL     Git checkouts use exact SHA (not HEAD/latest)
  T.5    PASS   CRITICAL     instruction.md doesn't leak solution content
  T.6    SKIP   CRITICAL     Dockerfile exists, deterministic base image
  T.7    SKIP   IMPORTANT    task.toml metadata matches selected_benchmark_task
  T.8    WARN   RECOMMENDED  Oracle/reference solution exists
  T.9    SKIP   RECOMMENDED  No systematic verifier false-positive pattern
  T.10   SKIP   IMPORTANT    No shared mutable state between tasks
  O.a    SKIP   CRITICAL     Verifier handles equivalent solutions
  O.b    SKIP   IMPORTANT    Verifier rejects negated/inverted solutions
  O.c    PASS   CRITICAL     Empty/no-op solution gets reward=0
  O.d    PASS   CRITICAL     test.sh has error handling (set -e or traps)
  O.e    WARN   IMPORTANT    test.sh covers multiple aspects (>1 assertion)
  O.f    SKIP   RECOMMENDED  Edge cases handled (partial solutions, wrong forma
  O.g    SKIP   IMPORTANT    test.sh is deterministic (no uncontrolled randomne
  O.h    PASS   IMPORTANT    reward.txt output format is consistent
  O.i    PASS   RECOMMENDED  Verifier supports partial credit (0.0-1.0 range)
  R.1    PASS   CRITICAL     All tasks have instruction.md + test.sh
  R.2    PASS   CRITICAL     No MCP/Sourcegraph contamination in instruction.md
  R.3    PASS   IMPORTANT    Benchmark describes what it measures
  R.4    PASS   IMPORTANT    sdlc_phase populated in selected_benchmark_tasks.j
  R.5    PASS   RECOMMENDED  ERROR_CATALOG.md covers all fingerprinted errors
  R.6    SKIP   IMPORTANT    Multiple config results available for comparison
  R.7    WARN   CRITICAL     Baseline config results exist
  R.8    PASS   IMPORTANT    TASK_SELECTION.md documents methodology
  R.9    PASS   IMPORTANT    Difficulty distribution is documented and balanced
  R.10   SKIP   RECOMMENDED  Token/cost data captured per run
  R.11   PASS   RECOMMENDED  Error fingerprinting covers >=10 patterns
  R.12   PASS   IMPORTANT    Reproducibility instructions in CLAUDE.md
  R.13   PASS   RECOMMENDED  MANIFEST.json tracks run results

