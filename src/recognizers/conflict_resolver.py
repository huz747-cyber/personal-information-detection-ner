"""
Entity Conflict Resolution and Deduplication Engine.

Resolves span overlaps, deduplicates entities, and arbitrates competing labels
between Tier 1 deterministic recognizers (MyKad, Phone, Postcode, Gazetteers)
and Tier 2 Transformer token classification predictions using Calibrated
Dynamic Confidence Arbitration (Phase 6).

Arbitration Priority Hierarchy:
    1. Tier 1 Structured PII ('MYKAD', 'PHONE', 'POSTCODE') - Priority 100
       Highest certainty (checksum / Pos Malaysia routing prefix / context validation).
    2. High-Confidence Stitched PERSON Entities - Priority 90
       Patronymic compounds ('bin', 'binti', 'a/l') with confident constituents.
    3. High-Confidence Transformer Model Predictions - Priority 85
       Model predictions meeting category-calibrated confidence thresholds.
    4. Deterministic Gazetteers & Hardened Rules - Priority 70
       Statutory bodies, GLCs, states, and hardened corporate/address patterns.
       Serves as reliable fallback when transformer prediction is missing or uncertain.
    5. Low-Confidence Transformer Predictions - Priority 35
       Model predictions below calibrated thresholds, yielded to gazetteers on conflict.

Author: AI/ML Club
License: MIT
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from .title_recognizer import purge_title_false_positives


# Calibrated confidence thresholds by entity category for Phase 6 dynamic arbitration
DEFAULT_CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "PERSON": 0.50,
    "ORGANIZATION": 0.60,
    "LOCATION": 0.60,
}

# Known Malaysian institutional designator nouns
INSTITUTIONAL_PREFIXES: Tuple[str, ...] = (
    "Kementerian",
    "Jabatan",
    "Suruhanjaya",
    "Lembaga",
    "Majlis",
    "Pejabat",
    "Agensi",
    "Institut",
    "Pusat",
    "Perbadanan",
)

INSTITUTIONAL_PREFIX_REGEX = re.compile(
    r"\b(" + "|".join(INSTITUTIONAL_PREFIXES) + r")\s+$",
    re.IGNORECASE,
)


def recover_institutional_boundaries(
    entities: List[Dict[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    """Restores missing institutional designator prefixes (e.g. 'Kementerian', 'Jabatan')

    when preceded by official titles (e.g. 'Menteri') without absorbing the title words.

    Args:
        entities: Candidate entity dictionaries.
        text: Input text string.

    Returns:
        List of entities with repaired boundaries.
    """
    repaired: List[Dict[str, Any]] = []
    for ent in entities:
        if ent.get("label") != "ORGANIZATION":
            repaired.append(ent)
            continue

        start = ent["start"]
        end = ent["end"]
        preceding = text[:start]
        match = INSTITUTIONAL_PREFIX_REGEX.search(preceding)
        if match:
            new_start = match.start(1)
            repaired_ent = dict(ent)
            repaired_ent["start"] = new_start
            repaired_ent["text"] = text[new_start:end]
            repaired.append(repaired_ent)
        else:
            repaired.append(ent)

    return repaired


def get_entity_priority(
    entity: Dict[str, Any],
    source: str,
    thresholds: Optional[Dict[str, float]] = None,
) -> int:
    """Assigns an integer priority to an entity based on category, provenance, and calibrated confidence.

    Args:
        entity: The entity dictionary.
        source: Provenance indicator ('rule', 'gazetteer', 'stitched', 'model').
        thresholds: Optional mapping of category to calibrated confidence threshold.

    Returns:
        Integer priority (higher integer = higher priority).
    """
    label = entity.get("label", "")

    # 1. Structured personal identifiers have maximum authority
    if label in {"MYKAD", "PHONE", "POSTCODE"}:
        return 100

    thresh_map = thresholds if thresholds is not None else DEFAULT_CONFIDENCE_THRESHOLDS
    cat_thresh = thresh_map.get(label, 0.55)
    score = entity.get("score", 0.0)

    # 2. Confident model predictions take precedence over heuristic rules/gazetteers
    if source in {"model", "stitched"}:
        if score >= cat_thresh:
            return 90 if source == "stitched" else 85
        # Low confidence yields to gazetteers
        return 35

    # 3. Curated statutory/geographic gazetteers & hardened rules serve as reliable fallbacks
    if source in {"gazetteer", "rule"}:
        return 70

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
    reference_entities: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Removes model false positives where ID form prefixes (e.g. 'No.', 'K', 'P', 'NRIC')

    were misclassified as LOCATION or ORGANIZATION adjacent to structured PII.
    """
    ref = reference_entities if reference_entities is not None else entities
    structured_starts = [
        ent["start"] for ent in ref if ent.get("label") in {"MYKAD", "PHONE", "POSTCODE"}
    ]
    if not structured_starts:
        return entities

    cleaned: List[Dict[str, Any]] = []
    for ent in entities:
        if ent.get("label") in {"LOCATION", "ORGANIZATION"}:
            clean_token = ent.get("text", "").strip(" ./:,#-").lower()
            if clean_token in ID_FORM_LABEL_TOKENS:
                # Check if this token appears within 15 characters before any structured identifier
                if any(0 <= (s_start - ent["end"]) <= 15 for s_start in structured_starts):
                    continue

        cleaned.append(ent)

    return cleaned


ADDRESS_PREFIX_REGEX = re.compile(
    r"^(?:Jalan|Jln\.?|Lorong|Lrg\.?|Taman|Tmn\.?|Bandar|Bdr\.?|Kampung|Kg\.?|Presint|Seksyen)\b",
    re.IGNORECASE,
)


def purge_address_person_false_positives(
    entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Corrects model false positives where street or residential address lines

    (e.g. 'Jalan Sultan Ismail') were misclassified as PERSON due to named individuals
    within the geographic title.
    """
    cleaned: List[Dict[str, Any]] = []
    for ent in entities:
        if ent.get("label") == "PERSON" and ADDRESS_PREFIX_REGEX.match(ent.get("text", "")):
            fixed = dict(ent)
            fixed["label"] = "LOCATION"
            cleaned.append(fixed)
        else:
            cleaned.append(ent)
    return cleaned


def resolve_entity_conflicts(
    model_entities: List[Dict[str, Any]],
    rule_entities: List[Dict[str, Any]],
    text: str,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Merges, resolves overlaps, and deduplicates entities from all sources using

    calibrated dynamic confidence arbitration.

    Args:
        model_entities: Entities predicted by the Transformer (and patronymic stitcher).
        rule_entities: Entities produced by regex and gazetteer recognizers.
        text: The original input string.
        thresholds: Optional category-specific confidence thresholds.

    Returns:
        Consolidated, non-overlapping, deduplicated list of entities sorted by start offset.
    """
    # 1. Purge title misclassifications from model predictions
    clean_model_entities = purge_title_false_positives(model_entities, text)

    # 2. Correct address lines falsely tagged as PERSON
    clean_model_entities = purge_address_person_false_positives(clean_model_entities)

    # 3. Purge form label false positives from model entities using structured PII references
    clean_model_entities = purge_id_label_false_positives(
        clean_model_entities,
        text,
        reference_entities=clean_model_entities + rule_entities,
    )

    # 3. Recover institutional boundaries for organizations preceded by official titles
    clean_model_entities = recover_institutional_boundaries(clean_model_entities, text)

    # 4. Tag candidates with priority, length, and score
    tagged_candidates: List[Tuple[int, int, Dict[str, Any]]] = []

    for ent in rule_entities:
        priority = get_entity_priority(ent, source="rule", thresholds=thresholds)
        span_len = ent["end"] - ent["start"]
        tagged_candidates.append((priority, span_len, dict(ent)))

    for ent in clean_model_entities:
        # Check if this person was a stitched patronymic compound
        is_compound = ent["label"] == "PERSON" and any(
            p in ent["text"].lower() for p in (" bin ", " binti ", " bt.", " a/l ", " a/p ", " s/o ", " d/o ")
        )
        source = "stitched" if is_compound else "model"
        priority = get_entity_priority(ent, source=source, thresholds=thresholds)
        span_len = ent["end"] - ent["start"]
        tagged_candidates.append((priority, span_len, dict(ent)))

    # 5. Sort candidates:
    # First by priority tier (100 -> 90 -> 85 -> 70 -> 35),
    # then by confidence score (calibrated probability),
    # then by longest span (to break ties between equal-confidence candidates)
    tagged_candidates.sort(
        key=lambda item: (item[0], item[2].get("score", 0.0), item[1]),
        reverse=True,
    )

    # 6. Greedy non-overlapping span selection
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

    # 7. Sort strictly by start offset ascending
    accepted_entities.sort(key=lambda x: (x["start"], x["end"]))

    return accepted_entities
