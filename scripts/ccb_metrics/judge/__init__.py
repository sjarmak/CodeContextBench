"""CCB LLM Judge package.

Public API exports:
  LLMJudge         — core judge engine with multi-round voting
  JudgeInput       — input bundle for a single task evaluation
  JudgeResult      — output from the judge
  OracleBundle     — ground-truth oracle data for a task
  normalize_score  — map string/numeric labels to float scores
"""

from .engine import LLMJudge
from .models import JudgeInput, JudgeResult, OracleBundle, normalize_score
from .prompts import RUBRIC_CRITERIA_PROMPT

__all__ = [
    "LLMJudge",
    "JudgeInput",
    "JudgeResult",
    "OracleBundle",
    "normalize_score",
    "RUBRIC_CRITERIA_PROMPT",
]
