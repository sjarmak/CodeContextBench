# Canonical Evaluation Policy

This document defines the stable evaluation policy for the canonical
CodeScaleBench task set.

Use this document when you need to answer four questions precisely:

- what every canonical task must do
- what is allowed to vary by verifier family
- how artifact-oriented task variants relate to deterministic verification
- how reporting should interpret reward versus pass/fail

## Universal Policy

These rules apply to every canonical task, regardless of suite or verifier
family:

- Every task has a deterministic verifier.
- Every deterministic verifier writes `/logs/verifier/reward.txt`.
- Canonical verifiers should also write
  `/logs/verifier/validation_result.json`.
- `validation_result.json` is the semantic verifier contract; `reward.txt` is
  the scalar compatibility artifact.
- Reporting must preserve continuous `reward` separately from pass semantics.

The deterministic verifier is the authoritative benchmark outcome producer.
Artifact-oriented flows do not replace it; they give the verifier a structured
or family-specific input surface.

## Hybrid Output Policy

Canonical tasks intentionally use a hybrid output model. The benchmark does
not require one universal agent artifact format.

Supported output-contract patterns include:

- `answer_json_native`: the verifier directly scores a structured
  `/workspace/answer.json` contract
- `answer_json_bridge`: an artifact-oriented image or wrapper maps structured
  agent output into an existing deterministic verifier flow
- `repo_state`: the verifier scores repository state and tests, with no
  required structured artifact
- other family-specific contracts such as `solution_json` or
  `report_markdown`

Implications:

- Deterministic verification is universal.
- Artifact support is family-specific.
- `answer.json` is common, but it is not universal benchmark policy.
- Presence of `Dockerfile.artifact_only` does not imply the same verifier
  family or the same artifact semantics across tasks.

The maintained snapshot of current canonical coverage lives in
`configs/canonical_evaluation_audit.json`. Use that audit to answer
family-level questions such as which suites are `answer_json_native`,
`answer_json_bridge`, or still migrating to `validation_result.json`.

## Canonical Verifier Contract

Canonical verifiers should publish semantics through
`/logs/verifier/validation_result.json` using
`docs/reference/VALIDATION_RESULT_SCHEMA.md`.

That sidecar is where verifiers declare:

- `status` and `scorable`
- `scorer_family`
- `reward`
- `pass_threshold`
- `passed`
- `output_contract`
- `sub_scores`
- structured failure context

Downstream consumers should treat `passed` as the authoritative solved/pass
flag. They should not recompute solved status from `reward > 0`.

## Reporting Policy

Reporting and export code must keep these concepts separate:

- `reward`: continuous scalar produced by the deterministic verifier
- `passed`: authoritative pass/fail flag from verifier semantics
- `pass_threshold`: task or family policy threshold
- `scorer_family`: family that gives meaning to the reward
- `output_contract`: verifier-facing output mode

Mean reward is still useful, but mixed-family aggregates require caveats. A
0.7 from `test_ratio`, `oracle_checks`, and `checklist` should not be treated
as silently calibrated equivalents.

Operationally:

- use `passed` / `status` for pass-rate tables when available
- use `reward` for continuous-score summaries
- surface `scorer_family` and `output_contract` in reports and exports
- caveat or partition mixed-family reward aggregates

## Launch And Validation Expectations

Preflight checks, smoke runs, and launch docs should assume:

- the deterministic verifier always exists
- required artifacts come from the task's published output contract
- missing required artifacts are invalid-output conditions, not ordinary
  benchmark misses
- artifact-oriented image variants must preserve the same verifier semantics,
  even when the agent-facing output path differs by family

The benchmark should therefore validate artifact expectations from task
metadata and verifier contract, not from a blanket assumption that every task
must produce `/workspace/answer.json`.
