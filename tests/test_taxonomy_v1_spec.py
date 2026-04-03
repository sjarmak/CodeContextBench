"""Tests for taxonomy-v1-spec acceptance criteria."""

import json
import sys
from pathlib import Path

import pytest
import yaml

OBSERVATORY_DIR = Path(__file__).resolve().parent.parent / "observatory"
EXEMPLARS_DIR = OBSERVATORY_DIR / "exemplars"
TAXONOMY_PATH = OBSERVATORY_DIR / "taxonomy_v1.yaml"
SCHEMA_PATH = OBSERVATORY_DIR / "annotation_schema.json"
README_PATH = OBSERVATORY_DIR / "README.md"
EXEMPLARS_README_PATH = EXEMPLARS_DIR / "README.md"


@pytest.fixture(scope="module")
def taxonomy():
    with open(TAXONOMY_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def exemplar_files():
    return sorted(EXEMPLARS_DIR.glob("*.json"))


# ── AC1: taxonomy_v1.yaml ──────────────────────────────────────


def test_taxonomy_version_is_semver(taxonomy):
    """Version field must be '1.0.0'."""
    assert (
        taxonomy["version"] == "1.0.0"
    ), f"Expected '1.0.0', got '{taxonomy['version']}'"


def test_taxonomy_has_23_categories(taxonomy):
    """Must have exactly 23 categories."""
    assert (
        len(taxonomy["categories"]) == 23
    ), f"Expected 23 categories, got {len(taxonomy['categories'])}"


def test_all_categories_have_required_fields(taxonomy):
    """Each category must have name, description, polarity, detection_hints, examples."""
    required_fields = {"name", "description", "polarity", "detection_hints", "examples"}
    for cat in taxonomy["categories"]:
        missing = required_fields - set(cat.keys())
        assert (
            not missing
        ), f"Category '{cat.get('name', '?')}' missing fields: {missing}"


def test_all_categories_have_examples(taxonomy):
    """Each category must have >= 1 example."""
    for cat in taxonomy["categories"]:
        examples = cat.get("examples", [])
        assert (
            len(examples) >= 1
        ), f"Category '{cat['name']}' has {len(examples)} examples, need >= 1"


def test_category_polarity_values(taxonomy):
    """Polarity must be one of: failure, success, neutral."""
    valid_polarities = {"failure", "success", "neutral"}
    for cat in taxonomy["categories"]:
        assert (
            cat["polarity"] in valid_polarities
        ), f"Category '{cat['name']}' has invalid polarity: {cat['polarity']}"


# ── AC2: annotation_schema.json self-validates ─────────────────


def test_schema_self_validates(schema):
    """annotation_schema.json must be valid JSON Schema."""
    import jsonschema

    # Validate the schema itself against the JSON Schema meta-schema
    jsonschema.Draft202012Validator.check_schema(schema)


# ── AC3: observatory/README.md ─────────────────────────────────


def test_readme_exists():
    """observatory/README.md must exist."""
    assert README_PATH.is_file(), f"README not found at {README_PATH}"


def test_readme_has_overview_section():
    content = README_PATH.read_text()
    assert "## Overview" in content or "# Agent Reliability Observatory" in content


def test_readme_has_category_table():
    content = README_PATH.read_text()
    assert "retrieval_failure" in content
    assert "success_via_code_nav" in content
    assert "task_ambiguity" in content


def test_readme_has_usage_examples():
    content = README_PATH.read_text()
    assert "## Usage" in content or "### Reading an Annotation File" in content


def test_readme_has_bibtex_citation():
    content = README_PATH.read_text()
    assert "@misc{" in content or "@article{" in content
    assert "bibtex" in content.lower() or "BibTeX" in content


# ── AC4: observatory/exemplars/ ────────────────────────────────


def test_exemplar_directory_exists():
    assert EXEMPLARS_DIR.is_dir(), f"Exemplars dir not found at {EXEMPLARS_DIR}"


def test_at_least_20_exemplar_files(exemplar_files):
    assert (
        len(exemplar_files) >= 20
    ), f"Expected >= 20 exemplar JSON files, found {len(exemplar_files)}"


def test_exemplars_valid_against_schema(schema, exemplar_files):
    """Each exemplar must validate against annotation_schema.json."""
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for f in exemplar_files:
        with open(f) as fh:
            data = json.load(fh)
        errs = list(validator.iter_errors(data))
        if errs:
            errors.append(f"{f.name}: {errs[0].message}")
    assert not errors, f"Schema validation errors:\n" + "\n".join(errors)


def test_exemplars_cover_at_least_15_categories(exemplar_files, taxonomy):
    """Exemplars must cover at least 15 distinct taxonomy categories."""
    valid_names = {cat["name"] for cat in taxonomy["categories"]}
    covered = set()
    for f in exemplar_files:
        with open(f) as fh:
            data = json.load(fh)
        for ann in data.get("annotations", []):
            for cat in ann.get("categories", []):
                name = cat.get("name", "")
                if name in valid_names:
                    covered.add(name)
    assert len(covered) >= 15, (
        f"Only {len(covered)} distinct categories covered, need >= 15. "
        f"Covered: {sorted(covered)}"
    )


def test_exemplars_use_valid_category_names(exemplar_files, taxonomy):
    """All category names in exemplars must be valid taxonomy names."""
    valid_names = {cat["name"] for cat in taxonomy["categories"]}
    invalid = []
    for f in exemplar_files:
        with open(f) as fh:
            data = json.load(fh)
        for ann in data.get("annotations", []):
            for cat in ann.get("categories", []):
                name = cat.get("name", "")
                if name not in valid_names:
                    invalid.append(f"{f.name}: '{name}'")
    assert not invalid, f"Invalid category names: {invalid}"


# ── AC5: observatory/exemplars/README.md ───────────────────────


def test_exemplars_readme_exists():
    assert (
        EXEMPLARS_README_PATH.is_file()
    ), f"Exemplars README not found at {EXEMPLARS_README_PATH}"


def test_exemplars_readme_lists_files(exemplar_files):
    content = EXEMPLARS_README_PATH.read_text()
    for f in exemplar_files:
        assert f.name in content, f"Exemplar {f.name} not listed in exemplars/README.md"


# ── AC6: No breaking Python imports ───────────────────────────


def test_observatory_init_imports():
    """observatory package must be importable."""
    import observatory

    assert hasattr(observatory, "__version__")


def test_taxonomy_module_imports():
    from observatory.taxonomy import (
        load_taxonomy,
        valid_category_names,
        validate_annotation_categories,
    )

    taxonomy = load_taxonomy()
    assert taxonomy["version"] == "1.0.0"
    names = valid_category_names()
    assert len(names) == 23


def test_annotator_module_imports():
    from observatory.annotator import annotate_trial, annotate_all, compute_corpus_stats

    assert callable(annotate_trial)
    assert callable(annotate_all)


def test_signals_module_imports():
    from observatory.signals import extract_signals, extract_all

    assert callable(extract_signals)


def test_cli_module_imports():
    from observatory.cli import main

    assert callable(main)
