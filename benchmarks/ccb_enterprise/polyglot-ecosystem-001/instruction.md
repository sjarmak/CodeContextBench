# Add Evaluation Metadata Field to Flipt (Proto + Go)

**Repository:** flipt-io/flipt
**Access Scope:** You may modify files in `rpc/flipt/evaluation/` (protobuf schema + generated code) and `internal/server/evaluation/` (Go server). You may read `rpc/flipt/flipt.proto`, `internal/storage/`, and `internal/server/middleware/` to understand existing patterns.

## Context

Flipt is a feature flag platform built with Go and gRPC. Its API is defined in Protocol Buffer (`.proto`) files under `rpc/flipt/`, with generated Go code alongside. The evaluation server in `internal/server/evaluation/` constructs protobuf response objects returned to clients.

Operators have requested that evaluation responses include a `segment_match_type` field so clients can see whether the evaluation matched a segment using `ALL` (all constraints matched) or `ANY` (at least one constraint matched) logic. This information is already available in the evaluation flow but is not exposed in the response.

## Task

Add a `segment_match_type` string field to the evaluation responses. This requires changes to **both** the protobuf schema (`.proto` file) and the Go server code that constructs responses — a cross-language change.

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. **Understand the protobuf schema** — Read `rpc/flipt/evaluation/evaluation.proto`:
   - Find `VariantEvaluationResponse` and `BooleanEvaluationResponse` message types
   - Understand existing field numbering (you must pick the NEXT available field number)
   - Note: `VariantEvaluationResponse` already has `segment_keys` — the new field complements this

2. **Understand the Go evaluation flow** — Read `internal/server/evaluation/evaluation.go`:
   - `Variant()` method constructs `VariantEvaluationResponse` — find where it sets `SegmentKeys`
   - `Boolean()` method constructs `BooleanEvaluationResponse` — find where segment matching occurs
   - `Batch()` method wraps individual evaluations — ensure batch responses include the new field too

3. **Understand the storage layer** — Read `internal/storage/storage.go`:
   - Find `EvaluationRule` struct — it has a `SegmentOperator` field that indicates ALL vs ANY
   - The evaluation server already reads rules from storage — find where `SegmentOperator` is accessed
   - Also read `rpc/flipt/flipt.proto` to find the `SegmentOperator` enum definition

4. **Add the field to protobuf schema** — In `rpc/flipt/evaluation/evaluation.proto`:
   - Add `string segment_match_type = N;` to `VariantEvaluationResponse` (use next field number after existing fields)
   - The value should be "ALL", "ANY", or "" (empty when no segment matched)

5. **Update generated Go code** — In `rpc/flipt/evaluation/evaluation.pb.go`:
   - Add the `SegmentMatchType string` field to the `VariantEvaluationResponse` Go struct
   - Add a `GetSegmentMatchType() string` getter method following the pattern of existing getters
   - This is the generated code — match the exact patterns used by other fields

6. **Propagate to server code** — In `internal/server/evaluation/evaluation.go`:
   - In the `Variant()` method, after the evaluation logic determines which rule matched, set `SegmentMatchType` on the response
   - The rule's `SegmentOperator` (from `storage.EvaluationRule`) tells you ALL vs ANY
   - Convert the operator to a string: `flipt.SegmentOperator_AND_SEGMENT_OPERATOR` → "ALL", `flipt.SegmentOperator_OR_SEGMENT_OPERATOR` → "ANY"

### Hints

- `evaluation.proto` field numbers: VariantEvaluationResponse currently has fields 1-9. Use field number 10.
- In `evaluation.go`, the `Variant()` method around line 25-92 iterates `lastRank` rules. The matched rule's `SegmentOperator` is accessible.
- The storage `EvaluationRule` struct contains `SegmentOperator flipt.SegmentOperator` — trace how `flipt.SegmentOperator` enum maps to string values
- Look at how `SegmentKeys` is set in the response — set `SegmentMatchType` at the same location
- In `evaluation.pb.go`, search for `GetSegmentKeys` to find the pattern for adding a new getter
- Do NOT regenerate code with protoc — manually add the field to both .proto and .pb.go

## Success Criteria

- `evaluation.proto` has `segment_match_type` field in `VariantEvaluationResponse`
- `evaluation.pb.go` has matching `SegmentMatchType` field and getter
- `evaluation.go` populates `SegmentMatchType` from rule's `SegmentOperator`
- Proto field number is valid (no collision with existing fields)
- Changes span both proto and Go files (cross-language change)
- Go code compiles: `go build ./internal/server/evaluation/...`
