"""
Malaysian Honorific and Title Recognizer.

Identifies Malaysian federal, state, royal, religious, and academic honorifics and titles.
Acts as a guardian layer in conflict resolution to purge false-positive predictions
where English-trained models misclassify local titles (e.g. "Dato' Seri", "Tan Sri")
as organizations or locations.

Supported Titles:
    - Federal: 'Tun', 'Toh Puan', 'Tan Sri', 'Puan Sri'
    - State: 'Dato' Seri Utama', 'Datuk Seri Utama', 'Dato' Seri', 'Datuk Seri',
             'Datin Seri', 'Dato' Paduka', 'Datuk Paduka', 'Datin Paduka',
             'Dato'', 'Datuk', 'Datin'
    - Royal / Hereditary: 'Tengku', 'Raja', 'Syed', 'Sharifah', 'Megat', 'Nik', 'Wan'
    - Religious: 'Haji', 'Hajah', 'Ustaz', 'Ustazah'
    - Professional & Academic: 'Prof. Diraja', 'Prof. Dr.', 'Profesor Dr.',
                               'Profesor', 'Prof.', 'Dr.', 'Dr', 'Ir.', 'Ar.', 'Ts.'

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Set, Tuple


# Sorted descending by length to ensure multi-word titles match before individual words
MALAYSIAN_HONORIFICS: List[str] = [
    # State compound titles
    "Dato' Seri Utama", "Datuk Seri Utama",
    "Dato' Seri", "Datuk Seri", "Datin Seri",
    "Dato' Paduka", "Datuk Paduka", "Datin Paduka",
    "Dato'", "Datuk", "Datin",
    # Federal titles
    "Tan Sri", "Puan Sri",
    "Tun", "Toh Puan",
    # Academic & Professional titles
    "Prof. Diraja", "Prof. Dr.", "Profesor Dr.", "Profesor", "Prof.", "Prof",
    "Dr.", "Dr", "Ir.", "Ir", "Ar.", "Ar", "Ts.", "Ts",
    # Religious titles
    "Haji", "Hajah", "Ustaz", "Ustazah",
    # Hereditary prefixes
    "Tengku", "Raja", "Syed", "Sharifah", "Megat",
]

# Regex pattern matching any recognized title (case-insensitive)
TITLE_REGEX = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in sorted(MALAYSIAN_HONORIFICS, key=len, reverse=True)) + r")\b\.?",
    re.IGNORECASE,
)


def find_malaysian_titles(text: str) -> List[Dict[str, Any]]:
    """Identifies all Malaysian honorific and title spans in text.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries with label 'TITLE'.
    """
    if not text:
        return []

    titles: List[Dict[str, Any]] = []
    matched_spans: List[Tuple[int, int]] = []

    for match in TITLE_REGEX.finditer(text):
        start, end = match.start(), match.end()
        # Ensure longest title match takes precedence
        if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
            continue

        titles.append({
            "text": text[start:end],
            "label": "TITLE",
            "score": 0.99,
            "start": start,
            "end": end,
        })
        matched_spans.append((start, end))

    return titles


def purge_title_false_positives(
    entities: List[Dict[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    """Removes entities where a title was misclassified as ORGANIZATION or LOCATION.

    Example:
        An entity 'Dato' Ser' tagged as ORGANIZATION is stripped because it overlaps
        with the recognized state honorific 'Dato' Seri'.

    Args:
        entities: List of predicted entity dictionaries.
        text: Original input text string.

    Returns:
        Filtered list of entities free from title misclassifications.
    """
    if not entities:
        return []

    titles = find_malaysian_titles(text)
    if not titles:
        return entities

    purged: List[Dict[str, Any]] = []

    for ent in entities:
        # Check if this entity is a non-PERSON (e.g. ORGANIZATION or LOCATION)
        # that overlaps with a known honorific/title
        if ent["label"] in {"ORGANIZATION", "LOCATION"}:
            is_false_title = False
            for t in titles:
                # Overlap condition: start < t_end and t_start < end
                if max(ent["start"], t["start"]) < min(ent["end"], t["end"]):
                    # If the entity span is substantially contained within or matches the title
                    overlap_len = min(ent["end"], t["end"]) - max(ent["start"], t["start"])
                    ent_len = ent["end"] - ent["start"]
                    if overlap_len / ent_len >= 0.70:
                        is_false_title = True
                        break

            if is_false_title:
                continue

        purged.append(ent)

    return purged
