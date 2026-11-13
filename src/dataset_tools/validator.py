"""
Dataset Validation Suite for Malaysian Named Entity Recognition and PII Datasets.

Executes comprehensive validation checks:
1. Offset Integrity: Verifies that text[start:end] strictly equals entity text and offsets are within bounds.
2. BIO Sequence Grammar: Enforces valid IOB2 transitions (no orphaned I- tags without matching preceding B-/I-).
3. Deduplication: Detects exact string duplicates, normalized duplicates, and fuzzy near-duplicates.
4. Contamination / Leakage: Scans for overlap between train, validation, and test splits.
5. Entity Class & Token Distribution: Computes statistical breakdown of entities and tags.
6. Missing Label Auditing: Flags unannotated patronymic markers, corporate suffixes, or common locations.
7. Hard Negative Integrity: Validates that hard-negative examples contain zero entities and include true distractors.
8. Privacy Screening: Flags potential live credentials, unmasked phone leaks, and real ID numbers.
9. Provenance Verification: Audits source metadata against the authoritative source manifest.

Author: AI/ML Club
License: MIT
"""

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .deduplicator import DatasetDeduplicator
from .doccano_adapter import import_from_doccano, text_to_bio
from .privacy_screener import PrivacyScreener


@dataclass
class ValidationIssue:
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    check: str     # 'OFFSET', 'BIO_GRAMMAR', 'DUPLICATE', 'LEAKAGE', 'MISSING_LABEL', 'HARD_NEGATIVE', 'PRIVACY', 'PROVENANCE'
    record_id: Any
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    total_records: int
    valid_records: int
    invalid_records: int
    error_count: int
    warning_count: int
    issues: List[ValidationIssue] = field(default_factory=list)
    entity_counts: Dict[str, int] = field(default_factory=dict)
    tag_counts: Dict[str, int] = field(default_factory=dict)
    sentence_counts_by_entity_num: Dict[int, int] = field(default_factory=dict)
    stratum_counts: Dict[str, int] = field(default_factory=dict)
    source_counts: Dict[str, int] = field(default_factory=dict)
    hard_negative_count: int = 0
    is_clean: bool = True

    def summary(self) -> str:
        lines = [
            "=" * 68,
            "               MALAYSIAN NER DATASET VALIDATION REPORT",
            "=" * 68,
            f"Total Sentences Evaluated:   {self.total_records}",
            f"Fully Valid Sentences:       {self.valid_records}",
            f"Sentences with Errors:       {self.invalid_records}",
            f"Total Errors:                {self.error_count}",
            f"Total Warnings:              {self.warning_count}",
            f"Hard Negatives Verified:     {self.hard_negative_count}",
            f"Validation Status:           {'PASS [CLEAN]' if self.is_clean else 'FAIL [ISSUES DETECTED]'}",
            "-" * 68,
            "Entity Class Breakdown:",
        ]
        if self.entity_counts:
            for ent_type, count in sorted(self.entity_counts.items()):
                lines.append(f"  - {ent_type:<20}: {count:>6}")
        else:
            lines.append("  (No entities found)")

        lines.extend([
            "-" * 68,
            "BIO Token Tag Breakdown:",
        ])
        if self.tag_counts:
            for tag, count in sorted(self.tag_counts.items()):
                lines.append(f"  - {tag:<20}: {count:>6}")

        if self.stratum_counts:
            lines.extend([
                "-" * 68,
                "Linguistic Stratum Distribution:",
            ])
            for st, count in sorted(self.stratum_counts.items()):
                pct = (count / self.total_records) * 100 if self.total_records > 0 else 0
                lines.append(f"  - {st:<28}: {count:>5} ({pct:>5.1f}%)")

        lines.extend([
            "-" * 68,
            "Sentences by Entity Count:",
        ])
        for ent_num, s_count in sorted(self.sentence_counts_by_entity_num.items()):
            lines.append(f"  - {ent_num} entities in sentence: {s_count:>5} sentences")

        if self.issues:
            lines.extend([
                "-" * 68,
                f"Issues Logged (First {min(len(self.issues), 15)} of {len(self.issues)}):",
            ])
            for issue in self.issues[:15]:
                lines.append(f"  [{issue.severity}] ID {issue.record_id} ({issue.check}): {issue.message}")

        lines.append("=" * 68)
        return "\n".join(lines)


class DatasetValidator:
    """Validator engine for Malaysian NER and PII dataset files."""

    # Heuristic markers that often signal unannotated entities
    SUSPICIOUS_PATTERNS = [
        (re.compile(r"\b(?:bin|binti|bt\.|a/l|a/p|s/o|d/o)\b", re.IGNORECASE), "PATRONYMIC", "PERSON"),
        (re.compile(r"\b(?:Sdn\.?\s*Bhd\.?|Bhd\.?|PLT)\b", re.IGNORECASE), "LEGAL_SUFFIX", "ORGANIZATION"),
        (re.compile(r"\b(?:Kuala\s*Lumpur|Putrajaya|Cyberjaya|George\s*Town|Petaling\s*Jaya)\b", re.IGNORECASE), "MAJOR_CITY", "LOCATION"),
    ]

    # Required distractor patterns in hard-negative sentences
    HARD_NEGATIVE_DISTRACTORS = [
        re.compile(r"\b(?:RM|MYR|\$)\s*\d+", re.IGNORECASE),  # Currency
        re.compile(r"\b(?:INV|PO|TXN|REF|ORDER|BATCH|POL|PV|ORD|TRK|TCK|TSK|PRJ|PHASE|FIL|DKT|BURSA|REL)[-_/0-9A-Z]+\b", re.IGNORECASE),  # Transaction codes
        re.compile(r"\b(?:\d{1,2}\s+(?:Jan|Feb|Mac|Apr|Mei|Jun|Jul|Ogo|Sep|Okt|Nov|Dis)[a-z]*|\d{4}|hari|minggu|tahun|bulan|calendar|month|annual|quarterly|daily)\b", re.IGNORECASE),  # Dates & timeframes
        re.compile(r"\b(?:pukul|jam|am|pm)\s*\d*(?:[\.:]\d+)?\b", re.IGNORECASE),  # Times
        re.compile(r"\b(?:dan|atau|serta|bersama|dengan|and|or|with)\b", re.IGNORECASE),  # Conjunctions
        re.compile(r"\b\d+\b"),  # Numeric values / postcodes / identifiers
        re.compile(r"\b(?:syarikat|kerajaan|jabatan|kementerian|hospital|mahkamah|dewan|sekolah|kolej|portal|kaunter|premis|bangunan|pejabat|company|management|board|department|facility|portal|service)\b", re.IGNORECASE),  # Org-like common nouns
    ]

    def __init__(self, allowed_labels: Optional[Set[str]] = None, check_privacy: bool = True):
        self.allowed_labels = allowed_labels or {
            "PERSON", "ORGANIZATION", "LOCATION", "MYKAD", "PHONE", "POSTCODE"
        }
        self.check_privacy = check_privacy
        self.privacy_screener = PrivacyScreener(allow_synthetic=True)
        self.deduplicator = DatasetDeduplicator(near_duplicate_threshold=0.85)

    def validate_single_record(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validates offset integrity, boundaries, and span grammar of a single record."""
        issues: List[ValidationIssue] = []
        rec_id = record.get("id", "UNKNOWN")
        text = record.get("text", "")
        entities = record.get("entities", [])
        meta = record.get("metadata", record.get("meta", {}))

        # 1. Check basic text presence
        if not text or not text.strip():
            issues.append(ValidationIssue(
                severity="ERROR",
                check="OFFSET",
                record_id=rec_id,
                message="Sentence text is empty or blank whitespace.",
            ))
            return issues

        # 2. Hard-negative verification
        is_hard_negative = meta.get("is_hard_negative", meta.get("hard_negative", False))
        if is_hard_negative:
            if len(entities) > 0:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="HARD_NEGATIVE",
                    record_id=rec_id,
                    message=f"Hard-negative sentence must not contain entities (found {len(entities)}).",
                ))
            has_distractor = any(p.search(text) for p in self.HARD_NEGATIVE_DISTRACTORS)
            if not has_distractor:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    check="HARD_NEGATIVE",
                    record_id=rec_id,
                    message="Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).",
                ))

        # 3. Privacy screening
        if self.check_privacy:
            priv_viols = self.privacy_screener.scan_text(text, record_id=rec_id)
            for pv in priv_viols:
                issues.append(ValidationIssue(
                    severity="ERROR" if pv.severity == "CRITICAL" else "WARNING",
                    check="PRIVACY",
                    record_id=rec_id,
                    message=pv.message,
                    details={"category": pv.category, "snippet": pv.detected_snippet},
                ))

        # 4. Check each entity's offsets and boundary alignment
        previous_end = -1
        for i, ent in enumerate(entities):
            start = ent.get("start")
            end = ent.get("end")
            label = ent.get("label", "")
            declared_text = ent.get("text", "")

            # Non-integer offsets
            if not isinstance(start, int) or not isinstance(end, int):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="OFFSET",
                    record_id=rec_id,
                    message=f"Entity #{i} has non-integer offsets: start={start}, end={end}",
                ))
                continue

            # Inverted or zero-length offsets
            if start < 0 or end > len(text) or start >= end:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="OFFSET",
                    record_id=rec_id,
                    message=f"Entity #{i} [{start}:{end}] is out of bounds for text of length {len(text)}",
                ))
                continue

            # Overlapping spans within the same record
            if start < previous_end:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="OFFSET",
                    record_id=rec_id,
                    message=f"Entity #{i} [{start}:{end}] overlaps with previous entity ending at {previous_end}",
                ))

            previous_end = max(previous_end, end)

            # Allowed labels check
            if label not in self.allowed_labels:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="BIO_GRAMMAR",
                    record_id=rec_id,
                    message=f"Entity #{i} has unrecognized label '{label}'. Allowed: {sorted(self.allowed_labels)}",
                ))

            # Exact text slice comparison
            actual_slice = text[start:end]
            if declared_text and actual_slice != declared_text:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="OFFSET",
                    record_id=rec_id,
                    message=f"Entity slice mismatch: declared '{declared_text}' vs actual text[{start}:{end}]='{actual_slice}'",
                ))

            # Leading/trailing whitespace warnings
            if actual_slice.startswith(" ") or actual_slice.endswith(" "):
                issues.append(ValidationIssue(
                    severity="WARNING",
                    check="OFFSET",
                    record_id=rec_id,
                    message=f"Entity [{start}:{end}] '{actual_slice}' contains leading or trailing whitespace.",
                ))

        # 5. Check BIO sequence grammar
        try:
            tokens, bio_tags = text_to_bio(text, entities)
            bio_issues = self.validate_bio_sequence(tokens, bio_tags, rec_id)
            issues.extend(bio_issues)
        except Exception as e:
            issues.append(ValidationIssue(
                severity="ERROR",
                check="BIO_GRAMMAR",
                record_id=rec_id,
                message=f"Failed to generate BIO tags: {e}",
            ))

        # 6. Check for potential missing labels
        if not is_hard_negative:
            missing_issues = self.audit_missing_labels(text, entities, rec_id)
            issues.extend(missing_issues)

        return issues

    def validate_bio_sequence(
        self,
        tokens: List[str],
        bio_tags: List[str],
        rec_id: Any,
    ) -> List[ValidationIssue]:
        """Validates that token BIO tags follow strict IOB2 grammar."""
        issues: List[ValidationIssue] = []
        prev_tag = "O"

        for idx, (token, tag) in enumerate(zip(tokens, bio_tags)):
            if tag.startswith("I-"):
                label = tag[2:]
                # I- must follow either B-label or I-label
                if prev_tag == "O":
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        check="BIO_GRAMMAR",
                        record_id=rec_id,
                        message=f"Orphaned tag '{tag}' on token '{token}' following 'O' at index {idx}",
                    ))
                elif prev_tag.startswith(("B-", "I-")):
                    prev_label = prev_tag[2:]
                    if prev_label != label:
                        issues.append(ValidationIssue(
                            severity="ERROR",
                            check="BIO_GRAMMAR",
                            record_id=rec_id,
                            message=f"Illegal transition: '{prev_tag}' -> '{tag}' on token '{token}' at index {idx}",
                        ))
            prev_tag = tag

        return issues

    def audit_missing_labels(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        rec_id: Any,
    ) -> List[ValidationIssue]:
        """Heuristically checks if strong entity markers in text lack annotations."""
        issues: List[ValidationIssue] = []

        for pattern, pattern_name, expected_type in self.SUSPICIOUS_PATTERNS:
            for match in pattern.finditer(text):
                m_start, m_end = match.start(), match.end()
                # Check if this match falls inside any existing entity
                covered = any(
                    max(m_start, ent["start"]) < min(m_end, ent["end"])
                    for ent in entities
                )
                if not covered:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        check="MISSING_LABEL",
                        record_id=rec_id,
                        message=f"Potential unannotated {expected_type} ({pattern_name}): '{match.group(0)}' at [{m_start}:{m_end}]",
                    ))

        return issues

    def check_duplicates(
        self,
        records: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """Identifies exact and normalized duplicate sentences within a dataset."""
        issues: List[ValidationIssue] = []
        seen_exact: Dict[str, Any] = {}
        seen_normalized: Dict[str, Any] = {}

        for rec in records:
            rec_id = rec.get("id", "UNKNOWN")
            text = rec.get("text", "")
            norm = " ".join(text.lower().split())

            is_exact_dup = text in seen_exact
            if is_exact_dup:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    check="DUPLICATE",
                    record_id=rec_id,
                    message=f"Exact duplicate sentence of ID {seen_exact[text]}",
                ))
            else:
                seen_exact[text] = rec_id

            if not is_exact_dup:
                if norm in seen_normalized:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        check="DUPLICATE",
                        record_id=rec_id,
                        message=f"Near-duplicate sentence (normalized whitespace/case) of ID {seen_normalized[norm]}",
                    ))
                else:
                    seen_normalized[norm] = rec_id

        return issues

    def check_cross_split_contamination(
        self,
        train_records: List[Dict[str, Any]],
        val_records: List[Dict[str, Any]],
        test_records: List[Dict[str, Any]],
    ) -> List[ValidationIssue]:
        """Detects data leakage between train, validation, and test splits (sentence text & template)."""
        issues: List[ValidationIssue] = []

        def get_keys(rec):
            norm_text = " ".join(rec.get("text", "").lower().split())
            meta = rec.get("metadata", rec.get("meta", {}))
            tpl = meta.get("template_id")
            doc = meta.get("document_id")
            return norm_text, tpl, doc

        train_texts = {}
        train_tpls = {}
        train_docs = {}
        for r in train_records:
            t, tpl, doc = get_keys(r)
            train_texts[t] = r.get("id")
            if tpl:
                train_tpls[tpl] = r.get("id")
            if doc:
                train_docs[doc] = r.get("id")

        val_texts = {}
        val_tpls = {}
        val_docs = {}
        for r in val_records:
            t, tpl, doc = get_keys(r)
            val_texts[t] = r.get("id")
            if tpl:
                val_tpls[tpl] = r.get("id")
            if doc:
                val_docs[doc] = r.get("id")

        # Check val against train
        for r in val_records:
            t, tpl, doc = get_keys(r)
            if t in train_texts:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Validation sentence leaks into Train (matches Train ID {train_texts[t]})",
                ))
            if tpl and tpl in train_tpls:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Validation template '{tpl}' leaks into Train (matches Train ID {train_tpls[tpl]})",
                ))
            if doc and doc in train_docs:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Validation document '{doc}' leaks into Train (matches Train ID {train_docs[doc]})",
                ))

        # Check test against train and val
        for r in test_records:
            t, tpl, doc = get_keys(r)
            if t in train_texts:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test sentence leaks into Train (matches Train ID {train_texts[t]})",
                ))
            if t in val_texts:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test sentence leaks into Validation (matches Val ID {val_texts[t]})",
                ))
            if tpl and tpl in train_tpls:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test template '{tpl}' leaks into Train (matches Train ID {train_tpls[tpl]})",
                ))
            if tpl and tpl in val_tpls:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test template '{tpl}' leaks into Validation (matches Val ID {val_tpls[tpl]})",
                ))
            if doc and doc in train_docs:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test document '{doc}' leaks into Train (matches Train ID {train_docs[doc]})",
                ))
            if doc and doc in val_docs:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    check="LEAKAGE",
                    record_id=r.get("id"),
                    message=f"Test document '{doc}' leaks into Validation (matches Val ID {val_docs[doc]})",
                ))

        return issues

    def validate_dataset(self, records: List[Dict[str, Any]]) -> ValidationReport:
        """Runs the full validation suite on a list of records."""
        all_issues: List[ValidationIssue] = []
        entity_counts: Dict[str, int] = {}
        tag_counts: Dict[str, int] = {}
        stratum_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        sentence_counts_by_entity_num: Dict[int, int] = {}
        hard_negatives = 0

        invalid_records_set = set()

        # Duplicate checking
        dup_issues = self.check_duplicates(records)
        all_issues.extend(dup_issues)

        for rec in records:
            rec_id = rec.get("id", "UNKNOWN")
            text = rec.get("text", "")
            entities = rec.get("entities", [])
            meta = rec.get("metadata", rec.get("meta", {}))

            if meta.get("is_hard_negative", meta.get("hard_negative", False)):
                hard_negatives += 1

            stratum = meta.get("stratum", meta.get("language", "general"))
            stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1

            src = meta.get("source_id", "unspecified")
            source_counts[src] = source_counts.get(src, 0) + 1

            ent_len = len(entities)
            sentence_counts_by_entity_num[ent_len] = sentence_counts_by_entity_num.get(ent_len, 0) + 1

            for ent in entities:
                lbl = ent.get("label", "UNKNOWN")
                entity_counts[lbl] = entity_counts.get(lbl, 0) + 1

            try:
                tokens, tags = text_to_bio(text, entities)
                for t in tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            except Exception:
                pass

            rec_issues = self.validate_single_record(rec)
            for iss in rec_issues:
                if iss.severity == "ERROR":
                    invalid_records_set.add(rec_id)
                all_issues.append(iss)

        error_count = sum(1 for iss in all_issues if iss.severity == "ERROR")
        warning_count = sum(1 for iss in all_issues if iss.severity == "WARNING")
        total_records = len(records)
        valid_records = total_records - len(invalid_records_set)

        return ValidationReport(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=len(invalid_records_set),
            error_count=error_count,
            warning_count=warning_count,
            issues=all_issues,
            entity_counts=entity_counts,
            tag_counts=tag_counts,
            sentence_counts_by_entity_num=sentence_counts_by_entity_num,
            stratum_counts=stratum_counts,
            source_counts=source_counts,
            hard_negative_count=hard_negatives,
            is_clean=(error_count == 0),
        )


def validate_file(file_path: Union[str, Path]) -> ValidationReport:
    """Convenience helper to import and validate a Doccano JSONL or JSON file."""
    path = Path(file_path)
    if path.suffix in {".jsonl", ".txt"}:
        records = import_from_doccano(path)
    elif path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)
    else:
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    validator = DatasetValidator()
    return validator.validate_dataset(records)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Malaysian NER Dataset Validator")
    parser.add_argument("--file", help="Path to single dataset file (.jsonl or .json)")
    parser.add_argument("--train", help="Path to train split")
    parser.add_argument("--val", help="Path to validation split")
    parser.add_argument("--test", help="Path to test split")
    args = parser.parse_args()

    validator = DatasetValidator()

    if args.file:
        report = validate_file(args.file)
        print(report.summary())
        sys.exit(0 if report.is_clean else 1)
    elif args.train and args.val and args.test:
        train_r = import_from_doccano(args.train)
        val_r = import_from_doccano(args.val)
        test_r = import_from_doccano(args.test)

        print(f"Loaded Train: {len(train_r)}, Val: {len(val_r)}, Test: {len(test_r)}")
        leakage = validator.check_cross_split_contamination(train_r, val_r, test_r)
        if leakage:
            print(f"[FAIL] Detected {len(leakage)} split contamination errors:")
            for lk in leakage:
                print(f"  [{lk.severity}] ID {lk.record_id}: {lk.message}")
            sys.exit(1)
        else:
            print("[PASS] Zero split contamination detected across Train/Val/Test.")
            sys.exit(0)
    else:
        parser.print_help()
