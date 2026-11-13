"""
Malaysian Patronymic Span Stitcher for Named Entity Recognition.

This module provides post-processing logic to consolidate Malaysian compound
and patronymic personal names that are frequently fragmented by standard
tokenizers and English-trained NER models.

Supported Patronymic Connectors:
    - Malay: 'bin', 'binti', 'bt.', 'bt'
    - Indian Malaysian: 'a/l' (anak lelaki), 'a/p' (anak perempuan), 's/o' (son of), 'd/o' (daughter of)

Linguistic Context & Rationale:
    In Malaysia, naming conventions rarely follow the Western [First Name] [Surname]
    paradigm. Instead, patronymics connect an individual's given name to their
    father's name. Standard pretrained models (e.g., CoNLL-2003 DistilBERT)
    frequently tag connectors like 'a/p' or 'bt.' as 'O' (Outside) or split on
    punctuation slashes, fracturing a single person's identity into two disconnected
    PERSON entities (e.g., 'Kavitha' and 'Subramaniam').

Design & Safety Guarantees:
    1. Label Strictness: Both constituent entities MUST be classified as 'PERSON'.
    2. Connector Strictness: Bridging text must strictly match an approved patronymic.
       Conjunctions ('and', 'dan', 'with', 'bersama') are strictly rejected.
    3. Offset Integrity: Start and end offsets are derived directly from the original text slice.
    4. Non-Inflation of Scores: Merged confidence score uses `min(prev_score, curr_score)`,
       ensuring confidence is never artificially inflated above constituent parts.

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Tuple


# Regex pattern strictly matching full patronymic connectors in the gap between tokens
PATRONYMIC_GAP_PATTERN = re.compile(
    r"^\s*(?:bin|binti|bt\.?|a\/l|a\/p|s\/o|d\/o)\s*$",
    re.IGNORECASE,
)

# Regex pattern matching partial patronymic prefixes absorbed into the preceding token
# e.g., 'Kavitha a' where the model tagged ' a' as part of the first name
PARTIAL_PREFIX_PATTERN = re.compile(
    r"(?:\s+[aAdDsS]|\s+bin|\s+bt)$",
    re.IGNORECASE,
)

# Regex pattern matching partial patronymic suffixes absorbed into the subsequent token
# e.g., 'p Subramaniam' where '/p' was split and 'p' attached to the second name
PARTIAL_SUFFIX_PATTERN = re.compile(
    r"^(?:[ploPLO]\b|ti\b)",
    re.IGNORECASE,
)


def is_patronymic_bridge(prev_text: str, gap_text: str, next_text: str) -> bool:
    """Evaluates whether the boundary between two PERSON entities forms a valid patronymic.

    Handles both clean gap separations (e.g. 'Kavitha' + ' a/p ' + 'Subramaniam')
    and boundary spill-overs caused by subword tokenizer splitting
    (e.g. 'Kavitha a' + '/p ' + 'Subramaniam').

    Args:
        prev_text: Surface text of the preceding entity.
        gap_text: Raw text between preceding and subsequent entity spans.
        next_text: Surface text of the following entity.

    Returns:
        True if the bridging text forms an approved Malaysian patronymic, False otherwise.
    """
    # 1. Clean gap match (standard case)
    if PATRONYMIC_GAP_PATTERN.match(gap_text):
        return True

    # 2. Connector prefix absorbed into prev_text (e.g., 'Kavitha a' with gap '/p ')
    prefix_match = PARTIAL_PREFIX_PATTERN.search(prev_text)
    if prefix_match:
        combined = prev_text[prefix_match.start() :] + gap_text
        if PATRONYMIC_GAP_PATTERN.match(combined):
            return True

    # 3. Connector suffix absorbed into next_text (e.g., gap 'a/' with next_text 'p Subramaniam')
    suffix_match = PARTIAL_SUFFIX_PATTERN.match(next_text)
    if suffix_match:
        combined = gap_text + next_text[: suffix_match.end()]
        if PATRONYMIC_GAP_PATTERN.match(combined):
            return True

    return False


def stitch_patronymic_entities(
    entities: List[Dict[str, Any]],
    original_text: str,
) -> List[Dict[str, Any]]:
    """Iteratively merges adjacent PERSON entities separated by Malaysian patronymics.

    Args:
        entities: List of entity dictionaries with 'text', 'label', 'score', 'start', 'end'.
        original_text: The complete original input string.

    Returns:
        Consolidated list of entity dictionaries with patronymics bridged.
    """
    if not entities or len(entities) < 2:
        return [dict(e) for e in entities]

    stitched: List[Dict[str, Any]] = []

    for ent in entities:
        if not stitched:
            stitched.append(dict(ent))
            continue

        prev = stitched[-1]

        # Patronymic stitching applies strictly between two PERSON entities
        if prev["label"] == "PERSON" and ent["label"] == "PERSON":
            gap_text = original_text[prev["end"] : ent["start"]]

            if is_patronymic_bridge(prev["text"], gap_text, ent["text"]):
                # Merge into the existing previous entity span
                prev["end"] = ent["end"]
                prev["text"] = original_text[prev["start"] : ent["end"]]

                # Enforce conservative non-inflation rule:
                # Joint entity confidence cannot exceed the confidence of either component.
                prev["score"] = round(min(prev["score"], ent["score"]), 4)
                continue

        # If not merged, append as a distinct entity
        stitched.append(dict(ent))

    return stitched
