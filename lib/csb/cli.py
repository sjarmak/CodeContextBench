"""csb — CodeScaleBench CLI.

Entry points::

    csb run config.yaml
    csb coverage [OPTIONS]
    csb validate config.yaml
    csb eval --suite quick --agent-command CMD
    csb report results.json
    csb estimate --suite quick --model sonnet

Run ``csb --help`` for full usage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="csb",
        description="CodeScaleBench — spec-enforcing benchmark runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  run       Launch a benchmark run from a config file.
  coverage  Report coverage gaps across runs.
  validate  Validate a run config file without executing.
  eval      Run benchmark tasks against an external agent command.
  report    Display results with CSB Score.
  estimate  Estimate API cost for a benchmark suite.
  diagnose  Run automated Observatory annotation on agent traces.

examples:
  csb run configs/my_run.yaml
  csb coverage --format json
  csb coverage --config baseline-local-direct --format json
  csb validate configs/my_run.yaml
  csb eval --suite quick --agent-command "./my_agent.sh"
  csb report results.json
  csb estimate --suite quick --model sonnet
  csb estimate --suite quick --model opus --format json
  csb diagnose --traces runs/my_run/trials --output diagnosis.json
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # ---- csb run ----
    run_p = sub.add_parser("run", help="Launch a benchmark run from a config file.")
    run_p.add_argument("config", help="Path to the run config YAML file.")
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Print planned tasks without executing (overrides config file setting).",
    )

    # ---- csb coverage ----
    cov_p = sub.add_parser("coverage", help="Report coverage gaps across runs.")
    cov_p.add_argument(
        "--config",
        dest="config_filter",
        default=None,
        metavar="CONFIG",
        help=(
            "Filter to a specific config name "
            "(e.g. 'baseline', 'baseline-local-direct', 'mcp', 'mcp-remote-direct'). "
            "Default: both baseline-local-direct and mcp-remote-direct."
        ),
    )
    cov_p.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    cov_p.add_argument(
        "--gaps",
        action="store_true",
        default=False,
        help="Show gap list (per task/config) instead of summary. Implies --format json.",
    )
    cov_p.add_argument(
        "--selection-file",
        default=None,
        metavar="PATH",
        help=(
            "Path to task selection JSON "
            "(default: configs/selected_benchmark_tasks.json)."
        ),
    )
    cov_p.add_argument(
        "--runs-dir",
        default=None,
        metavar="DIR",
        help=(
            "Override CSB_RUNS_DIR for this invocation. "
            "Must be absolute. Default: $CSB_RUNS_DIR."
        ),
    )

    # ---- csb validate ----
    val_p = sub.add_parser(
        "validate", help="Validate a run config file without executing."
    )
    val_p.add_argument("config", help="Path to the run config YAML file.")

    # ---- csb eval ----
    eval_p = sub.add_parser(
        "eval", help="Run benchmark tasks against an external agent command."
    )
    eval_p.add_argument(
        "--suite",
        choices=["quick", "full"],
        default="quick",
        help="Benchmark suite to run (default: quick).",
    )
    eval_p.add_argument(
        "--agent-command",
        required=True,
        metavar="CMD",
        help="Shell command to invoke for each task.",
    )
    eval_p.add_argument(
        "--output",
        default="csb_results.json",
        metavar="PATH",
        help="Path to write submission JSON (default: csb_results.json).",
    )
    eval_p.add_argument(
        "--timeout",
        type=int,
        default=300,
        metavar="SECONDS",
        help="Per-task timeout in seconds (default: 300).",
    )
    eval_p.add_argument(
        "--api-key",
        default=None,
        metavar="TOKEN",
        help=(
            "JWT API key for accessing the full benchmark suite. "
            "Without a valid key, only public-partition tasks are run."
        ),
    )

    # ---- csb estimate ----
    est_p = sub.add_parser("estimate", help="Estimate API cost for a benchmark suite.")
    est_p.add_argument(
        "--suite",
        choices=["quick", "full"],
        default="quick",
        help="Benchmark suite to estimate (default: quick).",
    )
    est_p.add_argument(
        "--model",
        default="sonnet",
        metavar="MODEL",
        help=(
            "Model to estimate costs for "
            "(e.g. sonnet, opus, gpt-4o, gpt-4.1). Default: sonnet."
        ),
    )
    est_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    # ---- csb report ----
    report_p = sub.add_parser(
        "report", help="Display benchmark results with CSB Score."
    )
    report_p.add_argument(
        "results_file",
        help="Path to the submission JSON file.",
    )
    report_p.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text).",
    )
    report_p.add_argument(
        "--browser",
        action="store_true",
        default=False,
        help="Launch interactive results browser on localhost.",
    )
    report_p.add_argument(
        "--port",
        type=int,
        default=8770,
        help="Port for local browser server (default: 8770).",
    )
    report_p.add_argument(
        "--no-baseline",
        action="store_true",
        default=False,
        help="Skip loading official baseline data for comparison.",
    )
    report_view = report_p.add_mutually_exclusive_group()
    report_view.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Group scores and annotations by taxonomy v2 dimensions.",
    )
    report_view.add_argument(
        "--detailed",
        action="store_true",
        default=False,
        help="Show per-leaf-category breakdown.",
    )

    # ---- csb diagnose ----
    diag_p = sub.add_parser(
        "diagnose",
        help="Run automated Observatory annotation on agent traces.",
    )
    diag_p.add_argument(
        "--traces",
        required=True,
        metavar="DIR",
        help="Directory containing agent trial traces.",
    )
    diag_p.add_argument(
        "--output",
        default="-",
        metavar="PATH",
        help="Output file path (default: stdout).",
    )
    diag_p.add_argument(
        "--calibration-data",
        default=None,
        metavar="PATH",
        help="Path to calibration report JSON (from cross-model comparison).",
    )
    diag_p.add_argument(
        "--model",
        default="haiku",
        metavar="MODEL",
        help="LLM model alias for annotation (default: haiku).",
    )
    diag_p.add_argument(
        "--backend",
        choices=["api", "claude-code"],
        default="api",
        help="Annotation backend (default: api).",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "run":
            return _cmd_run(args)
        if args.command == "coverage":
            return _cmd_coverage(args)
        if args.command == "validate":
            return _cmd_validate(args)
        if args.command == "eval":
            return _cmd_eval(args)
        if args.command == "report":
            return _cmd_report(args)
        if args.command == "estimate":
            return _cmd_estimate(args)
        if args.command == "diagnose":
            return _cmd_diagnose(args)
    except KeyboardInterrupt:
        print("\n[csb] Interrupted.", file=sys.stderr)
        return 130

    parser.print_help()
    return 1


# ---------------------------------------------------------------------------
# csb run
# ---------------------------------------------------------------------------


def _cmd_run(args) -> int:
    from lib.csb.run_config import (
        load_run_config,
        validate_run_config_env,
        RunConfigError,
    )
    from lib.csb.harness_runner import launch_run

    try:
        config = load_run_config(args.config)
    except RunConfigError as exc:
        print(f"[csb run] ERROR: {exc}", file=sys.stderr)
        return 1

    # CLI --dry-run flag overrides config file
    if args.dry_run:
        import dataclasses

        config = config.model_copy(update={"dry_run": True})

    try:
        warnings = validate_run_config_env(config)
    except RunConfigError as exc:
        print(f"[csb run] ERROR: {exc}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"[csb run] WARN: {w}")

    try:
        return launch_run(config, _REPO_ROOT)
    except ValueError as exc:
        print(f"[csb run] ERROR: {exc}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# csb coverage
# ---------------------------------------------------------------------------


def _cmd_coverage(args) -> int:
    from lib.csb.gap_scanner import compute_coverage_report, compute_gap_report

    # Resolve CSB_RUNS_DIR
    runs_dir_str = args.runs_dir or os.environ.get("CSB_RUNS_DIR", "")
    if not runs_dir_str:
        print(
            "[csb coverage] ERROR: CSB_RUNS_DIR is not set. "
            "Export it or pass --runs-dir.",
            file=sys.stderr,
        )
        return 1
    runs_dir = Path(runs_dir_str)
    if not runs_dir.is_absolute():
        print(
            f"[csb coverage] ERROR: CSB_RUNS_DIR must be absolute, got: {runs_dir_str!r}",
            file=sys.stderr,
        )
        return 1

    # Resolve selection file
    if args.selection_file:
        selection_file = Path(args.selection_file)
    else:
        selection_file = _REPO_ROOT / "configs" / "selected_benchmark_tasks.json"
    if not selection_file.exists():
        print(
            f"[csb coverage] ERROR: Selection file not found: {selection_file}",
            file=sys.stderr,
        )
        return 1

    # Resolve config filter
    configs = _resolve_config_filter(args.config_filter)

    if args.gaps:
        report = compute_gap_report(runs_dir, selection_file, configs)
        print(json.dumps(report, indent=2))
        return 0

    report = compute_coverage_report(runs_dir, selection_file, configs)

    if args.format == "json":
        print(json.dumps(report, indent=2))
        return 0

    # Text output
    print(f"\nCSB Coverage Report")
    print(f"  Runs dir:  {report['csb_runs_dir']}")
    print(f"  Tasks:     {report['total_tasks']}")
    print(f"  Generated: {report['generated_at']}")
    print()

    any_gap = False
    for config_name, stats in report["configs"].items():
        scored = stats["scored"]
        total = stats["total_tasks"]
        pct = stats["coverage_pct"]
        bar = _coverage_bar(pct)
        print(f"  {config_name}")
        print(f"    {bar}  {pct:.1f}%  ({scored}/{total} scored)")
        if stats["invalid_output"]:
            print(f"    ⚠  {stats['invalid_output']} invalid_output")
        if stats["verifier_error"]:
            print(f"    ✗  {stats['verifier_error']} verifier_error")
        if stats["quarantined"]:
            print(f"    ⚑  {stats['quarantined']} quarantined")
        if stats["missing"]:
            print(f"    ○  {stats['missing']} missing")
            any_gap = True
        print()

    if any_gap:
        print("  To see the gap list:  csb coverage --gaps")
    return 0


def _resolve_config_filter(config_filter: str | None) -> list[str]:
    """Resolve a user-supplied config alias to canonical names."""
    from lib.csb.gap_scanner import canonical_config

    if config_filter is None:
        return ["baseline-local-direct", "mcp-remote-direct"]

    canon = canonical_config(config_filter)
    if canon:
        return [canon]

    # If user typed something like "baseline-local-direct" exactly
    if config_filter in (
        "baseline-local-direct",
        "mcp-remote-direct",
        "baseline-local-artifact",
        "mcp-remote-artifact",
    ):
        return [config_filter]

    print(
        f"[csb coverage] WARN: Unknown config filter {config_filter!r}. "
        "Using both canonical configs.",
        file=sys.stderr,
    )
    return ["baseline-local-direct", "mcp-remote-direct"]


def _coverage_bar(pct: float, width: int = 20) -> str:
    filled = int(round(pct / 100.0 * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ---------------------------------------------------------------------------
# csb validate
# ---------------------------------------------------------------------------


def _cmd_validate(args) -> int:
    from lib.csb.run_config import (
        load_run_config,
        validate_run_config_env,
        RunConfigError,
    )

    print(f"[csb validate] Checking: {args.config}")

    try:
        config = load_run_config(args.config)
        print("[✓] YAML syntax valid")
        print("[✓] Schema validation passed")
    except RunConfigError as exc:
        print(f"[✗] {exc}", file=sys.stderr)
        return 1

    try:
        warnings = validate_run_config_env(config)
        print("[✓] Environment validation passed")
        for w in warnings:
            print(f"    ⚠ {w}")
    except RunConfigError as exc:
        print(f"[✗] {exc}", file=sys.stderr)
        return 1

    print()
    print(f"  Agent:        {config.agent.value}")
    print(f"  Model:        {config.model}")
    print(
        f"  Augmentation: {config.augmentation.value} → config={config.config_name()}"
    )
    print(f"  Category:     {config.category.value}")
    subset = config.resolved_task_subset(_REPO_ROOT)
    print(f"  Task subset:  {subset}")
    print(f"  Parallel:     {config.parallel or 'auto-detect'}")
    print(f"  Skip completed: {config.skip_completed}")
    print()
    print("[✓] Config valid")
    return 0


# ---------------------------------------------------------------------------
# csb eval
# ---------------------------------------------------------------------------


def _cmd_eval(args) -> int:
    from lib.csb.auth import InvalidKeyError, validate_api_key
    from lib.csb.eval_runner import run_eval

    # Determine whether the caller has access to the full suite.
    api_key: str | None = args.api_key
    public_only = False

    if args.suite == "full":
        if api_key is None:
            print(
                "[csb eval] No --api-key provided. "
                "Running public-partition tasks only.",
                file=sys.stderr,
            )
            public_only = True
        else:
            try:
                payload = validate_api_key(api_key)
            except InvalidKeyError as exc:
                print(
                    f"[csb eval] ERROR: Invalid API key — {exc}",
                    file=sys.stderr,
                )
                return 1

            granted_suite = payload.get("suite", "")
            if granted_suite != "full":
                print(
                    f"[csb eval] ERROR: API key grants suite={granted_suite!r}, "
                    f"but --suite full was requested.",
                    file=sys.stderr,
                )
                return 1

            print(
                f"[csb eval] API key validated (org={payload.get('org', 'unknown')}). "
                f"Running full suite.",
                file=sys.stderr,
            )

    try:
        run_eval(
            suite=args.suite,
            agent_command=args.agent_command,
            output_path=args.output,
            timeout=args.timeout,
            public_only=public_only,
        )
        return 0
    except ValueError as exc:
        print(f"[csb eval] ERROR: {exc}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# csb report
# ---------------------------------------------------------------------------


def _cmd_report(args) -> int:
    if args.browser:
        from lib.csb.report import serve_browser

        return serve_browser(
            results_path=args.results_file,
            port=args.port,
            include_baseline=not args.no_baseline,
        )

    from lib.csb.report import display_report

    view_mode = None
    if getattr(args, "summary", False):
        view_mode = "summary"
    elif getattr(args, "detailed", False):
        view_mode = "detailed"

    return display_report(
        results_path=args.results_file,
        fmt=args.format,
        view_mode=view_mode,
    )


# ---------------------------------------------------------------------------
# csb estimate
# ---------------------------------------------------------------------------


def _cmd_estimate(args) -> int:
    from lib.csb.cost_estimator import cmd_estimate

    return cmd_estimate(args)


# ---------------------------------------------------------------------------
# csb diagnose
# ---------------------------------------------------------------------------


def _cmd_diagnose(args) -> int:
    from lib.csb.diagnose import cmd_diagnose

    return cmd_diagnose(args)
