"""
Unit and regression tests for Malaysian patronymic name entity detection.

Tests the consolidation of Malaysian patronymic structures:
  - 'bin', 'binti', 'bt.', 'bt' (Malay)
  - 'a/l', 'a/p', 's/o', 'd/o' (Indian Malaysian)
"""

from pathlib import Path
import sys
import pytest

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from entity_extractor import PersonalInformationDetector  # noqa: E402
from patronymic_stitcher import is_patronymic_bridge, stitch_patronymic_entities  # noqa: E402


@pytest.fixture(scope="module")
def detector() -> PersonalInformationDetector:
    """Fixture providing an initialized detector with Malaysian patronymic stitching."""
    return PersonalInformationDetector(confidence_threshold=0.50, enable_patronymic_stitching=True)


# =========================================================================
# 1. Direct Unit Tests for Patronymic Boundary Detection
# =========================================================================

@pytest.mark.parametrize(
    "prev, gap, next_tok, expected",
    [
        ("Ahmad Faiz", " bin ", "Zulkifli", True),
        ("Siti Hajar", " binti ", "Osman", True),
        ("Nurul Huda", " bt. ", "Razali", True),
        ("Nurul Huda", " bt ", "Razali", True),
        ("Ravi", " a/l ", "Chandran", True),
        ("Kavitha", " a/p ", "Subramaniam", True),
        ("Dinesh", " s/o ", "Anand", True),
        ("Priya", " d/o ", "Mohan", True),
        # Case insensitivity
        ("MUHAMMAD", " BIN ", "ROSLI", True),
        ("SURESH", " A/L ", "MURUGAN", True),
        ("KAVITHA", " A/P ", "SUBRAMANIAM", True),
        # Tokenizer edge case: connector prefix absorbed into previous token
        ("Kavitha a", "/p ", "Subramaniam", True),
        ("Ravi A", "/L ", "Chandran", True),
        ("Dinesh S", "/O ", "Anand", True),
        ("Priya D", "/O ", "Mohan", True),
        # Negative tests: Conjunctions and common words MUST NOT match
        ("Ali", " dan ", "Abu", False),
        ("Sarah", " and ", "Emily", False),
        ("John", " with ", "Bob", False),
        ("Alice", " , ", "Charlie", False),
        ("Faiz", " - ", "Rosli", False),
    ],
)
def test_patronymic_boundary_logic(prev: str, gap: str, next_tok: str, expected: bool) -> None:
    """Validates boundary rule matching for clean and fractured patronymics."""
    assert is_patronymic_bridge(prev, gap, next_tok) is expected


# =========================================================================
# 2. Integration Tests: Model Inference on Malaysian Patronymic Structures
# =========================================================================

def test_malay_bin_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'bin' compound names are unified into a single PERSON entity."""
    sentence = "Ahmad Faiz bin Zulkifli submitted the quarterly report in Putrajaya."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Ahmad Faiz bin Zulkifli" in person_names
    assert "Ahmad Faiz" not in person_names
    assert "Zulkifli" not in person_names


def test_malay_binti_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'binti' compound names are unified into a single PERSON entity."""
    sentence = "Siti Hajar binti Osman joined the engineering team in Cyberjaya."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Siti Hajar binti Osman" in person_names


def test_malay_bt_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'bt.' abbreviated compound names are unified."""
    sentence = "Nurul Huda bt. Razali finalized the audit in Petaling Jaya."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Nurul Huda bt. Razali" in person_names


def test_indian_al_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'a/l' compound names are unified."""
    sentence = "Ravi a/l Chandran signed the project contract in George Town."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Ravi a/l Chandran" in person_names


def test_indian_ap_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'a/p' compound names are unified."""
    sentence = "Kavitha a/p Subramaniam delivered the keynote at Universiti Malaya."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Kavitha a/p Subramaniam" in person_names


def test_indian_so_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 's/o' compound names are unified."""
    sentence = "Dinesh s/o Anand visited Ipoh for the technical conference."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Dinesh s/o Anand" in person_names


def test_indian_do_stitching(detector: PersonalInformationDetector) -> None:
    """Verifies that 'd/o' compound names are unified."""
    sentence = "Priya d/o Mohan registered the business in Johor Bahru."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Priya d/o Mohan" in person_names


# =========================================================================
# 3. Non-Inflation of Confidence Scores and Offset Verification
# =========================================================================

def test_score_non_inflation(detector: PersonalInformationDetector) -> None:
    """Guarantees merged entity confidence does not exceed constituent component scores."""
    raw_entities = [
        {"text": "Kavitha", "label": "PERSON", "score": 0.9950, "start": 0, "end": 7},
        {"text": "Subramaniam", "label": "PERSON", "score": 0.9620, "start": 12, "end": 23},
    ]
    sentence = "Kavitha a/p Subramaniam"
    stitched = stitch_patronymic_entities(raw_entities, sentence)

    assert len(stitched) == 1
    # Score MUST be min(0.9950, 0.9620) = 0.9620, never inflated to 0.9950
    assert stitched[0]["score"] == 0.9620
    assert stitched[0]["text"] == "Kavitha a/p Subramaniam"
    assert stitched[0]["start"] == 0
    assert stitched[0]["end"] == 23


def test_offset_integrity(detector: PersonalInformationDetector) -> None:
    """Verifies that all entity offsets perfectly match original string slices."""
    sentence = "Ahmad Faiz bin Zulkifli and Kavitha a/p Subramaniam met in Putrajaya."
    entities = detector.detect(sentence)

    for ent in entities:
        slice_text = sentence[ent["start"] : ent["end"]]
        assert ent["text"] == slice_text, f"Offset mismatch: '{ent['text']}' != '{slice_text}'"


# =========================================================================
# 4. Negative Conjunction Tests (Reject False Merging)
# =========================================================================

def test_conjunction_negative_malay(detector: PersonalInformationDetector) -> None:
    """Verifies that Malay conjunction 'dan' between names does NOT trigger a merge."""
    sentence = "Ali dan Abu berjumpa di Kuala Lumpur."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    # Conjunction 'dan' MUST NOT trigger a merge into a single entity
    assert "Ali dan Abu" not in person_names
    assert "Ali" in person_names
    assert "Abu" in person_names


def test_conjunction_negative_english(detector: PersonalInformationDetector) -> None:
    """Verifies that English conjunction 'and' between names does NOT trigger a merge."""
    sentence = "Alice and Bob met at the office in London."
    entities = detector.detect(sentence)

    person_names = [e["text"] for e in entities if e["label"] == "PERSON"]
    assert "Alice and Bob" not in person_names
    assert "Alice" in person_names
    assert "Bob" in person_names


# =========================================================================
# 5. Redaction Test with Malaysian Names
# =========================================================================

def test_malaysian_redaction(detector: PersonalInformationDetector) -> None:
    """Verifies that patronymic names are masked as a unified single token."""
    sentence = "Contact Kavitha a/p Subramaniam regarding the Putrajaya project."
    redacted = detector.redact(sentence)

    # Must redact as "[PERSON]", NOT "[PERSON] a/p [PERSON]"
    assert "[PERSON]" in redacted
    assert "a/p" not in redacted
    assert "Kavitha" not in redacted
    assert "Subramaniam" not in redacted
