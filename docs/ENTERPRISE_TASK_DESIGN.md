# Enterprise Task Design

## Overview

Enterprise codebases differ from open-source projects in ways that affect AI agent performance: multi-team ownership, conflicting documentation, stale artifacts, partial context access, legacy dependencies, and polyglot service architectures. This document defines complexity dimensions and templates for simulating these conditions in CCB benchmark tasks.

## Complexity Dimensions

### 1. Multi-Team Ownership

**Simulation**: Workspace contains directories owned by different teams with distinct conventions (naming, error handling, logging). Agent is assigned to one team and must follow that team's patterns, not others.

**Template**: Create 2-3 team directories with intentionally different coding styles. Task instruction assigns the agent to a specific team. Verifier checks that new code follows the assigned team's conventions.

### 2. Conflicting Documentation

**Simulation**: Workspace has multiple docs (README, CONTRIBUTING, inline comments) that contradict each other on the correct approach. Agent must identify the authoritative source.

**Template**: Place a README with outdated instructions and inline code comments with current behavior. Task requires the agent to implement a feature — the correct approach follows the code, not the stale README. Verifier checks the implementation matches actual codebase patterns.

### 3. Stale Artifacts

**Simulation**: Workspace includes deprecated config files, unused imports, dead code paths, and outdated test fixtures. Agent must distinguish active from stale code.

**Template**: Include both `config.yaml` (current) and `config.yaml.bak` (stale, different values). Task requires reading config — agent must use the active file. Verifier checks correct config values are used.

### 4. Partial Context

**Simulation**: Agent has access to a subset of the codebase. Some referenced modules, types, or APIs are unavailable. Agent must infer interfaces from usage patterns and available documentation.

**Template**: Workspace contains `service-a/` with full source but `service-b/` only has type stubs and README. Task requires implementing code in `service-a` that calls `service-b`. Verifier checks the integration matches `service-b`'s actual API (defined in stubs).

### 5. Legacy Dependencies

**Simulation**: Workspace uses an older library version with different API than current docs. Agent must work with what's installed, not what's in latest documentation.

**Template**: Pin a dependency to an older version in requirements.txt. Task requires using that library. Verifier checks the code uses the old API (which is what's available in the environment), not the new API from current docs.

### 6. Polyglot Services

**Simulation**: Workspace contains services in multiple languages (e.g., Python backend + TypeScript frontend + Go CLI). Agent must modify code across language boundaries while maintaining interface contracts.

**Template**: Create a 2-language workspace with a shared API contract (e.g., JSON schema). Task requires changes in both languages. Verifier checks both sides compile and the contract is maintained.

## Integration with Harbor Format

Each enterprise complexity dimension maps to standard Harbor task structure:

```
benchmarks/ccb_governance/{task_name}/
  task.toml              # Standard + governance_metadata section
  instruction.md         # Role assignment, team context, access scope
  environment/
    Dockerfile           # Build context, workspace setup
    workspace/           # Multi-team/multi-service layout
  tests/
    test.sh              # Correctness verification
```

**task.toml additions** for enterprise tasks:

```toml
[task.metadata]
complexity_dimension = "multi_team_ownership"  # Which dimension this tests
permitted_paths = ["team-platform/"]
restricted_paths = ["team-payments/"]
```

**Dockerfile pattern**: Copy the workspace directory structure, install language-specific dependencies. Keep environments minimal — the complexity is in the workspace layout, not the toolchain.

**Instruction.md pattern**: Establish the agent's role ("You are a developer on the Platform team"), state access constraints in natural language ("You may read team-payments/ for reference but must not modify it"), and describe the task. Never reference the evaluator or scoring.
