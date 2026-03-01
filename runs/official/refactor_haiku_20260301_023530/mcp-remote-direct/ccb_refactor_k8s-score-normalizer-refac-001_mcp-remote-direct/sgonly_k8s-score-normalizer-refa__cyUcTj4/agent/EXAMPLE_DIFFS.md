# Example Code Changes - ScoreExtensions → ScoreNormalizer Refactoring

## 1. Core Interface Definition (interface.go)

### Before:
```go
// ScoreExtensions is an interface for Score extended functionality.
type ScoreExtensions interface {
	// NormalizeScore is called for all node scores produced by the same plugin's "Score"
	// method. A successful run of NormalizeScore will update the scores list and return
	// a success status.
	NormalizeScore(ctx context.Context, state *CycleState, p *v1.Pod, scores NodeScoreList) *Status
}

// ScorePlugin is an interface that must be implemented by "Score" plugins to rank
// nodes that passed the filtering phase.
type ScorePlugin interface {
	Plugin
	// Score is called on each filtered node. It must return success and an integer
	// indicating the rank of the node. All scoring plugins must return success or
	// the pod will be rejected.
	Score(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (int64, *Status)

	// ScoreExtensions returns a ScoreExtensions interface if it implements one, or nil if does not.
	ScoreExtensions() ScoreExtensions
}
```

### After:
```go
// ScoreNormalizer is an interface for Score extended functionality.
type ScoreNormalizer interface {
	// NormalizeScore is called for all node scores produced by the same plugin's "Score"
	// method. A successful run of NormalizeScore will update the scores list and return
	// a success status.
	NormalizeScore(ctx context.Context, state *CycleState, p *v1.Pod, scores NodeScoreList) *Status
}

// ScorePlugin is an interface that must be implemented by "Score" plugins to rank
// nodes that passed the filtering phase.
type ScorePlugin interface {
	Plugin
	// Score is called on each filtered node. It must return success and an integer
	// indicating the rank of the node. All scoring plugins must return success or
	// the pod will be rejected.
	Score(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (int64, *Status)

	// ScoreNormalizer returns a ScoreNormalizer interface if it implements one, or nil if does not.
	ScoreNormalizer() ScoreNormalizer
}
```

**Key Changes:**
- Interface name: `ScoreExtensions` → `ScoreNormalizer`
- Method name: `ScoreExtensions()` → `ScoreNormalizer()`
- Return type: `ScoreExtensions` → `ScoreNormalizer`
- Updated comments to reflect new naming

---

## 2. Metrics Constants (metrics.go)

### Before:
```go
const (
	PreFilter                   = "PreFilter"
	Filter                      = "Filter"
	PreFilterExtensionAddPod    = "PreFilterExtensionAddPod"
	PreFilterExtensionRemovePod = "PreFilterExtensionRemovePod"
	PostFilter                  = "PostFilter"
	PreScore                    = "PreScore"
	Score                       = "Score"
	ScoreExtensionNormalize     = "ScoreExtensionNormalize"
	PreBind                     = "PreBind"
	Bind                        = "Bind"
	PostBind                    = "PostBind"
)
```

### After:
```go
const (
	PreFilter                   = "PreFilter"
	Filter                      = "Filter"
	PreFilterExtensionAddPod    = "PreFilterExtensionAddPod"
	PreFilterExtensionRemovePod = "PreFilterExtensionRemovePod"
	PostFilter                  = "PostFilter"
	PreScore                    = "PreScore"
	Score                       = "Score"
	ScoreNormalize              = "ScoreNormalize"
	PreBind                     = "PreBind"
	Bind                        = "Bind"
	PostBind                    = "PostBind"
)
```

**Key Changes:**
- Constant name: `ScoreExtensionNormalize` → `ScoreNormalize`
- Constant value: `"ScoreExtensionNormalize"` → `"ScoreNormalize"`

---

## 3. Runtime Framework (framework.go)

### Before:
```go
// Run NormalizeScore method for each ScorePlugin in parallel.
f.Parallelizer().Until(ctx, len(plugins), func(index int) {
	pl := plugins[index]
	if pl.ScoreExtensions() == nil {
		return
	}
	nodeScoreList := pluginToNodeScores[pl.Name()]
	status := f.runScoreExtension(ctx, pl, state, pod, nodeScoreList)
	// ... handle status ...
})

func (f *frameworkImpl) runScoreExtension(ctx context.Context, pl framework.ScorePlugin, state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
	if !state.ShouldRecordPluginMetrics() {
		return pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
	}
	startTime := time.Now()
	status := pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
	f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreExtensionNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
	return status
}
```

### After:
```go
// Run NormalizeScore method for each ScorePlugin in parallel.
f.Parallelizer().Until(ctx, len(plugins), func(index int) {
	pl := plugins[index]
	if pl.ScoreNormalizer() == nil {
		return
	}
	nodeScoreList := pluginToNodeScores[pl.Name()]
	status := f.runScoreNormalizer(ctx, pl, state, pod, nodeScoreList)
	// ... handle status ...
})

func (f *frameworkImpl) runScoreNormalizer(ctx context.Context, pl framework.ScorePlugin, state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
	if !state.ShouldRecordPluginMetrics() {
		return pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
	}
	startTime := time.Now()
	status := pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
	f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
	return status
}
```

**Key Changes:**
- Method calls: `pl.ScoreExtensions()` → `pl.ScoreNormalizer()`
- Function name: `runScoreExtension()` → `runScoreNormalizer()`
- Metrics constant: `metrics.ScoreExtensionNormalize` → `metrics.ScoreNormalize`

---

## 4. Plugin Implementation (example: taint_toleration.go)

### Before:
```go
// NormalizeScore invoked after scoring all nodes.
func (pl *TaintToleration) NormalizeScore(ctx context.Context, _ *framework.CycleState, pod *v1.Pod, scores framework.NodeScoreList) *framework.Status {
	return helper.DefaultNormalizeScore(framework.MaxNodeScore, true, scores)
}

// ScoreExtensions of the Score plugin.
func (pl *TaintToleration) ScoreExtensions() framework.ScoreExtensions {
	return pl
}
```

### After:
```go
// NormalizeScore invoked after scoring all nodes.
func (pl *TaintToleration) NormalizeScore(ctx context.Context, _ *framework.CycleState, pod *v1.Pod, scores framework.NodeScoreList) *framework.Status {
	return helper.DefaultNormalizeScore(framework.MaxNodeScore, true, scores)
}

// ScoreNormalizer of the Score plugin.
func (pl *TaintToleration) ScoreNormalizer() framework.ScoreNormalizer {
	return pl
}
```

**Key Changes:**
- Method name: `ScoreExtensions()` → `ScoreNormalizer()`
- Return type: `framework.ScoreExtensions` → `framework.ScoreNormalizer`
- Updated comment

---

## 5. Test Implementation (example: framework_test.go)

### Before:
```go
type TestScoreWithNormalizePlugin struct {
	name string
	inj  injectedResult
}

func (pl *TestScoreWithNormalizePlugin) Name() string {
	return pl.name
}

func (pl *TestScoreWithNormalizePlugin) Score(ctx context.Context, state *framework.CycleState, p *v1.Pod, nodeName string) (int64, *framework.Status) {
	return setScoreRes(pl.inj)
}

func (pl *TestScoreWithNormalizePlugin) ScoreExtensions() framework.ScoreExtensions {
	return pl
}

func (pl *TestScoreWithNormalizePlugin) NormalizeScore(ctx context.Context, state *framework.CycleState, pod *v1.Pod, scores framework.NodeScoreList) *framework.Status {
	return injectNormalizeRes(pl.inj, scores)
}
```

### After:
```go
type TestScoreWithNormalizePlugin struct {
	name string
	inj  injectedResult
}

func (pl *TestScoreWithNormalizePlugin) Name() string {
	return pl.name
}

func (pl *TestScoreWithNormalizePlugin) Score(ctx context.Context, state *framework.CycleState, p *v1.Pod, nodeName string) (int64, *framework.Status) {
	return setScoreRes(pl.inj)
}

func (pl *TestScoreWithNormalizePlugin) ScoreNormalizer() framework.ScoreNormalizer {
	return pl
}

func (pl *TestScoreWithNormalizePlugin) NormalizeScore(ctx context.Context, state *framework.CycleState, pod *v1.Pod, scores framework.NodeScoreList) *framework.Status {
	return injectNormalizeRes(pl.inj, scores)
}
```

**Key Changes:**
- Method name: `ScoreExtensions()` → `ScoreNormalizer()`
- Return type: `framework.ScoreExtensions` → `framework.ScoreNormalizer`

---

## 6. Test Call Site (example: node_affinity_test.go)

### Before:
```go
status = p.(framework.ScorePlugin).ScoreExtensions().NormalizeScore(ctx, state, test.pod, gotList)
if !status.IsSuccess() {
	t.Errorf("unexpected error: %v", status)
}
```

### After:
```go
status = p.(framework.ScorePlugin).ScoreNormalizer().NormalizeScore(ctx, state, test.pod, gotList)
if !status.IsSuccess() {
	t.Errorf("unexpected error: %v", status)
}
```

**Key Changes:**
- Method name in call chain: `ScoreExtensions()` → `ScoreNormalizer()`

---

## Summary of Replacements

| Pattern | Before | After | Count |
|---------|--------|-------|-------|
| Interface name | `ScoreExtensions interface` | `ScoreNormalizer interface` | 1 |
| Method declarations | `ScoreExtensions()` | `ScoreNormalizer()` | 14 |
| Return types | `framework.ScoreExtensions` | `framework.ScoreNormalizer` | 14 |
| Method calls | `pl.ScoreExtensions()` | `pl.ScoreNormalizer()` | 4 |
| Call chains | `.ScoreExtensions().NormalizeScore()` | `.ScoreNormalizer().NormalizeScore()` | 5 |
| Function name | `runScoreExtension()` | `runScoreNormalizer()` | 2 |
| Constant name | `ScoreExtensionNormalize` | `ScoreNormalize` | 1 |
| Comments | Updated references | Updated references | 8+ |
| **Total** | | | **40+** |

All 40+ replacements have been consistently applied across all 20 files.
