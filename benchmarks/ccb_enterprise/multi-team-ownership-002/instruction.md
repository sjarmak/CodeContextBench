# Add Evaluation Latency Tracking

**Repository:** flipt-io/flipt
**Your Team:** Evaluation Team
**Access Scope:** You own `internal/server/evaluation/`. You may read other packages to understand codebase patterns and interfaces, but all code changes must stay within your package.

## Context

You are a developer on the Flipt Evaluation Team. Your team is responsible for the feature flag evaluation engine that determines flag variant assignments. Other teams own storage, analytics, middleware, transport, and configuration — you may read their code to understand patterns, but must not modify their packages.

## Feature Request

**From:** VP Engineering
**Priority:** P1
**Context:** Preparing for SOC 2 compliance — we need observability into evaluation performance

We need to track how long feature flag evaluations take so we can set SLOs and identify performance regressions. Currently, we have no visibility into evaluation latency — when users report slow flag evaluations, we have no data to diagnose the issue.

Add a duration tracking component to the evaluation engine that:
- Records the wall-clock duration of each evaluation
- Provides aggregate statistics: total count, average duration, and P99 latency
- Is safe for concurrent use (our evaluation server handles many simultaneous gRPC requests)

### Deliverables

1. Create `internal/server/evaluation/duration.go` with a `DurationTracker` struct
2. Integrate it into the evaluation server — each evaluation should record its duration
3. All three evaluation paths (boolean, variant, and batch) must be instrumented
4. The code must compile

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. New file at `internal/server/evaluation/duration.go`
2. `DurationTracker` struct with methods to record durations and retrieve statistics (count, average, P99)
3. Thread-safe implementation
4. Integrated into the evaluation server and wired into all evaluation methods
5. All changes within `internal/server/evaluation/`
6. Code compiles: `go build ./internal/server/evaluation/...`

## Success Criteria

- `duration.go` exists with `DurationTracker` struct
- Thread-safe implementation
- Server struct integrates the tracker
- Evaluation methods record durations
- Go code compiles
- No changes outside `internal/server/evaluation/`
