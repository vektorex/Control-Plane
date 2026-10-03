"""
Normalization and string matching utilities for Entity Resolution in Knowledge Graph.
"""
import re
from typing import Optional


def normalize_entity_name(name: str) -> str:
    """
    Normalizes an entity name into canonical search form:
    lowercased, leading/trailing whitespace removed, noise punctuation stripped
    (dashes, underscores, exclamations, etc.) but dots preserved for version
    and package names (e.g. "React.JS"). Multiple spaces collapsed.
    """
    if not name:
        return ""
    cleaned = name.strip().lower()
    # Remove noise chars: anything that is NOT alphanumeric, whitespace, or a dot
    cleaned = re.sub(r"[^\w\s\.]", " ", cleaned)
    # Collapse multiple whitespace sequences into a single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_alias(alias: str) -> str:
    """
    Normalizes an alias for index lookup.
    Keeps alphanumeric characters, dots, hyphens, underscores, and forward-slashes
    (to preserve path-style aliases like 'frontend/app').
    Strips leading @ signs and other noise before normalization.
    """
    if not alias:
        return ""
    # Strip common prefix noise (@ symbols, leading spaces)
    stripped = alias.strip().lstrip("@").strip().lower()
    # Allow: word chars (a-z0-9_), dots, hyphens, forward-slashes
    result = re.sub(r"[^\w\.\-/]", "", stripped)
    return result


def normalize_entity_type(type_str: str) -> Optional[str]:
    """
    Normalizes an entity type string into snake_case lowercase and validates it
    against the controlled entity-type registry.
    Returns None when the type is unrecognised (not in ALLOWED_ENTITY_TYPES).
    Import is done lazily to avoid circular deps.
    """
    if not type_str:
        return None
    cleaned = type_str.strip().lower().replace(" ", "_").replace("-", "_")
    # Lazy import to prevent circular dependency with constants
    from backend.app.services.knowledge_graph.constants import ALLOWED_ENTITY_TYPES  # noqa: PLC0415
    return cleaned if cleaned in ALLOWED_ENTITY_TYPES else None


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes standard Levenshtein edit distance between two strings.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_string_similarity(s1: str, s2: str) -> float:
    """
    Calculates normalized similarity [0.0 - 1.0] based on Levenshtein distance.
    """
    norm1 = normalize_entity_name(s1)
    norm2 = normalize_entity_name(s2)
    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 1.0
    distance = levenshtein_distance(norm1, norm2)
    return max(0.0, 1.0 - (distance / max_len))
