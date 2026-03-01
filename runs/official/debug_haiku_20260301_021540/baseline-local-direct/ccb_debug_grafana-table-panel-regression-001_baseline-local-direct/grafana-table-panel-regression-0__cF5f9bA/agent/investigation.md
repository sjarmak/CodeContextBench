# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

Schema version 38 (v38) table panel migration has a regression where field override configurations are silently dropped for dashboards that don't have an explicit `fieldConfig.defaults.custom` object in the original JSON. The backend migration function prematurely exits when the custom object is missing, preventing override processing that should occur regardless of whether defaults.custom exists.

## Root Cause

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`
**Function:** `processPanelsV38()` (lines 90-137)
**Exact Problem:** Lines 120-123

```go
custom, ok := defaults["custom"].(map[string]interface{})
if !ok {
    continue  // ← REGRESSION: Skips entire panel including overrides processing
}
```

The conditional check on line 120 causes the function to skip processing the entire table panel if `fieldConfig.defaults.custom` doesn't exist. This means the `migrateOverrides()` function (line 135) is never called, leaving field overrides with the old property ID `custom.displayMode` unmigrated.

## Evidence

### Backend Implementation Issue

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`

The problematic code flow:

1. **Line 110:** Gets `fieldConfig` from panel
2. **Line 115:** Gets `defaults` from fieldConfig
3. **Lines 120-123:** Attempts to get `custom` from defaults, **exits if not found**
4. **Line 135:** `migrateOverrides()` is never reached if custom doesn't exist

```go
func processPanelsV38(panels []interface{}) {
    for _, panel := range panels {
        // ... panel type checks ...
        fieldConfig, ok := p["fieldConfig"].(map[string]interface{})
        if !ok {
            continue
        }

        defaults, ok := fieldConfig["defaults"].(map[string]interface{})
        if !ok {
            continue
        }

        custom, ok := defaults["custom"].(map[string]interface{})  // Line 120
        if !ok {
            continue  // ← REGRESSION: Exits here, skips migrateOverrides()
        }

        // Process displayMode -> cellOptions in defaults
        if displayMode, exists := custom["displayMode"]; exists {
            // ... migration logic ...
        }

        // This line is never reached if custom doesn't exist
        migrateOverrides(fieldConfig)  // Line 135
    }
}
```

### Frontend Implementation (Correct Behavior)

**File:** `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts` (lines 644-674)

The frontend correctly uses optional chaining and always processes overrides:

```typescript
if (oldVersion < 38 && finalTargetVersion >= 38) {
  panelUpgrades.push((panel: PanelModel) => {
    if (panel.type === 'table' && panel.fieldConfig !== undefined) {
      // Line 647: Uses optional chaining - doesn't require custom to exist
      const displayMode = panel.fieldConfig.defaults?.custom?.displayMode;

      // Line 650: Only migrates defaults if displayMode exists
      if (displayMode !== undefined) {
        panel.fieldConfig.defaults.custom.cellOptions =
          migrateTableDisplayModeToCellOptions(displayMode);
        delete panel.fieldConfig.defaults.custom.displayMode;
      }

      // Lines 659-669: ALWAYS processes overrides, regardless of defaults.custom
      if (panel.fieldConfig?.overrides) {
        for (const override of panel.fieldConfig.overrides) {
          for (let j = 0; j < (override.properties?.length || 0); j++) {
            if (override.properties[j].id === 'custom.displayMode') {
              override.properties[j].id = 'custom.cellOptions';
              override.properties[j].value =
                migrateTableDisplayModeToCellOptions(overrideDisplayMode);
            }
          }
        }
      }
    }
    return panel;
  });
}
```

### Panel Defaults Application

**File:** `/workspace/apps/dashboard/pkg/migration/frontend_defaults.go` (lines 102-117)

The `applyPanelDefaults()` function creates `defaults` but NOT `defaults.custom`:

```go
func applyPanelDefaults(panel map[string]interface{}) {
    // ...
    if _, exists := panel["fieldConfig"]; !exists {
        panel["fieldConfig"] = map[string]interface{}{
            "defaults":  map[string]interface{}{},  // ← Created here
            "overrides": []interface{}{},
        }
    } else {
        if fieldConfig, ok := panel["fieldConfig"].(map[string]interface{}); ok {
            if _, hasDefaults := fieldConfig["defaults"]; !hasDefaults {
                fieldConfig["defaults"] = map[string]interface{}{}  // ← But NOT custom
            }
            if _, hasOverrides := fieldConfig["overrides"]; !hasOverrides {
                fieldConfig["overrides"] = []interface{}{}
            }
        }
    }
}
```

## Affected Components

1. **Migration Package:** `apps/dashboard/pkg/migration/schemaversion/v38.go`
2. **Functions:**
   - `V38()` - Entry point (line 75)
   - `processPanelsV38()` - Panel processor with regression (line 90)
   - `migrateOverrides()` - Never called for missing custom objects (line 140)

3. **Schema Version:** v38
4. **Panel Type:** Table panels specifically
5. **Data Structure:**
   - `panel.fieldConfig.defaults.custom` (optional)
   - `panel.fieldConfig.overrides[].properties[].id` (may contain `custom.displayMode`)

## Why Dashboards With Explicit `defaults.custom` Are Unaffected

Dashboards that explicitly defined `fieldConfig.defaults.custom` in their JSON are unaffected because:

1. The explicit `custom` object is present in the input
2. Line 120 type assertion succeeds: `custom, ok := defaults["custom"].(map[string]interface{})`
3. The code proceeds to process both:
   - `defaults.custom.displayMode` (lines 126-132)
   - Field overrides (line 135)
4. Both `displayMode` properties are successfully migrated to `cellOptions`

Regression only occurs when:
- Dashboard has `fieldConfig.overrides[].properties[].id == "custom.displayMode"`
- But NO explicit `fieldConfig.defaults.custom` in the original JSON
- Frontend defaults logic creates empty `defaults` but not `defaults.custom`
- V38 exits early at line 120-123 before reaching override migration

## Test Coverage Gap

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38_test.go`

The test suite has 10 test scenarios for V38 migration, but **none of them test the regression case**:

All test cases include explicit `fieldConfig.defaults.custom` objects (lines 24, 38, 52, 66, 80, 94, 108, 122, 173, 186).

**Missing test case:** Table panel with field overrides containing `custom.displayMode` but NO `fieldConfig.defaults.custom` in the input.

## Migration Pipeline Flow

**File:** `/workspace/apps/dashboard/pkg/migration/migrate.go`

Order of operations:

1. **Line 71:** `trackOriginalFieldConfigCustom()` - Marks panels that originally had `defaults.custom`
2. **Lines 73-75:** `applyFrontendDefaults()` - Creates default structures
3. **Lines 79-85:** `applyPanelDefaults()` for top-level panels - Creates `defaults` (but not `custom`)
4. **Lines 119-127:** Run schema migrations including V38 - **Regression occurs here**
5. **Line 135:** `cleanupDashboardForSave()` - Final cleanup

At step 4, when V38 runs:
- `fieldConfig.defaults` exists (created in step 3)
- `fieldConfig.defaults.custom` does NOT exist (never created)
- V38 exits before processing overrides
- Field overrides remain with old property IDs

## Recommendation

The backend V38 migration should be fixed to match the frontend implementation:

1. **Separate defaults and overrides processing:** Process `defaults.custom.displayMode` only if custom exists
2. **Always process overrides:** Migrate `override.properties[].id == "custom.displayMode"` regardless of whether `defaults.custom` exists
3. **Add test coverage:** Include test case for table panels with overrides but no explicit `defaults.custom`

**Minimal fix required:**
- Move the `migrateOverrides(fieldConfig)` call outside of the `custom` existence check
- Optionally add defensive logic to handle missing custom objects in migrateOverrides()

This aligns the backend behavior with the tested and working frontend DashboardMigrator implementation.
