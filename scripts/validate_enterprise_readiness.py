#!/usr/bin/env python3
"""Validate enterprise readiness of CodeContextBench.

Checks whether the benchmark can answer 5 key enterprise validation questions:
  Q1: Does centralized context improve agent reliability? (2+ configs, 20+ tasks)
  Q2: Does it reduce engineering navigation time? (workflow_metrics with deltas)
  Q3: Does it enable AI under security constraints? (3+ governance tasks with compliance)
  Q4: Does it improve productivity relative to cost? (economic analysis ROI)
  Q5: Is performance consistent across organizational complexity? (reliability CI)

Usage:
    python3 scripts/validate_enterprise_readiness.py
    python3 scripts/validate_enterprise_readiness.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _load_report() -> dict | None:
    """Load enterprise_report.json."""
    path = REPORTS_DIR / "enterprise_report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def check_q1_reliability(report: dict | None) -> dict[str, Any]:
    """Q1: Does centralized context materially improve agent reliability?

    Requires: 2+ configs with 20+ tasks each.
    """
    result: dict[str, Any] = {
        "question": "Does centralized context materially improve agent reliability?",
        "requirement": "2+ configs with 20+ tasks each, measurable pass rate delta",
        "pass": False,
        "evidence": [],
    }
    if report is None:
        result["evidence"].append("enterprise_report.json not found")
        return result

    econ = (report.get("sections") or {}).get("economic_metrics")
    if not econ:
        result["evidence"].append("economic_metrics section missing")
        return result

    per_config = econ.get("per_config", {})
    configs_with_tasks = {
        cfg: data for cfg, data in per_config.items()
        if data.get("n_tasks", 0) >= 20
    }

    if len(configs_with_tasks) < 2:
        result["evidence"].append(
            f"Only {len(configs_with_tasks)} configs have 20+ tasks "
            f"(need 2+). Counts: "
            + ", ".join(f"{c}={d.get('n_tasks', 0)}" for c, d in per_config.items())
        )
        return result

    result["evidence"].append(
        f"{len(configs_with_tasks)} configs with 20+ tasks: "
        + ", ".join(f"{c}={d['n_tasks']}" for c, d in configs_with_tasks.items())
    )

    # Check pass rate delta
    roi = econ.get("roi_summary", {})
    bl_rate = roi.get("baseline_pass_rate")
    sg_rate = roi.get("sg_full_pass_rate")
    if bl_rate is not None and sg_rate is not None:
        delta = sg_rate - bl_rate
        result["evidence"].append(
            f"Pass rate delta: {delta:+.3f} (baseline={bl_rate:.3f}, SG_full={sg_rate:.3f})"
        )
        result["pass"] = True
    else:
        result["evidence"].append("Pass rates not available in roi_summary")

    return result


def check_q2_navigation(report: dict | None) -> dict[str, Any]:
    """Q2: Does it reduce engineering navigation time?

    Requires: workflow_metrics with category_deltas containing time savings.
    """
    result: dict[str, Any] = {
        "question": "Does it reduce engineering navigation time?",
        "requirement": "workflow_metrics with time deltas across categories",
        "pass": False,
        "evidence": [],
    }
    if report is None:
        result["evidence"].append("enterprise_report.json not found")
        return result

    wf = (report.get("sections") or {}).get("workflow_metrics")
    if not wf:
        result["evidence"].append("workflow_metrics section missing")
        return result

    deltas = wf.get("category_deltas", {})
    if not deltas:
        result["evidence"].append("No category_deltas in workflow_metrics")
        return result

    categories_with_data = 0
    for cat, data in deltas.items():
        saved = data.get("estimated_time_saved_seconds")
        if saved is not None:
            categories_with_data += 1
            result["evidence"].append(
                f"  {cat}: {saved:+.0f}s ({data.get('estimated_time_saved_pct', 0):+.1f}%)"
            )

    if categories_with_data >= 1:
        result["pass"] = True
        result["evidence"].insert(0, f"{categories_with_data} categories with time deltas")
    else:
        result["evidence"].append("No categories with time savings data")

    return result


def check_q3_governance(report: dict | None) -> dict[str, Any]:
    """Q3: Does it enable AI under enterprise security constraints?

    Requires: 3+ governance tasks with compliance scores.
    """
    result: dict[str, Any] = {
        "question": "Does it enable AI under enterprise security constraints?",
        "requirement": "3+ governance tasks with compliance scores",
        "pass": False,
        "evidence": [],
    }
    if report is None:
        result["evidence"].append("enterprise_report.json not found")
        return result

    gov = (report.get("sections") or {}).get("governance_report")
    if not gov:
        result["evidence"].append("governance_report section missing")
        return result

    agg = gov.get("aggregate", {})
    assessed = agg.get("tasks_assessed", 0)
    compliant = agg.get("tasks_compliant", 0)
    rate = agg.get("compliance_rate", 0)

    result["evidence"].append(
        f"Tasks assessed: {assessed}, compliant: {compliant}, rate: {rate:.0%}"
    )

    if assessed >= 3:
        result["pass"] = True
    else:
        result["evidence"].append(f"Need 3+ tasks assessed (have {assessed})")

    return result


def check_q4_cost(report: dict | None) -> dict[str, Any]:
    """Q4: Does it improve productivity relative to cost?

    Requires: economic analysis with ROI data.
    """
    result: dict[str, Any] = {
        "question": "Does it improve productivity relative to cost?",
        "requirement": "economic analysis with cost-per-task and pass rate data",
        "pass": False,
        "evidence": [],
    }
    if report is None:
        result["evidence"].append("enterprise_report.json not found")
        return result

    econ = (report.get("sections") or {}).get("economic_metrics")
    if not econ:
        result["evidence"].append("economic_metrics section missing")
        return result

    roi = econ.get("roi_summary", {})
    bl_cost = roi.get("baseline_avg_cost_usd")
    sg_cost = roi.get("sg_full_avg_cost_usd")
    cost_delta = roi.get("cost_delta_pct")
    pass_delta = roi.get("pass_rate_delta")

    if bl_cost is not None and sg_cost is not None:
        result["evidence"].append(
            f"Cost/task: baseline=${bl_cost:.2f}, SG_full=${sg_cost:.2f} "
            f"(delta: {cost_delta:+.0f}%)"
        )
        if pass_delta is not None:
            result["evidence"].append(f"Pass rate delta: {pass_delta:+.3f}")
        result["pass"] = True
    else:
        result["evidence"].append("Cost data not available in roi_summary")

    return result


def check_q5_consistency(report: dict | None) -> dict[str, Any]:
    """Q5: Is performance consistent across organizational complexity?

    Requires: reliability analysis with per-suite CIs.
    """
    result: dict[str, Any] = {
        "question": "Is performance consistent across organizational complexity?",
        "requirement": "reliability analysis with per-suite confidence intervals",
        "pass": False,
        "evidence": [],
    }
    if report is None:
        result["evidence"].append("enterprise_report.json not found")
        return result

    rel = (report.get("sections") or {}).get("reliability_metrics")
    if not rel:
        result["evidence"].append("reliability_metrics section missing")
        return result

    psc = rel.get("per_suite_config", {})
    if not psc:
        result["evidence"].append("No per_suite_config data")
        return result

    suites_with_ci = 0
    for suite, configs in psc.items():
        for cfg, data in configs.items():
            lo = data.get("ci_95_lower")
            hi = data.get("ci_95_upper")
            n = data.get("n_tasks", 0)
            if lo is not None and hi is not None and n > 0:
                suites_with_ci += 1
                result["evidence"].append(
                    f"  {suite}/{cfg}: n={n}, CI=[{lo:.2f}, {hi:.2f}]"
                )

    if suites_with_ci >= 2:
        result["pass"] = True
        result["evidence"].insert(0, f"{suites_with_ci} suite-config pairs with CIs")
    else:
        result["evidence"].append(
            f"Need 2+ suite-config pairs with CIs (have {suites_with_ci})"
        )

    # Cross-suite consistency
    cross = rel.get("cross_suite_consistency")
    if cross:
        cv = cross.get("coefficient_of_variation")
        if cv is not None:
            result["evidence"].append(f"Cross-suite CV: {cv:.3f}")

    return result


def validate_readiness() -> dict[str, Any]:
    """Run all 5 validation checks and return structured results."""
    report = _load_report()

    checks = [
        check_q1_reliability(report),
        check_q2_navigation(report),
        check_q3_governance(report),
        check_q4_cost(report),
        check_q5_consistency(report),
    ]

    n_pass = sum(1 for c in checks if c["pass"])

    return {
        "all_pass": n_pass == len(checks),
        "passed": n_pass,
        "total": len(checks),
        "checks": checks,
    }


def format_human(results: dict[str, Any]) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("Enterprise Readiness Validation")
    lines.append("=" * 40)
    lines.append("")

    for i, check in enumerate(results["checks"], 1):
        status = "PASS" if check["pass"] else "FAIL"
        lines.append(f"Q{i}: [{status}] {check['question']}")
        lines.append(f"     Requires: {check['requirement']}")
        for ev in check["evidence"]:
            lines.append(f"     {ev}")
        lines.append("")

    lines.append(f"Result: {results['passed']}/{results['total']} checks passed")
    if results["all_pass"]:
        lines.append("Enterprise readiness: VALIDATED")
    else:
        lines.append("Enterprise readiness: INCOMPLETE")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate enterprise readiness of CodeContextBench."
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output in JSON format",
    )
    args = parser.parse_args()

    results = validate_readiness()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_human(results))

    sys.exit(0 if results["all_pass"] else 1)


if __name__ == "__main__":
    main()
