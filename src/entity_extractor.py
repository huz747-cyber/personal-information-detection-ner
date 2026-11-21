"""
Personal Information Detection via Named Entity Recognition (NER).

This module wraps a pretrained DistilBERT token classification model
to identify sensitive entities such as PERSON, ORGANIZATION, and LOCATION
within arbitrary text.

Author: AI/ML Club
"""

from typing import Any, Dict, List, Optional
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

try:
    from patronymic_stitcher import stitch_patronymic_entities
except ImportError:
    from src.patronymic_stitcher import stitch_patronymic_entities

try:
    from recognizers import (
        find_mykad_entities,
        find_phone_entities,
        find_malaysian_org_entities,
        find_malaysian_postcodes,
        find_malaysian_locations,
        resolve_entity_conflicts,
    )
except ImportError:
    from src.recognizers import (
        find_mykad_entities,
        find_phone_entities,
        find_malaysian_org_entities,
        find_malaysian_postcodes,
        find_malaysian_locations,
        resolve_entity_conflicts,
    )


# Label normalization map: maps raw model entity labels to standardized, readable names.
DEFAULT_LABEL_MAP: Dict[str, str] = {
    "PER": "PERSON",
    "ORG": "ORGANIZATION",
    "LOC": "LOCATION",
    "PERSON": "PERSON",
    "ORGANIZATION": "ORGANIZATION",
    "LOCATION": "LOCATION",
    "MYKAD": "MYKAD",
    "PHONE": "PHONE",
    "POSTCODE": "POSTCODE",
}

# The target entity types for personal information detection
TARGET_ENTITIES = {"PERSON", "ORGANIZATION", "LOCATION", "MYKAD", "PHONE", "POSTCODE"}


class PersonalInformationDetector:
    """Detects personal information (PERSON, ORGANIZATION, LOCATION) in text using NER.

    Attributes:
        model_name: Hugging Face model identifier (default: 'dslim/distilbert-NER').
        device: Computation device (-1 for CPU, >=0 for CUDA GPU).
        pipeline: Hugging Face token-classification pipeline with subword aggregation.
    """

    def __init__(
        self,
        model_name: str = "dslim/distilbert-NER",
        device: Optional[int] = None,
        confidence_threshold: float = 0.50,
        enable_patronymic_stitching: bool = True,
        enable_hybrid: bool = True,
        include_structured_pii: bool = True,
        confidence_thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initializes the tokenizer, model, and inference pipeline.

        Args:
            model_name: Pretrained model repository ID on Hugging Face Hub.
            device: 0 for GPU if CUDA is available, or -1 for CPU. If None,
                auto-detects CUDA availability.
            confidence_threshold: Minimum prediction probability (0.0 to 1.0)
                to accept an entity.
            enable_patronymic_stitching: Whether to post-process and stitch
                Malaysian patronymic names (bin, binti, bt., a/l, a/p, s/o, d/o).
            enable_hybrid: Whether to run Tier 1 deterministic recognizers,
                gazetteers, and conflict resolution alongside the model.
            include_structured_pii: Whether to detect structured identifiers
                (MYKAD, PHONE, POSTCODE) in addition to PERSON, ORGANIZATION, LOCATION.
            confidence_thresholds: Optional per-category calibrated thresholds for
                dynamic arbitration (Phase 6).
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.enable_patronymic_stitching = enable_patronymic_stitching
        self.enable_hybrid = enable_hybrid
        self.include_structured_pii = include_structured_pii
        self.confidence_thresholds = confidence_thresholds

        # Auto-detect CUDA if device not explicitly specified
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = device

        print(f"[*] Loading NER model '{model_name}' on {'GPU' if self.device >= 0 else 'CPU'}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)

        # aggregation_strategy="simple" merges B- and I- subword tokens into
        # whole-word/multi-word entities with character start/end offsets.
        self.pipeline = pipeline(
            task="token-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            device=self.device,
        )
        print("[+] Model loaded successfully.")

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Extracts PERSON, ORGANIZATION, and LOCATION entities from the provided text.

        Args:
            text: Input string to analyze.

        Returns:
            A list of dictionary objects, each representing a detected entity:
            [
                {
                    "text": "Alice Smith",
                    "label": "PERSON",
                    "score": 0.998,
                    "start": 0,
                    "end": 11
                },
                ...
            ]
        """
        if not text or not text.strip():
            return []

        raw_entities = self.pipeline(text)
        detected_entities: List[Dict[str, Any]] = []

        for item in raw_entities:
            # Map raw label (e.g. 'PER') to standard label ('PERSON')
            raw_label = item.get("entity_group", item.get("entity", "")).upper()
            standard_label = DEFAULT_LABEL_MAP.get(raw_label, raw_label)

            # Filter only for target entities (PERSON, ORGANIZATION, LOCATION)
            if standard_label not in TARGET_ENTITIES:
                continue

            score = float(item.get("score", 0.0))
            if score < self.confidence_threshold:
                continue

            entity_text = item.get("word", "").strip()
            # Clean up potential leading subword punctuation or whitespace
            if entity_text.startswith("##"):
                entity_text = entity_text[2:]

            detected_entities.append(
                {
                    "text": entity_text,
                    "label": standard_label,
                    "score": round(score, 4),
                    "start": int(item.get("start", 0)),
                    "end": int(item.get("end", 0)),
                }
            )

        # Merge contiguous/adjacent sub-tokens of the same entity label
        # (e.g. WordPiece splits like 'Satya' -> 'Sa' + 'ty' + 'a' or 'Aris' -> 'Ari' + 's')
        merged_entities: List[Dict[str, Any]] = []
        for ent in detected_entities:
            if not merged_entities:
                merged_entities.append(dict(ent))
                continue

            prev = merged_entities[-1]
            between_text = text[prev["end"] : ent["start"]]
            if prev["label"] == ent["label"] and (ent["start"] <= prev["end"] or between_text in {"", " ", "-"}):
                prev["end"] = ent["end"]
                prev["text"] = text[prev["start"] : ent["end"]].strip()
                # Conservative non-inflation: joint entity confidence never exceeds constituent scores
                prev["score"] = round(min(prev["score"], ent["score"]), 4)
            else:
                merged_entities.append(dict(ent))

        # Consolidate Malaysian patronymic spans (e.g. 'Kavitha a/p Subramaniam')
        if self.enable_patronymic_stitching:
            merged_entities = stitch_patronymic_entities(merged_entities, text)

        # If hybrid mode is disabled, return raw model + stitched entities
        if not self.enable_hybrid:
            return merged_entities

        # Tier 1 Recognizers & Gazetteers
        rule_entities: List[Dict[str, Any]] = []

        # Structured PII Recognizers (MYKAD, PHONE, POSTCODE)
        if self.include_structured_pii:
            rule_entities.extend(find_mykad_entities(text))
            rule_entities.extend(find_phone_entities(text))
            rule_entities.extend(find_malaysian_postcodes(text))

        # Malaysian Organization and Location Gazetteers
        rule_entities.extend(find_malaysian_org_entities(text))
        rule_entities.extend(find_malaysian_locations(text))

        # Conflict resolution, title false-positive purging, and deduplication
        final_entities = resolve_entity_conflicts(
            merged_entities,
            rule_entities,
            text,
            thresholds=self.confidence_thresholds,
        )

        return final_entities

    def redact(self, text: str, placeholder_format: str = "[{label}]") -> str:
        """Replaces detected sensitive entities in text with redaction placeholders.

        Args:
            text: Original text string containing sensitive personal info.
            placeholder_format: Template for replacement, e.g. '[{label}]' -> '[PERSON]'.

        Returns:
            Redacted string with sensitive entities replaced.
        """
        entities = self.detect(text)
        if not entities:
            return text

        # Sort entities by start position in reverse order so replacement offsets
        # do not invalidate earlier spans.
        sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)

        redacted_chars = list(text)
        for ent in sorted_entities:
            start, end = ent["start"], ent["end"]
            replacement = placeholder_format.format(label=ent["label"])
            redacted_chars[start:end] = list(replacement)

        return "".join(redacted_chars)

    def format_report(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """Formats the detection results into an easy-to-read summary table.

        Args:
            text: The original analyzed sentence.
            entities: Output from `detect()`.

        Returns:
            Human-readable formatted string.
        """
        lines = [
            f"Input Text: \"{text}\"",
            "-" * 70,
            f"{'Entity':<25} | {'Type':<15} | {'Confidence':<10} | {'Offsets':<10}",
            "-" * 70,
        ]

        if not entities:
            lines.append("  (No PERSON, ORGANIZATION, or LOCATION entities detected)")
        else:
            for ent in entities:
                span_str = f"{ent['start']}:{ent['end']}"
                conf_str = f"{ent['score'] * 100:.1f}%"
                lines.append(f"{ent['text']:<25} | {ent['label']:<15} | {conf_str:<10} | {span_str:<10}")

        lines.append("-" * 70)
        return "\n".join(lines)
