# QuantLib Barrier Option Pricing Chain: Architecture Analysis

## Files Examined

### Instruments Layer
- **ql/instruments/barrieroption.hpp/cpp** — BarrierOption instrument definition; inherits from OneAssetOption; packages barrier type, barrier level, and rebate into arguments
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options; defines greeks and results structure
- **ql/option.hpp** — Base Option class inheriting from Instrument; holds payoff and exercise definitions
- **ql/instrument.hpp** — Abstract Instrument base class; implements LazyObject pattern with NPV() entry point and calculate()/performCalculations() chain

### LazyObject Pattern
- **ql/patterns/lazyobject.hpp** — Framework for lazy evaluation and caching; implements Observer/Observable pattern; provides calculate() method that calls performCalculations() on demand

### Pricing Engines (Analytic & Monte Carlo)
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — AnalyticBarrierEngine for European barrier options; directly computes closed-form pricing formulae using normal distributions
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — MCBarrierEngine template for Monte Carlo simulation; implements Brownian bridge correction; inherits from McSimulation<SingleVariate,RNG,S> and BarrierOption::engine; defines BarrierPathPricer and BiasedBarrierPathPricer

### Monte Carlo Framework
- **ql/pricingengines/mcsimulation.hpp** — McSimulation base template providing the framework for path generation and pricing; manages sampling loop, tolerance checking, and statistics accumulation
- **ql/methods/montecarlo/montecarlomodel.hpp** — MonteCarloModel template that orchestrates path generation and pricing; adds samples in batches; implements antithetic variate and control variate techniques

### Path Generation & Pricing
- **ql/methods/montecarlo/pathgenerator.hpp** — PathGenerator template that evolves a StochasticProcess1D through time steps using a Gaussian sequence generator; supports Brownian bridge construction
- **ql/methods/montecarlo/pathpricer.hpp** — Abstract PathPricer base template; applies option payoff logic to generated paths; BarrierPathPricer/BiasedBarrierPathPricer provide concrete implementations

### Stochastic Process & Term Structures
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess implements StochasticProcess1D; models log-normal price evolution; holds references to YieldTermStructure (risk-free rate, dividend yield) and BlackVolTermStructure
- **ql/termstructures/yieldtermstructure.hpp** — YieldTermStructure abstract base; provides discount factors and forward rates for different time points
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — BlackVolTermStructure abstract base; provides implied volatility for different strikes and maturities

---

## Dependency Chain

### 1. Entry Point: BarrierOption.NPV()
```
ql/instrument.hpp:168   Instrument::NPV() const
  └─> Returns: call calculate() then return NPV_ member
```

### 2. LazyObject Calculate Mechanism
```
ql/instrument.hpp:130   Instrument::calculate() const
  └─> Checks if expired, calls LazyObject::calculate() if active
      └─> ql/patterns/lazyobject.hpp:255   LazyObject::calculate() const
          └─> Checks calculated_ flag; prevents infinite recursion
              └─> Calls performCalculations()
```

### 3. Instrument-Engine Binding
```
ql/instrument.hpp:147   Instrument::performCalculations() const
  ├─> engine_->reset()
  ├─> setupArguments(engine_->getArguments())   [dispatches to BarrierOption::setupArguments]
  │   ├─> OneAssetOption::setupArguments() [sets payoff, exercise]
  │   └─> BarrierOption::setupArguments() [sets barrier, rebate, type]
  ├─> engine_->getArguments()->validate()
  ├─> engine_->calculate()   [DELEGATES TO PRICING ENGINE]
  └─> fetchResults(engine_->getResults())
```

### 4. Monte Carlo Engine Path (MCBarrierEngine)
```
ql/pricingengines/barrier/mcbarrierengine.hpp:78   MCBarrierEngine::calculate() const
  ├─> Validates barrier not triggered
  └─> McSimulation<SingleVariate,RNG,S>::calculate(tolerance, requiredSamples, maxSamples)
      └─> ql/pricingengines/mcsimulation.hpp:65   McSimulation::calculate()
          └─> Creates or reuses mcModel_ (MonteCarloModel instance)
              └─> ql/methods/montecarlo/montecarlomodel.hpp:92   addSamples(samples)
                  ├─> Loop: for each sample batch
                  │   ├─> pathGenerator()->next()   [Generates ONE FULL PATH]
                  │   │   └─> ql/methods/montecarlo/pathgenerator.hpp:123   PathGenerator::next()
                  │   │       ├─> Gets Gaussian sequence from GSG (sequence generator)
                  │   │       ├─> Optionally applies Brownian bridge transform
                  │   │       ├─> path[0] = process->x0()   [Initial spot]
                  │   │       └─> Loop i=1..timeSteps: evolve price
                  │   │           └─> path[i] = process->evolve(t, path[i-1], dt, dw)
                  │   │               └─> GeneralizedBlackScholesProcess::evolve()
                  │   │                   ├─> Accesses drift(t,x) [from rate/dividend TS]
                  │   │                   ├─> Accesses diffusion(t,x) [from volatility TS]
                  │   │                   └─> Applies discretization scheme (Euler)
                  │   │
                  │   └─> pathPricer()(path)   [PRICES THE PATH]
                  │       └─> ql/pricingengines/barrier/mcbarrierengine.hpp:150   BarrierPathPricer::operator()()
                  │           ├─> Checks if path triggers barrier
                  │           ├─> Applies option payoff if not triggered
                  │           ├─> Discounts to valuation date using discount factors
                  │           └─> Returns barrier-adjusted path payoff
                  │
                  └─> sampleAccumulator.add(price, weight)   [Accumulates statistics]
```

### 5. Analytic Engine Path (AnalyticBarrierEngine)
```
ql/pricingengines/barrier/analyticbarrierengine.hpp:49   AnalyticBarrierEngine::calculate() const
  └─> Directly computes closed-form barrier option price using Haug formulae
      ├─> Extracts market data from GeneralizedBlackScholesProcess:
      │   ├─> underlying() = process->x0()
      │   ├─> strike() = payoff->strike()
      │   ├─> volatility() = process->blackVolatility()->blackVol(T, K)
      │   ├─> riskFreeRate() = process->riskFreeRate()->zeroRate(T)
      │   ├─> dividendYield() = process->dividendYield()->zeroRate(T)
      │   └─> barrier(), rebate() from arguments
      └─> Applies closed-form formula with normal distribution evaluations
```

### 6. Term Structure Query Chain (used by both engines)
```
GeneralizedBlackScholesProcess
  ├─> Handle<YieldTermStructure> riskFreeRate_;
  │   └─> riskFreeRate()->zeroRate(t) or discount(t)
  ├─> Handle<YieldTermStructure> dividendYield_;
  │   └─> dividendYield()->zeroRate(t) or discount(t)
  ├─> Handle<BlackVolTermStructure> blackVolTS_;
  │   └─> blackVolatility()->blackVol(t, K)
  └─> Handle<LocalVolTermStructure> localVolTS_;
      └─> localVolatility()->localVol(t, S) [if local vol model]

YieldTermStructure (abstract interface)
  ├─> discountImpl(t) → discount factor at time t
  ├─> forwardRateImpl(t) → forward rate at time t
  └─> (implementations: FlatForward, PiecewiseYieldCurve, etc.)

BlackVolTermStructure (abstract interface)
  ├─> blackVolImpl(t, K) → implied volatility
  ├─> blackVarianceImpl(t, K) → accumulated variance
  └─> (implementations: BlackConstantVol, SmileSectionCurve, etc.)
```

### 7. Path Evolution Detail (StochasticProcess1D interface)
```
ql/processes/blackscholesprocess.hpp:54   GeneralizedBlackScholesProcess : StochasticProcess1D
  ├─> x0() → Initial spot (Handle<Quote>)
  ├─> drift(t, x) → Computes μ(t,S) = r(t) - q(t) - σ²(t,S)/2
  ├─> diffusion(t, x) → Computes σ(t,S) from volatility surface
  ├─> evolve(t, x, dt, dw) → Applies discretization
  │   └─> x_new = apply(x, drift*dt + diffusion*sqrt(dt)*dw)
  │       └─> apply(x, dx) → x_new = x * exp(dx)  [log-normal updating]
  └─> Notifies observers when term structures change (via registerWith)
```

### 8. PricingEngine Base Architecture
```
ql/pricingengines/barrier/analyticbarrierengine.hpp:46   AnalyticBarrierEngine : BarrierOption::engine
ql/pricingengines/barrier/mcbarrierengine.hpp:57          MCBarrierEngine : BarrierOption::engine, McSimulation<...>

BarrierOption::engine : GenericEngine<BarrierOption::arguments, BarrierOption::results>
  ├─> Provides arguments_ (BarrierOption::arguments)
  │   ├─> barrierType, barrier, rebate
  │   ├─> payoff, exercise (inherited from OneAssetOption::arguments)
  │   └─> underlyingType, riskFreeRate, dividendYield, volatility (inherited)
  └─> Provides results_ (BarrierOption::results)
      └─> value, errorEstimate, valuationDate
```

---

## Analysis

### Design Patterns

**1. LazyObject Pattern (Lazy Evaluation + Caching)**
- Instruments are LazyObject instances inheriting the lazy evaluation framework
- NPV() triggers calculate() which checks calculated_ flag
- If dependencies change, calculated_ is reset via Observer notification
- performCalculations() is deferred until requested or dependencies invalidate cache
- Supports freeze() to keep cached results even when inputs change

**2. Strategy Pattern (Pricing Engines)**
- Instrument defines abstract calculate() contract
- Different engines implement specific pricing methodologies:
  - Analytic engines compute closed-form formulae
  - Monte Carlo engines simulate stochastic paths
  - Finite-difference engines discretize the PDE
- Engine is swappable via setPricingEngine() without changing Instrument code

**3. Template Method Pattern (McSimulation)**
- McSimulation defines the Monte Carlo loop structure:
  1. Generate path
  2. Price path
  3. Accumulate statistics
  4. Check convergence
- Derived engines override pathGenerator(), pathPricer(), timeGrid() to specialize behavior
- Control variates and antithetic variates handled polymorphically

**4. Observer Pattern (Term Structure Notifications)**
- GeneralizedBlackScholesProcess registers as observer with term structures
- When a term structure changes (e.g., market quote updated), it notifies process
- Process notifies the pricing engine via LazyObject::update()
- This cascades through the dependency graph: BarrierOption → Engine → Process → TermStructures

**5. Handle/Body Pattern (Smart Pointers)**
- Market objects (YieldTermStructure, BlackVolTermStructure, Quote) use Handle<T>
- Handle enables reference counting, observer registration, and automatic cleanup
- Circular dependencies between observers handled safely

### Component Responsibilities

**BarrierOption (Instrument)**
- Stores barrier type, level, rebate; validates parameters
- setupArguments() marshals data into engine-specific argument structure
- Delegates to engine via performCalculations()

**GeneralizedBlackScholesProcess (StochasticProcess)**
- Models underlying price dynamics: dS/S = (r-q)dt + σdW
- Interfaces with term structures for rates/vols at arbitrary times
- evolve() applies discretization; drift/diffusion computed on-demand
- Works with both analytic and Monte Carlo engines

**MCBarrierEngine (Monte Carlo Pricing)**
- Creates time grid based on exercise date
- Instantiates PathGenerator with process and time grid
- Instantiates PathPricer (BarrierPathPricer or BiasedBarrierPathPricer)
- MonteCarloModel orchestrates sampling loop; adds batches until convergence
- Results accumulated in sample accumulator (computes mean, variance, error estimate)

**PathGenerator (Path Construction)**
- Takes Gaussian sequence from random number generator
- Optionally applies Brownian bridge reordering for path-dependent options
- Iteratively evolves process: path[i] = process.evolve(path[i-1], dt, dw_i)
- Returns Sample<Path> with weight (importance sampling aware)

**BarrierPathPricer (Single-Path Valuation)**
- Checks if path crossed barrier level at any time step
- If barrier triggered: payoff = rebate; else payoff = vanilla option payoff
- Discounts payoff by discount factors from risk-free term structure
- Returns single path value

**YieldTermStructure & BlackVolTermStructure (Market Data)**
- Provide interface to query rates/vols at any time
- Implementations bootstrap from market instruments (LIBOR deposits, swaps, options)
- Changes notify observers, triggering recalculation

### Data Flow

1. **Initialization**
   - User creates BarrierOption with payoff, exercise, barrier terms
   - User sets GeneralizedBlackScholesProcess (holds term structure handles)
   - User assigns pricing engine (e.g., MCBarrierEngine with parameters)

2. **NPV Request**
   - option.NPV() called
   - Instrument::calculate() checks if expired/calculated
   - LazyObject::calculate() invokes performCalculations()

3. **Pricing (Monte Carlo)**
   - Instrument::performCalculations() calls engine->calculate()
   - MCBarrierEngine::calculate() invokes McSimulation::calculate()
   - McSimulation::calculate() iterates: generate paths → price paths → accumulate stats
   - For each path:
     * PathGenerator pulls next Gaussian sequence
     * Applies Brownian bridge correction
     * Evolves process backward/forward through time grid
     * At each time step: drift/diffusion fetched from process
       - drift/diffusion access term structures (rates, volatility)
     * Returns full path (sequence of spot prices)
   - PathPricer evaluates barrier condition & payoff on path
   - Path value added to statistics accumulator
   - Loop continues until error estimate drops below tolerance

4. **Results Retrieval**
   - MCBarrierEngine sets results_.value = accumulator.mean()
   - Instrument::fetchResults() copies engine results to NPV_, errorEstimate_
   - NPV() returns cached NPV_ value

### Term Structure Integration

**Pricing Engine Queries:**
- **Analytic Engine**: Single query at valuation time
  - σ = blackVolTS->blackVol(T, K)
  - r = riskFreeTS->zeroRate(T)
  - q = dividendTS->zeroRate(T)

- **Monte Carlo Engine**: Multiple queries per path
  - At each time step t_i:
    - drift uses r(t_i) from riskFreeTS and q(t_i) from dividendTS
    - diffusion uses σ(t_i, S_i) from blackVolTS (may include smile/skew)
  - Creates time grid with exercise date as boundary

### Barrier Option Specifics

**Barrier Pricing Challenges:**
- Path-dependent: payoff depends on barrier crossing, not just final spot
- Simulation bias: discrete monitoring may miss barrier crossings
- Brownian bridge correction used in MCBarrierEngine to reduce bias by:
  - Computing probability that barrier crossed between time steps
  - Adjusting path weight to account for potential crossing
  - BiasedBarrierPathPricer option skips correction for speed (less accurate)

**Arguments Flow:**
1. BarrierOption stores: barrier type, barrier level, rebate
2. setupArguments() copies these plus payoff/exercise into engine's arguments_
3. Engine validates all arguments
4. BarrierPathPricer receives: barrier info, payoff, strike, discount factors
5. For each path: checks if min(path) < barrier or max(path) > barrier (depending on type)

---

## Summary

The QuantLib barrier option pricing chain implements a sophisticated dependency injection architecture combining lazy evaluation (LazyObject), strategy pattern (swappable engines), and observer pattern (term structure notifications). A BarrierOption.NPV() call triggers a LazyObject.calculate() → Instrument.performCalculations() → Engine.calculate() chain. The engine (either Analytic or Monte Carlo) queries a GeneralizedBlackScholesProcess, which in turn interfaces with YieldTermStructure and BlackVolTermStructure to obtain market-implied rates and volatilities. Monte Carlo engines use a PathGenerator to evolve the process through a time grid, with PathPricers evaluating barrier conditions and option payoffs on each simulated path, while analytics engines directly compute closed-form formulae. The entire system maintains data consistency through an observer pattern where term structure changes automatically invalidate cached calculations.
