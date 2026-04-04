"""LLM-assisted annotator for the Agent Reliability Observatory.

Reads a trial's task prompt, truncated trajectory, and signal vector,
then asks a Claude model to propose taxonomy categories.  Designed to
calibrate against heuristic annotations and surface categories the
heuristic rules cannot detect (e.g. decomposition_failure, stale_context).

Supports two backends:
- ``claude-code``: Uses the ``claude`` CLI in print mode (default).
  Requires the ``claude`` CLI to be installed and authenticated.
- ``api``: Uses the Anthropic Python SDK directly.
  Requires ``ANTHROPIC_API_KEY`` in the environment.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from observatory.taxonomy import load_taxonomy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model alias mapping (used by both backends)
# ---------------------------------------------------------------------------

_MODEL_ALIASES = {
    "haiku": "haiku",
    "sonnet": "sonnet",
    "opus": "opus",
}

_API_MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}


def _resolve_model_alias(model: str) -> str:
    """Resolve to a short alias for claude CLI (haiku/sonnet/opus)."""
    return _MODEL_ALIASES.get(model, model)


def _resolve_model_api(model: str) -> str:
    """Resolve to a full model ID for the Anthropic API."""
    return _API_MODEL_MAP.get(model, model)


# ---------------------------------------------------------------------------
# JSON Schema for structured output (claude --json-schema)
# ---------------------------------------------------------------------------

_ANNOTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "string"},
                },
                "required": ["name", "confidence", "evidence"],
            },
        },
    },
    "required": ["categories"],
}


# ---------------------------------------------------------------------------
# Taxonomy prompt fragment
# ---------------------------------------------------------------------------

def _taxonomy_yaml() -> str:
    """Return the full taxonomy YAML as a string for prompt injection."""
    path = Path(__file__).parent / "taxonomy_v1.yaml"
    return path.read_text()


# ---------------------------------------------------------------------------
# Trial data loading
# ---------------------------------------------------------------------------

def _read_text(path: Path, max_chars: int = 0) -> str | None:
    """Read a text file, optionally truncating to *max_chars*."""
    try:
        text = path.read_text(errors="replace")
        if max_chars > 0 and len(text) > max_chars:
            return text[:max_chars] + "\n... [truncated]"
        return text
    except (FileNotFoundError, OSError):
        return None


def _load_json(path: Path) -> Any | None:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _truncate_trajectory(traj: dict | None, first_n: int = 30, last_n: int = 10) -> list[dict]:
    """Return a truncated list of trajectory steps (first N + last N).

    If the trajectory has fewer than first_n + last_n steps, all steps
    are returned.
    """
    if traj is None:
        return []
    steps = traj.get("steps") or []
    if len(steps) <= first_n + last_n:
        return steps
    return steps[:first_n] + [{"_marker": f"... ({len(steps) - first_n - last_n} steps omitted) ..."}] + steps[-last_n:]


def _summarise_step(step: dict) -> dict:
    """Produce a compact summary of a trajectory step for the prompt.

    Keeps tool call name + truncated arguments, and a short observation
    excerpt.  This controls prompt size.
    """
    summary: dict[str, Any] = {}
    tool_calls = step.get("tool_calls") or []
    if tool_calls:
        calls = []
        for tc in tool_calls:
            entry: dict[str, Any] = {"tool": tc.get("function_name", "?")}
            args = tc.get("arguments")
            if isinstance(args, dict):
                # Keep only short string args
                compact = {}
                for k, v in args.items():
                    s = str(v)
                    compact[k] = s[:200] + "..." if len(s) > 200 else s
                entry["args"] = compact
            elif isinstance(args, str):
                entry["args"] = args[:200] + ("..." if len(args) > 200 else "")
            calls.append(entry)
        summary["tool_calls"] = calls

    # Compact observation
    obs = step.get("observation") or {}
    results = obs.get("results") or []
    if results:
        excerpts = []
        for r in results[:2]:  # at most 2 result blocks
            content = str(r.get("content", ""))
            excerpts.append(content[:300] + ("..." if len(content) > 300 else ""))
        summary["observation"] = excerpts

    if "_marker" in step:
        summary["_marker"] = step["_marker"]

    return summary


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_prompt(
    instruction: str | None,
    trajectory_steps: list[dict],
    signals: dict,
    taxonomy_yaml: str,
) -> str:
    """Build the annotation prompt for the LLM."""
    parts: list[str] = []

    parts.append(
        "You are an expert annotator for the Agent Reliability Observatory. "
        "Your job is to read a coding-agent trial (task prompt, trajectory, "
        "and extracted signals) and assign taxonomy categories that explain "
        "why the agent succeeded or failed.\n"
    )

    parts.append("## Taxonomy\n")
    parts.append("The following YAML defines all valid categories. "
                 "You MUST only use category names from this taxonomy.\n")
    parts.append(f"```yaml\n{taxonomy_yaml}```\n")

    parts.append("## Task instruction\n")
    if instruction:
        parts.append(f"```\n{instruction[:4000]}\n```\n")
    else:
        parts.append("(not available)\n")

    parts.append("## Trajectory (truncated)\n")
    if trajectory_steps:
        compact = [_summarise_step(s) for s in trajectory_steps]
        parts.append(f"```json\n{json.dumps(compact, indent=1, default=str)[:12000]}\n```\n")
    else:
        parts.append("(no trajectory available)\n")

    parts.append("## Extracted signals\n")
    # Filter out large/unhelpful fields
    filtered = {k: v for k, v in signals.items()
                if k not in ("tool_calls_by_name", "trial_path") and v is not None}
    parts.append(f"```json\n{json.dumps(filtered, indent=1, default=str)}\n```\n")

    parts.append(
        "## Instructions\n"
        "Based on the above, assign one or more taxonomy categories to this trial. "
        "For each category, provide:\n"
        "- **name**: exact category name from the taxonomy\n"
        "- **confidence**: a number 0-1 (0.9=high, 0.6=medium, 0.3=low)\n"
        "- **evidence**: a brief explanation citing specific trajectory steps or signals\n\n"
        "Return your answer as a JSON object with a single key \"categories\" "
        "containing an array of objects, each with keys: name, confidence, evidence.\n"
        "If no categories apply, return: {\"categories\": []}\n"
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Validation helper (shared by both backends)
# ---------------------------------------------------------------------------

def _validate_categories(categories: list, trial_dir: str | Path) -> list[dict]:
    """Validate and filter LLM-returned categories against the taxonomy."""
    taxonomy_names = {cat["name"] for cat in load_taxonomy()["categories"]}
    valid = []
    for cat in categories:
        if not isinstance(cat, dict):
            continue
        name = cat.get("name")
        if name not in taxonomy_names:
            logger.warning("LLM returned unknown category '%s' for %s", name, trial_dir)
            continue
        valid.append({
            "name": name,
            "confidence": float(cat.get("confidence", 0.6)),
            "evidence": str(cat.get("evidence", "")),
        })
    return valid


# ---------------------------------------------------------------------------
# Backend: claude-code (subprocess)
# ---------------------------------------------------------------------------

def _find_claude_cli() -> str:
    """Locate the claude CLI binary."""
    path = shutil.which("claude")
    if path is None:
        raise FileNotFoundError(
            "claude CLI not found on PATH. "
            "Install it: https://docs.anthropic.com/en/docs/claude-code"
        )
    return path


def annotate_trial_claude_code(
    trial_dir: str | Path,
    signals: dict,
    model: str = "haiku",
) -> list[dict]:
    """Annotate a single trial by spawning a ``claude -p`` subprocess.

    Uses the currently authenticated Claude Code account — no API key needed.
    """
    claude_bin = _find_claude_cli()
    trial_dir = Path(trial_dir)

    instruction = _read_text(trial_dir / "agent" / "instruction.txt", max_chars=4000)
    traj = _load_json(trial_dir / "agent" / "trajectory.json")
    truncated = _truncate_trajectory(traj, first_n=30, last_n=10)
    taxonomy = _taxonomy_yaml()
    prompt = _build_prompt(instruction, truncated, signals, taxonomy)
    model_alias = _resolve_model_alias(model)
    schema_str = json.dumps(_ANNOTATION_SCHEMA)

    try:
        result = subprocess.run(
            [
                claude_bin, "-p",
                "--output-format", "json",
                "--json-schema", schema_str,
                "--model", model_alias,
                "--no-session-persistence",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.error(
                "claude CLI failed for %s (rc=%d): %s",
                trial_dir, result.returncode, result.stderr[:500],
            )
            return []

        envelope = json.loads(result.stdout)

        if envelope.get("is_error"):
            logger.error(
                "claude CLI returned error for %s: %s",
                trial_dir, envelope.get("result", "")[:500],
            )
            return []

        # Structured output is in the structured_output field
        structured = envelope.get("structured_output")
        if structured and isinstance(structured, dict):
            categories = structured.get("categories", [])
        else:
            # Fall back to parsing the result text
            raw = envelope.get("result", "").strip()
            if not raw:
                return []
            parsed = json.loads(raw)
            categories = parsed.get("categories", parsed) if isinstance(parsed, dict) else parsed

        if not isinstance(categories, list):
            logger.warning("Non-list categories from claude CLI for %s", trial_dir)
            return []

        return _validate_categories(categories, trial_dir)

    except subprocess.TimeoutExpired:
        logger.error("claude CLI timed out for %s", trial_dir)
        return []
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse claude CLI output for %s: %s", trial_dir, exc)
        return []
    except Exception as exc:
        logger.error("Error running claude CLI for %s: %s", trial_dir, exc)
        return []


async def _annotate_one_claude_code(
    idx: int,
    trial_dir: Path,
    signals: dict,
    model: str,
    sem: asyncio.Semaphore,
    claude_bin: str,
    taxonomy: str,
) -> tuple[int, list[dict]]:
    """Async wrapper: spawn one claude -p subprocess under a semaphore."""
    async with sem:
        instruction = _read_text(trial_dir / "agent" / "instruction.txt", max_chars=4000)
        traj = _load_json(trial_dir / "agent" / "trajectory.json")
        truncated = _truncate_trajectory(traj, first_n=30, last_n=10)
        prompt = _build_prompt(instruction, truncated, signals, taxonomy)
        model_alias = _resolve_model_alias(model)
        schema_str = json.dumps(_ANNOTATION_SCHEMA)

        try:
            proc = await asyncio.create_subprocess_exec(
                claude_bin, "-p",
                "--output-format", "json",
                "--json-schema", schema_str,
                "--model", model_alias,
                "--no-session-persistence",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                logger.error(
                    "claude CLI failed for trial %d (%s): %s",
                    idx, trial_dir, stderr.decode()[:500],
                )
                return idx, []

            envelope = json.loads(stdout.decode())

            if envelope.get("is_error"):
                logger.error(
                    "claude CLI error for trial %d (%s): %s",
                    idx, trial_dir, envelope.get("result", "")[:500],
                )
                return idx, []

            structured = envelope.get("structured_output")
            if structured and isinstance(structured, dict):
                categories = structured.get("categories", [])
            else:
                raw = envelope.get("result", "").strip()
                if not raw:
                    return idx, []
                parsed = json.loads(raw)
                categories = parsed.get("categories", parsed) if isinstance(parsed, dict) else parsed

            if not isinstance(categories, list):
                return idx, []

            return idx, _validate_categories(categories, trial_dir)

        except asyncio.TimeoutError:
            logger.error("claude CLI timed out for trial %d (%s)", idx, trial_dir)
            return idx, []
        except json.JSONDecodeError as exc:
            logger.error("JSON parse error for trial %d (%s): %s", idx, trial_dir, exc)
            return idx, []
        except Exception as exc:
            logger.error("Error for trial %d (%s): %s", idx, trial_dir, exc)
            return idx, []


def annotate_batch_claude_code(
    trials: list[str | Path],
    signals_list: list[dict],
    model: str = "haiku",
    max_concurrent: int = 5,
) -> list[list[dict]]:
    """Annotate a batch of trials using parallel ``claude -p`` subprocesses."""
    if len(trials) != len(signals_list):
        raise ValueError(
            f"trials ({len(trials)}) and signals_list ({len(signals_list)}) "
            "must have the same length"
        )

    claude_bin = _find_claude_cli()
    taxonomy = _taxonomy_yaml()
    sem = asyncio.Semaphore(max_concurrent)

    async def _run_all() -> list[list[dict]]:
        results: list[list[dict]] = [[] for _ in trials]
        tasks = [
            _annotate_one_claude_code(
                i, Path(t), s, model, sem, claude_bin, taxonomy,
            )
            for i, (t, s) in enumerate(zip(trials, signals_list))
        ]
        done = 0
        for coro in asyncio.as_completed(tasks):
            idx, cats = await coro
            results[idx] = cats
            done += 1
            print(f"  [{done}/{len(trials)}] annotated", file=sys.stderr)
        return results

    return asyncio.run(_run_all())


# ---------------------------------------------------------------------------
# Backend: api (Anthropic SDK — original)
# ---------------------------------------------------------------------------

def annotate_trial_api(
    trial_dir: str | Path,
    signals: dict,
    model: str = "haiku",
) -> list[dict]:
    """Annotate a single trial using the Anthropic API directly.

    Requires ``ANTHROPIC_API_KEY`` in the environment.
    """
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic SDK not installed — run: pip install anthropic")
        return []

    trial_dir = Path(trial_dir)
    instruction = _read_text(trial_dir / "agent" / "instruction.txt", max_chars=4000)
    traj = _load_json(trial_dir / "agent" / "trajectory.json")
    truncated = _truncate_trajectory(traj, first_n=30, last_n=10)
    taxonomy = _taxonomy_yaml()

    prompt = _build_prompt(instruction, truncated, signals, taxonomy)
    model_id = _resolve_model_api(model)

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=model_id,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw = "\n".join(lines).strip()
        parsed = json.loads(raw)
        # Handle both {"categories": [...]} and bare [...] formats
        if isinstance(parsed, dict):
            categories = parsed.get("categories", [])
        elif isinstance(parsed, list):
            categories = parsed
        else:
            logger.warning("LLM returned unexpected type for %s", trial_dir)
            return []
        return _validate_categories(categories, trial_dir)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM JSON for %s: %s", trial_dir, exc)
        return []
    except Exception as exc:
        logger.error("API error annotating %s: %s", trial_dir, exc)
        return []


def annotate_batch_api(
    trials: list[str | Path],
    signals_list: list[dict],
    model: str = "haiku",
    max_concurrent: int = 5,
) -> list[list[dict]]:
    """Annotate a batch of trials using the Anthropic API with concurrency."""
    if len(trials) != len(signals_list):
        raise ValueError(
            f"trials ({len(trials)}) and signals_list ({len(signals_list)}) "
            "must have the same length"
        )

    try:
        import anthropic
    except ImportError:
        logger.error("anthropic SDK not installed — run: pip install anthropic")
        return [[] for _ in trials]

    sem = asyncio.Semaphore(max_concurrent)
    taxonomy = _taxonomy_yaml()

    async def _annotate_one(
        idx: int, trial_dir: Path, signals: dict, aclient: Any,
    ) -> tuple[int, list[dict]]:
        async with sem:
            instruction = _read_text(trial_dir / "agent" / "instruction.txt", max_chars=4000)
            traj = _load_json(trial_dir / "agent" / "trajectory.json")
            truncated = _truncate_trajectory(traj, first_n=30, last_n=10)
            prompt = _build_prompt(instruction, truncated, signals, taxonomy)
            model_id = _resolve_model_api(model)

            try:
                message = await aclient.messages.create(
                    model=model_id,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = message.content[0].text.strip()
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    categories = parsed.get("categories", [])
                elif isinstance(parsed, list):
                    categories = parsed
                else:
                    return idx, []
                return idx, _validate_categories(categories, trial_dir)
            except json.JSONDecodeError as exc:
                logger.error("JSON parse error for trial %d (%s): %s", idx, trial_dir, exc)
                return idx, []
            except Exception as exc:
                logger.error("API error for trial %d (%s): %s", idx, trial_dir, exc)
                return idx, []

    async def _run_all() -> list[list[dict]]:
        aclient = anthropic.AsyncAnthropic()
        results: list[list[dict]] = [[] for _ in trials]
        tasks = [
            _annotate_one(i, Path(t), s, aclient)
            for i, (t, s) in enumerate(zip(trials, signals_list))
        ]
        done = 0
        for coro in asyncio.as_completed(tasks):
            idx, cats = await coro
            results[idx] = cats
            done += 1
            print(f"  [{done}/{len(trials)}] annotated", file=sys.stderr)
        return results

    return asyncio.run(_run_all())


# ---------------------------------------------------------------------------
# Unified dispatch
# ---------------------------------------------------------------------------

def annotate_trial_llm(
    trial_dir: str | Path,
    signals: dict,
    model: str = "haiku",
    backend: str = "claude-code",
) -> list[dict]:
    """Annotate a single trial using an LLM.

    Parameters
    ----------
    trial_dir : str or Path
        Path to the trial directory.
    signals : dict
        Pre-extracted signal vector for this trial.
    model : str
        Model alias (``'haiku'``, ``'sonnet'``, ``'opus'``) or full model ID.
    backend : str
        ``'claude-code'`` (default) uses the ``claude`` CLI.
        ``'api'`` uses the Anthropic Python SDK.
    """
    if backend == "claude-code":
        return annotate_trial_claude_code(trial_dir, signals, model)
    elif backend == "api":
        return annotate_trial_api(trial_dir, signals, model)
    else:
        raise ValueError(f"Unknown backend: {backend!r}. Use 'claude-code' or 'api'.")


def annotate_batch(
    trials: list[str | Path],
    signals_list: list[dict],
    model: str = "haiku",
    max_concurrent: int = 5,
    backend: str = "claude-code",
) -> list[list[dict]]:
    """Annotate a batch of trials using the LLM, with concurrency control.

    Parameters
    ----------
    trials : list of str or Path
        Trial directory paths.
    signals_list : list of dict
        Corresponding signal vectors (same length as *trials*).
    model : str
        Model alias or full model ID.
    max_concurrent : int
        Maximum number of concurrent calls/subprocesses.
    backend : str
        ``'claude-code'`` (default) or ``'api'``.
    """
    if backend == "claude-code":
        return annotate_batch_claude_code(trials, signals_list, model, max_concurrent)
    elif backend == "api":
        return annotate_batch_api(trials, signals_list, model, max_concurrent)
    else:
        raise ValueError(f"Unknown backend: {backend!r}. Use 'claude-code' or 'api'.")


# ---------------------------------------------------------------------------
# Judge scoring integration
# ---------------------------------------------------------------------------

def _build_judge_input(trial_dir: Path, signals: dict) -> Any:
    """Build a JudgeInput from a trial directory for dimension scoring.

    Imports from scripts/csb_metrics/judge and scripts/evaluation/run_judge
    to reuse the existing judge infrastructure.
    """
    # Add scripts/ to path for imports
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from csb_metrics.judge import JudgeInput
    from csb_metrics.judge.oracle import discover_oracle

    instruction = _read_text(trial_dir / "agent" / "instruction.txt", max_chars=3000) or ""

    # Extract code changes from transcript
    agent_output = _extract_code_changes(trial_dir)

    # Build tool call summary from signals
    tool_calls_by_name = signals.get("tool_calls_by_name") or {}
    if tool_calls_by_name:
        sorted_tools = sorted(tool_calls_by_name.items(), key=lambda x: x[1], reverse=True)
        tool_summary = " ".join(f"{n}:{c}" for n, c in sorted_tools[:15])
    else:
        tool_summary = "(no tool calls recorded)"

    mcp_tools = [name for name in tool_calls_by_name if name.startswith("mcp__")]

    # Discover oracle ground truth for grounded scoring
    raw_task_id = signals.get("task_id") or "unknown"
    benchmark = signals.get("benchmark") or "unknown"
    benchmarks_dir = Path(__file__).resolve().parent.parent / "benchmarks"

    # Clean task_id: strip config prefix and trial hash
    import re
    _clean_prefixes = ("mcp_", "baseline_", "cursor_", "sgonly_", "github_", "augment_")
    _hash_re = re.compile(r"^(.+?)_[a-z0-9]{5,8}$")
    clean_id = raw_task_id
    for pfx in _clean_prefixes:
        if clean_id.startswith(pfx):
            clean_id = clean_id[len(pfx):]
            break
    m = _hash_re.match(clean_id)
    if m:
        clean_id = m.group(1)

    oracle = discover_oracle(clean_id, benchmark, benchmarks_dir)

    return JudgeInput(
        task_id=raw_task_id,
        task_description=instruction,
        code_changes=agent_output,
        tool_calls=tool_summary,
        verifier_reward=float(signals.get("reward") or 0.0),
        oracle_ground_truth=oracle.ground_truth_text,
        oracle_expected_approach=oracle.expected_approach,
        oracle_evaluation_criteria=oracle.evaluation_criteria,
        oracle_context_files=oracle.context_files,
        mcp_tools_used=mcp_tools,
        oracle_confidence=oracle.confidence,
    )


def _extract_code_changes(trial_dir: Path) -> str:
    """Extract agent code changes from transcript (lightweight version).

    Reads the Claude Code JSONL transcript and extracts Edit/Write calls.
    """
    transcript = trial_dir / "agent" / "claude-code.txt"
    if not transcript.is_file():
        return "(no code changes recorded)"

    edits: list[str] = []
    writes: dict[str, str] = {}
    budget = 20_000  # chars

    try:
        for line in transcript.open(errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            message = entry.get("message") or {}
            for block in message.get("content") or []:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                inp = block.get("input") or {}
                if name == "Edit":
                    fp = inp.get("file_path", "")
                    old_s = inp.get("old_string", "")
                    new_s = inp.get("new_string", "")
                    if fp and (new_s or old_s):
                        edits.append(f"Edit {fp}:\n-{old_s}\n+{new_s}")
                elif name == "Write":
                    fp = inp.get("file_path", "")
                    content = inp.get("content", "")
                    if fp and content:
                        writes[fp] = content
    except OSError:
        return "(error reading transcript)"

    parts = []
    if edits:
        parts.append("=== Edits ===\n" + "\n---\n".join(edits))
    if writes:
        items = [f"Write {fp}:\n{body}" for fp, body in writes.items()]
        parts.append("=== Written Files ===\n" + "\n---\n".join(items))

    if not parts:
        return "(no code changes recorded)"

    summary = "\n\n".join(parts)
    if len(summary) > budget:
        summary = summary[:budget] + "\n[... truncated ...]"
    return summary


def judge_trial(
    trial_dir: str | Path,
    signals: dict,
    model: str = "haiku",
    backend: str = "claude-code",
) -> dict | None:
    """Run the LLM judge on a single trial and return dimension scores.

    Parameters
    ----------
    trial_dir : str or Path
        Path to the trial directory.
    signals : dict
        Pre-extracted signal vector for this trial.
    model : str
        Model alias (used to select the judge model).
    backend : str
        ``'claude-code'`` routes through the claude CLI backend (``cc:model``).
        ``'api'`` uses the Anthropic SDK backend (``claude-model-id``).

    Returns
    -------
    dict or None
        Judge result dict with keys: judge_score, dimension_scores,
        reasoning. Returns None on error.
    """
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from csb_metrics.judge import LLMJudge

    trial_dir = Path(trial_dir)

    # Map backend + model to judge model identifier
    if backend == "claude-code":
        judge_model = f"cc:{_resolve_model_alias(model)}"
    else:
        judge_model = _resolve_model_api(model)

    try:
        judge = LLMJudge(model=judge_model)
        judge_input = _build_judge_input(trial_dir, signals)
        result = judge.evaluate(judge_input)
        return {
            "judge_score": round(result.judge_score, 4),
            "dimension_scores": {
                dim: round(score, 4)
                for dim, score in result.dimension_scores.items()
            },
            "judge_model": judge_model,
        }
    except Exception as exc:
        logger.error("Judge error for %s: %s", trial_dir, exc)
        return None
