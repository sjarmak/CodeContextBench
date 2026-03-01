# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes in Terraform

## Summary

Terraform generates phantom in-place update changes for resources with provider-schema-defined sensitive attributes because of an **asymmetry between how sensitivity marks are applied during refresh and how they are compared during planning**. The refresh path re-applies only marks from the prior state (excluding schema-defined marks), while the plan comparison checks for mark equality without accounting for the schema-defined marks that should be present on the planned value.

## Root Cause

The root cause is a **multi-layer sensitivity mark gap** spanning four packages:

1. **Graph Evaluation Layer** (`internal/terraform/node_resource_abstract_instance.go`): Provider responses are processed without schema-defined sensitive marks
2. **State Serialization Layer** (`internal/states/instance_object.go`): State storage only preserves marks that were already on the value, missing schema-defined marks
3. **Plan Comparison Layer** (`internal/terraform/node_resource_abstract_instance.go`): The mark comparison uses incomplete mark sets
4. **Expression Evaluation Layer** (`internal/terraform/evaluate.go`): Compensating workaround that applies schema marks only for expression evaluation, creating asymmetry

## Evidence

### 1. Provider Response Processing (Refresh Path)

**File:** `internal/terraform/node_resource_abstract_instance.go:619-723`

The `refresh()` method receives an unmarked provider response and re-applies marks from the prior state:

```go
// Line 620-626: Extract marks from prior state
priorVal := state.Value
var priorPaths []cty.PathValueMarks
if priorVal.ContainsMarked() {
    priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()
}

// Line 636-642: Provider returns unmarked value
resp = provider.ReadResource(providers.ReadResourceRequest{
    TypeName:     n.Addr.Resource.Resource.Type,
    PriorState:   priorVal,
    ...
})

// Line 718-720: Re-apply only prior marks to new value
if len(priorPaths) > 0 {
    ret.Value = ret.Value.MarkWithPaths(priorPaths)
}
```

**Critical Issue**: `priorPaths` contains only marks that were stored in state. Schema-defined sensitive attributes are NOT stored in state because the value never had those marks applied before encoding.

### 2. State Serialization (Incomplete Sensitivity Recording)

**File:** `internal/states/instance_object.go:94-137`

The `Encode()` method removes all marks and stores only those that were present:

```go
// Line 98: Unmark the value and extract mark paths
val, pvm := o.Value.UnmarkDeepWithPaths()

// Line 131: Store only the extracted marks
return &ResourceInstanceObjectSrc{
    AttrSensitivePaths:  pvm,  // Only marks that were on the value
    ...
}
```

**Critical Issue**: `pvm` (PathValueMarks) contains only marks that were on the value. Schema-defined sensitive attributes from the provider schema are never marked ON the value during refresh, so they are not included in `AttrSensitivePaths` stored in the state file.

The state file's `sensitive_attributes` section reflects incomplete sensitivity:
- ✅ Includes marks from variable references (e.g., `var.db_password` marked sensitive)
- ❌ Excludes schema-defined sensitive paths (e.g., `password` attribute with `Sensitive: true`)

### 3. Plan Comparison (Mark Asymmetry)

**File:** `internal/terraform/node_resource_abstract_instance.go:868-1208`

The `plan()` method extracts marks from config and prior state, then compares them:

```go
// Line 868-869: Extract marks from configuration and prior state
unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()

// Line 998-1000: Re-apply configuration marks to planned value
if len(unmarkedPaths) > 0 {
    plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
}

// Line 1018: Compare for RequiresReplace filtering
plannedChangedVal, plannedPathDiags := hcl.ApplyPath(plannedNewVal, path, nil)

// Line 1208: Convert NoOp to Update if marks differ
if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
    action = plans.Update
}
```

**Critical Issue**:
- `unmarkedPaths` contains only marks from the configuration (sensitive variable references)
- `priorPaths` contains only marks from prior state (excluding schema-defined marks)
- The comparison at line 1208 detects a difference because the planned value has configuration marks but the prior value doesn't have schema marks
- Since the underlying VALUES are identical (confirmed by line 1082), the diff is ONLY in sensitivity metadata

This causes the phantom in-place update even though `eqV.True()` at line 1083 would show no value changes.

### 4. Compensating Workaround (Asymmetric Application)

**File:** `internal/terraform/evaluate.go:689-723`

The expression evaluator applies schema-defined sensitive marks ONLY when reading resources for evaluation:

```go
// Line 689-695: Applied during planned value expression evaluation
if schema.ContainsSensitive() {
    afterMarks = append(afterMarks, schema.ValueMarks(val, nil)...)
}
instances[key] = val.MarkWithPaths(afterMarks)

// Line 714-723: Applied during current state expression evaluation
if schema.ContainsSensitive() {
    var marks []cty.PathValueMarks
    val, marks = val.UnmarkDeepWithPaths()
    marks = append(marks, schema.ValueMarks(val, nil)...)
    val = val.MarkWithPaths(marks)
}
instances[key] = val
```

**Critical Issue**: This compensating workaround is applied ONLY in the expression evaluator (`GetResource()`) when resources are read for evaluating HCL expressions. It does NOT apply to:
- Values during the plan comparison phase (line 1208)
- Values during state refresh (line 719)
- Values stored in state

This creates an asymmetry where:
- Values FOR EVALUATION are marked with schema-defined sensitivity
- Values FOR COMPARISON and STORAGE are NOT marked with schema-defined sensitivity

### 5. JSON Output Manifestation

**File:** `internal/command/jsonstate/state.go:402-406`

When generating `terraform show -json` output, the code applies schema marks to generate accurate sensitivity metadata:

```go
// Line 402-406: Schema marks ARE applied for JSON output
value, marks := riObj.Value.UnmarkDeepWithPaths()
if schema.ContainsSensitive() {
    marks = append(marks, schema.ValueMarks(value, nil)...)
}
s := SensitiveAsBool(value.MarkWithPaths(marks))
v, err := ctyjson.Marshal(s, s.Type())
```

However, this happens AFTER the state was already serialized without schema marks. The `sensitive_values` section in JSON output appears more complete than `sensitive_attributes` in the actual state file because this code layer applies marks during DISPLAY, not during STORAGE.

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`** (Graph Evaluation)
   - `refresh()`: Lines 619-723 - Doesn't apply schema marks to refreshed state
   - `plan()`: Lines 868-1208 - Compares marks without schema-defined sensitivity

2. **`internal/states/instance_object.go`** (State Serialization)
   - `Encode()`: Lines 94-137 - Stores incomplete sensitivity marks

3. **`internal/states/instance_object_src.go`** (State Deserialization)
   - `Decode()`: Lines 77-104 - Applies stored marks without schema marks

4. **`internal/terraform/evaluate.go`** (Expression Evaluation - Compensation Only)
   - `GetResource()`: Lines 689-695, 714-723 - Applies schema marks for evaluation only

5. **`internal/command/jsonstate/state.go`** (JSON Output)
   - `marshalResources()`: Lines 402-406, 453-456 - Applies schema marks during display

## Causal Chain

1. **Provider Response** → Provider returns unmarked value (providers don't mark values)
2. **Refresh Processing** → `refresh()` re-applies only prior-state marks (schema marks were never stored)
3. **State Encoding** → `Encode()` stores only marks on the value (excludes schema marks)
4. **State Storage** → State file has incomplete `sensitive_attributes`
5. **State Decoding** → `Decode()` applies stored marks (still missing schema marks)
6. **Plan Extraction** → `plan()` extracts `priorPaths` from decoded state (missing schema marks)
7. **Plan Comparison** → Mark equality check finds difference between `plannedNewVal` (has config marks) and `priorVal` (missing schema marks)
8. **Phantom Update** → Line 1208 converts `NoOp` to `Update` due to mark inequality despite value equality
9. **JSON Display** → `jsonstate.marshalResources()` applies schema marks for display, showing accurate sensitivity in JSON but incomplete in state file

## Recommendation

The fix requires ensuring schema-defined sensitive paths are present in the marks throughout the pipeline:

### Option A (Preferred): Apply Schema Marks at Source
- **When**: During `refresh()` at line 718, after retrieving the provider response
- **Where**: In `internal/terraform/node_resource_abstract_instance.go`
- **How**: After line 718, apply schema-defined marks using `schema.ValueMarks()` before storing the value
- **Benefit**: Ensures schema marks flow through the entire pipeline consistently

### Option B: Store Schema Marks During Encoding
- **When**: In `Encode()` before storing state
- **Where**: In `internal/states/instance_object.go:94-137`
- **How**: Before encoding, append schema-defined marks to the extracted marks
- **Benefit**: Ensures state file records complete sensitivity information
- **Challenge**: Requires access to provider schema during state encoding, which isn't currently available

### Option C: Apply Schema Marks During Plan Comparison
- **When**: In `plan()` before the mark equality check at line 1208
- **Where**: In `internal/terraform/node_resource_abstract_instance.go:1208`
- **How**: Augment both `plannedNewVal` marks and `priorPaths` with schema marks before comparison
- **Benefit**: Targeted fix that only affects plan phase
- **Challenge**: Still leaves state storage incomplete

### Diagnostic Steps
1. Compare `AttrSensitivePaths` in state file for resources with schema-defined sensitive attributes—should include full paths
2. Verify `terraform show -json` contains complete `sensitive_values` matching schema definitions
3. Check that phantom diffs disappear after refresh when schema marks are properly propagated
4. Ensure no false positives by verifying actual value changes still produce legitimate update actions

## Related Files to Review

- `internal/configs/configschema/schema.go` - Contains `ValueMarks()` and `ContainsSensitive()` methods
- `internal/lang/marks/marks.go` - Mark constants and utilities
- `internal/plans/objchange/objchange.go` - Value comparison logic
- `internal/command/jsonplan/plan.go` - How `BeforeSensitive` and `AfterSensitive` are populated for plan JSON output
