"""CLI entrypoint for the Agent Reliability Observatory."""

import argparse
import json
import sys
from pathlib import Path


def cmd_extract(args):
    """Extract signals from trial directories."""
    from observatory.signals import extract_all

    runs_dir = Path(args.runs_dir)
    if not runs_dir.is_dir():
        print(f"Error: runs directory not found: {runs_dir}", file=sys.stderr)
        sys.exit(1)

    signals = extract_all(runs_dir)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(signals, f, indent=2, default=str)

    print(f"Extracted signals from {len(signals)} trials", file=sys.stderr)


def cmd_annotate(args):
    """Generate heuristic annotations from extracted signals."""
    from observatory.annotator import annotate_all

    signals_path = Path(args.signals)
    if not signals_path.is_file():
        print(f"Error: signals file not found: {signals_path}", file=sys.stderr)
        sys.exit(1)

    with open(signals_path) as f:
        signals_list = json.load(f)

    annotations = annotate_all(signals_list)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(annotations, f, indent=2, default=str)

    total_categories = sum(len(a["categories"]) for a in annotations["annotations"])
    print(
        f"Annotated {len(annotations['annotations'])} trials "
        f"with {total_categories} total category assignments",
        file=sys.stderr,
    )


def cmd_report(args):
    """Generate reliability report from annotations."""
    from observatory.report import generate_report

    annotations_path = Path(args.annotations)
    if not annotations_path.is_file():
        print(f"Error: annotations file not found: {annotations_path}", file=sys.stderr)
        sys.exit(1)

    with open(annotations_path) as f:
        annotations = json.load(f)

    output_dir = Path(args.output)
    md_path, json_path = generate_report(annotations, output_dir)

    print(f"Report written to {md_path} and {json_path}", file=sys.stderr)


def cmd_llm_annotate(args):
    """Generate LLM-assisted annotations for a sample of trials."""
    import random
    from datetime import datetime, timezone

    from observatory.llm_annotator import annotate_trial_llm, judge_trial
    from observatory.taxonomy import load_taxonomy

    signals_path = Path(args.signals)
    if not signals_path.is_file():
        print(f"Error: signals file not found: {signals_path}", file=sys.stderr)
        sys.exit(1)

    with open(signals_path) as f:
        signals_list = json.load(f)

    # Filter to trials that have trajectories on disk
    has_trajectory = [
        s for s in signals_list
        if s.get("trial_path")
        and (Path(s["trial_path"]) / "agent" / "trajectory.json").is_file()
    ]
    if not has_trajectory:
        print("Error: no trials with trajectory files found", file=sys.stderr)
        sys.exit(1)

    backend = args.backend
    run_judge = args.judge
    sample_size = min(args.sample_size, len(has_trajectory))
    sampled = random.sample(has_trajectory, sample_size)
    print(
        f"Sampled {sample_size} trials (from {len(has_trajectory)} with trajectories)",
        file=sys.stderr,
    )
    print(f"Backend: {backend}, Model: {args.model}, Judge: {run_judge}", file=sys.stderr)

    taxonomy = load_taxonomy()
    now = datetime.now(timezone.utc).isoformat()
    annotations = []
    judge_count = 0

    for i, sig in enumerate(sampled, 1):
        print(f"[{i}/{sample_size}] Annotating...", file=sys.stderr, end="")
        trial_dir = sig["trial_path"]
        cats = annotate_trial_llm(trial_dir, sig, model=args.model, backend=backend)

        reward_val = sig.get("reward")
        annotation = {
            "task_id": sig.get("task_id") or "unknown",
            "trial_path": sig.get("trial_path") or "",
            "reward": float(reward_val) if reward_val is not None else 0.0,
            "passed": bool(sig.get("passed")) if sig.get("passed") is not None else False,
            "categories": cats,
            "annotated_at": now,
        }
        for key in ("config_name", "benchmark", "model"):
            if sig.get(key):
                annotation[key] = sig[key]

        # Run judge scoring if requested
        if run_judge:
            print(" judging...", file=sys.stderr, end="")
            judge_result = judge_trial(
                trial_dir, sig, model=args.model, backend=backend,
            )
            if judge_result:
                annotation["judge"] = judge_result
                judge_count += 1

        print(" done", file=sys.stderr)
        annotations.append(annotation)

    result = {
        "schema_version": "observatory-annotation-v1",
        "taxonomy_version": str(taxonomy["version"]),
        "generated_at": now,
        "annotator": {
            "type": "llm",
            "identity": f"observatory.llm_annotator model={args.model} backend={backend}",
        },
        "annotations": annotations,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(result, f, indent=2, default=str)

    total_categories = sum(len(a["categories"]) for a in annotations)
    summary = (
        f"Done: {len(annotations)}/{sample_size} trials annotated "
        f"with {total_categories} category assignments"
    )
    if run_judge:
        summary += f", {judge_count} judge scores"
    summary += f". Output: {output}"
    print(summary, file=sys.stderr)


def cmd_train(args):
    """Train per-category classifiers from LLM-labeled data."""
    from observatory.classifier import evaluate, format_eval_markdown, save_model, train

    model = train(
        llm_file=args.labels,
        signals_file=args.signals,
        min_positive=args.min_positive,
        lr=args.lr,
        epochs=args.epochs,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_model(model, output)

    n_clf = len(model["classifiers"])
    n_skip = len(model["skipped_categories"])
    print(
        f"Trained {n_clf} classifiers on {model['training_samples']} samples "
        f"({n_skip} categories skipped, < {model['min_positive']} positive)",
        file=sys.stderr,
    )
    for cat, clf in sorted(model["classifiers"].items()):
        print(
            f"  {cat}: {clf['positive_count']}/{clf['total_count']} positive, "
            f"train_acc={clf['train_accuracy']:.2f}",
            file=sys.stderr,
        )

    # If --eval is provided, evaluate on the same data (quick sanity check)
    if args.eval:
        eval_results = evaluate(model, args.labels, args.signals)
        print("\n" + format_eval_markdown(eval_results, model), file=sys.stderr)

    print(f"Model saved to {output}", file=sys.stderr)


def cmd_predict(args):
    """Predict categories for all trials using a trained classifier."""
    from observatory.classifier import load_model, predict_all

    model = load_model(args.model)
    with open(args.signals) as f:
        signals_list = json.load(f)

    result = predict_all(signals_list, model, threshold=args.threshold)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(result, f, indent=2)

    n = len(result["annotations"])
    total_cats = sum(len(a["categories"]) for a in result["annotations"])
    print(
        f"Predicted {total_cats} category assignments across {n} trials "
        f"(threshold={args.threshold}). Output: {output}",
        file=sys.stderr,
    )


def cmd_ensemble(args):
    """Run two-tier ensemble annotation (heuristic + classifier) on full corpus."""
    from observatory.ensemble import ensemble_all
    from observatory.classifier import load_model

    model = load_model(args.model)
    with open(args.signals) as f:
        signals_list = json.load(f)

    result = ensemble_all(
        signals_list, model,
        classifier_threshold=args.threshold,
        classifier_min_f1=args.min_f1,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(result, f, indent=2)

    n = len(result["annotations"])
    total_cats = sum(len(a["categories"]) for a in result["annotations"])
    tiers = result.get("tier_counts", {})
    print(
        f"Ensemble: {total_cats} assignments across {n} trials "
        f"(heuristic={tiers.get('heuristic', 0)}, classifier={tiers.get('classifier', 0)}). "
        f"Output: {output}",
        file=sys.stderr,
    )


def cmd_validate(args):
    """Validate annotation files against schema and taxonomy."""
    import jsonschema

    from observatory.taxonomy import valid_category_names

    annotations_path = Path(args.annotations)
    if not annotations_path.is_file():
        print(f"Error: annotations file not found: {annotations_path}", file=sys.stderr)
        sys.exit(1)

    # Load annotations
    try:
        with open(annotations_path) as f:
            annotations = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    errors = []

    # Validate against JSON Schema
    schema_path = Path(__file__).parent / "annotation_schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=annotations, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")

    # Validate category names against taxonomy
    valid_names = valid_category_names()
    for i, ann in enumerate(annotations.get("annotations", [])):
        for cat in ann.get("categories", []):
            name = cat.get("name", "")
            if name not in valid_names:
                errors.append(
                    f"Annotation [{i}] ({ann.get('task_id', '?')}): "
                    f"unknown category '{name}'"
                )

    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    n_annotations = len(annotations.get("annotations", []))
    print(
        f"Validation passed: {n_annotations} annotations, all valid.",
        file=sys.stderr,
    )
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        prog="observatory",
        description="Agent Reliability Observatory — trace-backed reliability analysis for CodeScaleBench",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract signals from trial directories")
    p_extract.add_argument("--runs-dir", required=True, help="Path to runs/_raw directory")
    p_extract.add_argument("--output", required=True, help="Output signals JSON file")
    p_extract.set_defaults(func=cmd_extract)

    # annotate
    p_annotate = subparsers.add_parser("annotate", help="Generate heuristic annotations from signals")
    p_annotate.add_argument("--signals", required=True, help="Input signals JSON file")
    p_annotate.add_argument("--output", required=True, help="Output annotations JSON file")
    p_annotate.set_defaults(func=cmd_annotate)

    # report
    p_report = subparsers.add_parser("report", help="Generate reliability report from annotations")
    p_report.add_argument("--annotations", required=True, help="Input annotations JSON file")
    p_report.add_argument("--output", required=True, help="Output directory for report files")
    p_report.set_defaults(func=cmd_report)

    # llm-annotate
    p_llm = subparsers.add_parser("llm-annotate", help="Generate LLM-assisted annotations for a sample of trials")
    p_llm.add_argument("--signals", required=True, help="Input signals JSON file")
    p_llm.add_argument("--output", required=True, help="Output annotations JSON file")
    p_llm.add_argument("--sample-size", type=int, default=50, help="Number of trials to sample (default: 50)")
    p_llm.add_argument("--model", default="haiku", help="Model alias: haiku, sonnet, opus (default: haiku)")
    p_llm.add_argument(
        "--backend", default="claude-code", choices=["claude-code", "api"],
        help="LLM backend: 'claude-code' uses the claude CLI (default), "
             "'api' uses the Anthropic SDK (requires ANTHROPIC_API_KEY)",
    )
    p_llm.add_argument(
        "--judge", action="store_true", default=False,
        help="Also run the LLM judge to produce dimension scores "
             "(correctness, completeness, code_quality, retrieval_quality, efficiency)",
    )
    p_llm.set_defaults(func=cmd_llm_annotate)

    # train
    p_train = subparsers.add_parser("train", help="Train classifiers from LLM-labeled data")
    p_train.add_argument("--labels", required=True, help="LLM annotation JSON (training labels)")
    p_train.add_argument("--signals", required=True, help="Full signals JSON (features)")
    p_train.add_argument("--output", required=True, help="Output model JSON file")
    p_train.add_argument("--min-positive", type=int, default=3, help="Min positive examples per category (default: 3)")
    p_train.add_argument("--lr", type=float, default=0.1, help="Learning rate (default: 0.1)")
    p_train.add_argument("--epochs", type=int, default=300, help="Training epochs (default: 300)")
    p_train.add_argument("--eval", action="store_true", help="Evaluate on training data after training")
    p_train.set_defaults(func=cmd_train)

    # predict
    p_predict = subparsers.add_parser("predict", help="Predict categories using trained classifier")
    p_predict.add_argument("--model", required=True, help="Trained model JSON file")
    p_predict.add_argument("--signals", required=True, help="Signals JSON to predict on")
    p_predict.add_argument("--output", required=True, help="Output annotations JSON file")
    p_predict.add_argument("--threshold", type=float, default=0.5, help="Prediction threshold (default: 0.5)")
    p_predict.set_defaults(func=cmd_predict)

    # ensemble
    p_ensemble = subparsers.add_parser("ensemble", help="Run two-tier ensemble annotation (heuristic + classifier)")
    p_ensemble.add_argument("--signals", required=True, help="Signals JSON file")
    p_ensemble.add_argument("--model", required=True, help="Trained classifier model JSON")
    p_ensemble.add_argument("--output", required=True, help="Output annotations JSON file")
    p_ensemble.add_argument("--threshold", type=float, default=0.5, help="Classifier prediction threshold (default: 0.5)")
    p_ensemble.add_argument("--min-f1", type=float, default=0.7, help="Minimum train accuracy to use classifier (default: 0.7)")
    p_ensemble.set_defaults(func=cmd_ensemble)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate annotation files")
    p_validate.add_argument("--annotations", required=True, help="Annotation JSON file to validate")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    args.func(args)
