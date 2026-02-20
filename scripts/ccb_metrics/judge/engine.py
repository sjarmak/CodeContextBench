"""Core LLM judge engine with multi-round voting.

Constructs prompts, calls the LLM backend (Anthropic or OpenAI),
parses responses, and optionally runs multi-round voting for ensemble
scoring. Default judge is OpenAI (gpt-4o) to avoid same-model-family
bias when evaluating Claude agent outputs.

Dimension weights:
  correctness=0.30, completeness=0.25, code_quality=0.20,
  retrieval_quality=0.15, efficiency=0.10
"""

from __future__ import annotations

import subprocess
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from .backends import create_backend
from .models import JudgeInput, JudgeResult, normalize_score
from .prompts import (
    DIRECT_REVIEW_PROMPT,
    REFERENCE_COMPLETENESS_PROMPT,
    REFERENCE_CORRECTNESS_PROMPT,
    RUBRIC_CRITERIA_PROMPT,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS: dict[str, float] = {
    "correctness": 0.30,
    "completeness": 0.25,
    "code_quality": 0.20,
    "retrieval_quality": 0.15,
    "efficiency": 0.10,
}

DEFAULT_DIMENSIONS: list[str] = list(DIMENSION_WEIGHTS)

_JUDGE_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_ccb_commit() -> str:
    """Return the current git commit SHA or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _render_prompt(template: str, judge_input: JudgeInput) -> str:
    """Fill in prompt template placeholders from JudgeInput."""
    criteria_text = (
        "\n".join(f"- {c}" for c in judge_input.oracle_evaluation_criteria)
        if judge_input.oracle_evaluation_criteria
        else "(none provided)"
    )
    context_text = (
        "\n".join(judge_input.oracle_context_files)
        if judge_input.oracle_context_files
        else "(none provided)"
    )
    return template.format(
        task_description=judge_input.task_description,
        agent_output=judge_input.code_changes or "(no code changes recorded)",
        reference_answer=judge_input.oracle_ground_truth or "(none provided)",
        evaluation_criteria=criteria_text,
        context_files=context_text,
    )


def _format_criteria(criteria: list[dict]) -> str:
    """Format a criteria list for inclusion in the rubric prompt."""
    lines: list[str] = []
    for i, c in enumerate(criteria, 1):
        metric = c.get("metric", f"criterion_{i}")
        max_score = c.get("max_score", 1)
        description = c.get("description", "")
        lines.append(f"Criterion {i}: **{metric}** (max score: {max_score})")
        lines.append(f"  {description}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _parse_criteria_scores(
    response: dict, criteria: list[dict]
) -> tuple[dict[str, dict], float]:
    """Extract per-criterion scores from LLM response.

    Returns:
        (criteria_scores, rubric_score) where rubric_score is normalized mean.
    """
    raw = response.get("criteria_scores", {})
    criteria_scores: dict[str, dict] = {}
    normalized_scores: list[float] = []

    for c in criteria:
        metric = c.get("metric", "")
        max_score = float(c.get("max_score", 1) or 1)
        entry = raw.get(metric, {})
        if isinstance(entry, dict):
            raw_score = float(entry.get("score", 0.0))
            reasoning = entry.get("reasoning", "")
        else:
            raw_score = 0.0
            reasoning = ""
        # Clamp to valid range
        raw_score = max(0.0, min(raw_score, max_score))
        normalized = raw_score / max_score if max_score > 0 else 0.0
        criteria_scores[metric] = {
            "score": raw_score,
            "max_score": max_score,
            "normalized_score": round(normalized, 4),
            "reasoning": reasoning,
        }
        normalized_scores.append(normalized)

    rubric_score = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.0
    return criteria_scores, round(rubric_score, 4)


def _select_prompt(judge_input: JudgeInput) -> str:
    """Select the appropriate prompt template based on oracle availability."""
    if judge_input.oracle_ground_truth and judge_input.oracle_ground_truth.strip():
        return REFERENCE_CORRECTNESS_PROMPT
    if judge_input.oracle_evaluation_criteria:
        return REFERENCE_COMPLETENESS_PROMPT
    return DIRECT_REVIEW_PROMPT


def _parse_dimension_scores(
    response: dict, dimensions: list[str]
) -> dict[str, float]:
    """Extract dimension scores from parsed API response dict."""
    raw = response.get("dimension_scores", {})
    scores: dict[str, float] = {}
    for dim in dimensions:
        entry = raw.get(dim, {})
        if isinstance(entry, dict):
            score = normalize_score(entry.get("score", 0.0))
        else:
            score = normalize_score(entry)
        scores[dim] = score
    return scores


def _weighted_score(dimension_scores: dict[str, float]) -> float:
    """Compute weighted average across active dimensions."""
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, score in dimension_scores.items():
        w = DIMENSION_WEIGHTS.get(dim, 0.0)
        weighted_sum += score * w
        total_weight += w
    if total_weight == 0.0:
        return 0.0
    return weighted_sum / total_weight


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class LLMJudge:
    """LLM-based judge for CCB benchmark tasks.

    Args:
        model: Model identifier. Supports Anthropic (``claude-*``) and
            OpenAI (``gpt-*``, ``o1-*``, ``o3-*``, ``o4-*``) models.
            Using a different model family from the agent avoids
            same-family evaluation bias.
        temperature: Sampling temperature (0.0 = deterministic).
        rounds: Default number of voting rounds for evaluate_with_voting.
        dimensions: Subset of dimensions to evaluate. Defaults to all 5.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        rounds: int = 1,
        dimensions: Optional[list[str]] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.rounds = rounds
        self.dimensions: list[str] = dimensions if dimensions else list(DEFAULT_DIMENSIONS)
        invalid = set(self.dimensions) - set(DIMENSION_WEIGHTS)
        if invalid:
            raise ValueError(f"Invalid dimensions: {invalid}. Valid: {list(DIMENSION_WEIGHTS)}")
        self._backend = create_backend(
            model=model, temperature=temperature
        )
        self._ccb_commit: Optional[str] = None  # lazy-loaded

    # ---- public API ----

    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        """Run a single-round evaluation.

        Args:
            judge_input: Input bundle for the task.

        Returns:
            JudgeResult with dimension_scores and judge_score.
        """
        template = _select_prompt(judge_input)
        user_prompt = _render_prompt(template, judge_input)
        system_prompt = (
            "You are a precise code evaluator. Always respond with valid JSON only."
        )

        response = self._backend.call(system_prompt, user_prompt)
        dim_scores = _parse_dimension_scores(response, self.dimensions)
        judge_score = _weighted_score(dim_scores)
        reasoning = response.get("reasoning", "")

        provenance = self._build_provenance(rounds=1, rationale=reasoning)

        return JudgeResult(
            task_id=judge_input.task_id,
            benchmark="",
            config="",
            judge_score=judge_score,
            dimension_scores=dim_scores,
            oracle_confidence="high" if (judge_input.oracle_ground_truth or "").strip() else "low",
            model=self.model,
            temperature=self.temperature,
            rounds=1,
            vote_distribution={},
            judged_at=datetime.now(timezone.utc).isoformat(),
            provenance=provenance,
        )

    def evaluate_with_voting(
        self, judge_input: JudgeInput, rounds: int = 3
    ) -> JudgeResult:
        """Run multi-round evaluation with majority voting per dimension.

        Args:
            judge_input: Input bundle for the task.
            rounds: Number of independent scoring rounds.

        Returns:
            JudgeResult with vote_distribution and confidence.
        """
        template = _select_prompt(judge_input)
        user_prompt = _render_prompt(template, judge_input)
        system_prompt = (
            "You are a precise code evaluator. Always respond with valid JSON only."
        )

        all_dim_scores: list[dict[str, float]] = []
        for _ in range(rounds):
            response = self._backend.call(system_prompt, user_prompt)
            dim_scores = _parse_dimension_scores(response, self.dimensions)
            all_dim_scores.append(dim_scores)

        # Majority-vote per dimension (median tie-break when no majority)
        voted_dims: dict[str, float] = {}
        vote_distribution: dict[str, dict] = {}
        for dim in self.dimensions:
            per_round = [d.get(dim, 0.0) for d in all_dim_scores]
            counter = Counter(per_round)
            majority_score, majority_count = counter.most_common(1)[0]
            if majority_count * 2 <= rounds and rounds > 1:
                # No majority — use median as deterministic tie-break
                sorted_scores = sorted(per_round)
                majority_score = sorted_scores[len(sorted_scores) // 2]
                majority_count = counter[majority_score]
            voted_dims[dim] = majority_score
            vote_distribution[dim] = {
                "score": majority_score,
                "majority_count": majority_count,
                "rounds": rounds,
                "all_scores": per_round,
            }

        judge_score = _weighted_score(voted_dims)

        # Overall confidence = max majority fraction across dimensions
        max_majority = max(
            vote_distribution[d]["majority_count"] for d in self.dimensions
        )
        confidence_float = max_majority / rounds

        provenance = self._build_provenance(rounds=rounds)

        return JudgeResult(
            task_id=judge_input.task_id,
            benchmark="",
            config="",
            judge_score=judge_score,
            dimension_scores=voted_dims,
            oracle_confidence="high" if (judge_input.oracle_ground_truth or "").strip() else "low",
            model=self.model,
            temperature=self.temperature,
            rounds=rounds,
            vote_distribution=vote_distribution,
            judged_at=datetime.now(timezone.utc).isoformat(),
            provenance={**provenance, "confidence": confidence_float},
        )

    def evaluate_with_criteria(
        self,
        judge_input: JudgeInput,
        criteria: list[dict],
    ) -> tuple[dict[str, dict], float]:
        """Score agent output against AAA rubric criteria from criteria.json.

        Args:
            judge_input: Task input bundle.
            criteria: List of {metric, description, max_score} dicts.

        Returns:
            (criteria_scores, rubric_score) where:
              criteria_scores = {metric: {score, max_score, normalized_score, reasoning}}
              rubric_score = mean of normalized per-criterion scores (0.0 – 1.0)
        """
        if not criteria:
            return {}, 0.0

        criteria_text = _format_criteria(criteria)
        user_prompt = RUBRIC_CRITERIA_PROMPT.format(
            task_description=judge_input.task_description,
            agent_output=judge_input.code_changes or "(no output)",
            criteria_text=criteria_text,
        )
        system_prompt = (
            "You are a precise rubric evaluator. Always respond with valid JSON only."
        )

        response = self._backend.call(system_prompt, user_prompt)
        return _parse_criteria_scores(response, criteria)

    # ---- internals ----

    def _build_provenance(self, rounds: int, rationale: str = "") -> dict:
        """Build the provenance dict for a JudgeResult."""
        if self._ccb_commit is None:
            self._ccb_commit = _get_ccb_commit()
        prov: dict = {
            "model_id": self.model,
            "temperature": self.temperature,
            "rounds": rounds,
            "ccb_commit": self._ccb_commit,
            "judge_version": _JUDGE_VERSION,
        }
        if rationale:
            prov["rationale"] = rationale
        return prov
