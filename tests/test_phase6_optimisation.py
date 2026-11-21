"""
Dedicated Unit and Regression Tests for Phase 6: Generalisation, Robustness & Hybrid Architecture.

Tests:
    1. Dynamic Confidence Arbitration in Conflict Resolver.
    2. Corporate Suffix Regex Hardening (anti-greediness and case sensitivity).
    3. Location Address Regex Hardening (anti-runaway matching).
    4. Honorific-Organizational Boundary Recovery (prefix recovery without title absorption).
    5. Regression safeguards for previously diagnosed boundary failure cases.
"""

from pathlib import Path
import sys
import pytest

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from recognizers.conflict_resolver import (  # noqa: E402
    DEFAULT_CONFIDENCE_THRESHOLDS,
    get_entity_priority,
    recover_institutional_boundaries,
    resolve_entity_conflicts,
)
from recognizers.org_gazetteer import find_malaysian_org_entities  # noqa: E402
from recognizers.location_recognizer import find_malaysian_locations  # noqa: E402


# =========================================================================
# 1. Dynamic Confidence Arbitration Tests
# =========================================================================

def test_confident_model_beats_gazetteer_overlap() -> None:
    """Verifies that a confident model prediction (score >= 0.60) takes priority

    over an overlapping rule/gazetteer span (Priority 85 > 70).
    """
    text = "Kunjungan ke Pavilion Kuala Lumpur pada hari ini."
    # Model predicts full venue
    model_entities = [
        {"text": "Pavilion Kuala Lumpur", "label": "LOCATION", "score": 0.96, "start": 13, "end": 34}
    ]
    # Gazetteer predicts only the nested city
    rule_entities = [
        {"text": "Kuala Lumpur", "label": "LOCATION", "score": 0.98, "start": 22, "end": 34}
    ]

    resolved = resolve_entity_conflicts(model_entities, rule_entities, text)

    assert len(resolved) == 1
    assert resolved[0]["text"] == "Pavilion Kuala Lumpur"
    assert resolved[0]["start"] == 13
    assert resolved[0]["end"] == 34


def test_low_confidence_model_yields_to_gazetteer() -> None:
    """Verifies that a low-confidence model prediction (score < threshold) yields

    to a verified gazetteer entity (Priority 70 > 35).
    """
    text = "Pengumuman rasmi daripada Bank Negara Malaysia."
    # Flawed/low-confidence model prediction
    model_entities = [
        {"text": "Bank Negara", "label": "ORGANIZATION", "score": 0.35, "start": 26, "end": 37}
    ]
    # Curated gazetteer match
    rule_entities = [
        {"text": "Bank Negara Malaysia", "label": "ORGANIZATION", "score": 0.98, "start": 26, "end": 46}
    ]

    resolved = resolve_entity_conflicts(model_entities, rule_entities, text)

    assert len(resolved) == 1
    assert resolved[0]["text"] == "Bank Negara Malaysia"
    assert resolved[0]["start"] == 26
    assert resolved[0]["end"] == 46


def test_gazetteer_fallback_when_model_silent() -> None:
    """Verifies that gazetteers act as reliable fallbacks when the transformer predicts nothing."""
    text = "Sila serahkan borang permohonan kepada KWSP dan LHDN."
    model_entities = []  # Model misses statutory acronyms
    rule_entities = find_malaysian_org_entities(text)

    resolved = resolve_entity_conflicts(model_entities, rule_entities, text)

    matched_texts = [e["text"] for e in resolved]
    assert "KWSP" in matched_texts
    assert "LHDN" in matched_texts


def test_per_category_threshold_evaluation() -> None:
    """Verifies that priority respects independent category confidence thresholds."""
    ent_person = {"label": "PERSON", "score": 0.52}
    ent_org_low = {"label": "ORGANIZATION", "score": 0.55}
    ent_org_high = {"label": "ORGANIZATION", "score": 0.65}

    # PERSON threshold is 0.50 -> 0.52 is confident (85)
    assert get_entity_priority(ent_person, source="model") == 85
    # ORG threshold is 0.60 -> 0.55 is low-confidence (35)
    assert get_entity_priority(ent_org_low, source="model") == 35
    # ORG threshold is 0.60 -> 0.65 is confident (85)
    assert get_entity_priority(ent_org_high, source="model") == 85


# =========================================================================
# 2. Heuristic Recognizer Hardening Tests
# =========================================================================

def test_corporate_regex_anti_greediness() -> None:
    """Verifies that corporate suffix regex does not swallow preceding lowercase verbs."""
    text = "Don't worry one, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 5.35 PM under batch 6."
    orgs = find_malaysian_org_entities(text)

    matched_texts = [e["text"] for e in orgs]
    assert "Maxis Berhad" in matched_texts
    assert not any("submitted" in t for t in matched_texts)
    assert not any("proposal" in t for t in matched_texts)


def test_corporate_regex_capitalized_spans() -> None:
    """Verifies multi-word capitalized corporate entities are matched cleanly."""
    text = "Syarikat Kerjaya Prospek Group Berhad dan Apex Logistics PLT menandatangani perjanjian."
    orgs = find_malaysian_org_entities(text)

    matched_texts = [e["text"] for e in orgs]
    assert any("Kerjaya Prospek Group Berhad" in t for t in matched_texts)
    assert any("Apex Logistics PLT" in t for t in matched_texts)


def test_location_regex_anti_runaway() -> None:
    """Verifies that address regex does not swallow following dates or prepositions."""
    text = "Projek perintis di Sungai Petani pada April 2024 di bawah inisiatif 4."
    locs = find_malaysian_locations(text)

    matched_texts = [l["text"] for l in locs]
    assert "Sungai Petani" in matched_texts
    # Must not swallow "pada April 2024 di bawah..."
    for t in matched_texts:
        assert "April" not in t
        assert "inisiatif" not in t


def test_location_regex_standard_addresses() -> None:
    """Verifies detection of standard street and residential patterns."""
    text = "Beralamat di Jalan Sultan Ismail dan Taman Tun Dr Ismail serta Presint 2."
    locs = find_malaysian_locations(text)

    matched_texts = [l["text"] for l in locs]
    assert any("Jalan Sultan Ismail" in t for t in matched_texts)
    assert any("Taman Tun Dr Ismail" in t for t in matched_texts)
    assert any("Presint 2" in t for t in matched_texts)


# =========================================================================
# 3. Honorific-Organizational Boundary Recovery Tests
# =========================================================================

def test_boundary_recovery_reclaims_prefix() -> None:
    """Verifies that 'Kementerian' is restored when preceded by 'Menteri'."""
    text = "Menteri Kementerian Belia dan Sukan, Saifuddin bin Nasution merasmikan majlis."
    flawed_model_entities = [
        {"label": "ORGANIZATION", "text": "Belia dan Sukan", "start": 20, "end": 35, "score": 0.96}
    ]

    repaired = recover_institutional_boundaries(flawed_model_entities, text)

    assert len(repaired) == 1
    assert repaired[0]["text"] == "Kementerian Belia dan Sukan"
    assert repaired[0]["start"] == 8
    assert repaired[0]["end"] == 35


def test_boundary_recovery_does_not_absorb_title() -> None:
    """Verifies that ministerial titles ('Menteri') are NOT absorbed into the organization."""
    text = "Menteri Kementerian Kemajuan Desa dan Wilayah mengumumkan dasar baru."
    flawed_model_entities = [
        {"label": "ORGANIZATION", "text": "Kemajuan Desa dan Wilayah", "start": 20, "end": 45, "score": 0.98}
    ]

    repaired = recover_institutional_boundaries(flawed_model_entities, text)

    assert len(repaired) == 1
    assert repaired[0]["text"] == "Kementerian Kemajuan Desa dan Wilayah"
    assert "Menteri" not in repaired[0]["text"]
    assert repaired[0]["start"] == 8


def test_boundary_recovery_no_false_expansion() -> None:
    """Verifies that organizations without preceding institutional prefixes remain unaltered."""
    text = "Lawatan kerja ke Universiti Malaya telah dijadualkan."
    model_entities = [
        {"label": "ORGANIZATION", "text": "Universiti Malaya", "start": 17, "end": 34, "score": 0.99}
    ]

    repaired = recover_institutional_boundaries(model_entities, text)

    assert len(repaired) == 1
    assert repaired[0]["text"] == "Universiti Malaya"
    assert repaired[0]["start"] == 17
    assert repaired[0]["end"] == 34
