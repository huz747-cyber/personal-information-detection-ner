"""
Malaysian NRIC / MyKad Pattern Recognizer.

Detects and validates Malaysian National Registration Identity Card (NRIC / MyKad)
numbers in unstructured text using syntactic structure, date validation, and
official JPN (Jabatan Pendaftaran Negara) place-of-birth routing codes.

Security & Ethical Notice:
    This recognizer strictly verifies algorithmic formatting rules (valid birth date
    and registered JPN state/country codes). It does NOT verify whether an identity
    document actually exists in the JPN database or belongs to a real individual.
    All test cases MUST use synthetic identifiers only.

Formats Supported:
    - Standard hyphenated: 'YYMMDD-PB-###G' (e.g. '950315-10-5231')
    - Unhyphenated with context: 'YYMMDD105231' preceded/followed by keywords
      such as 'NRIC', 'MyKad', 'IC', 'No. K/P', 'Kad Pengenalan'.

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Optional, Set


# Standard JPN Place of Birth Codes
# Source: Jabatan Pendaftaran Negara Malaysia (State & Foreign Registration Codes)
VALID_PB_CODES: Set[str] = {
    # Malaysian States & Federal Territories
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16",
    # Born Outside Malaysia / Naturalized / Special Status
    "21", "22", "23", "24", "25", "26", "27", "28", "29",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "60", "61", "62", "63", "64", "65", "66", "67", "68",
    "71", "72", "74", "75", "76", "77", "78", "79",
    "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93",
    "98", "99",
}

# Maximum days per month (using 29 for February to accept leap year synthetic dates)
DAYS_PER_MONTH: Dict[int, int] = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}

# Hyphenated MyKad pattern: 6 digits - 2 digits - 4 digits
MYKAD_HYPHEN_REGEX = re.compile(r"\b(\d{6})-(\d{2})-(\d{4})\b")

# Unhyphenated 12-digit pattern: requires context to avoid capturing random numbers
MYKAD_UNHYPHEN_REGEX = re.compile(r"\b(\d{6})(\d{2})(\d{4})\b")

# Surrounding context keywords required for unhyphenated 12-digit strings
CONTEXT_KEYWORD_REGEX = re.compile(
    r"(?i)\b(?:nric|mykad|ic\s*no|no\.?\s*k\/?p|kad\s*pengenalan|nombor\s*k\/?p)\b"
)


def validate_mykad_parts(dob_str: str, pb_str: str, seq_str: str) -> bool:
    """Validates the constituent substrings of a candidate MyKad number.

    Args:
        dob_str: 6-digit YYMMDD date string.
        pb_str: 2-digit place of birth code.
        seq_str: 4-digit sequence number.

    Returns:
        True if all components pass calendar and JPN state routing validation.
    """
    if len(dob_str) != 6 or len(pb_str) != 2 or len(seq_str) != 4:
        return False

    try:
        mm = int(dob_str[2:4])
        dd = int(dob_str[4:6])
    except ValueError:
        return False

    if mm < 1 or mm > 12:
        return False

    if dd < 1 or dd > DAYS_PER_MONTH[mm]:
        return False

    if pb_str not in VALID_PB_CODES:
        return False

    return True


def mask_mykad(raw_number: str) -> str:
    """Masks the trailing 4 digits of a MyKad number for privacy-compliant logging.

    Example:
        '950315-10-5231' -> '950315-10-****'
    """
    clean = raw_number.strip()
    if "-" in clean:
        parts = clean.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-****"
    if len(clean) == 12:
        return f"{clean[:8]}****"
    return clean[:4] + "****"


def find_mykad_entities(text: str) -> List[Dict[str, Any]]:
    """Scans text and returns detected and validated Malaysian MyKad entities.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries conforming to the unified schema:
        [
            {
                "text": "950315-10-5231",
                "label": "MYKAD",
                "score": 0.99,
                "start": 14,
                "end": 28
            }
        ]
    """
    if not text:
        return []

    entities: List[Dict[str, Any]] = []
    matched_spans: List[Tuple[int, int]] = []

    # 1. Hyphenated MyKad matches (high confidence if parts validate)
    for match in MYKAD_HYPHEN_REGEX.finditer(text):
        dob_str = match.group(1)
        pb_str = match.group(2)
        seq_str = match.group(3)

        if validate_mykad_parts(dob_str, pb_str, seq_str):
            start, end = match.start(), match.end()
            entities.append({
                "text": text[start:end],
                "label": "MYKAD",
                "score": 0.99,
                "start": start,
                "end": end,
            })
            matched_spans.append((start, end))

    # 2. Unhyphenated 12-digit matches (require contextual proof)
    for match in MYKAD_UNHYPHEN_REGEX.finditer(text):
        start, end = match.start(), match.end()

        # Skip if already covered by a hyphenated match
        if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
            continue

        dob_str = match.group(1)
        pb_str = match.group(2)
        seq_str = match.group(3)

        if validate_mykad_parts(dob_str, pb_str, seq_str):
            # Check context window (up to 30 characters before or after)
            window_start = max(0, start - 30)
            window_end = min(len(text), end + 30)
            surrounding_context = text[window_start:window_end]

            if CONTEXT_KEYWORD_REGEX.search(surrounding_context):
                entities.append({
                    "text": text[start:end],
                    "label": "MYKAD",
                    "score": 0.95,
                    "start": start,
                    "end": end,
                })
                matched_spans.append((start, end))

    return entities
