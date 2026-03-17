#!/usr/bin/env python3
"""Validate distribution and statistical power of the core benchmark manifest.

Produces a distribution summary and power analysis for:
- Overall retrieval effect (paired t-test)
- LOC-band moderation
- Single vs multi-repo moderation

Output: configs/core_manifest_validation.json
"""

import json
import math
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MANIFEST_FILE = ROOT / "configs" / "core_benchmark_manifest.json"
OUTPUT_FILE = ROOT / "configs" / "core_manifest_validation.json"


def loc_band(loc):
    if loc is None:
        return "unknown"
    if loc < 400_000:
        return "<400K"
    if loc < 2_000_000:
        return "400K-2M"
    if loc < 8_000_000:
        return "2M-8M"
    if loc < 40_000_000:
        return "8M-40M"
    return ">40M"


def paired_t_power(n, effect_size=0.05, sigma=0.3, alpha=0.05):
    """Approximate power for a one-sample t-test on paired deltas."""
    from math import sqrt, erf
    z_alpha = 1.96 if alpha == 0.05 else 1.645
    ncp = effect_size / (sigma / sqrt(n)) if n > 0 else 0
    # Normal approximation to power
    power = 0.5 * (1 + erf((ncp - z_alpha) / sqrt(2)))
    return round(power, 3)


def main():
    manifest = json.loads(MANIFEST_FILE.read_text())
    tasks = manifest["tasks"]
    n = len(tasks)

    # Distribution analysis
    loc_dist = Counter(t["loc_band"] for t in tasks)
    nrepos_dist = Counter(t["n_repos"] for t in tasks)
    suite_dist = Counter(t["benchmark"] for t in tasks)
    vq_dist = Counter(t["verifier_quality"] for t in tasks)

    single_repo = sum(1 for t in tasks if t["n_repos"] == 1)
    multi_repo = n - single_repo

    # Retrieval-sensitive vs control suites
    control_suites = {
        "csb_sdlc_design", "csb_sdlc_refactor", "csb_sdlc_debug",
        "csb_sdlc_document", "csb_org_platform",
    }
    retrieval_sensitive = sum(1 for t in tasks if t["benchmark"] not in control_suites)
    control = n - retrieval_sensitive

    # Power analysis
    # Typical sigma estimates from existing paired data
    sigma_overall = 0.30  # reward delta std dev
    sigma_loc = 0.28
    sigma_repo = 0.32

    power_overall = paired_t_power(n, 0.05, sigma_overall)
    power_loc_small = paired_t_power(
        sum(1 for t in tasks if t["loc_band"] in ("<400K", "400K-2M")),
        0.05, sigma_loc,
    )
    power_loc_large = paired_t_power(
        sum(1 for t in tasks if t["loc_band"] in ("2M-8M", "8M-40M", ">40M")),
        0.05, sigma_loc,
    )
    power_single = paired_t_power(single_repo, 0.05, sigma_repo)
    power_multi = paired_t_power(multi_repo, 0.05, sigma_repo)

    # Minimum n for 80% power
    def min_n_for_power(sigma, effect=0.05, target_power=0.80):
        for test_n in range(10, 2000):
            if paired_t_power(test_n, effect, sigma) >= target_power:
                return test_n
        return ">2000"

    validation = {
        "manifest_total": n,
        "target_total": manifest["target_total"],
        "shortfall": manifest["target_total"] - n,
        "distribution": {
            "loc_bands": dict(sorted(loc_dist.items())),
            "n_repos": {str(k): v for k, v in sorted(nrepos_dist.items())},
            "single_repo": single_repo,
            "multi_repo": multi_repo,
            "retrieval_sensitive": retrieval_sensitive,
            "control": control,
            "suites": dict(sorted(suite_dist.items())),
            "verifier_quality": dict(vq_dist),
        },
        "power_analysis": {
            "assumptions": {
                "effect_size": 0.05,
                "alpha": 0.05,
                "sigma_overall": sigma_overall,
                "sigma_loc_subgroup": sigma_loc,
                "sigma_repo_subgroup": sigma_repo,
            },
            "overall": {"n": n, "power": power_overall},
            "loc_small_repos": {
                "n": sum(1 for t in tasks if t["loc_band"] in ("<400K", "400K-2M")),
                "power": power_loc_small,
            },
            "loc_large_repos": {
                "n": sum(1 for t in tasks if t["loc_band"] in ("2M-8M", "8M-40M", ">40M")),
                "power": power_loc_large,
            },
            "single_repo": {"n": single_repo, "power": power_single},
            "multi_repo": {"n": multi_repo, "power": power_multi},
            "min_n_80pct_power": {
                "overall": min_n_for_power(sigma_overall),
                "subgroup_loc": min_n_for_power(sigma_loc),
                "subgroup_repo": min_n_for_power(sigma_repo),
            },
        },
        "recommendations": [],
    }

    # Generate recommendations
    if n < manifest["target_total"]:
        validation["recommendations"].append(
            f"Manifest has {n}/{manifest['target_total']} tasks. "
            f"Shortfall of {manifest['target_total'] - n} tasks in "
            f"csb_sdlc_understand ({suite_dist.get('csb_sdlc_understand', 0)}/8) "
            f"and csb_sdlc_document ({suite_dist.get('csb_sdlc_document', 0)}/4)."
        )
    if power_overall < 0.80:
        validation["recommendations"].append(
            f"Overall power {power_overall} < 0.80. Need {min_n_for_power(sigma_overall)} tasks minimum."
        )
    if power_single < 0.50:
        validation["recommendations"].append(
            f"Single-repo subgroup power is low ({power_single}). Consider whether single-repo moderation is testable."
        )

    OUTPUT_FILE.write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
