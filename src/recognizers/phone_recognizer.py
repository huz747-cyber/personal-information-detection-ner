"""
Malaysian Phone Number Pattern Recognizer.

Detects both mobile and landline/fixed-line telephone numbers across Malaysian
telecommunication formats, including international dialling code (+60) and national prefix (0).

Supported Formats:
    - Mobile (010, 012-019 with 7 digits; 011 with 8 digits):
        e.g., '+6012-345 6789', '012-3456789', '011-1234 5678', '+60 11-12345678'
    - Fixed Line / Landline:
        e.g., '03-8888 1234' (Klang Valley / Putrajaya), '04-226 1234' (Penang),
              '082-421 234' (Sarawak), '+603-2144 5678'

False-Positive Protection:
    - Rejects dates (e.g., '2026-11-13')
    - Rejects monetary amounts (e.g., 'RM 1000')
    - Rejects IP addresses (e.g., '192.168.1.1')
    - Requires strict word boundaries and validates dialling code length

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List


# Comprehensive Malaysian phone regex covering mobile (010-019) and landlines (03-09, 082-089)
MY_PHONE_REGEX = re.compile(
    r"""
    (?<!\d)                      # Negative lookbehind: ensure not part of a larger number/IP
    (?:\+?60[\s-]?|0)            # Country code (+60) or national trunk prefix (0)
    (?:
        # Mobile 011 (8-digit subscriber)
        11[\s-]?\d{4}[\s-]?\d{4}
        |
        # Mobile 010, 012-019 (7-digit subscriber)
        1[02-9][\s-]?\d{3}[\s-]?\d{4}
        |
        # Klang Valley / Selangor / Putrajaya 03 (8-digit subscriber)
        3[\s-]?\d{4}[\s-]?\d{4}
        |
        # Peninsular Landlines 04, 05, 06, 07, 09 (7-digit subscriber)
        [4-79][\s-]?\d{3}[\s-]?\d{4}
        |
        # Sabah / Sarawak / Labuan 082 - 089 (6 to 7 digit subscriber)
        8[2-9][\s-]?\d{2,3}[\s-]?\d{3,4}
    )
    (?!\d)                       # Negative lookahead: ensure not part of a larger number
    """,
    re.VERBOSE,
)


def find_phone_entities(text: str) -> List[Dict[str, Any]]:
    """Extracts verified Malaysian phone numbers from text.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries with label 'PHONE'.
    """
    if not text:
        return []

    entities: List[Dict[str, Any]] = []

    for match in MY_PHONE_REGEX.finditer(text):
        start, end = match.start(), match.end()
        candidate = text[start:end]

        # Additional guard against date strings like '2026-11-13'
        if candidate.startswith("20") and "-" in candidate:
            continue

        entities.append({
            "text": candidate,
            "label": "PHONE",
            "score": 0.98,
            "start": start,
            "end": end,
        })

    return entities
