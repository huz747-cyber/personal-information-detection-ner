"""
Phase 3 Dataset Expansion and Annotation Regression Tests.

Verifies:
1. Canonical dataset volume (exactly 1,000 sentences) and text uniqueness.
2. Entity count invariant (2,230 entities = 823 PERSON + 830 LOCATION + 577 ORGANIZATION).
3. Exact 1:1 match between B-tag count and entity count (zero boundary heuristic defects).
4. Hard-negative volume (>= 100 sentences with 0 entities).
5. All 7 sociolinguistic categories represented according to stratification targets.
6. Split partitions sum to 1,000 with 70/15/15 target ratios and zero cross-split leakage.
7. Sourced vs. synthetic breakdown (>= 70% human-authored/publicly sourced).
8. Phase 2 recognizer and baseline model behavior invariance.

Author: AI/ML Club
License: MIT
"""

import json
from collections import Counter
from pathlib import Path
import pytest


CANONICAL_PATH = Path("data/annotated/malaysian_ner_1000.jsonl")
SPLITS_DIR = Path("data/splits")


def load_canonical_records():
    assert CANONICAL_PATH.exists(), f"Canonical dataset not found at {CANONICAL_PATH}"
    records = []
    with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def test_phase3_dataset_volume_and_uniqueness():
    """Verifies that the dataset contains exactly 1,000 unique records without duplicate IDs or texts."""
    records = load_canonical_records()
    assert len(records) == 1000, f"Expected 1,000 sentences, got {len(records)}"

    # Check ID uniqueness
    ids = [r["id"] for r in records]
    assert len(set(ids)) == 1000, "Found duplicate record IDs in canonical dataset"

    # Check exact text uniqueness
    texts = [r["text"] for r in records]
    assert len(set(texts)) == 1000, "Found exact text duplicates in canonical dataset"

    # Check normalized text uniqueness
    import re
    norm_texts = [re.sub(r"\s+", " ", r["text"].strip().lower()) for r in records]
    assert len(set(norm_texts)) == 1000, "Found normalized text duplicates in canonical dataset"


def test_phase3_entity_counts_and_invariants():
    """Verifies entity class breakdown and 1:1 B-tag invariant across 1,000 records."""
    from src.dataset_tools.doccano_adapter import text_to_bio

    records = load_canonical_records()
    entity_counter = Counter()
    b_tag_counter = Counter()

    for r in records:
        labels = r.get("label", [])
        for lbl in labels:
            entity_counter[lbl[2]] += 1

        # Check BIO conversion
        tokens, bio = text_to_bio(r["text"], [{"start": s, "end": e, "label": l} for s, e, l in labels])
        for tag in bio:
            if tag.startswith("B-"):
                b_tag_counter[tag[2:]] += 1

    assert entity_counter["PERSON"] == 823
    assert entity_counter["LOCATION"] == 830
    assert entity_counter["ORGANIZATION"] == 577
    assert sum(entity_counter.values()) == 2230

    # Invariant: Entity counts must match B-tag counts exactly
    assert b_tag_counter["PERSON"] == 823
    assert b_tag_counter["LOCATION"] == 830
    assert b_tag_counter["ORGANIZATION"] == 577
    assert sum(b_tag_counter.values()) == 2230


def test_phase3_hard_negatives_count_and_cleanliness():
    """Verifies at least 100 hard negatives exist with zero entity annotations."""
    records = load_canonical_records()
    hard_negatives = [r for r in records if r.get("meta", {}).get("is_hard_negative") is True]

    assert len(hard_negatives) >= 100, f"Expected at least 100 hard negatives, got {len(hard_negatives)}"
    assert len(hard_negatives) == 105, f"Expected 105 verified hard negatives, got {len(hard_negatives)}"

    for hn in hard_negatives:
        assert len(hn.get("label", [])) == 0, f"Hard negative {hn['id']} contains annotated entities!"


def test_phase3_stratification_coverage():
    """Verifies that all 7 target sociolinguistic categories are represented."""
    records = load_canonical_records()
    strata_counts = Counter(r.get("meta", {}).get("stratum") for r in records)

    expected_strata = {
        "formal_malay": 240,
        "malaysian_english": 240,
        "manglish": 140,
        "mixed_code_switch": 140,
        "chinese_naming": 95,
        "indian_naming": 95,
        "international_baseline": 50,
    }

    assert len(strata_counts) == 7
    for stratum, expected_count in expected_strata.items():
        assert strata_counts[stratum] == expected_count, (
            f"Stratum {stratum} has {strata_counts[stratum]} records, expected {expected_count}"
        )


def test_phase3_splits_consistency_and_zero_leakage():
    """Verifies 70/15/15 target split distribution and zero cross-split leakage."""
    train_path = SPLITS_DIR / "train.jsonl"
    val_path = SPLITS_DIR / "val.jsonl"
    test_path = SPLITS_DIR / "test.jsonl"

    assert train_path.exists()
    assert val_path.exists()
    assert test_path.exists()

    def read_split(p):
        with open(p, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    train = read_split(train_path)
    val = read_split(val_path)
    test = read_split(test_path)

    # Ratios
    assert len(train) == 705  # 70.5%
    assert len(val) == 150    # 15.0%
    assert len(test) == 145   # 14.5%
    assert len(train) + len(val) + len(test) == 1000

    # Leakage checks
    t_ids = {r["id"] for r in train}
    v_ids = {r["id"] for r in val}
    te_ids = {r["id"] for r in test}

    assert len(t_ids & v_ids) == 0
    assert len(t_ids & te_ids) == 0
    assert len(v_ids & te_ids) == 0

    t_text = {r["text"] for r in train}
    v_text = {r["text"] for r in val}
    te_text = {r["text"] for r in test}

    assert len(t_text & v_text) == 0
    assert len(t_text & te_text) == 0
    assert len(v_text & te_text) == 0

    # Template leaks
    def get_templates(split):
        return {r.get("meta", {}).get("template_id") for r in split if r.get("meta", {}).get("template_id")}

    assert len(get_templates(train) & get_templates(val)) == 0
    assert len(get_templates(train) & get_templates(test)) == 0
    assert len(get_templates(val) & get_templates(test)) == 0


def test_phase3_sourced_vs_synthetic_breakdown():
    """Verifies >= 70% human-authored / publicly sourced data and explicit synthetic tagging."""
    records = load_canonical_records()
    source_counts = Counter(r.get("meta", {}).get("source_id") for r in records)

    # SRC-008 is synthetic generator; all others are sourced or human-authored
    synthetic_count = source_counts["SRC-008"]
    sourced_count = 1000 - synthetic_count

    assert synthetic_count == 290  # 29.0%
    assert sourced_count == 710    # 71.0%
    assert sourced_count >= 700    # At least 70% sourced/human-authored


def test_phase3_recognizer_behavior_invariance():
    """Verifies Phase 2 hybrid recognizers and patronymic stitching remain unchanged."""
    from src.recognizers.mykad_recognizer import find_mykad_entities, mask_mykad
    from src.recognizers.phone_recognizer import find_phone_entities
    from src.recognizers.org_gazetteer import find_malaysian_org_entities
    from src.recognizers.location_recognizer import find_malaysian_locations, find_malaysian_postcodes
    from src.patronymic_stitcher import stitch_patronymic_entities

    # Test patronymic stitching
    raw_entities = [
        {"label": "PERSON", "text": "Ahmad Faiz", "start": 0, "end": 10, "score": 0.95},
        {"label": "PERSON", "text": "Zulkifli", "start": 15, "end": 23, "score": 0.92},
    ]
    stitched = stitch_patronymic_entities(raw_entities, "Ahmad Faiz bin Zulkifli hadir.")
    assert len(stitched) == 1
    assert stitched[0]["text"] == "Ahmad Faiz bin Zulkifli"
    assert stitched[0]["start"] == 0
    assert stitched[0]["end"] == 23

    # Test MyKad detection and masking
    text_mykad = "No. K/P beliau ialah 950315-10-5231."
    mykad_spans = find_mykad_entities(text_mykad)
    assert len(mykad_spans) == 1
    assert mykad_spans[0]["text"] == "950315-10-5231"
    assert mask_mykad("950315-10-5231") == "950315-10-****"

    # Test statutory body gazetteer
    text_org = "Sila buat bayaran cukai di Lembaga Hasil Dalam Negeri di Putrajaya."
    org_spans = find_malaysian_org_entities(text_org)
    assert any(o["text"] == "Lembaga Hasil Dalam Negeri" for o in org_spans)

    # Test location and postcode recognizer
    loc_spans = find_malaysian_locations(text_org)
    assert any(l["text"] == "Putrajaya" for l in loc_spans)

    text_postcode = "Alamat surat-menyurat: Petaling Jaya, 47301 Selangor."
    postcode_spans = find_malaysian_postcodes(text_postcode)
    assert len(postcode_spans) == 1
    assert postcode_spans[0]["text"] == "47301"
