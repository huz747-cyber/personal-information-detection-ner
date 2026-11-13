"""
Unit tests for Malaysian NER dataset tools.

Tests:
1. Doccano export/import round-trip integrity.
2. Character span to IOB2 BIO conversion and back.
3. DatasetValidator offset integrity, BIO grammar, duplicates, and leakage checks.
4. DatasetSplitter reproducibility, stratified ratios, and leakage prevention.

Author: AI/ML Club
License: MIT
"""

import json
from pathlib import Path
import pytest

from src.dataset_tools.doccano_adapter import (
    bio_to_spans,
    export_to_doccano,
    import_from_doccano,
    text_to_bio,
    tokenize_with_offsets,
)
from src.dataset_tools.splitter import DatasetSplitter
from src.dataset_tools.validator import DatasetValidator, ValidationIssue


@pytest.fixture
def sample_ner_records():
    return [
        {
            "id": "my-01",
            "text": "Ahmad Faiz bin Zulkifli hadir taklimat di Putrajaya.",
            "entities": [
                {"text": "Ahmad Faiz bin Zulkifli", "label": "PERSON", "start": 0, "end": 23},
                {"text": "Putrajaya", "label": "LOCATION", "start": 42, "end": 51},
            ],
            "metadata": {"stratum": "formal_malay", "domain": "government"},
        },
        {
            "id": "my-02",
            "text": "Siti Hajar binti Osman bertugas di Cyberjaya.",
            "entities": [
                {"text": "Siti Hajar binti Osman", "label": "PERSON", "start": 0, "end": 22},
                {"text": "Cyberjaya", "label": "LOCATION", "start": 35, "end": 44},
            ],
            "metadata": {"stratum": "formal_malay", "domain": "technology"},
        },
        {
            "id": "my-03",
            "text": "Ravi a/l Chandran signed the contract in George Town.",
            "entities": [
                {"text": "Ravi a/l Chandran", "label": "PERSON", "start": 0, "end": 17},
                {"text": "George Town", "label": "LOCATION", "start": 41, "end": 52},
            ],
            "metadata": {"stratum": "malaysian_english", "domain": "corporate"},
        },
        {
            "id": "my-04",
            "text": "Tan Wei Jun joined CIMB Bank in Kuala Lumpur yesterday.",
            "entities": [
                {"text": "Tan Wei Jun", "label": "PERSON", "start": 0, "end": 11},
                {"text": "CIMB Bank", "label": "ORGANIZATION", "start": 19, "end": 28},
                {"text": "Kuala Lumpur", "label": "LOCATION", "start": 32, "end": 44},
            ],
            "metadata": {"stratum": "chinese_naming", "domain": "banking"},
        },
    ]


def test_tokenize_with_offsets():
    text = "Dato' Seri Wan Azizah binti Wan Ismail ke Hospital Kuala Lumpur!"
    tokens = tokenize_with_offsets(text)
    assert len(tokens) > 0
    for tok, start, end in tokens:
        assert text[start:end] == tok


def test_text_to_bio_and_bio_to_spans():
    text = "Ahmad Faiz bin Zulkifli hadir di Putrajaya."
    entities = [
        {"text": "Ahmad Faiz bin Zulkifli", "label": "PERSON", "start": 0, "end": 23},
        {"text": "Putrajaya", "label": "LOCATION", "start": 33, "end": 42},
    ]
    tokens, bio_tags = text_to_bio(text, entities)

    assert "B-PERSON" in bio_tags
    assert "I-PERSON" in bio_tags
    assert "B-LOCATION" in bio_tags
    assert "O" in bio_tags

    reconstructed = bio_to_spans(tokens, bio_tags, text=text)
    assert len(reconstructed) == 2
    assert reconstructed[0]["text"] == "Ahmad Faiz bin Zulkifli"
    assert reconstructed[0]["label"] == "PERSON"
    assert reconstructed[0]["start"] == 0
    assert reconstructed[0]["end"] == 23

    assert reconstructed[1]["text"] == "Putrajaya"
    assert reconstructed[1]["label"] == "LOCATION"
    assert reconstructed[1]["start"] == 33
    assert reconstructed[1]["end"] == 42


def test_doccano_export_import_roundtrip(tmp_path, sample_ner_records):
    out_file = tmp_path / "doccano_export.jsonl"
    count = export_to_doccano(sample_ner_records, out_file)
    assert count == len(sample_ner_records)
    assert out_file.exists()

    imported = import_from_doccano(out_file)
    assert len(imported) == len(sample_ner_records)

    for orig, imp in zip(sample_ner_records, imported):
        assert imp["text"] == orig["text"]
        assert len(imp["entities"]) == len(orig["entities"])
        for o_ent, i_ent in zip(orig["entities"], imp["entities"]):
            assert i_ent["label"] == o_ent["label"]
            assert i_ent["start"] == o_ent["start"]
            assert i_ent["end"] == o_ent["end"]
            assert i_ent["text"] == o_ent["text"]


def test_validator_clean_records(sample_ner_records):
    validator = DatasetValidator()
    report = validator.validate_dataset(sample_ner_records)
    assert report.is_clean is True
    assert report.error_count == 0
    assert report.valid_records == 4
    assert report.entity_counts["PERSON"] == 4
    assert report.entity_counts["LOCATION"] == 4
    assert report.entity_counts["ORGANIZATION"] == 1


def test_validator_detects_offset_errors():
    bad_record = {
        "id": "err-01",
        "text": "Ali pergi ke Shah Alam.",
        "entities": [
            # Inverted offset
            {"text": "Ali", "label": "PERSON", "start": 5, "end": 2},
            # Text mismatch
            {"text": "Petaling Jaya", "label": "LOCATION", "start": 13, "end": 22},
        ],
    }
    validator = DatasetValidator()
    report = validator.validate_dataset([bad_record])
    assert report.is_clean is False
    assert report.error_count >= 2
    offset_errors = [iss for iss in report.issues if iss.check == "OFFSET"]
    assert len(offset_errors) >= 2


def test_validator_detects_invalid_bio_sequence():
    validator = DatasetValidator()
    # Test orphaned I- tag without B-
    tokens = ["Faiz", "bin", "Zulkifli"]
    bad_bio = ["I-PERSON", "I-PERSON", "I-PERSON"]
    issues = validator.validate_bio_sequence(tokens, bad_bio, rec_id="test-bio")
    assert len(issues) == 1
    assert issues[0].severity == "ERROR"
    assert "Orphaned" in issues[0].message

    # Test illegal label transition: B-LOC -> I-PER
    tokens2 = ["Kuala", "Lumpur"]
    bad_bio2 = ["B-LOCATION", "I-PERSON"]
    issues2 = validator.validate_bio_sequence(tokens2, bad_bio2, rec_id="test-trans")
    assert len(issues2) == 1
    assert issues2[0].severity == "ERROR"
    assert "Illegal transition" in issues2[0].message


def test_validator_detects_duplicates():
    dup_records = [
        {"id": "d-1", "text": "Ali hadir ke mesyuarat di Putrajaya.", "entities": []},
        {"id": "d-2", "text": "Ali hadir ke mesyuarat di Putrajaya.", "entities": []},
        {"id": "d-3", "text": " ali hadir ke mesyuarat di Putrajaya. ", "entities": []},
    ]
    validator = DatasetValidator()
    report = validator.validate_dataset(dup_records)
    dup_issues = [iss for iss in report.issues if iss.check == "DUPLICATE"]
    assert len(dup_issues) == 2


def test_validator_detects_split_contamination():
    train = [{"id": "tr-1", "text": "Ali melawat Hospital Kuala Lumpur.", "entities": []}]
    val = [{"id": "va-1", "text": "Siti pergi ke Ipoh.", "entities": []}]
    test = [{"id": "te-1", "text": " ali melawat hospital kuala lumpur. ", "entities": []}]

    validator = DatasetValidator()
    leakage = validator.check_cross_split_contamination(train, val, test)
    assert len(leakage) == 1
    assert leakage[0].check == "LEAKAGE"
    assert leakage[0].record_id == "te-1"


def test_validator_missing_label_heuristic():
    unlabeled = {
        "id": "miss-1",
        "text": "Ahmad Faiz bin Zulkifli dan Megah Holdings Sdn. Bhd. beroperasi di Putrajaya.",
        "entities": [],  # Completely unannotated
    }
    validator = DatasetValidator()
    report = validator.validate_dataset([unlabeled])
    missing = [iss for iss in report.issues if iss.check == "MISSING_LABEL"]
    # Should flag patronymic marker, corporate suffix, and major city
    assert len(missing) >= 2


def test_splitter_reproducibility_and_ratios(tmp_path):
    # Generate 20 synthetic records across 2 strata
    records = []
    for i in range(20):
        stratum = "formal_malay" if i < 10 else "malaysian_english"
        records.append({
            "id": f"rec-{i}",
            "text": f"Synthetic text number {i} for evaluation purposes.",
            "entities": [{"text": "Synthetic", "label": "ORGANIZATION", "start": 0, "end": 9}],
            "metadata": {"stratum": stratum},
        })

    splitter_1 = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
    t1, v1, te1 = splitter_1.split_records(records)

    splitter_2 = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
    t2, v2, te2 = splitter_2.split_records(records)

    # Determinism
    assert [r["id"] for r in t1] == [r["id"] for r in t2]
    assert [r["id"] for r in v1] == [r["id"] for r in v2]
    assert [r["id"] for r in te1] == [r["id"] for r in te2]

    # Proportions
    assert len(t1) + len(v1) + len(te1) == 20
    assert len(t1) == 14  # 70% of 20
    assert len(v1) + len(te1) == 6  # 30% held-out
    assert abs(len(v1) - 3) <= 1
    assert abs(len(te1) - 3) <= 1


def test_splitter_file_export(tmp_path, sample_ner_records):
    in_file = tmp_path / "all_data.jsonl"
    export_to_doccano(sample_ner_records, in_file)

    splitter = DatasetSplitter(seed=42)
    res = splitter.split_and_save(in_file, tmp_path / "splits")

    assert res["total"] == 4
    assert (tmp_path / "splits" / "train.jsonl").exists()
    assert (tmp_path / "splits" / "val.jsonl").exists()
    assert (tmp_path / "splits" / "test.jsonl").exists()
