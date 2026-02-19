"""Prompt templates for the CCB LLM Judge.

Three evaluation strategies:
  REFERENCE_CORRECTNESS_PROMPT — when ground-truth answer is available
  REFERENCE_COMPLETENESS_PROMPT — when ground-truth criteria list is available
  DIRECT_REVIEW_PROMPT — fallback when no oracle data exists

Each template uses {placeholders}:
  task_description, agent_output, reference_answer, evaluation_criteria, context_files

Each specifies JSON output with:
  reasoning, dimension_scores (correctness/completeness/code_quality/retrieval_quality/efficiency
  each with score+evidence), overall_score, confidence
"""

REFERENCE_CORRECTNESS_PROMPT = """\
You are an expert code evaluator assessing an AI coding agent's output against \
a known-correct reference answer.

## Task Description
{task_description}

## Reference Answer
{reference_answer}

## Evaluation Criteria
{evaluation_criteria}

## Relevant Context Files
{context_files}

## Agent Output
{agent_output}

## Instructions
Compare the agent's output to the reference answer. Score each dimension on a \
3-point scale: 1.0 (correct/complete), 0.5 (partially correct), 0.0 (incorrect/missing).

Respond with ONLY valid JSON in this exact format:
{{
  "reasoning": "<brief explanation of your assessment>",
  "dimension_scores": {{
    "correctness": {{"score": <float>, "evidence": "<what matched or diverged from reference>"}},
    "completeness": {{"score": <float>, "evidence": "<what requirements were met or missed>"}},
    "code_quality": {{"score": <float>, "evidence": "<code style, idioms, structure>"}},
    "retrieval_quality": {{"score": <float>, "evidence": "<how well agent found relevant code/context>"}},
    "efficiency": {{"score": <float>, "evidence": "<tool usage efficiency, unnecessary steps>"}}
  }},
  "overall_score": <float>,
  "confidence": "<high|medium|low>"
}}
"""

REFERENCE_COMPLETENESS_PROMPT = """\
You are an expert code evaluator assessing an AI coding agent's output against \
a checklist of expected criteria.

## Task Description
{task_description}

## Reference Answer
{reference_answer}

## Evaluation Criteria (Checklist)
{evaluation_criteria}

## Relevant Context Files
{context_files}

## Agent Output
{agent_output}

## Instructions
Evaluate the agent's output against each criterion in the checklist. Score each \
dimension on a 3-point scale: 1.0 (fully met), 0.5 (partially met), 0.0 (not met).

Respond with ONLY valid JSON in this exact format:
{{
  "reasoning": "<brief explanation of criteria coverage>",
  "dimension_scores": {{
    "correctness": {{"score": <float>, "evidence": "<criteria met correctly>"}},
    "completeness": {{"score": <float>, "evidence": "<fraction of checklist items addressed>"}},
    "code_quality": {{"score": <float>, "evidence": "<code style, idioms, structure>"}},
    "retrieval_quality": {{"score": <float>, "evidence": "<how well agent found relevant code/context>"}},
    "efficiency": {{"score": <float>, "evidence": "<tool usage efficiency, unnecessary steps>"}}
  }},
  "overall_score": <float>,
  "confidence": "<high|medium|low>"
}}
"""

DIRECT_REVIEW_PROMPT = """\
You are an expert code evaluator assessing an AI coding agent's output based on \
the task description alone. No reference answer is available.

## Task Description
{task_description}

## Reference Answer
{reference_answer}

## Evaluation Criteria
{evaluation_criteria}

## Relevant Context Files
{context_files}

## Agent Output
{agent_output}

## Instructions
Assess the agent's output based on general software engineering quality, adherence \
to the task description, and the evaluation criteria provided. Score each dimension \
on a 3-point scale: 1.0 (excellent), 0.5 (adequate), 0.0 (poor/missing).

Respond with ONLY valid JSON in this exact format:
{{
  "reasoning": "<brief explanation of your assessment>",
  "dimension_scores": {{
    "correctness": {{"score": <float>, "evidence": "<whether the solution addresses the task>"}},
    "completeness": {{"score": <float>, "evidence": "<whether all aspects of the task are covered>"}},
    "code_quality": {{"score": <float>, "evidence": "<code style, idioms, structure>"}},
    "retrieval_quality": {{"score": <float>, "evidence": "<how well agent found relevant code/context>"}},
    "efficiency": {{"score": <float>, "evidence": "<tool usage efficiency, unnecessary steps>"}}
  }},
  "overall_score": <float>,
  "confidence": "<high|medium|low>"
}}
"""
