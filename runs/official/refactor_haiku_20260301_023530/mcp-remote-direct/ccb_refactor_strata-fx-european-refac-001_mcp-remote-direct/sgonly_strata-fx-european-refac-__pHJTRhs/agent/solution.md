# FxVanillaOption → FxEuropeanOption Refactoring Analysis

## Task Overview
Rename the `FxVanillaOption` type family to `FxEuropeanOption` throughout the OpenGamma Strata codebase to clarify that these classes represent European-exercise FX options (not American or other styles).

## Files Examined

### Core Joda-Beans Product Model Classes (4 files)
These are the primary domain model classes that must be renamed:
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxVanillaOption.java** — Core vanilla FX option product class (Joda-Beans, implements `FxOptionProduct`)
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxVanillaOptionTrade.java** — Trade wrapper for vanilla FX option (Joda-Beans, implements `FxOptionTrade`)
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOption.java** — Resolved form of vanilla FX option used by pricers (Joda-Beans, implements `ResolvedProduct`)
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOptionTrade.java** — Resolved trade form (Joda-Beans, implements `ResolvedTrade`)

### Pricer Classes (4 files)
Black and Vanna-Volga pricers for vanilla options:
- **modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionProductPricer.java** — Black model product pricer
- **modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionTradePricer.java** — Black model trade pricer
- **modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxVanillaOptionProductPricer.java** — Vanna-Volga product pricer
- **modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxVanillaOptionTradePricer.java** — Vanna-Volga trade pricer

### Measure/Calculation Classes (4 files)
High-level calculation APIs:
- **modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculations.java** — Public calculation API, aggregates pricer results into named measures
- **modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionMeasureCalculations.java** — Internal calculations, coordinates Black and Vanna-Volga pricers
- **modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculationFunction.java** — Implements `CalculationFunction<FxVanillaOptionTrade>`, integrates into calculation engine
- **modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionMethod.java** — Enum (`BLACK`, `VANNA_VOLGA`) determining pricing method

### Product Type Constant (1 file)
- **modules/product/src/main/java/com/opengamma/strata/product/ProductType.java** — Defines `FX_VANILLA_OPTION` constant with string value `"FxVanillaOption"` and description `"FX Vanilla Option"`

### Loader/CSV Plugin (1 file)
- **modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxVanillaOptionTradeCsvPlugin.java** — Parses/writes FxVanillaOptionTrade from/to CSV

### Dependent Classes (files using FxVanillaOption types)
These files hold references to FxVanillaOption and must be updated:
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxSingleBarrierOption.java** — Wraps `FxVanillaOption underlyingOption`; builder and factory methods
- **modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxSingleBarrierOption.java** — Wraps `ResolvedFxVanillaOption underlyingOption`; builder and factory methods
- **modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxSingleBarrierOptionProductPricer.java** — Uses `BlackFxVanillaOptionProductPricer` to price underlying vanilla option
- **modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxSingleBarrierOptionTradeCsvPlugin.java** — Parses `FxVanillaOptionTrade` via resolver, extracts `FxVanillaOption product`
- **modules/loader/src/main/java/com/opengamma/strata/loader/csv/CsvWriterUtils.java** — Public static method `writeFxVanillaOption()` delegates to `FxVanillaOptionTradeCsvPlugin.INSTANCE`
- **modules/loader/src/main/java/com/opengamma/strata/loader/csv/TradeCsvInfoResolver.java** — Interface with default method `parseFxVanillaOptionTrade()`

### Test Files (14 files)
Core product tests:
- **modules/product/src/test/java/com/opengamma/strata/product/fxopt/FxVanillaOptionTest.java**
- **modules/product/src/test/java/com/opengamma/strata/product/fxopt/FxVanillaOptionTradeTest.java**
- **modules/product/src/test/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOptionTest.java**
- **modules/product/src/test/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOptionTradeTest.java**

Pricer tests:
- **modules/pricer/src/test/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionProductPricerTest.java**
- **modules/pricer/src/test/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionTradePricerTest.java**
- **modules/pricer/src/test/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxVanillaOptionProductPricerTest.java**

Measure/calculation tests:
- **modules/measure/src/test/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionMethodTest.java**
- **modules/measure/src/test/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculationsTest.java**
- **modules/measure/src/test/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculationFunctionTest.java**

Dependent tests:
- **modules/pricer/src/test/java/com/opengamma/strata/pricer/fxopt/BlackFxSingleBarrierOptionProductPricerTest.java** — References `BlackFxVanillaOptionProductPricer`
- **modules/loader/src/test/java/com/opengamma/strata/loader/csv/TradeCsvLoaderTest.java** — CSV loader tests, including `test_load_fx_vanilla_option()` and barrier tests using vanilla options
- **modules/measure/src/test/java/com/opengamma/strata/measure/fxopt/FxOptionVolatilitiesMarketDataFunctionTest.java** — Market data function tests
- **modules/pricer/src/test/java/com/opengamma/strata/pricer/fxopt/ImpliedTrinomialTreeFxSingleBarrierOptionProductPricerTest.java** — Barrier pricer tests

## Dependency Chain

```
Definition Layer:
  1. FxVanillaOption (product model)
  2. FxVanillaOptionTrade (product trade wrapper)
  3. ResolvedFxVanillaOption (resolved product)
  4. ResolvedFxVanillaOptionTrade (resolved trade)
  5. ProductType.FX_VANILLA_OPTION (constant)

Pricer Layer:
  6. BlackFxVanillaOptionProductPricer ← depends on ResolvedFxVanillaOption
  7. BlackFxVanillaOptionTradePricer ← depends on ResolvedFxVanillaOptionTrade
  8. VannaVolgaFxVanillaOptionProductPricer ← depends on ResolvedFxVanillaOption
  9. VannaVolgaFxVanillaOptionTradePricer ← depends on ResolvedFxVanillaOptionTrade

Measure Layer:
  10. FxVanillaOptionMeasureCalculations ← depends on BlackFx/VannaVolga pricers
  11. FxVanillaOptionTradeCalculations ← depends on FxVanillaOptionMeasureCalculations
  12. FxVanillaOptionTradeCalculationFunction ← depends on FxVanillaOptionTrade, Calculations
  13. FxVanillaOptionMethod (enum) ← no direct dependency

Loader/CSV Layer:
  14. FxVanillaOptionTradeCsvPlugin ← depends on FxVanillaOptionTrade
  15. FxSingleBarrierOptionTradeCsvPlugin ← depends on FxVanillaOptionTrade (calls resolver.parseFxVanillaOptionTrade)
  16. CsvWriterUtils ← depends on FxVanillaOption, FxVanillaOptionTradeCsvPlugin
  17. TradeCsvInfoResolver ← defines parseFxVanillaOptionTrade() default method

Barrier Option Integration:
  18. FxSingleBarrierOption ← wraps FxVanillaOption
  19. ResolvedFxSingleBarrierOption ← wraps ResolvedFxVanillaOption
  20. BlackFxSingleBarrierOptionProductPricer ← uses BlackFxVanillaOptionProductPricer

Tests (transitively depend on renamed classes):
  21-34. All test files
```

## Refactoring Strategy

### Phase 1: Rename Core Classes (7 files)
1. `FxVanillaOption` → `FxEuropeanOption`
2. `FxVanillaOptionTrade` → `FxEuropeanOptionTrade`
3. `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`
4. `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`
5. `BlackFxVanillaOptionProductPricer` → `BlackFxEuropeanOptionProductPricer`
6. `BlackFxVanillaOptionTradePricer` → `BlackFxEuropeanOptionTradePricer`
7. `VannaVolgaFxVanillaOptionProductPricer` → `VannaVolgaFxEuropeanOptionProductPricer`
8. `VannaVolgaFxVanillaOptionTradePricer` → `VannaVolgaFxEuropeanOptionTradePricer`

### Phase 2: Update Measure Classes (4 files)
9. `FxVanillaOptionMeasureCalculations` → `FxEuropeanOptionMeasureCalculations`
10. `FxVanillaOptionTradeCalculations` → `FxEuropeanOptionTradeCalculations`
11. `FxVanillaOptionTradeCalculationFunction` → `FxEuropeanOptionTradeCalculationFunction`
12. `FxVanillaOptionMethod` → `FxEuropeanOptionMethod` (enum)

### Phase 3: Update CSV Loader (2 files)
13. `FxVanillaOptionTradeCsvPlugin` → `FxEuropeanOptionTradeCsvPlugin`
14. Update `TradeCsvInfoResolver` method names and implementations

### Phase 4: Update Constants (1 file)
15. `ProductType.FX_VANILLA_OPTION` constant: update string value from `"FxVanillaOption"` to `"FxEuropeanOption"`

### Phase 5: Update All References (5 files)
16. `FxSingleBarrierOption` — import, field type, Javadoc
17. `ResolvedFxSingleBarrierOption` — import, field type, Javadoc
18. `BlackFxSingleBarrierOptionProductPricer` — import, variable names, field names
19. `FxSingleBarrierOptionTradeCsvPlugin` — imports, method calls
20. `CsvWriterUtils` — method signature, delegated calls

### Phase 6: Update All Tests (14 files)
21-34. Update imports, class references, variable names, test method names

## Critical Changes per File Type

### Joda-Beans Classes
Each Joda-Beans file has auto-generated Meta/Builder inner classes. Renaming requires:
- Class name
- Auto-generated `Meta` inner class name
- Auto-generated `Builder` inner class name
- Javadoc comments
- All method parameters and return types

**Example: FxVanillaOption.java → FxEuropeanOption.java**
```java
// OLD
@BeanDefinition
public final class FxVanillaOption
    implements FxOptionProduct, Resolvable<ResolvedFxVanillaOption>, ImmutableBean, Serializable {
  // ...
  public ResolvedFxVanillaOption resolve(ReferenceData refData) { ... }
  static class Meta extends DirectMetaBean { ... }
  static class Builder extends DirectFieldsBeanBuilder<FxVanillaOption> { ... }
}

// NEW
@BeanDefinition
public final class FxEuropeanOption
    implements FxOptionProduct, Resolvable<ResolvedFxEuropeanOption>, ImmutableBean, Serializable {
  // ...
  public ResolvedFxEuropeanOption resolve(ReferenceData refData) { ... }
  static class Meta extends DirectMetaBean { ... }
  static class Builder extends DirectFieldsBeanBuilder<FxEuropeanOption> { ... }
}
```

### ProductType Constant
```java
// OLD
public static final ProductType FX_VANILLA_OPTION = ProductType.of("FxVanillaOption", "FX Vanilla Option");

// NEW
public static final ProductType FX_EUROPEAN_OPTION = ProductType.of("FxEuropeanOption", "FX European Option");
```

### CSV Plugin Renaming
Requires file rename + internal method names:
```
FxVanillaOptionTradeCsvPlugin.java → FxEuropeanOptionTradeCsvPlugin.java
```

## Implementation Approach

1. **Read source files** using Sourcegraph MCP tools
2. **Create renamed files** in local workspace with updated content
3. **Update all references** systematically
4. **Verify with local compilation** (if applicable)
5. **Document changes** with diff sections

## Affected Test Patterns
- `FxVanillaOptionTest` → `FxEuropeanOptionTest`
- `FxVanillaOptionTradeTest` → `FxEuropeanOptionTradeTest`
- `test_load_fx_vanilla_option()` → `test_load_fx_european_option()`
- Variable names: `VANILLA_OPTION` → `EUROPEAN_OPTION`, etc.

## Files to Rename (23 total)
```
Core product model: 4 files
  FxVanillaOption.java
  FxVanillaOptionTrade.java
  ResolvedFxVanillaOption.java
  ResolvedFxVanillaOptionTrade.java

Pricers: 4 files
  BlackFxVanillaOptionProductPricer.java
  BlackFxVanillaOptionTradePricer.java
  VannaVolgaFxVanillaOptionProductPricer.java
  VannaVolgaFxVanillaOptionTradePricer.java

Measure: 3 files
  FxVanillaOptionMeasureCalculations.java
  FxVanillaOptionTradeCalculations.java
  FxVanillaOptionTradeCalculationFunction.java
  FxVanillaOptionMethod.java (RENAME enum)

CSV Loader: 1 file
  FxVanillaOptionTradeCsvPlugin.java

Tests: 7 files
  FxVanillaOptionTest.java
  FxVanillaOptionTradeTest.java
  ResolvedFxVanillaOptionTest.java
  ResolvedFxVanillaOptionTradeTest.java
  BlackFxVanillaOptionProductPricerTest.java
  BlackFxVanillaOptionTradePricerTest.java
  VannaVolgaFxVanillaOptionProductPricerTest.java
```

## Scope Summary

**Total files to modify: 34**
- **Files to rename (file + class): 23**
- **Files to update references only: 11**
  - FxSingleBarrierOption.java
  - ResolvedFxSingleBarrierOption.java
  - BlackFxSingleBarrierOptionProductPricer.java
  - FxSingleBarrierOptionTradeCsvPlugin.java
  - CsvWriterUtils.java
  - TradeCsvInfoResolver.java
  - ProductType.java
  - 7 test files

## Code Changes

### ProductType.java
```diff
- public static final ProductType FX_VANILLA_OPTION = ProductType.of("FxVanillaOption", "FX Vanilla Option");
+ public static final ProductType FX_EUROPEAN_OPTION = ProductType.of("FxEuropeanOption", "FX European Option");
```

### FxVanillaOptionTrade.java (→ FxEuropeanOptionTrade.java)
```diff
- public final class FxVanillaOptionTrade
-     implements FxOptionTrade, ResolvableTrade<ResolvedFxVanillaOptionTrade>, ImmutableBean, Serializable {
+ public final class FxEuropeanOptionTrade
+     implements FxOptionTrade, ResolvableTrade<ResolvedFxEuropeanOptionTrade>, ImmutableBean, Serializable {

- private FxVanillaOptionTrade(
+ private FxEuropeanOptionTrade(
      TradeInfo info,
-     FxVanillaOption product,
+     FxEuropeanOption product,
      AdjustablePayment premium) {

- /**\n   * Creates an equivalent {@code FxVanillaOptionTrade} using ...
+ /**\n   * Creates an equivalent {@code FxEuropeanOptionTrade} using ...

- public ResolvedFxVanillaOptionTrade resolve(ReferenceData refData) {
-   return ResolvedFxVanillaOptionTrade.builder()
+ public ResolvedFxEuropeanOptionTrade resolve(ReferenceData refData) {
+   return ResolvedFxEuropeanOptionTrade.builder()

- return SummarizerUtils.summary(this, ProductType.FX_VANILLA_OPTION, buf.toString(), ...);
+ return SummarizerUtils.summary(this, ProductType.FX_EUROPEAN_OPTION, buf.toString(), ...);
```

### FxSingleBarrierOption.java (dependencies)
```diff
- private FxVanillaOption underlyingOption;
+ private FxEuropeanOption underlyingOption;

- public static FxSingleBarrierOption of(FxVanillaOption underlyingOption, Barrier barrier, CurrencyAmount rebate) {
+ public static FxSingleBarrierOption of(FxEuropeanOption underlyingOption, Barrier barrier, CurrencyAmount rebate) {
```

### ResolvedFxSingleBarrierOption.java (dependencies)
```diff
- private ResolvedFxVanillaOption underlyingOption;
+ private ResolvedFxEuropeanOption underlyingOption;

- public static ResolvedFxSingleBarrierOption of(
-     ResolvedFxVanillaOption underlyingOption,
+ public static ResolvedFxSingleBarrierOption of(
+     ResolvedFxEuropeanOption underlyingOption,
```

### FxVanillaOptionTradeCsvPlugin.java (→ FxEuropeanOptionTradeCsvPlugin.java)
```diff
- class FxVanillaOptionTradeCsvPlugin implements TradeCsvParserPlugin, TradeCsvWriterPlugin<FxVanillaOptionTrade> {
+ class FxEuropeanOptionTradeCsvPlugin implements TradeCsvParserPlugin, TradeCsvWriterPlugin<FxEuropeanOptionTrade> {

- static FxVanillaOptionTrade parse(CsvRow row, TradeInfo info, TradeCsvInfoResolver resolver) {
+ static FxEuropeanOptionTrade parse(CsvRow row, TradeInfo info, TradeCsvInfoResolver resolver) {

- protected void writeFxVanillaOption(CsvOutput.CsvRowOutputWithHeaders csv, FxVanillaOption product) {
+ protected void writeFxEuropeanOption(CsvOutput.CsvRowOutputWithHeaders csv, FxEuropeanOption product) {

- private FxVanillaOptionTradeCsvPlugin() {
+ private FxEuropeanOptionTradeCsvPlugin() {
```

### TradeCsvInfoResolver.java (dependencies)
```diff
- public default FxVanillaOptionTrade parseFxVanillaOptionTrade(CsvRow row, TradeInfo info) {
-   return FxVanillaOptionTradeCsvPlugin.parse(row, info, this);
+ public default FxEuropeanOptionTrade parseFxEuropeanOptionTrade(CsvRow row, TradeInfo info) {
+   return FxEuropeanOptionTradeCsvPlugin.parse(row, info, this);

- public default FxVanillaOptionTrade completeTrade(CsvRow row, FxVanillaOptionTrade trade) {
+ public default FxEuropeanOptionTrade completeTrade(CsvRow row, FxEuropeanOptionTrade trade) {
```

### CsvWriterUtils.java (dependencies)
```diff
- public static void writeFxVanillaOption(CsvOutput.CsvRowOutputWithHeaders csv, FxVanillaOption product) {
-   FxVanillaOptionTradeCsvPlugin.INSTANCE.writeFxVanillaOption(csv, product);
+ public static void writeFxEuropeanOption(CsvOutput.CsvRowOutputWithHeaders csv, FxEuropeanOption product) {
+   FxEuropeanOptionTradeCsvPlugin.INSTANCE.writeFxEuropeanOption(csv, product);
```

### Test Files Example
```diff
- public class FxVanillaOptionTest {
+ public class FxEuropeanOptionTest {

- public void test_builder() {
-   FxVanillaOption test = sut();
+ public void test_builder() {
+   FxEuropeanOption test = sut();

- @Test
- public void test_load_fx_vanilla_option() {
+ @Test
+ public void test_load_fx_european_option() {
```

## Verification Checklist

- [ ] All 4 core product classes renamed
- [ ] All 4 pricer classes renamed
- [ ] All 4 measure classes renamed
- [ ] CSV plugin renamed
- [ ] ProductType constant updated
- [ ] All dependent imports updated
- [ ] No references to `FxVanillaOption*` remain
- [ ] All method signatures updated to use `FxEuropeanOption*`
- [ ] All Joda-Beans Meta/Builder inner classes updated
- [ ] All test classes renamed and updated
- [ ] Test methods updated (e.g., `test_load_fx_vanilla_option`)
- [ ] CSV test data paths/references updated if applicable

## Implementation Summary

This refactoring affects **34 files** across multiple modules:

**Core Renames (13 files):**
- 4 product model classes (FxEuropeanOption, FxEuropeanOptionTrade, ResolvedFxEuropeanOption, ResolvedFxEuropeanOptionTrade)
- 4 pricer classes (BlackFxEuropeanOptionProductPricer, BlackFxEuropeanOptionTradePricer, VannaVolgaFxEuropeanOptionProductPricer, VannaVolgaFxEuropeanOptionTradePricer)
- 4 measure/calculation classes (FxEuropeanOptionMeasureCalculations, FxEuropeanOptionTradeCalculations, FxEuropeanOptionTradeCalculationFunction, FxEuropeanOptionMethod)
- 1 CSV plugin (FxEuropeanOptionTradeCsvPlugin)

**Content Updates (7 files):**
- ProductType.java (constant rename)
- FxSingleBarrierOption.java, ResolvedFxSingleBarrierOption.java (dependency updates)
- BlackFxSingleBarrierOptionProductPricer.java (pricer reference updates)
- FxSingleBarrierOptionTradeCsvPlugin.java (CSV plugin references)
- CsvWriterUtils.java, TradeCsvInfoResolver.java (method signature updates)

**Test Updates (14 files):**
- Product tests, pricer tests, measure tests, CSV loader tests

The refactoring improves API clarity by explicitly stating that these are **European-exercise** FX options, eliminating ambiguity with other exercise styles (American, Bermuda, etc.).
