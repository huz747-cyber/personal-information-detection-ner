"""
Unit tests for Phase 2.6 dataset tools.

Tests:
1. Privacy screener (credentials, live phones, credit cards, residential addresses).
2. Deduplication engine (exact, normalized, fuzzy near-duplicates).
3. Provenance and manifest auditor.
4. Inter-annotator agreement metrics and disagreement logging.
5. Template-grouped and document-isolated splitting.
6. Hard negative validation rules.

Author: AI/ML Club
License: MIT
"""

import pytest
from src.dataset_tools.agreement import (
    AnnotationAgreementCalculator,
    DisagreementCase,
    adjudicate_disagreement,
)
from src.dataset_tools.deduplicator import DatasetDeduplicator
from src.dataset_tools.privacy_screener import PrivacyScreener
from src.dataset_tools.provenance import ProvenanceAuditor
from src.dataset_tools.splitter import DatasetSplitter
from src.dataset_tools.validator import DatasetValidator


def test_privacy_screener_detects_credentials():
    screener = PrivacyScreener()
    bad_text = "Here is the production db access: password=SuperSecret99! and api_key=ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    viols = screener.scan_text(bad_text, record_id="priv-01")
    assert len(viols) >= 1
    assert any(v.category == "CREDENTIAL" for v in viols)


def test_privacy_screener_detects_credit_cards():
    screener = PrivacyScreener()
    # Valid Visa card passing Luhn: 4532 0150 0000 0007
    bad_text = "Sila buat bayaran menggunakan kad 4532 0150 0000 0007 di kaunter."
    viols = screener.scan_text(bad_text, record_id="priv-02")
    assert any(v.category == "CREDIT_CARD" for v in viols)


def test_privacy_screener_allows_synthetic_and_flags_live_phone():
    screener = PrivacyScreener(allow_synthetic=True)
    # Synthetic approved phone
    synth_text = "Hubungi pegawai di +6012-345 6789 untuk bantuan."
    assert len(screener.scan_text(synth_text, record_id="priv-synth")) == 0

    # Unmasked live personal mobile number
    live_text = "Sila whatsapp nombor peribadi 016-9876543 sekarang."
    viols = screener.scan_text(live_text, record_id="priv-live")
    assert len(viols) == 1
    assert viols[0].category == "PHONE_LEAK"


def test_privacy_screener_flags_residential_addresses():
    screener = PrivacyScreener()
    res_text = "Penghantaran dibuat ke No. 42B, Jalan Melati 3, Taman Anggerik."
    viols = screener.scan_text(res_text, record_id="priv-res")
    assert any(v.category == "RESIDENTIAL_ADDRESS" for v in viols)


def test_deduplicator_fuzzy_and_normalized():
    dedup = DatasetDeduplicator(near_duplicate_threshold=0.80)
    records = [
        {"id": "r1", "text": "Ahmad Faiz bin Zulkifli telah hadir ke mesyuarat di Putrajaya pagi ini."},
        {"id": "r2", "text": "ahmad faiz bin zulkifli telah hadir ke mesyuarat di putrajaya pagi ini."},  # Normalized
        {"id": "r3", "text": "Ahmad Faiz bin Zulkifli telah hadir ke mesyuarat di Putrajaya petang ini."}, # Fuzzy near-dup
        {"id": "r4", "text": "Siti Hajar binti Osman bertugas di Cyberjaya untuk projek baharu."},       # Unique
    ]
    clusters, uniques = dedup.find_duplicates(records)
    assert len(clusters) == 2
    assert len(uniques) == 2
    assert {u["id"] for u in uniques} == {"r1", "r4"}


def test_provenance_auditor(tmp_path):
    auditor = ProvenanceAuditor(manifest_path="data/SOURCE_MANIFEST.csv")
    valid_records = [
        {"id": "rec-1", "text": "Teks formal.", "metadata": {"source_id": "SRC-001"}},
        {"id": "rec-2", "text": "Teks bebas.", "metadata": {"source_id": "SRC-007"}},
    ]
    report = auditor.audit_dataset(valid_records)
    assert report.total_records == 2
    assert report.unverified_records == 0
    assert report.is_compliant is True

    bad_records = [
        {"id": "rec-3", "text": "Teks haram.", "metadata": {"source_id": "SRC-999"}},
    ]
    report_bad = auditor.audit_dataset(bad_records)
    assert report_bad.unverified_records == 1
    assert report_bad.is_compliant is False


def test_annotation_agreement_calculator():
    calc = AnnotationAgreementCalculator()
    ann1 = [
        {
            "id": "s-1",
            "text": "Ahmad Faiz bin Zulkifli pergi ke Universiti Malaya di Kuala Lumpur.",
            "entities": [
                {"start": 0, "end": 23, "label": "PERSON", "text": "Ahmad Faiz bin Zulkifli"},
                {"start": 33, "end": 50, "label": "ORGANIZATION", "text": "Universiti Malaya"},
                {"start": 54, "end": 66, "label": "LOCATION", "text": "Kuala Lumpur"},
            ],
        },
        {
            "id": "s-2",
            "text": "Dato' Seri Wan Azizah di Menara Maybank.",
            "entities": [
                {"start": 11, "end": 21, "label": "PERSON", "text": "Wan Azizah"},
                {"start": 25, "end": 39, "label": "ORGANIZATION", "text": "Menara Maybank"},
            ],
        },
    ]

    ann2 = [
        {
            "id": "s-1",
            "text": "Ahmad Faiz bin Zulkifli pergi ke Universiti Malaya di Kuala Lumpur.",
            "entities": [
                {"start": 0, "end": 23, "label": "PERSON", "text": "Ahmad Faiz bin Zulkifli"},  # Match
                {"start": 33, "end": 50, "label": "LOCATION", "text": "Universiti Malaya"},     # Class disagreement
                {"start": 54, "end": 66, "label": "LOCATION", "text": "Kuala Lumpur"},          # Match
            ],
        },
        {
            "id": "s-2",
            "text": "Dato' Seri Wan Azizah di Menara Maybank.",
            "entities": [
                {"start": 0, "end": 21, "label": "PERSON", "text": "Dato' Seri Wan Azizah"},    # Boundary disagreement (included title)
                {"start": 25, "end": 39, "label": "ORGANIZATION", "text": "Menara Maybank"},   # Match
            ],
        },
    ]

    report = calc.evaluate_pair(ann1, ann2)
    assert report.total_evaluated_sentences == 2
    assert report.matched_exact_entities == 3
    assert report.class_disagreements == 1
    assert report.boundary_disagreements == 1
    assert report.exact_span_f1 > 0.5
    assert report.cohens_kappa > 0.5

    # Test adjudication
    case = report.disagreement_details[0]
    adjudicated = adjudicate_disagreement(
        case,
        chosen_span={"start": 33, "end": 50, "label": "ORGANIZATION", "text": "Universiti Malaya"},
        reason="Universiti Malaya is a public university institution classified as ORGANIZATION.",
    )
    assert adjudicated.resolution is not None
    assert "ORGANIZATION" in adjudicated.adjudication_notes


def test_splitter_group_template_isolation():
    # Sentences sharing template_id must stay in the same split
    records = []
    for i in range(15):
        records.append({
            "id": f"t1_{i}",
            "text": f"Template 1 sentence variant {i}.",
            "entities": [],
            "metadata": {"template_id": "tpl-01", "stratum": "formal_malay"},
        })
    for i in range(15):
        records.append({
            "id": f"t2_{i}",
            "text": f"Template 2 sentence variant {i}.",
            "entities": [],
            "metadata": {"template_id": "tpl-02", "stratum": "formal_malay"},
        })
    for i in range(15):
        records.append({
            "id": f"t3_{i}",
            "text": f"Template 3 sentence variant {i}.",
            "entities": [],
            "metadata": {"template_id": "tpl-03", "stratum": "formal_malay"},
        })

    splitter = DatasetSplitter(seed=42)
    train, val, test = splitter.split_records(records)

    def get_templates(recs):
        return {r["metadata"]["template_id"] for r in recs}

    train_tpls = get_templates(train)
    val_tpls = get_templates(val)
    test_tpls = get_templates(test)

    # Zero template leakage
    assert len(train_tpls & val_tpls) == 0
    assert len(train_tpls & test_tpls) == 0
    assert len(val_tpls & test_tpls) == 0


def test_validator_hard_negative_checks():
    validator = DatasetValidator()

    # Good hard negative with currency distractor and 0 entities
    good_hn = {
        "id": "hn-01",
        "text": "Syarikat membayar ganti rugi sebanyak RM 50000 kepada mangsa banjir.",
        "entities": [],
        "metadata": {"is_hard_negative": True},
    }
    issues_good = validator.validate_single_record(good_hn)
    assert not any(i.severity == "ERROR" and i.check == "HARD_NEGATIVE" for i in issues_good)

    # Bad hard negative with an entity
    bad_hn_ent = {
        "id": "hn-02",
        "text": "Ali membayar ganti rugi sebanyak RM 50000.",
        "entities": [{"start": 0, "end": 3, "label": "PERSON", "text": "Ali"}],
        "metadata": {"is_hard_negative": True},
    }
    issues_bad = validator.validate_single_record(bad_hn_ent)
    assert any(i.severity == "ERROR" and i.check == "HARD_NEGATIVE" for i in issues_bad)


def test_text_to_bio_entity_invariant_and_punctuation():
    """Phase 2.6.1 Audit A: Verifies that entity spans with internal punctuation or single characters
    produce exactly one B- tag, ensuring Total Entities == B-Tag Count.
    """
    from src.dataset_tools.doccano_adapter import text_to_bio

    text = "Contract signed with D&O Green Technologies Berhad in Melaka."
    entities = [
        {"start": 21, "end": 50, "label": "ORGANIZATION", "text": "D&O Green Technologies Berhad"},
        {"start": 54, "end": 60, "label": "LOCATION", "text": "Melaka"},
    ]
    tokens, bio = text_to_bio(text, entities)

    # Invariant: exactly one B-ORGANIZATION and one B-LOCATION
    assert bio.count("B-ORGANIZATION") == 1
    assert bio.count("B-LOCATION") == 1
    assert bio.count("B-PERSON") == 0

    # Ensure '&' inside D&O is tagged I-ORGANIZATION, not B-ORGANIZATION
    amp_idx = tokens.index("&")
    assert bio[amp_idx] == "I-ORGANIZATION"


def test_doccano_schema_and_roundtrip_fidelity():
    """Phase 2.6.1 Audit H: Verifies strict Doccano JSONL format and roundtrip offset consistency."""
    import json
    import tempfile
    from src.dataset_tools.doccano_adapter import export_to_doccano, import_from_doccano

    records = [
        {
            "id": "doc-01",
            "text": "Datuk Seri Anwar Ibrahim ke Putrajaya.",
            "entities": [
                {"start": 0, "end": 24, "label": "PERSON", "text": "Datuk Seri Anwar Ibrahim"},
                {"start": 28, "end": 37, "label": "LOCATION", "text": "Putrajaya"},
            ],
            "metadata": {"stratum": "formal_malay", "source_id": "SRC-005"},
        }
    ]

    with tempfile.NamedTemporaryFile("w+", suffix=".jsonl", delete=False, encoding="utf-8") as tf:
        temp_path = tf.name

    try:
        export_to_doccano(records, temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            assert "text" in data
            assert "label" in data
            assert isinstance(data["label"], list)
            assert data["label"] == [[0, 24, "PERSON"], [28, 37, "LOCATION"]]

        reimported = import_from_doccano(temp_path)
        assert len(reimported) == 1
        assert reimported[0]["text"] == records[0]["text"]
        assert len(reimported[0]["entities"]) == 2
        for orig_e, reimp_e in zip(records[0]["entities"], reimported[0]["entities"]):
            assert orig_e["start"] == reimp_e["start"]
            assert orig_e["end"] == reimp_e["end"]
            assert orig_e["label"] == reimp_e["label"]
            assert orig_e["text"] == reimp_e["text"]
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_dataset_release_checker_safeguards():
    """Phase 2.6.2 Audit A: Verifies that DatasetReleaseChecker properly discriminates
    between research, commercial training, and redistribution tiers.
    """
    import tempfile
    from src.dataset_tools.release_checker import DatasetReleaseChecker

    checker = DatasetReleaseChecker()
    mock_records = [
        {"id": "rec-01", "text": "Sample 1", "metadata": {"source_id": "SRC-007"}},  # Independent
        {"id": "rec-02", "text": "Sample 2", "metadata": {"source_id": "SRC-008"}},  # Synthetic
        {"id": "rec-03", "text": "Sample 3", "metadata": {"source_id": "SRC-001"}},  # Mesolitica News
        {"id": "rec-04", "text": "Sample 4", "metadata": {"source_id": "SRC-004"}},  # CoNLL Reuters
    ]

    # Individual record dimension checks
    elig_indep = checker.check_record(mock_records[0])
    assert elig_indep["commercial_training"] is True
    assert elig_indep["raw_text_redistribution"] is True

    elig_meso = checker.check_record(mock_records[2])
    assert elig_meso["research_use"] is True
    assert elig_meso["commercial_training"] is False
    assert elig_meso["raw_text_redistribution"] is False

    elig_conll = checker.check_record(mock_records[3])
    assert elig_conll["research_use"] is True
    assert elig_conll["commercial_training"] is False
    assert elig_conll["raw_text_redistribution"] is False

    with tempfile.TemporaryDirectory() as tmp_dir:
        meta = checker.generate_release_manifests(mock_records, output_dir=tmp_dir)
        assert meta["total_canonical_records"] == 4
        assert meta["research_eligible_count"] == 4
        assert meta["commercial_training_eligible_count"] == 2
        assert meta["raw_redistribution_eligible_count"] == 2
        assert meta["excluded_from_commercial_count"] == 2
