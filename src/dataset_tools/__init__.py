"""
Dataset tools package for Malaysian NER and structured PII.

Provides:
- Doccano adapter (import, export, BIO conversion)
- Dataset validator (BIO syntax, offsets, duplicates, leakage, class distribution)
- Reproducible stratified dataset splitter
"""

from .doccano_adapter import (
    bio_to_spans,
    export_to_doccano,
    import_from_doccano,
    text_to_bio,
)
from .validator import DatasetValidator, ValidationReport
from .splitter import DatasetSplitter

__all__ = [
    "export_to_doccano",
    "import_from_doccano",
    "text_to_bio",
    "bio_to_spans",
    "DatasetValidator",
    "ValidationReport",
    "DatasetSplitter",
]
