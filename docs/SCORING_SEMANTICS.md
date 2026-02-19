# Scoring Semantics

How each benchmark is scored, what the numbers mean, and known limitations.

## Scoring Types

| Type | Range | Description |
|------|-------|-------------|
| **binary** | 0.0 or 1.0 | Pass/fail — all tests must pass |
| **checklist** | 0.0–1.0 continuous | Weighted sum of boolean checks |
| **test-ratio** | 0.0–1.0 continuous | Fraction of test cases passing |
| **similarity** | 0.0–1.0 continuous | Semantic or keyword similarity to ground truth |
| **F1-hybrid** | 0.0–1.0 continuous | Detection F1 blended with fix quality |
| **ordering** | 0.0–1.0 continuous | Position-exact-match blended with rank correlation |
| **external** | 0.0–1.0 continuous | External verifier (e.g., TheAgentCompany eval) |

## Per-Benchmark Scoring (Active Suites)

### SWE-bench Pro
- **Type**: test-ratio (pytest-based)
- **Mechanism**: Runs project-specific pytest suite; score = fraction of tests passing
- **Good score**: 1.0 (all repo tests pass)
- **Limitations**: Upstream test suites vary in granularity. Some tasks have 1 test (binary effective), others have 50+. Score does not penalize regressions in unrelated tests.

### LargeRepo
- **Type**: checklist (compilation + keyword + test)
- **Mechanism**: Weighted checks: keyword presence (0.3), relevant file changes in ≥2 files (0.2), test additions (0.2), unit tests pass (0.3)
- **Good score**: ≥0.7 (keyword found, tests pass, multi-file changes)
- **Limitations**: Keyword-based scoring can't verify implementation correctness. Compilation check provides strong signal but only covers modified packages.

### DocGen
- **Type**: checklist (weighted keyword checks)
- **Mechanism**: Multi-check scoring: file exists (0.1), minimum content (0.1), keyword presence with negation filtering (0.8 across checks)
- **Good score**: ≥0.7 (comprehensive documentation with key concepts)
- **Limitations**: Keyword checks are context-aware (reject negated mentions) but can't verify technical accuracy. Minimum word count prevents empty-file gaming.

### CrossRepo
- **Type**: similarity (patch validation)
- **Mechanism**: `score = 0.4 * file_coverage + 0.6 * pattern_score`
- **Good score**: ≥0.6 (correct files modified with expected patterns)
- **Limitations**: Pattern matching is regex-based and may miss valid alternative implementations. Fallback diff collection restricted to expected file paths to prevent gaming.

### Enterprise
- **Type**: checklist (multi-signal)
- **Mechanism**: Weighted checks for impact analysis accuracy, refactoring completeness, dependency discovery precision
- **Good score**: ≥0.6 (correct dependencies identified, accurate impact assessment)
- **Limitations**: Enterprise tasks have complex multi-dimensional scoring; partial credit for partially correct analyses.

### PyTorch
- **Type**: diff_similarity (diff-based)
- **Mechanism**: Compares agent's code changes against expected ground-truth diff; score = 0.35 * file_recall + 0.45 * line_recall + 0.20 * line_precision. sgt-001 uses a custom verifier (file + pattern checks).
- **Good score**: >= 0.5 (correct files touched with matching changes)
- **Limitations**: Diff similarity rewards matching the reference solution line-by-line; functionally equivalent but differently structured fixes may score lower.

### NavProve
- **Type**: checklist (navigation accuracy)
- **Mechanism**: Checks whether agent correctly traced provenance, located target behaviors, and provided accurate justification
- **Good score**: ≥0.6 (correct navigation path with supporting evidence)
- **Limitations**: Scoring rewards matching expected navigation targets; alternative valid paths may receive lower scores.

### CodeReview
- **Type**: F1-hybrid (detection + fix quality)
- **Mechanism**: `score = 0.5 * detection_F1 + 0.5 * fix_score`. Detection matches reported defects to expected defects by file path. Fix scoring checks for correct fix patterns with multiple acceptable alternatives.
- **Good score**: ≥0.7 (most defects found and fixed)
- **Limitations**: Fix pattern matching accepts alternatives but may miss novel correct approaches. Detection is file-path-based — reporting the right file but wrong defect counts as a match.

### DIBench
- **Type**: test-ratio
- **Mechanism**: Runs dependency installation tests; score = fraction passing
- **Good score**: 1.0 (all dependencies installed correctly)
- **Limitations**: Network-dependent tasks may fail due to registry availability.

### Governance
- **Type**: checklist (policy compliance)
- **Mechanism**: Checks for correct access control implementation, policy enforcement, audit trail completeness
- **Good score**: ≥0.7 (policies correctly implemented and enforced)
- **Limitations**: Binary checks for policy presence may miss subtle implementation errors.

### NLQA
- **Type**: similarity (answer quality)
- **Mechanism**: Compares agent's natural-language answer against reference answer using keyword and semantic matching
- **Good score**: ≥0.6 (accurate answer with relevant code references)
- **Limitations**: NL similarity can't fully verify technical accuracy of complex architectural explanations.

### Onboarding
- **Type**: checklist (comprehension checks)
- **Mechanism**: Checks for correct identification of key components, workflows, and dependencies
- **Good score**: ≥0.6 (accurate orientation and component identification)
- **Limitations**: Keyword-based checks may miss valid alternative descriptions.

### Security
- **Type**: checklist (security analysis accuracy)
- **Mechanism**: Checks for correct CVE identification, reachability assessment, and mitigation recommendations
- **Good score**: ≥0.7 (correct vulnerabilities identified with accurate reachability analysis)
- **Limitations**: Security analysis scoring is pattern-based; novel but correct security insights may score lower.

### TAC (TheAgentCompany)
- **Type**: external (TAC eval.py)
- **Mechanism**: External evaluator from TheAgentCompany; scores task completion
- **Good score**: 1.0
- **Limitations**: External verifier — not modified by this project.

### LinuxFLBench
- **Type**: checklist (fault localization accuracy)
- **Mechanism**: Checks if agent identified correct buggy file and functions. Ground truth loaded from `tests/ground_truth.json`.
- **Good score**: ≥0.7 (correct file and at least one correct function)
- **Limitations**: Only accepts exact file path and function name matches.

### Investigation
- **Type**: checklist (investigation thoroughness)
- **Mechanism**: Checks for correct root cause identification, evidence gathering, and impact assessment
- **Good score**: ≥0.6 (correct root cause with supporting evidence)
- **Limitations**: Multi-dimensional scoring may not capture all valid investigation approaches.

### SWE-Perf
- **Type**: external (task-specific verifier)
- **Mechanism**: Performance benchmarks with custom verification
- **Good score**: 1.0
- **Limitations**: External verifiers — not modified by this project.

## Score Distribution Expectations

| Benchmark | Expected Baseline Range | Notes |
|-----------|------------------------|-------|
| SWE-bench Pro | 0.3–0.5 | Hard real-world bugs |
| LargeRepo | 0.2–0.5 | Large codebase navigation required |
| DocGen | 0.5–0.8 | Documentation generation is tractable |
| CrossRepo | 0.3–0.6 | Multi-repo coordination is hard |
| Enterprise | 0.2–0.5 | Complex multi-dimensional enterprise tasks |
| PyTorch | 0.05–0.25 | Diff similarity; 11 tasks |
| NavProve | 0.3–0.6 | Navigation and tracing tasks |
| CodeReview | 0.3–0.6 | Finding + fixing defects |
| DIBench | 0.4–0.7 | Dependency installation |
| Governance | 0.3–0.6 | Policy enforcement tasks |
| NLQA | 0.3–0.6 | Natural-language Q&A about code |
| Onboarding | 0.3–0.6 | Codebase orientation |
| Security | 0.3–0.6 | Security analysis |
| TAC | 0.3–0.6 | Tool-augmented, network-dependent |
| LinuxFLBench | 0.2–0.5 | Kernel fault localization |
| Investigation | 0.3–0.6 | Deep debugging |
| SWE-Perf | 0.3–0.6 | Performance optimization |

## Defect Annotation Format

Code review and security review tasks in `ccb_test/` use
`tests/expected_defects.json` to define ground truth defects.  Each defect
entry supports the following optional annotation fields for richer analysis.
These fields are informational metadata; **scoring logic is unchanged**.

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `defect_type` | string enum | Classifies the nature of the defect (see enum below) |
| `line_start` | integer | First line of the defect location in the source file |
| `line_end` | integer | Last line of the defect location in the source file |

### `defect_type` Enum Values

| Value | Description |
|-------|-------------|
| `null-deref` | Null/nil pointer dereference |
| `resource-leak` | Resource (memory, handle, cache) not properly released |
| `race-condition` | Concurrent access without proper synchronization |
| `injection` | Input validation bypass allowing injection or unauthorized input |
| `logic-error` | Inverted condition, off-by-one, wrong operator, or other logic mistake |
| `buffer-overflow` | Write past allocated buffer bounds |
| `use-after-free` | Access to memory after deallocation |
| `other` | Defect that does not fit the above categories |

### Example

```json
{
  "id": "defect-1",
  "file": "lib/vtls/openssl.c",
  "line_start": 992,
  "line_end": 997,
  "type": "security",
  "severity": "high",
  "defect_type": "buffer-overflow",
  "description": "Buffer bounds check removed from SSL password callback."
}
```

### Ground Truth Registry Integration

When `defect_type` is present in an `expected_defects.json` entry, the ground
truth extraction in `scripts/ccb_metrics/ground_truth.py` populates
`TaskGroundTruth.defect_annotations` -- a list of `DefectAnnotation` objects
carrying `defect_id`, `file`, `defect_type`, `line_start`, and `line_end`.
Tasks without `defect_type` fields produce an empty annotations list.  The
serialized registry (`configs/ground_truth_files.json`) includes annotations
only when non-empty.

## Archived Suite Scoring (for reference)

The following suites are archived and not included in official evaluation:

- **LoCoBench**: similarity (weighted multi-signal) — keyword overlap, file references, code blocks, structural coherence
- **RepoQA**: similarity (semantic retrieval) — binary in practice (correct function or not)
- **DependEval**: ordering (position-exact + Kendall tau) — `score = 0.6 * position_exact_match + 0.4 * kendall_tau_normalized`
- **K8s Docs**: checklist (weighted keyword checks) — superseded by DocGen
