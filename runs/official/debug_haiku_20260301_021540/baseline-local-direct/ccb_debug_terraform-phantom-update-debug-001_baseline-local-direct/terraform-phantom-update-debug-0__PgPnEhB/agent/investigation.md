# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place updates for resources with provider-schema-defined sensitive attributes because the code never applies schema sensitivity marks to planned values during the planning phase. These marks are only applied late in the evaluator (for expression evaluation), creating an asymmetry where the planned state lacks schema marks but comparison code detects the mark difference and converts NoOp actions to Updates. Additionally, the state file serialization never captures schema-defined sensitivity, causing incomplete `sensitive_values` in JSON output.

## Root Cause

The root cause is an **asymmetry in sensitivity mark application** across three code paths:

1. **Planning Phase** (`internal/terraform/node_resource_abstract_instance.go` - `plan()` method):
   - Provider responses come back **without any marks** (providers are forbidden from adding marks)
   - Code applies marks from **config values only** (line 999: `plannedNewVal.MarkWithPaths(unmarkedPaths)`)
   - **Never applies** marks from provider schema's `Sensitive: true` declarations
   - Planned state is stored with incomplete marks

2. **State Serialization** (`internal/states/instance_object.go` - `Encode()` method):
   - Line 98: `val, pvm := o.Value.UnmarkDeepWithPaths()` extracts marks from the value
   - Line 131: `AttrSensitivePaths: pvm` saves only marks that exist on the value
   - Since schema marks were never on the planned value, they're never serialized to state
   - State file records incomplete sensitivity metadata

3. **Evaluation Phase** (`internal/terraform/evaluate.go` - `GetResource()` method):
   - Lines 689-695 and 714-723: Schema marks ARE applied here via `schema.ValueMarks(val, nil)`
   - **But only during expression evaluation**, not during planning
   - This creates late-binding of schema sensitivity that doesn't affect the plan phase

## Evidence

### Provider Response Has No Marks
- **File**: `internal/terraform/node_resource_abstract_instance.go`
- **Line 916**: `plannedNewVal := resp.PlannedState`
- **Fact**: Provider's `PlanResourceChange()` returns values without any marks (by protocol design)

### Plan Function Applies Config Marks Only
- **File**: `internal/terraform/node_resource_abstract_instance.go`
- **Lines 865-869**:
  ```go
  unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
  unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()
  ```
  - `unmarkedPaths` extracts marks from the config value (config-based sensitivity)
  - `priorPaths` extracts marks from the prior state (also config-based)

- **Lines 998-1000**:
  ```go
  unmarkedPlannedNewVal := plannedNewVal
  if len(unmarkedPaths) > 0 {
      plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
  }
  ```
  - Only config marks from `unmarkedPaths` are applied, NOT schema marks

- **Lines 1167-1169** (replace path): Same pattern - only config marks

### Refresh Function Perpetuates Config-Only Marks
- **File**: `internal/terraform/node_resource_abstract_instance.go`
- **Lines 623-626**:
  ```go
  var priorPaths []cty.PathValueMarks
  if priorVal.ContainsMarked() {
      priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()
  }
  ```
  - Extracts marks from prior state
  - `priorPaths` contains only marks that were stored in state file

- **Lines 718-720**:
  ```go
  if len(priorPaths) > 0 {
      ret.Value = ret.Value.MarkWithPaths(priorPaths)
  }
  ```
  - Re-applies marks from prior state
  - Since prior state only had config marks, no schema marks are added here

### State Serialization Saves Incomplete Sensitivity
- **File**: `internal/states/instance_object.go`
- **Lines 94-137** (`Encode()` method):
  ```go
  val, pvm := o.Value.UnmarkDeepWithPaths()  // Line 98
  // ... serialization ...
  return &ResourceInstanceObjectSrc{
      // ...
      AttrSensitivePaths:  pvm,  // Line 131
      // ...
  }, nil
  ```
  - `pvm` contains only marks that are ON the value at serialization time
  - Since planned value never had schema marks applied, they're not in `pvm`
  - State file's `AttrSensitivePaths` is incomplete

### State Decoding Restores Incomplete Marks
- **File**: `internal/states/instance_object_src.go`
- **Lines 88-91**:
  ```go
  if os.AttrSensitivePaths != nil {
      val = val.MarkWithPaths(os.AttrSensitivePaths)
  }
  ```
  - Restores marks from `AttrSensitivePaths` when decoding state
  - These marks are incomplete (missing schema marks)

### Evaluator Applies Schema Marks Late
- **File**: `internal/terraform/evaluate.go`
- **Lines 689-695** (planned resources):
  ```go
  afterMarks := change.AfterValMarks
  if schema.ContainsSensitive() {
      afterMarks = append(afterMarks, schema.ValueMarks(val, nil)...)
  }
  instances[key] = val.MarkWithPaths(afterMarks)
  ```
  - Schema marks ARE applied via `schema.ValueMarks()`
  - **But only during expression evaluation**, not during planning

- **Lines 714-723** (current state resources):
  ```go
  if schema.ContainsSensitive() {
      var marks []cty.PathValueMarks
      val, marks = val.UnmarkDeepWithPaths()
      marks = append(marks, schema.ValueMarks(val, nil)...)
      val = val.MarkWithPaths(marks)
  }
  ```
  - Same compensating logic applied to state resources for evaluation

### Mark Comparison Detects Asymmetry
- **File**: `internal/terraform/node_resource_abstract_instance.go`
- **Line 1208**:
  ```go
  if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
      action = plans.Update
  }
  ```
  - Converts NoOp to Update if marks differ
  - The condition triggers when:
    - Unmarked values are equal (action was NoOp)
    - But marks between planned and prior state differ
  - In the schema-sensitivity case, the prior state lacks schema marks that ideally should be present

### JSON Output Shows Incomplete Sensitivity
- **File**: `internal/command/jsonplan/values.go`
- **Lines 212-235**:
  ```go
  markedAfter := changeV.After  // Line 213
  changeV.After, _ = changeV.After.UnmarkDeep()  // Line 219

  s := jsonstate.SensitiveAsBool(markedAfter)  // Line 230
  v, err := ctyjson.Marshal(s, s.Type())  // Line 231
  resource.SensitiveValues = v  // Line 235
  ```
  - `markedAfter` is the value from the plan change (which lacks schema marks)
  - `SensitiveAsBool()` converts marks to boolean sensitivity indicators
  - Since schema marks were never on `markedAfter`, the JSON output omits them

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`**
   - `plan()` method: Applies config marks only to provider response
   - `refresh()` method: Perpetuates config-only marks
   - Line 1208: Detects mark asymmetry and converts to Update

2. **`internal/states/instance_object.go`**
   - `Encode()` method: Serializes incomplete marks to state file

3. **`internal/states/instance_object_src.go`**
   - `Decode()` method: Restores incomplete marks when reading state

4. **`internal/terraform/evaluate.go`**
   - `GetResource()` method: Applies schema marks as compensating workaround, but only during expression evaluation

5. **`internal/command/jsonplan/values.go`**
   - Converts plan values to JSON, capturing only marks present on the value

6. **`internal/command/jsonstate/state.go`**
   - `SensitiveAsBool()` function: Converts marks to boolean indicators for JSON serialization

## Causal Chain

1. **Symptom**: `terraform plan` shows resource "will be updated in-place" with no visible attribute changes and `terraform show -json` shows incomplete `sensitive_values`

2. **First hop**: Provider's `PlanResourceChange()` and `ReadResource()` return values without any sensitivity marks (by protocol design - providers are forbidden from marking)

3. **Second hop**: The `plan()` method in `node_resource_abstract_instance.go` (line 999) applies marks from config values only (`unmarkedPaths`), ignoring provider schema's `Sensitive: true` declarations

4. **Third hop**: The `refresh()` method (line 718-720) perpetuates config-only marks by re-applying marks extracted from prior state, which itself only contained config marks

5. **Fourth hop**: When encoding the planned state to the state file via `instance_object.go`'s `Encode()` method (line 98-131), only marks that exist on the value are serialized. Since schema marks were never applied, they're never saved to `AttrSensitivePaths`

6. **Fifth hop**: When the state file is read back via `instance_object_src.go`'s `Decode()` method, marks are restored from `AttrSensitivePaths`, but these are incomplete (line 88-91)

7. **Sixth hop**: The mark comparison at line 1208 in `plan()` detects that prior state and planned state have different marks (due to the missing schema marks), and converts the action from NoOp to Update

8. **Seventh hop**: When generating JSON output via `jsonplan/values.go` (line 230), `SensitiveAsBool()` converts marks on the planned value to sensitivity indicators. Since schema marks were never on the planned value, the JSON output omits them

9. **Root cause**: The only place schema marks are applied is in `evaluate.go`'s `GetResource()` method (lines 689-695, 714-723), but this happens during expression evaluation, **not** during the planning phase when the planned state is being built and serialized

## Recommendation

### Fix Strategy

The fix requires **applying schema marks at the point of plan creation**, not just during evaluation:

1. **In `node_resource_abstract_instance.go`'s `plan()` method**:
   - After receiving the provider response (line 916), and after applying config marks (line 999), also apply schema marks to the planned value
   - Similar application is needed in the replace path (after line 1164)
   - Schema marks should be obtained via `schema.ValueMarks(plannedNewVal, nil)`

2. **In `node_resource_abstract_instance.go`'s `refresh()` method**:
   - After applying prior state marks (line 720), also apply schema marks to the refreshed value
   - This ensures consistency between planned and refreshed states

3. **Update mark comparison logic**:
   - The compensating workaround in `evaluate.go` can then be simplified or removed, since schema marks will already be present where needed
   - Alternatively, mark comparison logic (line 1208) needs to understand that schema marks are expected and should not trigger an Update action when they're the only difference

### Diagnostic Steps

To verify this issue:

1. Create a resource with a provider schema attribute marked `Sensitive: true`
2. Apply the configuration: `terraform apply`
3. Verify the state file shows `sensitive_attributes` for the sensitive attribute
4. Run `terraform plan` immediately (no config changes)
5. Check:
   - Whether plan shows phantom Update action (indicates line 1208 was triggered)
   - Whether `terraform show -json` omits the sensitive attribute from `sensitive_values` (indicates schema marks were never on the planned value)

### Implementation Priority

This is a **high-priority fix** because it affects:
- Correctness of plan output (phantom updates confuse users)
- Security audit trails (incomplete `sensitive_values` makes it unclear what's sensitive)
- CI/CD reliability (plans that appear to change when they haven't cause confusion)
