# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

After upgrading from v10.3 to v10.4, dashboards with table panels lose their field override configuration during import if `fieldConfig.defaults.custom` was not explicitly set in the original JSON. The root cause is a **conditional logic flaw in the V38 migration's field configuration tracking mechanism** combined with incomplete override preservation logic in the cleanup phase.

## Root Cause

**Primary Issue:** The `trackOriginalFieldConfigCustom()` function only marks panels that had `fieldConfig.defaults.custom` in the original input. For dashboards with overrides containing `custom.displayMode` but **no explicit custom object in defaults**, this tracking flag is **not set**, causing the cleanup phase to improperly filter out fieldConfig structures.

**Location:**
- Tracking logic: `apps/dashboard/pkg/migration/frontend_defaults.go:1150-1158` (`trackPanelOriginalFieldConfigCustom()`)
- Cleanup logic: `apps/dashboard/pkg/migration/frontend_defaults.go:600-662` (`filterDefaultValues()`)
- V38 Migration: `apps/dashboard/pkg/migration/schemaversion/v38.go:115-131`

## Evidence

### Code Reference 1: Incomplete Tracking Logic
File: `apps/dashboard/pkg/migration/frontend_defaults.go:1150-1158`

```go
// trackPanelOriginalFieldConfigCustom recursively tracks fieldConfig.defaults.custom in panels
func trackPanelOriginalFieldConfigCustom(panel map[string]interface{}) {
    // Mark if this panel had fieldConfig.defaults.custom in original input
    if fieldConfig, ok := panel["fieldConfig"].(map[string]interface{}); ok {
        if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
            if _, hasCustom := defaults["custom"]; hasCustom {
                panel["_originallyHadFieldConfigCustom"] = true  // ← ONLY marked if custom exists
            }
        }
    }
}
```

**Problem:** This function only sets `_originallyHadFieldConfigCustom = true` if `defaults["custom"]` exists. For dashboards with:
- `fieldConfig.defaults` = empty object `{}`
- `fieldConfig.overrides` = array with `custom.displayMode` properties

The marker is **NOT set**, even though the panel has fieldConfig with custom properties in overrides.

### Code Reference 2: V38 Migration Processing
File: `apps/dashboard/pkg/migration/schemaversion/v38.go:115-131`

```go
// Process defaults.custom if it exists
if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
    if custom, ok := defaults["custom"].(map[string]interface{}); ok {
        // Process displayMode in defaults (conditional - skipped if custom doesn't exist)
        if displayMode, exists := custom["displayMode"]; exists {
            custom["cellOptions"] = migrateTableDisplayModeToCellOptions(displayModeStr)
            delete(custom, "displayMode")
        }
    }
}

// Update any overrides referencing the cell display mode
// This must be called regardless of whether defaults.custom exists
migrateOverrides(fieldConfig)  // ← Processes overrides independently
```

**Correct Behavior:** V38 properly migrates overrides using `migrateOverrides()` even when `defaults.custom` doesn't exist (line 130-131).

### Code Reference 3: Cleanup Phase Preservation Logic
File: `apps/dashboard/pkg/migration/frontend_defaults.go:654-659`

```go
// Preserve custom object if it was originally present, even if empty
if panel["_originallyHadFieldConfigCustom"] == true {  // ← Depends on tracking flag
    if _, hasCustom := defaults["custom"]; !hasCustom {
        defaults["custom"] = map[string]interface{}{}
    }
}
```

**Issue:** This code **only preserves** the custom object if the tracking flag is true. For dashboards where:
1. Original JSON has NO explicit `defaults.custom`
2. V38 migration successfully migrates overrides to use `custom.cellOptions`
3. Cleanup runs

The flag is false, so no protective measures are applied to preserve fieldConfig/overrides.

### Code Reference 4: FieldConfig Filtering Logic
File: `apps/dashboard/pkg/migration/frontend_defaults.go:602-629`

```go
// Filter out properties that match defaults
for prop, defaultValue := range defaults {
    if panelValue, exists := panel[prop]; exists {
        if isEqual(panelValue, defaultValue) {  // Compares to { defaults: {}, overrides: [] }
            if prop == "fieldConfig" {
                if panel["_originallyHadFieldConfigCustom"] == true {  // ← Only protects if flag is true
                    // Ensure custom is preserved...
                    continue
                }
            }
            delete(panel, prop)  // ← Removes fieldConfig if empty and flag is false
        }
    }
}
```

**Critical Issue:** If fieldConfig becomes empty (or appears to match the default) and `_originallyHadFieldConfigCustom == false`, the entire fieldConfig structure—including any migrated overrides—is deleted.

## Migration Execution Flow

```
1. trackOriginalFieldConfigCustom()
   ├─ Checks: Does panel.fieldConfig.defaults.custom exist?
   ├─ For panels WITHOUT defaults.custom: _originallyHadFieldConfigCustom = NOT SET ✗
   └─ For panels WITH defaults.custom: _originallyHadFieldConfigCustom = true ✓

2. applyPanelDefaults()
   └─ Adds empty fieldConfig if missing, ensures defaults/overrides exist

3. V38 Migration
   ├─ Processes defaults.displayMode → cellOptions (if defaults.custom exists)
   └─ Processes overrides.displayMode → cellOptions (regardless of defaults) ✓

4. Cleanup Phase (cleanupPanelForSaveWithContext)
   ├─ filterDefaultValues()
   │  ├─ Checks: _originallyHadFieldConfigCustom == true?
   │  ├─ For FALSE (no original custom): No preservation logic applied
   │  └─ Deletes fieldConfig if it appears to match default empty value
   └─ Result: Overrides and fieldConfig lost ✗
```

## Affected Components

1. **Backend Migration Package:** `apps/dashboard/pkg/migration/`
   - `migrate.go` - Migration orchestration (line 71: calls tracking too early)
   - `frontend_defaults.go` - Tracking and cleanup logic (primary issue)
   - `schemaversion/v38.go` - Table migration handler

2. **Dashboard Schema Version:** V38 (Table panel displayMode → cellOptions)

3. **Affected Panel Type:** Table panels in v10.3 dashboards imported to v10.4

## Why Dashboards With Explicit `defaults.custom` Are Unaffected

For dashboards that **explicitly set** `fieldConfig.defaults.custom` in the original JSON:

1. `trackOriginalFieldConfigCustom()` **sets the flag to true** (line 1156)
2. During cleanup, the preservation logic **activates** (line 655)
3. Custom object is **protected** and preserved
4. Overrides are **retained** within the fieldConfig structure

## Recommendation: Fix Strategy

**Root Fix Required:**
The tracking logic must differentiate between:
1. Panels that had **no fieldConfig** at all (safe to remove if empty after cleanup)
2. Panels that had **fieldConfig but no custom** (must preserve fieldConfig if it contains overrides)
3. Panels that had **explicit custom object** (must preserve custom even if empty)

**Implementation Approach:**
1. Modify `trackOriginalFieldConfigCustom()` to track presence of fieldConfig itself, not just custom
2. OR: Modify `migrateOverrides()` to mark the panel when it finds custom.displayMode properties in overrides
3. Ensure preservation logic in cleanup checks for **presence of overrides** in addition to the custom tracking flag
4. Add test case covering the regression scenario: Table panel with overrides but no defaults.custom

**Affected Files to Fix:**
- `apps/dashboard/pkg/migration/frontend_defaults.go` (tracking and cleanup logic)
- `apps/dashboard/pkg/migration/schemaversion/v38.go` (enhanced override tracking)
- `apps/dashboard/pkg/migration/schemaversion/v38_test.go` (add regression test case)

## Key Test Case

The V38 test suite includes a test at line 444 of `v38_test.go`:
- **Name:** "table with missing defaults.custom but overrides with custom.displayMode"
- **Input:** Table with empty `defaults: {}` but overrides with `custom.displayMode`
- **Expected:** Overrides migrated to `custom.cellOptions`, fieldConfig preserved
- **Current Status:** Test case exists and should pass with fixed code

