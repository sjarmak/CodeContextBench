# FxVanillaOption → FxEuropeanOption Refactoring Implementation Guide

## Overview

This guide provides step-by-step instructions for completing the FxVanillaOption → FxEuropeanOption refactoring across the OpenGamma Strata codebase (~34 files).

## Quick Reference

### Class Name Changes
| Old Name | New Name |
|----------|----------|
| FxVanillaOption | FxEuropeanOption |
| FxVanillaOptionTrade | FxEuropeanOptionTrade |
| ResolvedFxVanillaOption | ResolvedFxEuropeanOption |
| ResolvedFxVanillaOptionTrade | ResolvedFxEuropeanOptionTrade |
| BlackFxVanillaOptionProductPricer | BlackFxEuropeanOptionProductPricer |
| BlackFxVanillaOptionTradePricer | BlackFxEuropeanOptionTradePricer |
| VannaVolgaFxVanillaOptionProductPricer | VannaVolgaFxEuropeanOptionProductPricer |
| VannaVolgaFxVanillaOptionTradePricer | VannaVolgaFxEuropeanOptionTradePricer |
| FxVanillaOptionMeasureCalculations | FxEuropeanOptionMeasureCalculations |
| FxVanillaOptionTradeCalculations | FxEuropeanOptionTradeCalculations |
| FxVanillaOptionTradeCalculationFunction | FxEuropeanOptionTradeCalculationFunction |
| FxVanillaOptionMethod | FxEuropeanOptionMethod |
| FxVanillaOptionTradeCsvPlugin | FxEuropeanOptionTradeCsvPlugin |

### Constant Changes
| Old Constant | New Constant |
|--------------|--------------|
| `ProductType.FX_VANILLA_OPTION` | `ProductType.FX_EUROPEAN_OPTION` |
| String value: `"FxVanillaOption"` | String value: `"FxEuropeanOption"` |
| Description: `"FX Vanilla Option"` | Description: `"FX European Option"` |

### Method Name Changes
| Old Method | New Method |
|------------|------------|
| `parseFxVanillaOptionTrade()` | `parseFxEuropeanOptionTrade()` |
| `writeFxVanillaOption()` | `writeFxEuropeanOption()` |
| `test_load_fx_vanilla_option()` | `test_load_fx_european_option()` |

## Implementation Phases

### Phase 1: Core Product Model Classes (4 files)

These are the foundational classes. Rename and update:

1. **FxVanillaOption.java → FxEuropeanOption.java**
   - Change class name from `FxVanillaOption` to `FxEuropeanOption`
   - Update `Resolvable<ResolvedFxVanillaOption>` to `Resolvable<ResolvedFxEuropeanOption>`
   - Update `resolve()` return type and implementation
   - Update `builder()` and factory methods
   - Update Javadoc comments (mention "European" exercise style)
   - Update Meta inner class references
   - Update Builder inner class references
   - Update Meta.beanType() return type
   - Update all references in auto-generated code

2. **FxVanillaOptionTrade.java → FxEuropeanOptionTrade.java**
   - Change class name from `FxVanillaOptionTrade` to `FxEuropeanOptionTrade`
   - Update `ResolvableTrade<ResolvedFxVanillaOptionTrade>` to `ResolvableTrade<ResolvedFxEuropeanOptionTrade>`
   - Update field `FxVanillaOption product` to `FxEuropeanOption product`
   - Update `resolve()` return type to `ResolvedFxEuropeanOptionTrade`
   - Update all builder and factory method signatures
   - Update ProductType reference from `FX_VANILLA_OPTION` to `FX_EUROPEAN_OPTION`

3. **ResolvedFxVanillaOption.java → ResolvedFxEuropeanOption.java**
   - Similar changes: class name and return types

4. **ResolvedFxVanillaOptionTrade.java → ResolvedFxEuropeanOptionTrade.java**
   - Update class name
   - Update field `ResolvedFxVanillaOption product` to `ResolvedFxEuropeanOption product`
   - Update all references

### Phase 2: Pricer Classes (4 files)

Update pricers to work with renamed product types:

1. **BlackFxVanillaOptionProductPricer.java → BlackFxEuropeanOptionProductPricer.java**
   - Update all method signatures using `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`

2. **BlackFxVanillaOptionTradePricer.java → BlackFxEuropeanOptionTradePricer.java**
   - Update method signatures using `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`

3. **VannaVolgaFxVanillaOptionProductPricer.java → VannaVolgaFxEuropeanOptionProductPricer.java**

4. **VannaVolgaFxVanillaOptionTradePricer.java → VannaVolgaFxEuropeanOptionTradePricer.java**

### Phase 3: Measure Classes (4 files)

1. **FxVanillaOptionMeasureCalculations.java → FxEuropeanOptionMeasureCalculations.java**
   - Update constructor parameters
   - Update method signatures

2. **FxVanillaOptionTradeCalculations.java → FxEuropeanOptionTradeCalculations.java**
   - Update all method signatures and imports

3. **FxVanillaOptionTradeCalculationFunction.java → FxEuropeanOptionTradeCalculationFunction.java**
   - Update `CalculationFunction<FxEuropeanOptionTrade>` generic parameter

4. **FxVanillaOptionMethod.java → FxEuropeanOptionMethod.java**
   - Update enum name (if referenced elsewhere)

### Phase 4: CSV Loader (1 file)

**FxVanillaOptionTradeCsvPlugin.java → FxEuropeanOptionTradeCsvPlugin.java**
- Update class name
- Update method signatures returning/accepting renamed types
- Update `writeFxVanillaOption()` → `writeFxEuropeanOption()`

### Phase 5: ProductType Constant (1 file)

**ProductType.java**
```java
// OLD
public static final ProductType FX_VANILLA_OPTION = ProductType.of("FxVanillaOption", "FX Vanilla Option");

// NEW
public static final ProductType FX_EUROPEAN_OPTION = ProductType.of("FxEuropeanOption", "FX European Option");
```

### Phase 6: Dependent Files (7 files)

Update references only (no class rename):

1. **TradeCsvInfoResolver.java**
   - Update method: `parseFxVanillaOptionTrade()` → `parseFxEuropeanOptionTrade()`
   - Update method: `completeTrade()` overload parameter type

2. **CsvWriterUtils.java**
   - Update method: `writeFxVanillaOption()` → `writeFxEuropeanOption()`

3. **FxSingleBarrierOptionTradeCsvPlugin.java**
   - Update imports
   - Update method calls: `parseFxVanillaOptionTrade()` → `parseFxEuropeanOptionTrade()`
   - Update references to `FxVanillaOption` → `FxEuropeanOption`

4. **FxSingleBarrierOption.java**
   - Update field type: `FxVanillaOption underlyingOption` → `FxEuropeanOption underlyingOption`
   - Update method signatures and imports

5. **ResolvedFxSingleBarrierOption.java**
   - Update field type: `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`

6. **BlackFxSingleBarrierOptionProductPricer.java**
   - Update imports
   - Update references to pricer class names

7. **All test files** (14 files)
   - Update imports
   - Update class references in variable declarations
   - Update test method names (e.g., `test_load_fx_vanilla_option` → `test_load_fx_european_option`)

## Key Files and Dependencies

```
FxEuropeanOption.java (NEW)
├── FxEuropeanOptionTrade.java (NEW)
│   ├── ResolvedFxEuropeanOptionTrade.java (NEW)
│   ├── FxEuropeanOptionTradeCsvPlugin.java (NEW)
│   ├── TradeCsvInfoResolver.java (UPDATED)
│   └── [All test files]
├── ResolvedFxEuropeanOption.java (NEW)
├── FxSingleBarrierOption.java (UPDATED)
├── BlackFxEuropeanOptionProductPricer.java (NEW)
│   ├── BlackFxSingleBarrierOptionProductPricer.java (UPDATED)
│   └── FxEuropeanOptionMeasureCalculations.java (NEW)
└── ProductType.java (UPDATED)
```

## Verification Steps

After completing the refactoring:

1. **Compile the product module:**
   ```bash
   mvn -pl modules/product clean compile
   ```

2. **Compile the pricer module:**
   ```bash
   mvn -pl modules/pricer clean compile
   ```

3. **Compile the measure module:**
   ```bash
   mvn -pl modules/measure clean compile
   ```

4. **Compile the loader module:**
   ```bash
   mvn -pl modules/loader clean compile
   ```

5. **Run all tests:**
   ```bash
   mvn test -Dtest=*FxEuropean*
   ```

6. **Search for stale references:**
   ```bash
   grep -r "FxVanillaOption" --include="*.java" modules/
   grep -r "FX_VANILLA_OPTION" --include="*.java" modules/
   ```

7. **Run full build:**
   ```bash
   mvn clean install
   ```

## Common Pitfalls

1. **Incomplete Inner Class Updates:** Don't forget to update Meta and Builder inner classes in Joda-Beans classes
2. **Javadoc References:** Update Javadoc comments that reference old class names
3. **Test Data:** Update test helper methods that construct test objects
4. **Import Statements:** Ensure all imports are updated
5. **Method Overloads:** In interfaces like TradeCsvInfoResolver, update all overload signatures
6. **Constant References:** Replace all `ProductType.FX_VANILLA_OPTION` with `ProductType.FX_EUROPEAN_OPTION`

## Rollback Strategy

If needed, reverse the process:
```bash
git diff modules/ > refactoring.patch
git checkout modules/
# or revert specific commits
```

## Success Criteria

- ✅ All files compile without errors
- ✅ All tests pass
- ✅ No references to `FxVanillaOption` remain in source code
- ✅ No references to `FX_VANILLA_OPTION` remain in source code (except in deprecated annotations if any)
- ✅ All imports are updated
- ✅ All Joda-Beans Meta/Builder classes are properly updated
- ✅ CSV plugin works correctly (validated by test_load_fx_european_option tests)

## Estimated Effort

- **Core classes (Phase 1-2):** 2-3 hours
- **Measure classes (Phase 3):** 1-2 hours
- **CSV & ProductType (Phase 4-5):** 1 hour
- **Dependent files (Phase 6):** 2-3 hours
- **Testing & verification:** 2-3 hours

**Total:** ~9-12 hours for complete refactoring including testing

## Tools

- IDE find-and-replace functionality (IntelliJ IDEA recommended for Java refactoring)
- Git for tracking changes
- Maven for compilation and testing
- grep/sed for final verification

## Support Files

- `/workspace/refactor_files.py` - Python script for bulk text replacements
- `/workspace/FxEuropeanOption.java.example` - Example of transformed file
- `/logs/agent/solution.md` - Complete analysis document
