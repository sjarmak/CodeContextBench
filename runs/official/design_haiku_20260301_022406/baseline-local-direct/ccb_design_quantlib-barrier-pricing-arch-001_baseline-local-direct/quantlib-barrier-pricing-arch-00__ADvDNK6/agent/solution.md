# QuantLib Barrier Option Pricing Chain Analysis

## Files Examined

### Core Instrument Classes
- **ql/instruments/barrieroption.hpp** — Entry point class defining BarrierOption with barrier type, barrier level, and rebate parameters; extends OneAssetOption
- **ql/instruments/barrieroption.cpp** — BarrierOption implementation with setupArguments() method that populates BarrierOption::arguments
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options; provides greeks and expiration checks
- **ql/option.hpp** — Base option class with payoff and exercise; implements setupArguments() for payoff and exercise
- **ql/instrument.hpp** — Abstract base class implementing LazyObject pattern; defines NPV(), calculate(), performCalculations(), and fetchResults()

### Design Pattern Infrastructure
- **ql/patterns/lazyobject.hpp** — Lazy evaluation framework with cached results; implements calculate() triggering performCalculations() on demand
- **ql/pricingengine.hpp** — Abstract PricingEngine base class and GenericEngine template; defines interface with getArguments(), getResults(), reset(), calculate()

### Analytic Pricing Engine
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — Analytic barrier pricing engine extending BarrierOption::engine
- **ql/pricingengines/barrier/analyticbarrierengine.cpp** — Analytic implementation using closed-form Black-Scholes formulas with helper methods (A, B, C, D, E, F) for barrier adjustments

### Monte Carlo Pricing Framework
- **ql/pricingengines/mcsimulation.hpp** — Generic Monte Carlo simulation framework; provides calculate() orchestration, error tolerance management, and sample accumulation
- **ql/methods/montecarlo/montecarlomodel.hpp** — Core Monte Carlo model connecting path generator and path pricer; implements addSamples() loop that generates paths and prices them
- **ql/methods/montecarlo/mctraits.hpp** — Trait classes (SingleVariate, MultiVariate) defining path_generator_type and path_pricer_type templates
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — Monte Carlo barrier engine with timeGrid(), pathGenerator(), and pathPricer() implementations
- **ql/pricingengines/barrier/mcbarrierengine.cpp** — BarrierPathPricer and BiasedBarrierPathPricer implementations with barrier detection and Brownian bridge correction

### Path Generation and Pricing
- **ql/methods/montecarlo/pathgenerator.hpp** — Template class generating price paths from stochastic process and Gaussian sequence generator
- **ql/methods/montecarlo/pathpricer.hpp** — Abstract PathPricer base class defining operator() interface for pricing individual paths

### Stochastic Processes
- **ql/stochasticprocess.hpp** — Abstract StochasticProcess base class defining drift(), diffusion(), evolve() interfaces and discretization strategies
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess implementing geometric Brownian motion with time-dependent rates and volatility; holds references to yield and Black-vol term structures

### Term Structures
- **ql/termstructures/yieldtermstructure.hpp** — YieldTermStructure providing discount factors for both risk-free rates and dividend yields
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — BlackVolTermStructure providing implied volatilities for variance calculations

---

## Dependency Chain

### 1. Entry Point: BarrierOption.NPV()
```
ql/instruments/barrieroption.hpp:52
  └─ Instrument::NPV() [inline call]
       └─ ql/instrument.hpp:169
```

### 2. LazyObject Trigger Mechanism
```
ql/instrument.hpp:169 (Instrument::NPV)
  └─ Instrument::calculate() [virtual override]
       └─ ql/instrument.hpp:130-139
            ├─ if isExpired(): setupExpired() → return
            └─ else: LazyObject::calculate()
                 └─ ql/patterns/lazyobject.hpp:255-266
                      └─ if !calculated_ && !frozen_:
                           └─ performCalculations()
```

### 3. Engine Invocation Path
```
ql/patterns/lazyobject.hpp:255 (LazyObject::calculate)
  └─ performCalculations() [pure virtual]
       └─ ql/instrument.hpp:100 (Instrument::performCalculations override)
            ├─ engine_->reset()
            ├─ setupArguments(engine_->getArguments())
            │    └─ ql/instruments/barrieroption.cpp:40
            │         └─ OneAssetOption::setupArguments()
            │              └─ ql/option.hpp:92 (populates payoff, exercise)
            ├─ engine_->getArguments()->validate()
            ├─ engine_->calculate() [virtual dispatch]
            │    ├─ Analytic: ql/pricingengines/barrier/analyticbarrierengine.cpp:36
            │    └─ MC: ql/pricingengines/barrier/mcbarrierengine.hpp:78
            └─ fetchResults(engine_->getResults())
                 └─ ql/instrument.hpp:156 (copies NPV_, errorEstimate_, valuationDate_)
```

### 4a. Analytic Barrier Pricing Path
```
ql/pricingengines/barrier/analyticbarrierengine.cpp:36 (calculate)
  ├─ process_->x0()                          [current spot]
  ├─ process_->riskFreeRate()->discount()    [from YieldTermStructure]
  ├─ process_->dividendYield()->discount()   [from YieldTermStructure]
  ├─ stdDeviation()                          [queries BlackVolTermStructure]
  └─ Compute A(), B(), C(), D(), E(), F()   [closed-form barrier formulas]
       └─ CumulativeNormalDistribution cumulative()
```

### 4b. Monte Carlo Barrier Pricing Path
```
ql/pricingengines/barrier/mcbarrierengine.hpp:78 (MCBarrierEngine::calculate)
  └─ McSimulation<SingleVariate,RNG,S>::calculate()
       └─ ql/pricingengines/mcsimulation.hpp:65
            ├─ Initialize: mcModel_ = MonteCarloModel<...>(pathGenerator(), pathPricer(), ...)
            │    └─ ql/methods/montecarlo/montecarlomodel.hpp:62
            │         ├─ pathGenerator: PathGenerator<RSG>(process, timeGrid, ...)
            │         │    └─ ql/methods/montecarlo/pathgenerator.hpp:49-100
            │         │         ├─ StochasticProcess1D::drift(), diffusion()
            │         │         ├─ RSG (random sequence generator)
            │         │         └─ BrownianBridge for interpolation
            │         └─ pathPricer: BarrierPathPricer (or BiasedBarrierPathPricer)
            │              └─ ql/pricingengines/barrier/mcbarrierengine.cpp:27
            │                   ├─ Barrier trigger detection (Brownian bridge correction)
            │                   ├─ diffProcess_->diffusion() queries volatility
            │                   ├─ discounts_ (precomputed from YieldTermStructure)
            │                   └─ PlainVanillaPayoff evaluation
            │
            ├─ Loop: mcModel_->addSamples(batch_size)
            │    └─ ql/methods/montecarlo/montecarlomodel.hpp:92-125
            │         ├─ pathGenerator_->next()
            │         │    └─ Evolves path using process_->evolve()
            │         ├─ pathPricer_(path)
            │         │    └─ BarrierPathPricer::operator()(path)
            │         ├─ antithetic variance reduction (if enabled)
            │         └─ sampleAccumulator_.add(price, weight)
            │
            └─ Return: sampleAccumulator_.mean()
```

### 5. Stochastic Process to Term Structures
```
GeneralizedBlackScholesProcess (ql/processes/blackscholesprocess.hpp)
  ├─ Constructor: Handle<Quote> x0
  │    └─ Current spot price (observable)
  ├─ Constructor: Handle<YieldTermStructure> dividendTS
  │    └─ Dividend yield curve
  │         └─ Provides: discount(), zeroRate()
  ├─ Constructor: Handle<YieldTermStructure> riskFreeTS
  │    └─ Risk-free rate curve
  │         └─ Provides: discount(), zeroRate()
  ├─ Constructor: Handle<BlackVolTermStructure> blackVolTS
  │    └─ Implied volatility surface
  │         └─ Provides: blackVol(maturity, strike), blackVariance()
  │
  └─ Method implementations query term structures:
       ├─ drift(t, x)
       │    └─ riskFreeRate()->zeroRate(t) - dividendYield()->zeroRate(t)
       ├─ diffusion(t, x)
       │    └─ blackVolatility()->blackVol(t, spot)
       └─ evolve(t, x, dt, dw)
            └─ Uses drift and diffusion for discretization
```

### 6. TimeGrid Creation (for Monte Carlo)
```
ql/pricingengines/barrier/mcbarrierengine.hpp:217 (timeGrid)
  └─ Extract residualTime from arguments_.exercise->lastDate()
       └─ process_->time(date)
            └─ Creates TimeGrid(residualTime, numSteps)
```

### 7. Term Structure Hierarchy
```
YieldTermStructure (ql/termstructures/yieldtermstructure.hpp)
  └─ TermStructure
       └─ LazyObject (Observable/Observer pattern)
            └─ Caches discount factors and forward rates

BlackVolTermStructure (ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp)
  └─ VolatilityTermStructure
       └─ TermStructure
            └─ LazyObject
                 └─ Caches volatility values by (maturity, strike)
```

---

## Analysis

### Design Patterns Identified

1. **LazyObject Pattern** (ql/patterns/lazyobject.hpp)
   - Defers expensive calculations until results are first requested
   - Caches results and marks as `calculated_`
   - Registers as Observer to input data structures (term structures, stochastic process)
   - On notification: resets `calculated_` flag, triggering recalculation on next access
   - **Key benefit**: Avoids redundant recalculations; integrates seamlessly with market data changes

2. **Strategy Pattern** (Engine dispatch)
   - BarrierOption::engine serves as abstract base
   - Concrete engines: AnalyticBarrierEngine, MCBarrierEngine, FdBlackScholesBarrierEngine
   - Selection deferred to runtime based on exercise type and dividend schedule
   - **Key benefit**: Extensible; new pricing methods can be added without modifying instrument

3. **Template Method Pattern** (GenericEngine)
   - GenericEngine<Arguments, Results> defines generic get/set interface
   - Derived engines implement only the calculate() method
   - **Key benefit**: Reduces boilerplate; standardizes arguments/results handling

4. **Command Pattern** (Pricing Engine)
   - Arguments structure encapsulates input data
   - Results structure encapsulates output
   - engine.reset() + setupArguments() + calculate() forms a command sequence
   - **Key benefit**: Decouples instrument from pricing logic; enables reuse across instruments

5. **Observer Pattern** (Term Structures)
   - Term structures are Observable
   - Instruments and processes register as Observers
   - Changes trigger notifyObservers() → invalidate cache
   - **Key benefit**: Propagates market data changes; ensures up-to-date valuations

6. **Traits Pattern** (Monte Carlo)
   - MCTraits (SingleVariate, MultiVariate) define path_generator_type, path_pricer_type
   - Compile-time polymorphism via templates
   - **Key benefit**: Zero runtime overhead; compile-time specialization for different models

### Component Responsibilities

**Instrument (BarrierOption)**
- Holds financial parameters: barrier, rebate, payoff, exercise
- Implements NPV() interface
- Delegates pricing to engine via LazyObject/Observer mechanism

**PricingEngine**
- Abstract interface: getArguments(), getResults(), reset(), calculate()
- Populates results structure with prices and greeks
- Registers as observer to process (for analytic engines)

**AnalyticBarrierEngine**
- Queries process for current spot, rates, dividends, volatility
- Applies closed-form Black-Scholes barrier adjustment formulas
- O(1) computation; no randomness

**MCBarrierEngine + McSimulation**
- Manages simulation loop: sample generation → pricing → accumulation
- Implements error estimation and adaptive sampling
- Creates PathGenerator and PathPricer on demand (virtual methods)

**PathGenerator**
- Discretizes stochastic process over TimeGrid
- Generates random samples using Gaussian sequence generator
- Applies Brownian bridge for variance reduction
- Returns Path objects with full trajectory

**BarrierPathPricer**
- Evaluates individual sample paths
- Detects barrier crossing using Brownian bridge correction (ql/pricingengines/barrier/mcbarrierengine.cpp:71-72)
- Discounts payoff back to valuation date
- Returns single price per path

**GeneralizedBlackScholesProcess**
- Encapsulates geometric Brownian motion dynamics
- Queries term structures for rates and volatility on demand
- Provides drift(), diffusion(), evolve() for path generation
- Registers as observer to detect market data changes

**YieldTermStructure**
- Caches discount factors indexed by maturity
- Provides discount(t), zeroRate(t) interfaces
- Used for both risk-free rates and dividend yields
- Lazy evaluation: rates computed via interpolation on first access

**BlackVolTermStructure**
- Caches volatilities indexed by (maturity, strike)
- Provides blackVol(t, K), blackVariance(t, K) interfaces
- Often implements smile/skew surfaces
- Used by process for stochastic vol computation

### Data Flow Through the Pricing Chain

1. **Setup Phase**
   - Instrument holds barrier parameters
   - Engine holds stochastic process reference
   - Process holds term structure handles

2. **Trigger Phase**
   - User calls barrieroption.NPV()
   - Instrument::NPV() → Instrument::calculate()
   - LazyObject checks `calculated_` flag (initially false)

3. **Argument Population Phase**
   - Instrument::performCalculations() calls setupArguments()
   - BarrierOption::setupArguments() populates:
     - payoff, exercise (from Option base)
     - barrierType, barrier, rebate (from BarrierOption)

4. **Validation Phase**
   - Engine validates arguments (barrier > 0, rebate ≥ 0, payoff valid)

5. **Pricing Phase**
   - **Analytic**: Direct formula evaluation
     - Queries process.x0() → spot price
     - Queries process.riskFreeRate()->discount(t) → DF
     - Queries process.dividendYield()->discount(t) → dividend DF
     - Queries process.blackVolatility()->blackVol(t, K) → vol
     - Applies barrier formulas

   - **Monte Carlo**: Sampling loop
     - Create TimeGrid from exercise maturity
     - For each sample:
       - PathGenerator evolves spot via process.evolve()
       - Process queries drift from YieldTermStructure
       - Process queries diffusion from BlackVolTermStructure
       - PathPricer checks barrier trigger (queries process diffusion again)
       - Accumulate PnL

6. **Result Extraction Phase**
   - Instrument::fetchResults() reads engine.results()
   - Copies NPV_, errorEstimate_, valuationDate_, additionalResults

### Interface Contracts

**Between Instrument and Engine**
```cpp
Arguments: barrierType, barrier, rebate, payoff, exercise
Results:   value, errorEstimate, valuationDate, delta, gamma, vega, ...
Contract:  engine.calculate() must populate all declared Results fields
```

**Between PathGenerator and Process**
```cpp
Process interface required:
  - x0() → initial value
  - drift(t, x) → drift term
  - diffusion(t, x) → volatility term
  - evolve(t0, x0, dt, dw) → next state
  - time(date) → calendar conversion
```

**Between PathPricer and Path**
```cpp
Path provides:
  - operator[](i) → spot at time grid step i
  - length() → number of steps
  - timeGrid() → TimeGrid reference (for timing and dt)
```

**Between Process and Term Structures**
```cpp
YieldTermStructure interface:
  - discount(t) → exp(-∫r(u)du from 0 to t)

BlackVolTermStructure interface:
  - blackVol(t, K) → σ(t, K) for variance computation
```

---

## Summary

The QuantLib barrier option pricing chain implements a sophisticated architecture combining lazy evaluation, strategy-based engine dispatch, and term structure integration. The LazyObject pattern defers expensive pricing calculations and caches results, invalidating caches through observer notifications when market data changes. Pricing occurs via either analytic closed-form formulas (AnalyticBarrierEngine) or Monte Carlo simulation (MCBarrierEngine), both operating on a shared GeneralizedBlackScholesProcess that queries yield and volatility term structures on demand. The Monte Carlo framework orchestrates path generation (PathGenerator) using a stochastic process discretization and individual path pricing (PathPricer) with barrier detection, accumulating statistics until desired convergence. This design elegantly separates concerns: instruments specify financial parameters, engines implement pricing logic, processes encapsulate dynamics, and term structures provide market data, all linked through observer patterns and template-based traits for compile-time specialization.
