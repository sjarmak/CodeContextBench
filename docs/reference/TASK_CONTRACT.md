# Benchmark Task Contract

## Agent Navigation
- `docs/reference/README.md` is the reference index for agent navigation.
- This file is the stable contract for publishing CodeScaleBench tasks that should run across Harbor-compatible harnesses.
- Use `scripts/validate_tasks_preflight.py` to enforce the low-cost checks in this spec before launch.

This document defines the minimum task contract for registry-ready benchmark
tasks. The goal is to make a task runnable under any Harbor-compatible harness
without task-specific patches, hidden path assumptions, or harness-specific
startup behavior.

Registry-ready also means the base task can run under plain local Docker for
users who are not using Daytona or Harbor-managed cloud infrastructure.

## Core Principle

A task must define its execution contract in the task itself, not in a
particular harness.

Harnesses may differ in startup flow, transcript format, or tool availability.
The task image, instruction, and verifier must still agree on:

- where the working repo lives
- where the agent should write its required artifact
- which files the verifier is allowed to depend on
- what counts as a valid task outcome versus an infrastructure invalid

For canonical tasks, this task-level execution contract sits inside the hybrid
evaluation policy documented in
`docs/reference/CANONICAL_EVALUATION_POLICY.md`: deterministic verifier reward
is universal, while required artifacts remain family-specific.

## Required Task Contract

Every task should expose one canonical contract:

- `TASK_WORKDIR`: the directory the agent should treat as its workspace
- `TASK_REPO_ROOT`: the repo root the verifier should score against
- `TASK_OUTPUT`: the required primary output artifact, if the task requires one

Recommended defaults:

- `TASK_WORKDIR=/workspace` for most tasks
- `TASK_REPO_ROOT=$TASK_WORKDIR`
- `TASK_OUTPUT=/logs/agent/solution.md` for narrative answers
- `TASK_OUTPUT=/workspace/solution.json`, `/workspace/review.json`, or `/workspace/answer.json` for structured-output tasks

Not every canonical task requires `answer.json`. `TASK_OUTPUT` should describe
the actual verifier-facing contract for that family, including repo-state tasks
that do not require a structured artifact.

If a task uses `/app` instead of `/workspace`, that is valid, but the task must
use it consistently across:

- `instruction.md`
- `tests/test.sh` or `tests/eval.sh`
- `environment/Dockerfile`
- `environment/Dockerfile.sg_only`
- `environment/Dockerfile.artifact_only` when present

Do not rely on a harness to guess these paths.

For third-party harnesses, the baseline image should remain directly runnable
with ordinary Docker mounts for `/tests` and `/logs`. Harbor-specific helper
paths are allowed in sg-only or artifact variants, but the base task contract
must not require a Harbor-only orchestrator feature.

## Verifier Rules

A robust verifier must:

- read its workspace contract from task-defined paths or env, not from harness-specific assumptions
- fail clearly when the required output artifact is missing
- distinguish `invalid run` from `valid benchmark fail`
- avoid depending on a harness transcript or final message format

Missing required output is an invalid run when the verifier cannot establish
that the agent actually produced a scorable answer. It should not silently look
like a clean `reward=0.0` benchmark miss.

Canonical tasks should treat `reward.txt` as the scalar compatibility artifact
and `validation_result.json` as the semantic verifier contract. The JSON
sidecar is where verifiers should record scorer family, pass semantics,
sub-scores, and failure context.

Artifact-oriented variants should preserve this separation. A wrapper that asks
the agent for `answer.json` may feed or bridge into an existing deterministic
verifier, but it does not change the underlying requirement that reward and
pass/fail semantics come from the verifier contract rather than from the mere
presence of an artifact.

At minimum, verifiers should:

- emit a clear error for missing required output
- write reward artifacts only after classifying whether the run was scorable
- for canonical tasks, also write `/logs/verifier/validation_result.json`
  using `docs/reference/VALIDATION_RESULT_SCHEMA.md`
- avoid hardcoded assumptions like `cd /app` unless that is the published task contract

## Image Variant Parity

All image variants for a task must preserve the same verifier-facing contract.

That includes:

- same logical workdir
- same expected output location
- same verifier dependencies
- same repo-restore semantics when the verifier needs the full repo

Important rule:

- `Dockerfile.sg_only` may remove or truncate local source for the agent, but it must not change the verifier contract.

If the verifier depends on restored source, the sg-only variant must provide a
restore contract such as:

- `/tmp/.sg_only_clone_manifest.json`
- `/tmp/.sg_only_mode`
- `/tests/sgonly_verifier_wrapper.sh`

If the verifier depends on `/repo_full`, `/utils`, or another image-provided
path, the sg-only and artifact variants must preserve that dependency.

The baseline image should not depend on Daytona-specific SDKs, sidecars, or
mount conventions. If a task truly needs an orchestrator-specific feature, that
requirement must be documented explicitly instead of being implied by the
verifier.

## Resource Contract

Task resource requests should reflect real needs, not conservative guesses.

Rules:

- request only the storage the task actually needs
- treat `storage > 10G` as exceptional and justify it in task metadata or suite notes
- prefer making the task runnable on standard Daytona limits unless the repo genuinely exceeds them
- do not inherit `20G` as a generator default for shallow-clone grep or
  document-only tasks

Overprovisioned storage requests create avoidable routing failures and make task
portability worse.

## Harness Independence

A registry-ready task must not depend on:

- Claude Code transcript layout
- OpenHands plugin startup behavior
- MCP tool side effects
- Harbor exception formatting
- a specific agent producing a final natural-language summary

The verifier should score files, repo changes, and explicit outputs. It should
not need to know which harness produced them.

## What Counts As Invalid

These should be classified as invalid process outcomes, not benchmark misses:

- required output artifact missing
- verifier cannot find the declared workdir or repo root
- sg-only variant cannot restore the repo the verifier needs
- agent runtime crashed before producing any scorable output
- infrastructure rejected the task before execution, such as sandbox create failure or storage-cap rejection

These may be valid benchmark failures:

- required output exists but is wrong
- tests run and fail on the agent's changes
- structured artifact parses but does not satisfy task requirements

## Author Checklist

Before publishing a task, confirm:

- `instruction.md` names the required output artifact when the task needs one
- `tests/test.sh` or `tests/eval.sh` uses the published task paths consistently
- `Dockerfile`, `Dockerfile.sg_only`, and `Dockerfile.artifact_only` expose the same verifier contract
- sg-only mode includes a restore path when verification needs the full repo
- missing output is classified invalid, not hidden as a normal zero
- `task.toml` storage is justified and not inflated by default
- `python3 scripts/validate_tasks_preflight.py --task <task_dir>` passes
- new or changed tasks also pass `--smoke-runtime` before large batch use
- curated smoke coverage includes regression sentinels for task families that
  previously needed harness or variant fixes

## CI / Validation Guidance

`scripts/validate_tasks_preflight.py` should be treated as the minimum gate.

It should catch at least:

- hardcoded task paths without a contract variable fallback
- `Dockerfile` versus `Dockerfile.sg_only` workdir drift
- verifier references to paths not provided by task images
- sg-only restore-contract gaps for `/repo_full`-style verifiers
- storage requests above standard Daytona limits

That validator is intentionally cheap. It will not catch every runtime issue,
but it should catch the common portability failures before they burn compute.
