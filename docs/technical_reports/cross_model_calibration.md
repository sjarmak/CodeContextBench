# Cross-Model Judge Calibration

**Last Modified:** April 3, 2026

---

## 1. Introduction

When multiple LLM model families serve as annotation judges for the Agent Reliability Observatory, their agreement on taxonomy category assignments must be measured and calibrated. Systematic disagreement between model families indicates either ambiguous category definitions or model-specific biases that undermine annotation reliability.

This report documents the cross-model calibration methodology and results for Observatory annotation judges.

## 2. Methodology

### 2.1 Cohen's Kappa

For each taxonomy category, we construct a binary vector per model (1 = category assigned to trial, 0 = not assigned) across all shared trials. Cohen's kappa measures agreement beyond chance:

```
kappa = (p_observed - p_expected) / (1 - p_expected)
```

Where:

- `p_observed` = proportion of trials where both models agree
- `p_expected` = expected agreement by chance given marginal rates

### 2.2 Interpretation Scale

| Kappa Range | Interpretation             |
| ----------- | -------------------------- |
| < 0.00      | Less than chance agreement |
| 0.00 - 0.20 | Slight agreement           |
| 0.21 - 0.40 | Fair agreement             |
| 0.41 - 0.60 | Moderate agreement         |
| 0.61 - 0.80 | Substantial agreement      |
| 0.81 - 1.00 | Almost perfect agreement   |

Categories with kappa < 0.4 are flagged as **uncalibrated** and require taxonomy refinement or additional annotator guidelines.

### 2.3 Self-Preference Bias

Self-preference bias is estimated via assignment rate asymmetry: if Model A assigns a category at a significantly different rate than Model B on identical trials, this suggests the model preferentially detects patterns aligned with its own generation tendencies.

Full position-swap measurement (re-running annotations with models evaluating each other's outputs) is planned for future iterations.

## 3. Results

_This section is populated by running the calibration report script:_

```bash
python3 scripts/evaluation/calibration_report.py \
    --model-a-annotations <path-to-model-a-annotations> \
    --model-b-annotations <path-to-model-b-annotations> \
    --output-json reports/calibration.json \
    --output-md docs/technical_reports/cross_model_calibration.md
```

## 4. Interpretation Guidelines

1. **Uncalibrated categories** (kappa < 0.4) should not be used for cross-model comparisons without additional validation.
2. **High bias categories** (large position-swap delta) may reflect genuine model family differences in annotation strategy rather than errors.
3. Categories with high kappa but low base rates should be interpreted cautiously -- kappa can be unstable with sparse data.

## 5. Actions

- Refine taxonomy definitions for uncalibrated categories
- Add worked examples to annotator prompts for ambiguous categories
- Schedule position-swap annotation runs for bias quantification
