"""
Data Collection, Generation, and Assembly Pipeline for Malaysian NER.

Builds the canonical 1,000-sentence Malaysian NER dataset across 3 distinct sources:
1. Publicly sourced examples (Hansard, Bursa corporate announcements, WikiANN, Mesolitica, CoNLL baseline).
2. Independently authored examples (Malaysian workplace, legal, healthcare, everyday communication).
3. Realistic synthetic examples (Combinatorial templates across Malay, Chinese, Indian naming).

Stratification Target:
- Stratum 1: Standard Formal Malay (250)
- Stratum 2: Malaysian English (250)
- Stratum 3: Manglish & Conversational (150)
- Stratum 4: Malay-English Code-Switching (150)
- Stratum 5: Malaysian Chinese Naming Contexts (100)
- Stratum 6: Malaysian Indian Naming Contexts (100)
- Stratum 7: International Baseline (50)
Total = 1,000 sentences (including >= 100 hard negatives).

Author: AI/ML Club
License: MIT
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def make_record(
    rec_id: str,
    text: str,
    entity_tuples: List[Tuple[str, str]],
    source_id: str,
    source_type: str,
    stratum: str,
    language: str,
    domain: str,
    is_hard_negative: bool = False,
    document_id: Optional[str] = None,
    template_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to construct and strictly verify a dataset record with exact character offsets."""
    entities: List[Dict[str, Any]] = []
    labels: List[List[Any]] = []

    # Find each entity in text with boundary checks
    cursor = 0
    for ent_str, label in entity_tuples:
        idx = text.find(ent_str, cursor)
        if idx == -1:
            idx = text.find(ent_str)
        if idx == -1:
            raise ValueError(f"Entity '{ent_str}' not found in sentence: '{text}'")
        end = idx + len(ent_str)
        assert text[idx:end] == ent_str, f"Mismatch: '{text[idx:end]}' != '{ent_str}'"
        entities.append({
            "text": ent_str,
            "label": label,
            "start": idx,
            "end": end,
        })
        labels.append([idx, end, label])
        cursor = end

    # Sort strictly by start offset
    entities.sort(key=lambda x: (x["start"], x["end"]))
    labels.sort(key=lambda x: (x[0], x[1]))

    return {
        "id": rec_id,
        "text": text,
        "label": labels,
        "entities": entities,
        "meta": {
            "source_id": source_id,
            "source_type": source_type,
            "stratum": stratum,
            "language": language,
            "domain": domain,
            "is_hard_negative": is_hard_negative,
            "document_id": document_id,
            "template_id": template_id,
        },
    }
