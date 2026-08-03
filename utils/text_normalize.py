"""Text normalization utilities shared across agents.

Provides a single `normalize_text` function to standardize names and ontology
class identifiers by removing spaces, underscores, hyphens and lowercasing.

This prevents duplication of normalization logic and ensures fuzzy matching is
consistent across extraction and validation components.
"""

from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Normalize `text` for fuzzy matching.

    - Returns an empty string for falsy inputs.
    - Removes spaces, underscores and hyphens and lowercases the result.

    Examples:
        >>> normalize_text('Person')
        'person'
        >>> normalize_text('New_York')
        'newyork'
    """
    if not text:
        return ""
    return str(text).replace(" ", "").replace("_", "").replace("-", "").lower()
