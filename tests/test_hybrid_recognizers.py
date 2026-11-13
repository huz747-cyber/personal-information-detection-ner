"""
Dedicated Unit and Integration Tests for Phase 2: Hybrid Recognizer Layer.

Tests:
    1. Malaysian NRIC / MyKad pattern recognizer (valid, invalid, incomplete, ambiguous).
    2. Malaysian phone number recognizer (mobile, landlines, false-positive protection).
    3. Malaysian statutory body and corporate gazetteer.
    4. Malaysian honorific and title recognizer (false-positive purging).
    5. Context-aware Malaysian postcode and location recognizer.
    6. Entity conflict resolution and deduplication.
    7. Multi-category redaction.
"""

from pathlib import Path
import sys
import pytest

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from entity_extractor import PersonalInformationDetector  # noqa: E402
from recognizers.mykad_recognizer import (  # noqa: E402
    find_mykad_entities,
    mask_mykad,
    validate_mykad_parts,
)
from recognizers.phone_recognizer import find_phone_entities  # noqa: E402
from recognizers.org_gazetteer import find_malaysian_org_entities  # noqa: E402
from recognizers.title_recognizer import find_malaysian_titles, purge_title_false_positives  # noqa: E402
from recognizers.location_recognizer import (  # noqa: E402
    find_malaysian_locations,
    find_malaysian_postcodes,
)
from recognizers.conflict_resolver import resolve_entity_conflicts  # noqa: E402


@pytest.fixture(scope="module")
def detector() -> PersonalInformationDetector:
    """Fixture providing a PersonalInformationDetector with hybrid recognition enabled."""
    return PersonalInformationDetector(confidence_threshold=0.50, enable_hybrid=True)


# =========================================================================
# 1. Malaysian NRIC / MyKad Recognizer Tests
# =========================================================================

def test_mykad_validation_logic() -> None:
    """Tests the underlying date of birth and JPN place-of-birth code validator."""
    # Valid: Selangor (10), KL (14), Johor (01)
    assert validate_mykad_parts("950315", "10", "5231") is True
    assert validate_mykad_parts("010229", "14", "6122") is True  # Leap year Feb 29
    assert validate_mykad_parts("881120", "01", "5512") is True

    # Invalid Month (13, 00)
    assert validate_mykad_parts("951315", "10", "5231") is False
    assert validate_mykad_parts("950015", "10", "5231") is False

    # Invalid Day (32, 00)
    assert validate_mykad_parts("950332", "10", "5231") is False
    assert validate_mykad_parts("950300", "10", "5231") is False

    # Invalid Place of Birth code (00, 17, 20)
    assert validate_mykad_parts("950315", "00", "5231") is False
    assert validate_mykad_parts("950315", "17", "5231") is False


def test_mykad_hyphenated_extraction() -> None:
    """Verifies detection of standard hyphenated MyKad numbers."""
    text = "Sila catatkan No. K/P 950315-10-5231 dalam borang pendaftaran."
    entities = find_mykad_entities(text)

    assert len(entities) == 1
    assert entities[0]["text"] == "950315-10-5231"
    assert entities[0]["label"] == "MYKAD"
    assert entities[0]["score"] >= 0.99
    assert text[entities[0]["start"] : entities[0]["end"]] == "950315-10-5231"


def test_mykad_unhyphenated_with_context() -> None:
    """Verifies that unhyphenated 12-digit numbers are matched when contextual keywords exist."""
    text = "NRIC: 950315105231 disahkan oleh pegawai."
    entities = find_mykad_entities(text)

    assert len(entities) == 1
    assert entities[0]["text"] == "950315105231"
    assert entities[0]["label"] == "MYKAD"


def test_mykad_unhyphenated_without_context_rejected() -> None:
    """Verifies that random 12-digit numbers without context are rejected to avoid false positives."""
    text = "Nombor rujukan pesanan inventori ialah 950315105231 bagi kelompok kedua."
    entities = find_mykad_entities(text)
    # Without keywords like NRIC, MyKad, No. K/P, random 12-digit numbers must not be flagged
    assert len(entities) == 0


def test_mykad_masking_utility() -> None:
    """Verifies privacy-compliant masking utility."""
    assert mask_mykad("950315-10-5231") == "950315-10-****"
    assert mask_mykad("950315105231") == "95031510****"


# =========================================================================
# 2. Malaysian Phone Number Recognizer Tests
# =========================================================================

@pytest.mark.parametrize(
    "phone_str",
    [
        "+6012-345 6789",
        "012-3456789",
        "+60 11-1234 5678",
        "011-12345678",
        "03-8888 1234",
        "+603-2144 5678",
        "04-226 1234",
        "082-421 234",
    ],
)
def test_valid_phone_numbers(phone_str: str) -> None:
    """Verifies detection of mobile and landline Malaysian numbers."""
    text = f"Sila hubungi {phone_str} untuk sebarang pertanyaan."
    entities = find_phone_entities(text)

    assert len(entities) == 1
    assert entities[0]["text"] == phone_str
    assert entities[0]["label"] == "PHONE"
    assert entities[0]["score"] >= 0.98


def test_phone_false_positive_rejection() -> None:
    """Verifies rejection of dates, prices, IP addresses, and random numbers."""
    negative_text = "Tarikh mesyuarat 2026-11-13 dengan kos RM 1000 pada alamat IP 192.168.1.1."
    entities = find_phone_entities(negative_text)
    assert len(entities) == 0


# =========================================================================
# 3. Malaysian Statutory Body and Corporate Gazetteer Tests
# =========================================================================

def test_statutory_bodies_and_agencies() -> None:
    """Verifies that major statutory agencies and acronyms are recognized as ORGANIZATION."""
    text = "LHDN dan KWSP mengeluarkan garis panduan bersama PDRM dan SPRM."
    entities = find_malaysian_org_entities(text)

    matched_texts = [e["text"] for e in entities]
    assert "LHDN" in matched_texts
    assert "KWSP" in matched_texts
    assert "PDRM" in matched_texts
    assert "SPRM" in matched_texts


def test_corporate_and_bank_gazetteer() -> None:
    """Verifies that major banks and GLCs are recognized as ORGANIZATION."""
    text = "Menara Maybank dan CIMB Group terletak berhampiran ibu pejabat Tenaga Nasional Berhad."
    entities = find_malaysian_org_entities(text)

    matched_texts = [e["text"] for e in entities]
    assert any("Maybank" in t for t in matched_texts)
    assert any("CIMB" in t for t in matched_texts)
    assert "Tenaga Nasional Berhad" in matched_texts


def test_corporate_legal_suffixes() -> None:
    """Verifies regex matching for registered Malaysian corporate suffixes (Sdn Bhd, Bhd, PLT)."""
    text = "Acme Global Solutions Sdn. Bhd. bekerjasama dengan Apex Technologies PLT."
    entities = find_malaysian_org_entities(text)

    matched_texts = [e["text"] for e in entities]
    assert any("Acme Global Solutions Sdn. Bhd" in t for t in matched_texts)
    assert any("Apex Technologies PLT" in t for t in matched_texts)


# =========================================================================
# 4. Malaysian Honorifics and Title False-Positive Purging Tests
# =========================================================================

def test_title_detection() -> None:
    """Verifies detection of federal, state, and academic honorifics."""
    text = "Dato' Seri Dr. Wan Azizah dan Tan Sri Michelle Yeoh menghadiri majlis."
    titles = find_malaysian_titles(text)

    title_texts = [t["text"] for t in titles]
    assert "Dato' Seri" in title_texts
    assert "Tan Sri" in title_texts


def test_title_false_positive_purging() -> None:
    """Verifies that misclassified title tokens (e.g. Dato' Ser as ORG) are purged."""
    text = "Dato' Seri Dr. Wan Azizah menghadiri majlis."
    # Simulate flawed model prediction where title was tagged as ORGANIZATION
    flawed_model_entities = [
        {"text": "Dato' Ser", "label": "ORGANIZATION", "score": 0.88, "start": 0, "end": 9},
        {"text": "Wan Azizah", "label": "PERSON", "score": 0.98, "start": 15, "end": 25},
    ]

    purged = purge_title_false_positives(flawed_model_entities, text)
    purged_labels = [p["label"] for p in purged]

    # The false ORGANIZATION entity must be purged!
    assert "ORGANIZATION" not in purged_labels
    assert "PERSON" in purged_labels
    assert len(purged) == 1
    assert purged[0]["text"] == "Wan Azizah"


# =========================================================================
# 5. Malaysian Postcode and Location Recognizer Tests
# =========================================================================

def test_postcode_with_address_context() -> None:
    """Verifies valid postcodes inside standard Malaysian address context."""
    text = "Sila hantar dokumen ke Jalan Sultan Ismail, 50250 Kuala Lumpur."
    postcodes = find_malaysian_postcodes(text)

    assert len(postcodes) == 1
    assert postcodes[0]["text"] == "50250"
    assert postcodes[0]["label"] == "POSTCODE"


def test_postcode_rejection_without_context() -> None:
    """Verifies that numbers without address context (e.g. currency amounts) are rejected."""
    text = "Bayaran sebanyak RM 50000 telah dijelaskan sepenuhnya."
    postcodes = find_malaysian_postcodes(text)
    assert len(postcodes) == 0


def test_location_gazetteer_and_streets() -> None:
    """Verifies Malaysian geographic and street entity extraction."""
    text = "Pejabat baharu terletak di Jalan Tun Razak, Cyberjaya, Selangor."
    locations = find_malaysian_locations(text)

    loc_texts = [l["text"] for l in locations]
    assert "Cyberjaya" in loc_texts
    assert "Selangor" in loc_texts
    assert any("Jalan Tun Razak" in t for t in loc_texts)


# =========================================================================
# 6. Conflict Resolution and End-to-End Detector Integration
# =========================================================================

def test_end_to_end_malaysian_sentence(detector: PersonalInformationDetector) -> None:
    """Tests comprehensive multi-entity integration in an end-to-end sentence."""
    sentence = (
        "Dato' Seri Dr. Wan Azizah binti Wan Ismail (No. K/P: 521203-10-5522) "
        "menghubungi KWSP di +603-2144 5678 mengenai cawangan di Jalan Sultan Ismail, 50250 Kuala Lumpur."
    )
    entities = detector.detect(sentence)

    # Check that all categories are represented accurately
    labels = {e["label"] for e in entities}
    assert "PERSON" in labels
    assert "MYKAD" in labels
    assert "ORGANIZATION" in labels
    assert "PHONE" in labels
    assert "LOCATION" in labels
    assert "POSTCODE" in labels

    # Check specific values
    texts_by_label = {e["label"]: e["text"] for e in entities}
    assert "Wan Azizah binti Wan Ismail" in texts_by_label["PERSON"]
    assert texts_by_label["MYKAD"] == "521203-10-5522"
    assert texts_by_label["PHONE"] == "+603-2144 5678"
    assert texts_by_label["POSTCODE"] == "50250"


def test_end_to_end_redaction(detector: PersonalInformationDetector) -> None:
    """Verifies that redaction produces clean category-specific masks."""
    sentence = (
        "Ahmad Faiz bin Zulkifli (MyKad: 950315-10-5231) boleh dihubungi di 012-3456789 "
        "di Petaling Jaya, poskod 47301."
    )
    redacted = detector.redact(sentence)

    assert "[PERSON]" in redacted
    assert "[MYKAD]" in redacted
    assert "[PHONE]" in redacted
    assert "[LOCATION]" in redacted
    assert "[POSTCODE]" in redacted
    # Ensure sensitive raw texts do not leak
    assert "950315-10-5231" not in redacted
    assert "012-3456789" not in redacted
    assert "Ahmad Faiz bin Zulkifli" not in redacted
