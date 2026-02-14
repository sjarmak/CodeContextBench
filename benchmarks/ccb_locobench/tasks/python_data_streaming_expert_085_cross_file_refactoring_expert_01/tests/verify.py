#!/usr/bin/env python3
"""
LoCoBench-Agent Solution Verifier

Evaluates agent solutions against ground truth using keyword matching,
bigram overlap, structural analysis, and evidence-based code block scoring.

Scoring Weights:
- keyword_overlap: 0.40 (unigram + bigram blend for coherence)
- file_references: 0.25 (shows agent explored codebase)
- code_blocks: 0.15 (reduced - code blocks alone are weak signal)
- length_score: 0.10 (basic sanity check)
- structural_coherence: 0.10 (architectural analysis should be structured)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text."""
    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it',
        'its', 'you', 'your', 'they', 'them', 'their', 'we', 'our', 'i', 'me',
    }

    normalized = normalize_text(text)
    words = set(normalized.split())
    # Filter out stop words and short words
    keywords = {w for w in words if w not in stop_words and len(w) > 2}
    return keywords


def extract_bigrams(text: str) -> set[tuple[str, str]]:
    """Extract 2-word sequences from text after normalization and stop-word removal."""
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it',
        'its', 'you', 'your', 'they', 'them', 'their', 'we', 'our', 'i', 'me',
    }
    normalized = normalize_text(text)
    words = normalized.split()
    # Filter to content words (same criteria as unigrams)
    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    # Build bigrams from consecutive content words
    bigrams = set()
    for i in range(len(content_words) - 1):
        bigrams.add((content_words[i], content_words[i + 1]))
    return bigrams


def compute_keyword_overlap(solution: str, ground_truth: str) -> float:
    """Compute keyword overlap score blending unigram and bigram F1."""
    # --- Unigram overlap ---
    solution_keywords = extract_keywords(solution)
    truth_keywords = extract_keywords(ground_truth)

    if not truth_keywords:
        return 0.0

    overlap = solution_keywords & truth_keywords
    precision = len(overlap) / len(solution_keywords) if solution_keywords else 0.0
    recall = len(overlap) / len(truth_keywords)

    if precision + recall == 0:
        unigram_f1 = 0.0
    else:
        unigram_f1 = 2 * (precision * recall) / (precision + recall)

    # --- Bigram overlap ---
    solution_bigrams = extract_bigrams(solution)
    truth_bigrams = extract_bigrams(ground_truth)

    if not truth_bigrams:
        # If ground truth has no bigrams, fall back to unigram only
        return unigram_f1

    bi_overlap = solution_bigrams & truth_bigrams
    bi_precision = len(bi_overlap) / len(solution_bigrams) if solution_bigrams else 0.0
    bi_recall = len(bi_overlap) / len(truth_bigrams)

    if bi_precision + bi_recall == 0:
        bigram_f1 = 0.0
    else:
        bigram_f1 = 2 * (bi_precision * bi_recall) / (bi_precision + bi_recall)

    # Blend: 60% unigram + 40% bigram
    return 0.6 * unigram_f1 + 0.4 * bigram_f1


def check_file_references(solution: str, context_files: list[str]) -> float:
    """Check if solution references relevant files from context."""
    if not context_files:
        return 1.0  # No files to check

    # Normalize file paths (convert // to /)
    normalized_files = [f.replace('//', '/') for f in context_files]

    # Count file references in solution
    referenced = 0
    for filepath in normalized_files:
        # Check for full path or filename
        filename = Path(filepath).name
        if filepath in solution or filename in solution:
            referenced += 1

    # Return ratio of referenced files (with min threshold)
    ratio = referenced / len(normalized_files)
    # Cap at 1.0 and give partial credit
    return min(ratio * 2, 1.0)


def check_code_blocks(solution: str, ground_truth_text: str) -> float:
    """Check if solution contains code blocks with relevant content.

    Scores:
    - 1.0: code blocks contain at least one ground-truth keyword or file reference
    - 0.3: code blocks present but without relevant content
    - 0.0: no code blocks at all
    """
    # Look for markdown code blocks
    code_blocks = re.findall(r'```[\w]*\n([\s\S]*?)```', solution)

    if not code_blocks:
        # Check for inline code as a weaker signal
        inline_code = re.findall(r'`([^`]+)`', solution)
        if not inline_code:
            return 0.0
        # Treat inline code snippets as code block content
        code_blocks = inline_code

    # Extract ground-truth keywords and file references for relevance check
    gt_keywords = extract_keywords(ground_truth_text)

    # Combine all code block content
    all_code_text = ' '.join(code_blocks)
    code_keywords = extract_keywords(all_code_text)

    # Check if any ground-truth keyword appears in code blocks
    if gt_keywords & code_keywords:
        return 1.0

    # Code blocks exist but contain no relevant content
    return 0.3


def check_structural_coherence(solution: str) -> float:
    """Check if solution has structural organization.

    Architectural analysis should be well-structured with sections.

    Scores:
    - 1.0: more than 2 distinct sections
    - 0.5: 1-2 sections
    - 0.0: no discernible structure
    """
    section_count = 0

    # Count markdown headers (# or ##, etc.)
    headers = re.findall(r'^#{1,6}\s+.+', solution, re.MULTILINE)
    section_count += len(headers)

    # Count numbered list items (1., 2., 3., etc.) as section indicators
    # Only count top-level numbered items (not sub-items)
    numbered_items = re.findall(r'^\d+\.\s+', solution, re.MULTILINE)
    section_count += len(numbered_items)

    # Count bold section-like markers (**Section Name:**)
    bold_sections = re.findall(r'^\*\*[^*]+\*\*[:\s]', solution, re.MULTILINE)
    section_count += len(bold_sections)

    if section_count > 2:
        return 1.0
    elif section_count >= 1:
        return 0.5
    else:
        return 0.0


def evaluate_solution(
    solution_text: str,
    ground_truth: dict[str, Any] | str,
    context_files: list[str] | None = None,
) -> dict[str, Any]:
    """
    Evaluate solution against ground truth.

    Returns a dictionary with score (0.0-1.0) and detailed metrics.
    """
    # Handle ground_truth as string or dict
    if isinstance(ground_truth, dict):
        truth_text = json.dumps(ground_truth)
    else:
        truth_text = str(ground_truth)

    # Compute component scores
    keyword_score = compute_keyword_overlap(solution_text, truth_text)
    file_ref_score = check_file_references(solution_text, context_files or [])
    code_block_score = check_code_blocks(solution_text, truth_text)
    structural_score = check_structural_coherence(solution_text)

    # Check solution length (penalize very short solutions)
    solution_len = len(solution_text.split())
    length_score = min(solution_len / 100, 1.0)  # Full credit at 100+ words

    # Weighted combination
    # keyword_overlap: 0.40 - primary semantic signal (unigram + bigram)
    # file_references: 0.25 - shows agent explored the codebase correctly
    # code_blocks: 0.15 - reduced; code blocks alone are a weak signal
    # length_score: 0.10 - basic sanity check
    # structural_coherence: 0.10 - architectural analysis should be structured
    final_score = (
        0.40 * keyword_score +
        0.25 * file_ref_score +
        0.15 * code_block_score +
        0.10 * length_score +
        0.10 * structural_score
    )

    return {
        "score": round(final_score, 4),
        "metrics": {
            "keyword_overlap": round(keyword_score, 4),
            "file_references": round(file_ref_score, 4),
            "code_blocks": round(code_block_score, 4),
            "length_score": round(length_score, 4),
            "structural_coherence": round(structural_score, 4),
        },
        "solution_words": solution_len,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LoCoBench-Agent Solution Verifier")
    parser.add_argument("--solution", required=True, help="Path to solution file")
    parser.add_argument("--ground-truth", required=True, help="Path to ground truth JSON")
    parser.add_argument("--output", required=True, help="Path to output reward JSON")
    args = parser.parse_args()

    # Read solution
    solution_path = Path(args.solution)
    if not solution_path.exists():
        result = {"score": 0.0, "error": f"Solution file not found: {args.solution}"}
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"Error: {result['error']}")
        return

    solution_text = solution_path.read_text()

    # Read ground truth
    truth_path = Path(args.ground_truth)
    if not truth_path.exists():
        result = {"score": 0.0, "error": f"Ground truth not found: {args.ground_truth}"}
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"Error: {result['error']}")
        return

    ground_truth_data = json.loads(truth_path.read_text())

    # Extract ground truth and context files
    ground_truth = ground_truth_data.get("ground_truth", ground_truth_data)
    context_files = ground_truth_data.get("context_files", [])

    # Evaluate
    result = evaluate_solution(solution_text, ground_truth, context_files)

    # Write output
    Path(args.output).write_text(json.dumps(result, indent=2))

    print(f"Evaluation complete:")
    print(f"  Score: {result['score']}")
    print(f"  Metrics: {result['metrics']}")


if __name__ == "__main__":
    main()
