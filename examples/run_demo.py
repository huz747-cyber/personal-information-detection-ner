"""
Demonstration script showing the Personal Information Detection prototype in action.

Reads sample test cases from `examples/sample_texts.json` and displays both
entity extraction (PERSON, ORGANIZATION, LOCATION) and automated PII redaction.
"""

import json
from pathlib import Path
import sys

# Add src directory to path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from entity_extractor import PersonalInformationDetector  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("PERSONAL INFORMATION DETECTION (NER) - DEMO")
    print("=" * 70)

    # Initialize the prototype detector
    detector = PersonalInformationDetector(confidence_threshold=0.50)

    # Load curated sample texts
    samples_path = Path(__file__).resolve().parent / "sample_texts.json"
    with open(samples_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    for i, item in enumerate(samples, 1):
        category = item["category"]
        text = item["text"]

        print(f"\n[Case {i}: {category}]")
        entities = detector.detect(text)
        print(detector.format_report(text, entities))

        redacted = detector.redact(text)
        print(f"Redacted Text: \"{redacted}\"")
        print()


if __name__ == "__main__":
    main()
