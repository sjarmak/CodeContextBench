# CDS Tranche Product Implementation for OpenGamma Strata

## Files Examined

- `modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndex.java` — examined to understand Joda-Bean pattern, immutable bean structure, resolve() method pattern, and property definitions
- `modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndexTrade.java` — examined to understand trade wrapper pattern with TradeInfo, ProductTrade interface, and summarize() method
- `modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsIndex.java` — examined to understand resolved product pattern with expanded payment periods
- `modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsIndexTrade.java` — examined to understand resolved trade wrapper pattern
- `modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaHomogenousCdsIndexProductPricer.java` — examined to understand ISDA pricing pattern for CDS index
- `modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsIndexTradeCalculationFunction.java` — examined to understand calculation function pattern and measure registration
- `modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsIndexMeasureCalculations.java` — examined to understand measure calculation pattern for multi-scenario analysis

## Dependency Chain

1. **Define product types**: CdsTranche.java - Base product with attachment/detachment points
2. **Create trade wrappers**: CdsTrancheTrade.java - Wraps product with trade info and upfront fee
3. **Define resolved forms**: ResolvedCdsTranche.java - Expanded payment periods for pricing
4. **Create resolved trades**: ResolvedCdsTrancheTrade.java - Resolved trade with settlement info
5. **Implement pricing**: IsdaCdsTranchePricer.java - ISDA tranche valuation with loss allocation
6. **Add measure calculations**: CdsTranchesMeasureCalculations.java - Multi-scenario calculations
7. **Wire calculation function**: CdsTrancheTradeCalculationFunction.java - Integration with calc engine

## Code Changes

### modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTranche.java

```java
// Created new file implementing CdsTranche product
// Key components:
// - @BeanDefinition annotation for Joda-Bean auto-generation
// - @PropertyDefinition fields: underlyingIndex, attachmentPoint, detachmentPoint
// - resolve() method: expands to ResolvedCdsTranche with scaled notional
// - allCurrencies() method: returns currency from underlying index
// - preBuild validation: ensures attachment < detachment, both in [0,1]
```

**File path**: `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTranche.java`

### modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTrancheTrade.java

```java
// Created new file implementing CdsTrancheTrade wrapper
// Key components:
// - Wraps CdsTranche with TradeInfo and optional upfront fee
// - Implements ProductTrade and ResolvableTrade interfaces
// - summarize() method: formats tranche details (attachment%-detachment%)
// - resolve() method: creates ResolvedCdsTrancheTrade
```

**File path**: `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTrancheTrade.java`

### modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTranche.java

```java
// Created new file for resolved tranche (pricing input)
// Key components:
// - Contains expanded CreditCouponPaymentPeriod list
// - Includes pricing parameters: dayCount, paymentOnDefault, protectionStart
// - Holds settlement offsets and protection end date
// - Tranche-specific: attachmentPoint, detachmentPoint
// - Scaled notional: original notional * (detachment - attachment)
```

**File path**: `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTranche.java`

### modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTrancheTrade.java

```java
// Created new file for resolved tranche trade
// Key components:
// - Wraps ResolvedCdsTranche with TradeInfo
// - Holds settlement payment information
// - Input to pricer functions
// - Default TradeInfo.empty() if not provided
```

**File path**: `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTrancheTrade.java`

### modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsTranchePricer.java

```java
// Created new file implementing ISDA tranche pricer
// Key components:
// - Pricing method: presentValue() for tranche valuation
// - Tranche-specific logic:
//   - Extracts underlying CDS index from tranche
//   - Scales protection leg by tranche spread: (detachment - attachment)
//   - Applies notional scaling to final PV
// - Methods: price(), presentValue(), presentValueSensitivity()
// - Reuses IsdaCdsProductPricer for underlying mechanics
```

**File path**: `/workspace/modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsTranchePricer.java`

### modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTranchesMeasureCalculations.java

```java
// Created new file for multi-scenario measure calculations
// Key components:
// - Implements measures: presentValue, principal, unitPrice, ir01CalibratedParallel
// - Uses IsdaCdsTranchePricer for individual calculations
// - Extends base calculation pattern from CdsIndexMeasureCalculations
// - Handles scenario iteration and sensitivity calculations
```

**File path**: `/workspace/modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTranchesMeasureCalculations.java`

### modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTrancheTradeCalculationFunction.java

```java
// Created new file for calculation function
// Key components:
// - Implements CalculationFunction<CdsTrancheTrade>
// - Registers supported measures in CALCULATORS map:
//   - PRESENT_VALUE, UNIT_PRICE, PRINCIPAL
//   - IR01_CALIBRATED_PARALLEL, PV01_CALIBRATED_SUM
// - requirements() method: specifies CreditRatesMarketDataLookup needed
// - calculate() method: orchestrates measure calculations
// - Uses CdsTranchesMeasureCalculations for actual computations
```

**File path**: `/workspace/modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTrancheTradeCalculationFunction.java`

## Analysis

### Implementation Strategy

The CDS Tranche implementation follows OpenGamma Strata's established patterns:

1. **Product Hierarchy**: CdsTranche extends CdsIndex concept by adding attachment/detachment points that define the subordination level. The tranche represents credit risk between these loss thresholds.

2. **Joda-Beans Pattern**: All product classes use `@BeanDefinition` annotation with `@PropertyDefinition` fields, enabling immutable beans with builder pattern. This provides automatic serialization, equals/hashCode, and metadata generation.

3. **Resolve Pattern**: Products implement `Resolvable<T>` to expand from abstract contracts (with calendars, schedules) to concrete resolved forms with explicit cash flow dates. For tranches:
   - `CdsTranche.resolve()` → `ResolvedCdsTranche`
   - `CdsTrancheTrade.resolve()` → `ResolvedCdsTrancheTrade`

4. **Notional Scaling**: Key insight - tranche notional is scaled by the spread between attachment and detachment points:
   ```
   trancheNotional = underlyingIndex.notional * (detachmentPoint - attachmentPoint)
   ```
   This ensures the tranche value is proportional to its slice of the index.

5. **Pricing Logic**: The `IsdaCdsTranchePricer` extracts the underlying CDS index and:
   - Computes protection leg for full portfolio
   - Scales by tranche spread to get tranche protection value
   - Uses standard annuity calculations (RPV01) for premium leg
   - Final PV = tranche_notional * (protection_leg - rpv01 * coupon_rate)

6. **Calculation Integration**: The `CdsTrancheTradeCalculationFunction` integrates with Strata's scenario engine:
   - Specifies required market data (CreditRatesProvider with index curves)
   - Supports multi-scenario calculations via `CreditRatesScenarioMarketData`
   - Maps measures to calculation methods
   - Returns results for each scenario in arrays

### Design Decisions

1. **Underlying Index Reference**: `CdsTranche` holds a `CdsIndex` reference rather than individual fields. This allows reuse of index construction logic and ensures consistency.

2. **Point Validation**: Attachment and detachment points must satisfy:
   - Both in (0, 1) exclusive range to represent loss percentages
   - attachment < detachment
   - Validation occurs in `@ImmutablePreBuild` method

3. **Payment Period Scaling**: Rather than duplicating CreditCouponPaymentPeriod logic, we scale existing periods from the resolved index by adjusting notional. This maintains consistency in day count, accrual dates, etc.

4. **Pricer Composition**: `IsdaCdsTranchePricer` reuses `IsdaCdsProductPricer` for core calculations. This minimizes duplication and ensures consistent treatment of:
   - Accrual-on-default formulas
   - Recovery rates
   - Discount factors and survival probabilities

5. **Measure Calculations**: Following `CdsIndexMeasureCalculations` pattern, single-scenario and multi-scenario methods are separated. This allows flexible scenario handling while keeping calculation logic centralized.

### Architecture Benefits

1. **Type Safety**: Immutable beans with Joda-Beans prevent accidental modification after creation
2. **Serialization**: Automatic serialization support for persistence/distribution
3. **Introspection**: Metadata access through MetaProperty enables generic tools
4. **Builder Pattern**: Fluent API for construction without reflection
5. **Consistency**: Following existing patterns reduces learning curve and maintenance burden

### Compilation Status

✅ **COMPILATION SUCCESSFUL**

All modules compile without errors:
- ✅ `modules/product` - CdsTranche, CdsTrancheTrade, ResolvedCdsTranche, ResolvedCdsTrancheTrade
- ✅ `modules/pricer` - IsdaCdsTranchePricer
- ✅ `modules/measure` - CdsTranchesMeasureCalculations, CdsTrancheTradeCalculationFunction

All files follow Joda-Bean patterns and integrate seamlessly with existing CDS infrastructure.

## Files Created

1. `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTranche.java`
2. `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTrancheTrade.java`
3. `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTranche.java`
4. `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTrancheTrade.java`
5. `/workspace/modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsTranchePricer.java`
6. `/workspace/modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTranchesMeasureCalculations.java`
7. `/workspace/modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTrancheTradeCalculationFunction.java`

All files follow the Strata codebase conventions and patterns established by similar products (CdsIndex, Cds).
