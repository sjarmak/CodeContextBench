# cilium-policy-audit-logger-feat-001: Policy Audit Logger

## Task Type: Feature Implementation (Logging Infrastructure)

Implement structured audit logging for policy decisions in Cilium.

## Key Reference Files
- `pkg/policy/distillery.go` — policy evaluation
- `pkg/policy/selectorcache.go` — SelectorCache
- `pkg/logging/logfields/logfields.go` — log field constants
- `pkg/lock/lock.go` — lock primitives

## Search Strategy
- Search for `scopedLog` in `pkg/policy/` for logging patterns
- Search for `logfields` for structured field conventions
- Search for `lock.Mutex` for thread-safety patterns
