"""
Malaysian Location and Context-Aware Postcode Recognizer.

Identifies Malaysian geographic entities:
    1. Malaysian Postcodes (POSTCODE): Validates 5-digit codes against POS Malaysia routing
       prefixes (01xxx to 98xxx) and strictly requires address/postal context keywords to prevent
       false positives on currency amounts (e.g. 'RM 50000') or arbitrary numbers.
    2. Malaysian Locations (LOCATION): States, federal territories, administrative districts,
       major cities, tech corridors, and street addresses (Jalan / Taman / Presint).

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Set, Tuple


# Pos Malaysia 2-digit routing prefixes mapped to Malaysian states & territories
VALID_POSTCODE_PREFIXES: Set[str] = {
    # Perlis (01-02), Kedah (05-09)
    "01", "02", "05", "06", "07", "08", "09",
    # Penang (10-14), Kelantan (15-18)
    "10", "11", "12", "13", "14", "15", "16", "17", "18",
    # Terengganu (20-24), Pahang (25-28)
    "20", "21", "22", "23", "24", "25", "26", "27", "28",
    # Perak (30-36)
    "30", "31", "32", "33", "34", "35", "36",
    # Selangor (40-48, 63-68)
    "40", "41", "42", "43", "44", "45", "46", "47", "48",
    # Kuala Lumpur (50-60), Putrajaya (62), Cyberjaya (63)
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60",
    "62", "63", "64", "65", "66", "67", "68",
    # Negeri Sembilan (70-73), Melaka (75-78)
    "70", "71", "72", "73", "75", "76", "77", "78",
    # Johor (80-86), Labuan (87)
    "80", "81", "82", "83", "84", "85", "86", "87",
    # Sabah (88-91), Sarawak (93-98)
    "88", "89", "90", "91", "93", "94", "95", "96", "97", "98",
}

# 5-digit postcode regex
POSTCODE_REGEX = re.compile(r"\b(\d{5})\b")

# Contextual keywords required near a 5-digit number to accept it as a postcode
POSTCODE_CONTEXT_REGEX = re.compile(
    r"(?i)\b(?:poskod|postcode|kod\s*pos|alamat|address|no\.?|jalan|jln|lorong|lrg|taman|tmn|bandar|kampung|kg|presint|seksyen|selangor|kuala\s*lumpur|putrajaya|penang|johor|perak|kedah|melaka|pahang|sabah|sarawak|negeri\s*sembilan|terengganu|kelantan|perlis|labuan|cyberjaya|petaling\s*jaya|shah\s*alam)\b"
)

# Comprehensive Malaysian states, federal territories, cities, and tech corridors
MALAYSIAN_LOCATION_NAMES: List[str] = [
    # Federal Territories & States
    "Wilayah Persekutuan Kuala Lumpur",
    "Wilayah Persekutuan Putrajaya",
    "Wilayah Persekutuan Labuan",
    "Kuala Lumpur",
    "Putrajaya",
    "Labuan",
    "Negeri Sembilan",
    "Pulau Pinang",
    "Penang",
    "Selangor",
    "Johor",
    "Perak",
    "Kedah",
    "Kelantan",
    "Terengganu",
    "Pahang",
    "Melaka",
    "Sabah",
    "Sarawak",
    "Perlis",
    # Major Cities & Urban Centers
    "Petaling Jaya",
    "Subang Jaya",
    "Shah Alam",
    "Cyberjaya",
    "George Town",
    "Georgetown",
    "Johor Bahru",
    "Kota Kinabalu",
    "Kuching",
    "Ipoh",
    "Klang",
    "Kuantan",
    "Seremban",
    "Alor Setar",
    "Kota Bharu",
    "Kuala Terengganu",
    "Kangar",
    # Commercial & Tech Hubs
    "Bandar Sunway",
    "Damansara Utama",
    "Kota Damansara",
    "Damansara",
    "Bangsar South",
    "Bangsar",
    "Mont Kiara",
    "Bukit Bintang",
    "Bukit Jalil",
    "Mid Valley City",
    "KLCC",
    "Bangi",
    "Kajang",
    "Ampang",
    "Rawang",
    "Sepang",
    "Nilai",
    "Taiping",
    "Batu Pahat",
    "Muar",
    "Kulai",
    "Iskandar Puteri",
    "Sandakan",
    "Tawau",
    "Miri",
    "Sibu",
    "Bintulu",
    "Labuan Federal Territory",
]

# Regex pattern for Malaysian street / residential address lines
# e.g., 'Jalan Tun Razak', 'Jalan Sultan Ismail', 'Taman Tun Dr Ismail', 'Presint 2'
# Hardened in Phase 6: Constrained to 1 to 4 capitalized/alphanumeric tokens,
# eliminating greedy absorption of following dates, prepositions, or clauses.
ADDRESS_LINE_REGEX = re.compile(
    r"\b(?i:Jalan|Jln\.?|Lorong|Lrg\.?|Taman|Tmn\.?|Bandar|Bdr\.?|Kampung|Kg\.?|Bukit|Sungai|Sg\.?|Presint|Seksyen)\s+[A-Z0-9][A-Za-z0-9'/-]*(?:\s+[A-Z0-9][A-Za-z0-9'/-]*){0,3}\b",
)


def find_malaysian_postcodes(text: str) -> List[Dict[str, Any]]:
    """Identifies verified Malaysian postcodes in text using routing and context validation.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries with label 'POSTCODE'.
    """
    if not text:
        return []

    entities: List[Dict[str, Any]] = []

    for match in POSTCODE_REGEX.finditer(text):
        candidate = match.group(1)
        prefix = candidate[:2]

        # 1. Routing prefix validation
        if prefix not in VALID_POSTCODE_PREFIXES:
            continue

        start, end = match.start(), match.end()

        # 2. Context window check (35 characters before or after)
        # Prevents false positive on numeric prices or quantities (e.g. 'RM 50000')
        win_start = max(0, start - 35)
        win_end = min(len(text), end + 35)
        context_window = text[win_start:win_end]

        # Also guard: if preceded immediately by currency symbol 'RM' or '$', reject
        preceding_text = text[max(0, start - 5) : start].strip()
        if preceding_text.endswith("RM") or preceding_text.endswith("$"):
            continue

        if POSTCODE_CONTEXT_REGEX.search(context_window):
            entities.append({
                "text": candidate,
                "label": "POSTCODE",
                "score": 0.98,
                "start": start,
                "end": end,
            })

    return entities


def find_malaysian_locations(text: str) -> List[Dict[str, Any]]:
    """Scans text for registered Malaysian states, cities, districts, and address lines.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries with label 'LOCATION'.
    """
    if not text:
        return []

    entities: List[Dict[str, Any]] = []
    matched_spans: List[Tuple[int, int]] = []

    # 1. Match specific location names (longest match precedence)
    sorted_locs = sorted(MALAYSIAN_LOCATION_NAMES, key=len, reverse=True)
    for loc_name in sorted_locs:
        pattern = re.compile(r"\b" + re.escape(loc_name) + r"\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
                continue

            entities.append({
                "text": text[start:end],
                "label": "LOCATION",
                "score": 0.98,
                "start": start,
                "end": end,
            })
            matched_spans.append((start, end))

    # 2. Match street / precinct / residential patterns (e.g. 'Jalan Sultan Ismail')
    for match in ADDRESS_LINE_REGEX.finditer(text):
        start, end = match.start(), match.end()
        # Avoid overriding an already matched location
        if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
            continue

        # Trim trailing punctuation/spaces
        candidate_text = text[start:end].rstrip(",. ")
        end = start + len(candidate_text)

        entities.append({
            "text": candidate_text,
            "label": "LOCATION",
            "score": 0.95,
            "start": start,
            "end": end,
        })
        matched_spans.append((start, end))

    return entities
