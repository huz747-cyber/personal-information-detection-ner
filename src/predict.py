"""
Inference script for Personal Information Detection using Pretrained DistilBERT.

Usage Examples:
    # 1. Run the built-in sample tests:
    python src/predict.py

    # 2. Run inference on custom text via CLI:
    python src/predict.py --text "Dr. Sarah Connor met with Cyberdyne Systems in Los Angeles."

    # 3. Redact sensitive entities from text:
    python src/predict.py --text "Jane Doe moved to Chicago to join Microsoft." --redact

    # 4. Interactive mode:
    python src/predict.py --interactive
"""

import argparse
import sys
from typing import List

# Allow direct script execution from repository root or src folder
try:
    from entity_extractor import PersonalInformationDetector
except ImportError:
    from src.entity_extractor import PersonalInformationDetector


# Representative test sentences covering Western and Malaysian contexts (synthetic identities)
SAMPLE_SENTENCES: List[str] = [
    "Dr. Aris Thorne visited the World Health Organization headquarters in Geneva.",
    "Elena Rostova accepted a software engineering role at Google in Zurich.",
    "Kavitha a/p Subramaniam attended the technical symposium at Universiti Malaya in Kuala Lumpur.",
    "Ahmad Faiz bin Zulkifli (No. K/P: 950315-10-5231) submitted the compliance report to LHDN in Putrajaya.",
    "Nurul Huda bt. Razali partnered with Ravi a/l Chandran on the Cyberjaya smart city initiative.",
    "Siti Hajar binti Osman can be contacted at +6012-345 6789 or at Jalan Sultan Ismail, 50250 Kuala Lumpur.",
    "Dato' Seri Dr. Wan Azizah binti Wan Ismail visited Hospital Kuala Lumpur.",
    "Alice and Bob met at Central Park in New York to discuss their startup, Acme AI Corp.",
    "Dinesh s/o Anand met Priya d/o Mohan in George Town, Penang.",
    "Yesterday, Johnathan Myers flew from Tokyo to London for the United Nations summit.",
]


def run_benchmark_tests(detector: PersonalInformationDetector) -> None:
    """Executes prediction across curated sample sentences to verify detection."""
    print("\n" + "=" * 70)
    print("RUNNING PROTOTYPE PREDICTION ON SAMPLE SENTENCES")
    print("=" * 70 + "\n")

    for i, sentence in enumerate(SAMPLE_SENTENCES, 1):
        print(f"[Test Case #{i}]")
        entities = detector.detect(sentence)
        report = detector.format_report(sentence, entities)
        print(report)

        # Also demonstrate redaction
        redacted = detector.redact(sentence)
        print(f"Redacted version: \"{redacted}\"\n")


def run_interactive_mode(detector: PersonalInformationDetector) -> None:
    """Runs a read-eval-print loop for users to test their own sentences."""
    print("\n" + "=" * 70)
    print("INTERACTIVE NER DETECTION MODE (type 'exit' or 'quit' to stop)")
    print("=" * 70 + "\n")

    while True:
        try:
            user_input = input("Enter text to analyze > ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "q"}:
                print("Exiting interactive mode.")
                break

            entities = detector.detect(user_input)
            print()
            print(detector.format_report(user_input, entities))
            print(f"Redacted text: \"{detector.redact(user_input)}\"\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive mode.")
            break


def main() -> None:
    """Entrypoint parsing CLI arguments and executing inference."""
    parser = argparse.ArgumentParser(
        description="Detect Personal Information (PERSON, ORGANIZATION, LOCATION) using DistilBERT NER."
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Input text string to analyze for sensitive entities.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a text file containing sentences to analyze.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Confidence score threshold for entity detection (default: 0.50).",
    )
    parser.add_argument(
        "--redact",
        action="store_true",
        help="If set, outputs the text with detected entities redacted.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch an interactive terminal session.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="dslim/distilbert-NER",
        help="Hugging Face model repository ID (default: 'dslim/distilbert-NER').",
    )
    parser.add_argument(
        "--no-stitching",
        action="store_true",
        help="Disable Malaysian patronymic span stitching (runs baseline model output).",
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable Tier 1 deterministic recognizers and gazetteers (runs neural model only).",
    )
    parser.add_argument(
        "--no-structured-pii",
        action="store_true",
        help="Exclude structured PII categories (MYKAD, PHONE, POSTCODE) from detection.",
    )

    args = parser.parse_args()

    # Initialize the detector
    detector = PersonalInformationDetector(
        model_name=args.model,
        confidence_threshold=args.threshold,
        enable_patronymic_stitching=not args.no_stitching,
        enable_hybrid=not args.no_hybrid,
        include_structured_pii=not args.no_structured_pii,
    )

    # 1. Interactive session
    if args.interactive:
        run_interactive_mode(detector)
        return

    # 2. File input
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
            sys.exit(1)

        print(f"\nAnalyzing {len(lines)} sentence(s) from '{args.file}':\n")
        for sentence in lines:
            entities = detector.detect(sentence)
            print(detector.format_report(sentence, entities))
            if args.redact:
                print(f"Redacted: \"{detector.redact(sentence)}\"")
            print()
        return

    # 3. Direct text argument
    if args.text:
        entities = detector.detect(args.text)
        print()
        print(detector.format_report(args.text, entities))
        if args.redact:
            print(f"Redacted: \"{detector.redact(args.text)}\"")
        print()
        return

    # 4. Default: run built-in test sentences
    run_benchmark_tests(detector)


if __name__ == "__main__":
    main()
