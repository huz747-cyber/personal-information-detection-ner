"""
Entity Conflict Resolution and Deduplication Engine.

Resolves span overlaps, deduplicates entities, and arbitrates competing labels
between Tier 1 deterministic recognizers (MyKad, Phone, Postcode, Gazetteers)
and Tier 2 Transformer token classification predictions.

Arbitration Priority Hierarchy:
    1. Tier 1 Structured PII ('MYKAD', 'PHONE', 'POSTCODE') - Highest certainty (regex + algorithmic/context validation)
    2. Title Protection - Strips model false positives where Malaysian titles were tagged as ORG/LOC
    3. Tier 1 Deterministic Gazetteers (Verified Malaysian statutory bodies, GLCs, states, cities)
    4. Stitched Malaysian PERSON Entities (Patronymic compound names)
    5. Standard Transformer Model Predictions (Novel/general open-vocabulary entities)

Author: AI/ML Club
License: MIT
"""

from typing import Any, Dict, List, Tuple
from .title_recognizer import purge_title_false_positives


def get_entity_priority(entity: Dict[str, Any], source: str) -> int:
    """Assigns an integer priority to an entity based on category and provenance.

    Args:
        entity: The entity dictionary.
        source: Provenance indicator ('rule', 'gazetteer', 'stitched', 'model').

    Returns:
        Integer priority (higher integer = higher priority).
    """
    label = entity["label"]

    # 1. Structured personal identifiers have maximum authority
    if label in {"MYKAD", "PHONE", "POSTCODE"}:
        return 100

    # 2. Curated statutory and geographic gazetteers take precedence over generalist models
    if source in {"gazetteer", "rule"}:
        return 80

    # 3. Patronymic-stitched compound person names
    if source == "stitched":
        return 60

    # 4. Standard model predictions
    return 40


def spans_overlap(ent_a: Dict[str, Any], ent_b: Dict[str, Any]) -> bool:
    """Checks whether two character offset spans overlap by at least one character."""
    return max(ent_a["start"], ent_b["start"]) < min(ent_a["end"], ent_b["end"])


ID_FORM_LABEL_TOKENS = {
    "no", "k", "p", "kp", "ic", "nric", "mykad", "tel", "fax", "poskod", "postcode"
}


def purge_id_label_false_positives(
    entities: List[Dict[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    """Removes model false positives where ID form prefixes (e.g. 'No.', 'K', 'P', 'NRIC')

    were misclassified as LOCATION or ORGANIZATION adjacent to structured PII.
    """
    structured_starts = [
        ent["start"] for ent in entities if ent["label"] in {"MYKAD", "PHONE", "POSTCODE"}
    ]
    if not structured_starts:
        return entities

    cleaned: List[Dict[str, Any]] = []
    for ent in entities:
        if ent["label"] in {"LOCATION", "ORGANIZATION"}:
            clean_token = ent["text"].strip(" ./:,#-").lower()
            if clean_token in ID_FORM_LABEL_TOKENS:
                # Check if this token appears within 15 characters before any structured identifier
                if any(0 <= (s_start - ent["end"]) <= 15 for s_start in structured_starts):
                    continue

        cleaned.append(ent)

    return cleaned


def resolve_entity_conflicts(
    model_entities: List[Dict[str, Any]],
    rule_entities: List[Dict[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    """Merges, resolves overlaps, and deduplicates entities from all sources.

    Args:
        model_entities: Entities predicted by the Transformer (and patronymic stitcher).
        rule_entities: Entities produced by regex and gazetteer recognizers.
        text: The original input string.

    Returns:
        Consolidated, non-overlapping, deduplicated list of entities sorted by start offset.
    """
    # 1. Purge title misclassifications from model predictions
    clean_model_entities = purge_title_false_positives(model_entities, text)

    # 2. Purge form label false positives (e.g. 'No. K/P' tagged as LOC)
    clean_model_entities = purge_id_label_false_positives(clean_model_entities + rule_entities, text)
    # Separate back into model vs rule
    clean_model_entities = [e for e in clean_model_entities if e in model_entities or e["label"] not in {"MYKAD", "PHONE", "POSTCODE"}]

    # 2. Tag candidates with priority and length
    tagged_candidates: List[Tuple[int, int, Dict[str, Any]]] = []

    for ent in rule_entities:
        priority = get_entity_priority(ent, source="rule")
        span_len = ent["end"] - ent["start"]
        tagged_candidates.append((priority, span_len, dict(ent)))

    for ent in clean_model_entities:
        # Check if this person was a stitched patronymic compound
        is_compound = ent["label"] == "PERSON" and any(
            p in ent["text"].lower() for p in (" bin ", " binti ", " bt.", " a/l ", " a/p ", " s/o ", " d/o ")
        )
        source = "stitched" if is_compound else "model"
        priority = get_entity_priority(ent, source=source)
        span_len = ent["end"] - ent["start"]
        tagged_candidates.append((priority, span_len, dict(ent)))

    # Sort candidates: highest priority first, then longest span first, then higher score
    tagged_candidates.sort(
        key=lambda item: (item[0], item[1], item[2].get("score", 0.0)),
        reverse=True,
    )

    # 3. Greedy non-overlapping span selection
    accepted_entities: List[Dict[str, Any]] = []

    for _, _, candidate in tagged_candidates:
        has_conflict = False
        for accepted in accepted_entities:
            if spans_overlap(candidate, accepted):
                has_conflict = True
                break

        if not has_conflict:
            # Re-slice text directly from original string to ensure exact boundary characters
            candidate["text"] = text[candidate["start"] : candidate["end"]]
            accepted_entities.append(candidate)

    # 4. Sort strictly by start offset ascending
    accepted_entities.sort(key=lambda x: (x["start"], x["end"]))

    return accepted_entities
