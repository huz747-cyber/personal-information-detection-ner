"""
Dataset tools package for Malaysian NER and structured PII.

Provides:
- Doccano adapter (import, export, BIO conversion)
- Dataset validator (BIO syntax, offsets, duplicates, leakage, class distribution, privacy, hard negatives)
- Document-grouped stratified dataset splitter
- Privacy screener (Luhn check, credential detection, live phone/MyKad detection)
- Deduplication and near-duplicate detection
- Provenance and licensing auditor
- Inter-annotator agreement and double-annotation quality control
"""

from .agreement import (
    AnnotationAgreementCalculator,
    AgreementReport,
    DisagreementCase,
    adjudicate_disagreement,
)
from .deduplicator import DatasetDeduplicator, DuplicateCluster
from .doccano_adapter import (
    bio_to_spans,
    export_to_doccano,
    import_from_doccano,
    text_to_bio,
    tokenize_with_offsets,
)
from .privacy_screener import PrivacyScreener, PrivacyViolation
from .provenance import ProvenanceAuditor, ProvenanceAuditReport, SourceRecord
from .splitter import DatasetSplitter
from .validator import DatasetValidator, ValidationIssue, ValidationReport

__all__ = [
    "export_to_doccano",
    "import_from_doccano",
    "text_to_bio",
    "bio_to_spans",
    "tokenize_with_offsets",
    "DatasetValidator",
    "ValidationReport",
    "ValidationIssue",
    "DatasetSplitter",
    "PrivacyScreener",
    "PrivacyViolation",
    "DatasetDeduplicator",
    "DuplicateCluster",
    "ProvenanceAuditor",
    "ProvenanceAuditReport",
    "SourceRecord",
    "AnnotationAgreementCalculator",
    "AgreementReport",
    "DisagreementCase",
    "adjudicate_disagreement",
]
