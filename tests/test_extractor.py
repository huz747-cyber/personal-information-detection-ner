"""
Unit tests for the PersonalInformationDetector module.
"""

from pathlib import Path
import sys
import pytest

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from entity_extractor import PersonalInformationDetector  # noqa: E402


@pytest.fixture(scope="module")
def detector() -> PersonalInformationDetector:
    """Fixture providing an initialized detector shared across test methods."""
    return PersonalInformationDetector(confidence_threshold=0.50)


def test_empty_and_whitespace_input(detector: PersonalInformationDetector) -> None:
    """Verifies that empty strings or whitespace return an empty entity list."""
    assert detector.detect("") == []
    assert detector.detect("   ") == []
    assert detector.redact("") == ""


def test_entity_schema(detector: PersonalInformationDetector) -> None:
    """Verifies that returned entities conform to expected dictionary schema."""
    sentence = "Satya Nadella spoke at Microsoft headquarters in Redmond."
    entities = detector.detect(sentence)

    assert len(entities) > 0
    for ent in entities:
        assert "text" in ent and isinstance(ent["text"], str)
        assert "label" in ent and ent["label"] in {"PERSON", "ORGANIZATION", "LOCATION"}
        assert "score" in ent and 0.0 <= ent["score"] <= 1.0
        assert "start" in ent and isinstance(ent["start"], int)
        assert "end" in ent and isinstance(ent["end"], int)
        assert ent["start"] < ent["end"]
        # Verify slice matches the text string
        assert ent["text"] in sentence[ent["start"] : ent["end"]] or sentence[ent["start"] : ent["end"]] in ent["text"]


def test_person_detection(detector: PersonalInformationDetector) -> None:
    """Verifies detection of PERSON entity."""
    sentence = "Barack Obama delivered the keynote address."
    entities = detector.detect(sentence)
    labels = [ent["label"] for ent in entities]
    texts = [ent["text"] for ent in entities]

    assert "PERSON" in labels
    assert any("Obama" in t for t in texts)


def test_organization_detection(detector: PersonalInformationDetector) -> None:
    """Verifies detection of ORGANIZATION entity."""
    sentence = "DeepMind researchers published a paper with Oxford University."
    entities = detector.detect(sentence)
    labels = [ent["label"] for ent in entities]

    assert "ORGANIZATION" in labels


def test_location_detection(detector: PersonalInformationDetector) -> None:
    """Verifies detection of LOCATION entity."""
    sentence = "The team traveled to Tokyo for the robotics exhibition."
    entities = detector.detect(sentence)
    labels = [ent["label"] for ent in entities]
    texts = [ent["text"] for ent in entities]

    assert "LOCATION" in labels
    assert any("Tokyo" in t for t in texts)


def test_redaction(detector: PersonalInformationDetector) -> None:
    """Verifies that sensitive entities are masked in the redacted output."""
    sentence = "Alice visited London to meet with DeepMind."
    redacted = detector.redact(sentence)

    assert "[PERSON]" in redacted or "[LOCATION]" in redacted or "[ORGANIZATION]" in redacted
    assert "Alice" not in redacted or "London" not in redacted
