# terraform-compact-diff-fmt-feat-001: Compact Diff Formatter

## Task Type: Feature Implementation (Output Formatting)

Implement a condensed plan diff formatter for Terraform.

## Key Reference Files
- `internal/command/format/diff.go` — existing formatter
- `internal/plans/changes.go` — change types
- `internal/plans/plan.go` — Plan struct
- `internal/addrs/resource.go` — resource addressing

## Search Strategy
- Search for `DiffFormatter` in `internal/command/format/`
- Search for `plans.Action` for action type constants
- Search for `AbsResourceInstance` for addressing pattern
