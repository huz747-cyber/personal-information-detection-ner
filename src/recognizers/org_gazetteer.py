"""
Malaysian Statutory Body and Corporate Organization Gazetteer.

Provides deterministic recognition for Malaysian government agencies, statutory bodies,
public institutions, and commercial conglomerates, resolving domain-mismatch errors
where standard models misclassify local organizations as locations.

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Set, Tuple


# Uppercase Acronyms (must be matched strictly case-sensitive with word boundaries to avoid false positives)
MALAYSIAN_ORG_ACRONYMS: Set[str] = {
    # Statutory Bodies & Agencies
    "LHDN", "KWSP", "EPF", "PERKESO", "SOCSO", "SSM", "PDRM", "SPRM", "MACC",
    "JPJ", "JIM", "KKM", "KPM", "MOF", "BNM", "MOH", "MOE", "MIDA", "MATRADE",
    "MARA", "FELDA", "JKR", "Bomba", "DOSM",
    # Public Universities & Hospitals
    "UM", "UKM", "USM", "UPM", "UTM", "UiTM", "IIUM", "UUM", "UNIMAS", "UMS", "HKL",
    # Major Corporates & GLCs
    "TNB", "TM", "CIMB", "RHB", "MAS", "KLSE",
}

# Multi-word and Proper Name Malaysian Organizations (matched case-insensitively)
MALAYSIAN_ORG_NAMES: List[str] = [
    # Statutory Bodies & Ministries
    "Lembaga Hasil Dalam Negeri Malaysia",
    "Lembaga Hasil Dalam Negeri",
    "Kumpulan Wang Simpanan Pekerja",
    "Pertubuhan Keselamatan Sosial",
    "Suruhanjaya Syarikat Malaysia",
    "Polis Diraja Malaysia",
    "Suruhanjaya Pencegahan Rasuah Malaysia",
    "Jabatan Pengangkutan Jalan",
    "Jabatan Imigresen Malaysia",
    "Jabatan Perkhidmatan Awam",
    "Jabatan Kastam Diraja Malaysia",
    "Kementerian Kesihatan Malaysia",
    "Kementerian Pendidikan Malaysia",
    "Kementerian Kewangan Malaysia",
    "Kementerian Pengajian Tinggi",
    "Kementerian Sumber Manusia",
    "Bank Negara Malaysia",
    "Bursa Malaysia",
    "Suruhanjaya Sekuriti Malaysia",
    # Public Universities
    "Universiti Malaya",
    "Universiti Kebangsaan Malaysia",
    "Universiti Sains Malaysia",
    "Universiti Putra Malaysia",
    "Universiti Teknologi Malaysia",
    "Universiti Teknologi MARA",
    "Universiti Islam Antarabangsa Malaysia",
    "Universiti Utara Malaysia",
    # Hospitals & Medical Centers
    "Hospital Kuala Lumpur",
    "Hospital Selayang",
    "Hospital Sungai Buloh",
    "Hospital Sultanah Aminah",
    "Hospital Queen Elizabeth",
    "Hospital Umum Sarawak",
    "Pusat Perubatan Universiti Malaya",
    # Major Corporates, Banks & GLCs
    "Tenaga Nasional Berhad",
    "Tenaga Nasional",
    "Petroliam Nasional Berhad",
    "Petronas Gas Berhad",
    "Petronas Dagangan Berhad",
    "Petronas",
    "Malayan Banking Berhad",
    "Menara Maybank",
    "Maybank Islamic Berhad",
    "Maybank",
    "CIMB Group Holdings Berhad",
    "CIMB Bank Berhad",
    "CIMB Bank",
    "CIMB Group",
    "Public Bank Berhad",
    "Public Bank",
    "RHB Bank Berhad",
    "RHB Bank",
    "AMMB Holdings Berhad",
    "AmBank",
    "Hong Leong Bank Berhad",
    "Hong Leong Bank",
    "Telekom Malaysia Berhad",
    "Telekom Malaysia",
    "Axiata Group Berhad",
    "Axiata Group",
    "Axiata",
    "CelcomDigi Berhad",
    "CelcomDigi",
    "Maxis Berhad",
    "Maxis",
    "Sime Darby Berhad",
    "Sime Darby Plantation Berhad",
    "Sime Darby",
    "AirAsia Group",
    "AirAsia",
    "Malaysia Airlines Berhad",
    "Malaysia Airlines",
    "Top Glove Corporation Berhad",
    "Top Glove",
    "IHH Healthcare Berhad",
    "MISC Berhad",
    "Gamuda Berhad",
    "YTL Corporation Berhad",
    "Sunway Berhad",
    "Sunway Group",
]

# Regex for detecting company entities ending with standard Malaysian corporate suffixes
MALAYSIAN_CORP_SUFFIX_REGEX = re.compile(
    r"\b[A-Z][A-Za-z0-9&/.-]+(?:\s+[A-Za-z0-9&/.-]+){0,4}\s+(?:Sdn\.?\s*Bhd\.?|Bhd\.?|PLT|Sendirian\s+Berhad|Berhad)\.?",
    re.IGNORECASE,
)


def find_malaysian_org_entities(text: str) -> List[Dict[str, Any]]:
    """Scans text for registered Malaysian organizations, statutory bodies, and corporate entities.

    Args:
        text: Input string to analyze.

    Returns:
        List of entity dictionaries with label 'ORGANIZATION'.
    """
    if not text:
        return []

    entities: List[Dict[str, Any]] = []
    matched_spans: List[Tuple[int, int]] = []

    # 1. Match full organization names (sorted by length descending for longest match precedence)
    sorted_org_names = sorted(MALAYSIAN_ORG_NAMES, key=len, reverse=True)
    for name in sorted_org_names:
        pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
                continue

            entities.append({
                "text": text[start:end],
                "label": "ORGANIZATION",
                "score": 0.98,
                "start": start,
                "end": end,
            })
            matched_spans.append((start, end))

    # 2. Match strict uppercase acronyms
    for acronym in MALAYSIAN_ORG_ACRONYMS:
        pattern = re.compile(r"\b" + re.escape(acronym) + r"\b")
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
                continue

            entities.append({
                "text": text[start:end],
                "label": "ORGANIZATION",
                "score": 0.98,
                "start": start,
                "end": end,
            })
            matched_spans.append((start, end))

    # 3. Match legal corporate entities ending with registered suffixes (Sdn Bhd, Bhd, PLT)
    for match in MALAYSIAN_CORP_SUFFIX_REGEX.finditer(text):
        start, end = match.start(), match.end()
        if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
            continue

        entities.append({
            "text": text[start:end],
            "label": "ORGANIZATION",
            "score": 0.96,
            "start": start,
            "end": end,
        })
        matched_spans.append((start, end))

    return entities
