"""Taxonomy loader and validator for the Observatory."""

from pathlib import Path
from typing import Optional, Set, Union

import yaml

_DEFAULT_TAXONOMY = Path(__file__).parent / "taxonomy_v1.yaml"

_cached_taxonomy = None
_cached_path = None


def _is_v2(taxonomy: dict) -> bool:
    """Return True if the taxonomy dict uses the v2 (dimensions) format."""
    return "dimensions" in taxonomy


def _extract_categories(taxonomy: dict) -> list:
    """Extract a flat list of category dicts from either v1 or v2 format.

    Args:
        taxonomy: Parsed taxonomy dict (v1 or v2).

    Returns:
        list of category dicts, each with at least a 'name' key.
    """
    if _is_v2(taxonomy):
        categories = []
        for dimension in taxonomy["dimensions"]:
            categories.extend(dimension.get("categories", []))
        return categories
    return taxonomy.get("categories", [])


def load_taxonomy(path: Optional[Union[str, Path]] = None) -> dict:
    """Load the taxonomy YAML and return the parsed dict.

    Supports both v1 format (flat 'categories' list) and v2 format
    (hierarchical 'dimensions' with nested categories).

    Args:
        path: Path to taxonomy YAML file. Defaults to taxonomy_v1.yaml
              shipped with the observatory package.

    Returns:
        dict — v1 has keys 'version' and 'categories';
        v2 has keys 'version' and 'dimensions' (list of dimension dicts,
        each containing a 'categories' list).
    """
    global _cached_taxonomy, _cached_path
    resolved = Path(path) if path else _DEFAULT_TAXONOMY
    if _cached_taxonomy is not None and _cached_path == resolved:
        return _cached_taxonomy
    with open(resolved) as f:
        data = yaml.safe_load(f)
    _cached_taxonomy = data
    _cached_path = resolved
    return data


def valid_category_names(path: Optional[Union[str, Path]] = None) -> Set[str]:
    """Return the set of all valid category name strings from the taxonomy.

    Works with both v1 (flat categories) and v2 (dimensions) formats.

    Args:
        path: Optional path to taxonomy YAML (forwarded to load_taxonomy).

    Returns:
        set of str category names.
    """
    taxonomy = load_taxonomy(path)
    return {cat["name"] for cat in _extract_categories(taxonomy)}


def validate_annotation_categories(annotation_dict):
    """Validate that all category names in an annotation dict are in the taxonomy.

    Args:
        annotation_dict: A single annotation dict with a 'categories' key
                         containing a list of dicts each with a 'name' field.

    Raises:
        ValueError: If any category name is not in the taxonomy.
    """
    valid = valid_category_names()
    categories = annotation_dict.get("categories", [])
    invalid = [cat["name"] for cat in categories if cat["name"] not in valid]
    if invalid:
        raise ValueError(
            f"Invalid category names not in taxonomy: {', '.join(sorted(invalid))}"
        )
