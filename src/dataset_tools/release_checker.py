"""
Dataset Release and Licensing Eligibility Checker (Phase 2.6.3 Reconciled).

Evaluates dataset sources across 6 independent legal permission dimensions:
1. research_training: Non-commercial academic research and benchmarking.
2. commercial_training: Commercial model training without copyright infringement risk.
3. raw_text_redistribution: Distributing raw sentence text in public releases.
4. derived_annotation_redistribution: Distributing standalone annotation metadata.
5. research_model_weights: Distributing model weights for research purposes.
6. commercial_model_weights: Distributing model weights for commercial deployment.

Each dimension uses strict categorical statuses:
- VERIFIED_ALLOWED: Express legal authority, permissive license, or factual exclusion.
- VERIFIED_RESTRICTED: Explicit license terms restrict this dimension (e.g., non-commercial only).
- UNVERIFIED: Insufficient statutory or contractual evidence; fails closed.
- NOT_APPLICABLE: Dimension does not apply to this asset type.

Enforces fail-closed safeguards: only VERIFIED_ALLOWED records enter release manifests.

Author: AI/ML Club
License: MIT
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Strict permission statuses
VERIFIED_ALLOWED = "VERIFIED_ALLOWED"
VERIFIED_RESTRICTED = "VERIFIED_RESTRICTED"
UNVERIFIED = "UNVERIFIED"
NOT_APPLICABLE = "NOT_APPLICABLE"

VALID_STATUSES = {VERIFIED_ALLOWED, VERIFIED_RESTRICTED, UNVERIFIED, NOT_APPLICABLE}

PERMISSION_DIMENSIONS = [
    "research_training",
    "commercial_training",
    "raw_text_redistribution",
    "derived_annotation_redistribution",
    "research_model_weights",
    "commercial_model_weights",
]


@dataclass
class SourceEligibilityProfile:
    source_id: str
    source_name: str
    licence: str
    research_training: str
    commercial_training: str
    raw_text_redistribution: str
    derived_annotation_redistribution: str
    research_model_weights: str
    commercial_model_weights: str
    rationale: str
    exclusion_reason: Optional[str] = None

    def __post_init__(self):
        for dim in PERMISSION_DIMENSIONS:
            val = getattr(self, dim)
            if val not in VALID_STATUSES:
                raise ValueError(f"Invalid status '{val}' for dimension '{dim}' in source {self.source_id}")

    # Backward compatibility properties
    @property
    def research_use(self) -> bool:
        return self.research_training == VERIFIED_ALLOWED

    @property
    def commercial_training_allowed(self) -> bool:
        return self.commercial_training == VERIFIED_ALLOWED

    @property
    def raw_text_redistribution_allowed(self) -> bool:
        return self.raw_text_redistribution == VERIFIED_ALLOWED

    @property
    def derived_annotation_redistribution_allowed(self) -> bool:
        return self.derived_annotation_redistribution == VERIFIED_ALLOWED

    @property
    def model_weight_distribution(self) -> bool:
        return self.research_model_weights == VERIFIED_ALLOWED


SOURCE_PROFILES: Dict[str, SourceEligibilityProfile] = {
    "SRC-001": SourceEligibilityProfile(
        source_id="SRC-001",
        source_name="Mesolitica Malaya NER Dataset",
        licence="MIT (Repository Code) / News Fair Dealing (Text)",
        research_training=VERIFIED_ALLOWED,
        commercial_training=UNVERIFIED,
        raw_text_redistribution=VERIFIED_RESTRICTED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=UNVERIFIED,
        rationale="Underlying Malay news text belongs to Malaysian publishers. Fair Dealing covers non-profit research, but commercial training and raw text redistribution carry third-party copyright risk.",
        exclusion_reason="Underlying news text lacks express commercial exploitation license.",
    ),
    "SRC-002": SourceEligibilityProfile(
        source_id="SRC-002",
        source_name="WikiANN PAN-X Malay Subset (ms)",
        licence="CC-BY-SA 4.0",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_ALLOWED,
        raw_text_redistribution=VERIFIED_ALLOWED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=VERIFIED_ALLOWED,
        rationale="Permissive under CC-BY-SA 4.0 with attribution and ShareAlike provisions.",
    ),
    "SRC-003": SourceEligibilityProfile(
        source_id="SRC-003",
        source_name="SEACrowd Malay NER Benchmark",
        licence="Apache 2.0",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_ALLOWED,
        raw_text_redistribution=VERIFIED_ALLOWED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=VERIFIED_ALLOWED,
        rationale="Permissive open-source benchmark under Apache 2.0.",
    ),
    "SRC-004": SourceEligibilityProfile(
        source_id="SRC-004",
        source_name="CoNLL-2003 English NER",
        licence="Reuters Open Research License",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_RESTRICTED,
        raw_text_redistribution=VERIFIED_RESTRICTED,
        derived_annotation_redistribution=VERIFIED_RESTRICTED,
        research_model_weights=VERIFIED_RESTRICTED,
        commercial_model_weights=VERIFIED_RESTRICTED,
        rationale="Reuters corpus is strictly limited to non-commercial academic research; commercial training and raw text redistribution are strictly prohibited.",
        exclusion_reason="Reuters Open Research License explicitly prohibits commercial use and raw text redistribution.",
    ),
    "SRC-005": SourceEligibilityProfile(
        source_id="SRC-005",
        source_name="Malaysian Parliamentary Hansard Excerpts",
        licence="Open Government Data / Public Record (Section 13(2)(h) Copyright Act 1987)",
        research_training=VERIFIED_ALLOWED,
        commercial_training=UNVERIFIED,
        raw_text_redistribution=UNVERIFIED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=UNVERIFIED,
        rationale="Official transcripts of parliamentary proceedings are non-infringing for reporting and parliamentary purposes under Section 13(2)(h) of the Malaysian Copyright Act 1987. However, Parliament of Malaysia has not published an express Open Government License granting commercial exploitation or bulk raw-text redistribution. Fails closed as UNVERIFIED for commercial use and raw redistribution.",
        exclusion_reason="Parliament of Malaysia has not issued an express commercial reuse license; fail-closed policy applies.",
    ),
    "SRC-006": SourceEligibilityProfile(
        source_id="SRC-006",
        source_name="Bursa Malaysia Corporate Disclosures",
        licence="Public Regulatory Disclosure",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_ALLOWED,
        raw_text_redistribution=VERIFIED_ALLOWED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=VERIFIED_ALLOWED,
        rationale="Factual public announcements (director appointments, registered addresses, dividends) lack copyrightable artistic expression under copyright law; fair use of factual public regulatory filings.",
    ),
    "SRC-007": SourceEligibilityProfile(
        source_id="SRC-007",
        source_name="Independent Project Authorship",
        licence="MIT License",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_ALLOWED,
        raw_text_redistribution=VERIFIED_ALLOWED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=VERIFIED_ALLOWED,
        rationale="Originally authored fictional and administrative sentences by project contributors; released unconditionally under MIT License.",
    ),
    "SRC-008": SourceEligibilityProfile(
        source_id="SRC-008",
        source_name="Combinatorial Synthetic Engine",
        licence="MIT License / CC0 Public Domain",
        research_training=VERIFIED_ALLOWED,
        commercial_training=VERIFIED_ALLOWED,
        raw_text_redistribution=VERIFIED_ALLOWED,
        derived_annotation_redistribution=VERIFIED_ALLOWED,
        research_model_weights=VERIFIED_ALLOWED,
        commercial_model_weights=VERIFIED_ALLOWED,
        rationale="Algorithmically generated via grammar templates and public domain slot entities; dedicated under MIT License.",
    ),
}


class DatasetReleaseChecker:
    """Audits records and produces dimension-specific release manifests enforcing fail-closed safeguards."""

    def __init__(self, profiles: Dict[str, SourceEligibilityProfile] = SOURCE_PROFILES):
        self.profiles = profiles

    def check_record(self, record: Dict[str, Any]) -> Dict[str, str]:
        """Returns categorical eligibility status across all 6 dimensions for a single record."""
        meta = record.get("metadata") or record.get("meta") or {}
        src_id = meta.get("source_id", "UNKNOWN")
        profile = self.profiles.get(src_id)
        if profile is None:
            # Unknown source fails closed across all dimensions
            return {dim: UNVERIFIED for dim in PERMISSION_DIMENSIONS}

        return {
            "research_training": profile.research_training,
            "commercial_training": profile.commercial_training,
            "raw_text_redistribution": profile.raw_text_redistribution,
            "derived_annotation_redistribution": profile.derived_annotation_redistribution,
            "research_model_weights": profile.research_model_weights,
            "commercial_model_weights": profile.commercial_model_weights,
            # Legacy alias
            "research_use": profile.research_training,
        }

    def is_eligible(self, record: Dict[str, Any], dimension: str) -> bool:
        """Fail-closed evaluator: returns True ONLY IF the dimension is VERIFIED_ALLOWED."""
        status = self.check_record(record).get(dimension)
        return status == VERIFIED_ALLOWED

    def generate_release_manifests(
        self,
        records: List[Dict[str, Any]],
        output_dir: str = "data/manifests",
    ) -> Dict[str, Any]:
        """Filters records into separate release subsets and saves machine-readable manifests."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        research_records = []
        commercial_training_records = []
        raw_redistribution_records = []
        metadata_redistribution_records = []
        research_weights_records = []
        commercial_weights_records = []

        excluded_from_commercial = []
        excluded_from_raw_redist = []
        excluded_from_metadata = []

        for r in records:
            r_id = r.get("id")
            meta = r.get("metadata") or r.get("meta") or {}
            src_id = meta.get("source_id", "UNKNOWN")
            profile = self.profiles.get(src_id)
            exclusion_reason = profile.exclusion_reason if profile else "Unknown source ID"

            # 1. Research Training
            if self.is_eligible(r, "research_training"):
                research_records.append(r)

            # 2. Commercial Training
            if self.is_eligible(r, "commercial_training"):
                commercial_training_records.append(r)
            else:
                excluded_from_commercial.append({
                    "id": r_id,
                    "source": src_id,
                    "reason": exclusion_reason,
                    "status": profile.commercial_training if profile else UNVERIFIED,
                })

            # 3. Raw-Text Redistribution
            if self.is_eligible(r, "raw_text_redistribution"):
                raw_redistribution_records.append(r)
            else:
                excluded_from_raw_redist.append({
                    "id": r_id,
                    "source": src_id,
                    "reason": exclusion_reason,
                    "status": profile.raw_text_redistribution if profile else UNVERIFIED,
                })

            # 4. Derived Annotation Metadata Redistribution
            if self.is_eligible(r, "derived_annotation_redistribution"):
                # Metadata without underlying text
                metadata_record = {
                    "id": r_id,
                    "source_id": src_id,
                    "entities": r.get("label", r.get("entities", [])),
                    "character_count": len(r.get("text", "")),
                }
                metadata_redistribution_records.append(metadata_record)
            else:
                excluded_from_metadata.append({
                    "id": r_id,
                    "source": src_id,
                    "reason": exclusion_reason,
                    "status": profile.derived_annotation_redistribution if profile else UNVERIFIED,
                })

            # 5. Research Model Weights
            if self.is_eligible(r, "research_model_weights"):
                research_weights_records.append(r)

            # 6. Commercial Model Weights
            if self.is_eligible(r, "commercial_model_weights"):
                commercial_weights_records.append(r)

        manifests_meta = {
            "total_canonical_records": len(records),
            "research_training_eligible_count": len(research_records),
            "commercial_training_eligible_count": len(commercial_training_records),
            "raw_redistribution_eligible_count": len(raw_redistribution_records),
            "derived_annotation_metadata_eligible_count": len(metadata_redistribution_records),
            "research_model_weights_eligible_count": len(research_weights_records),
            "commercial_model_weights_eligible_count": len(commercial_weights_records),
            "excluded_from_commercial_count": len(excluded_from_commercial),
            "excluded_from_raw_redistribution_count": len(excluded_from_raw_redist),
            "excluded_from_metadata_count": len(excluded_from_metadata),
            # Legacy key aliases
            "research_eligible_count": len(research_records),
            "model_weight_distribution_eligible_count": len(commercial_weights_records),
            "excluded_from_redistribution_count": len(excluded_from_raw_redist),
        }

        # Save Research Manifest
        with open(out_path / "release_research_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "All records eligible for non-commercial academic research and benchmarking under Fair Dealing / Research Licenses.",
                "dimension": "research_training",
                "count": len(research_records),
                "record_ids": [r["id"] for r in research_records],
            }, f, indent=2)

        # Save Commercial Training Manifest
        with open(out_path / "release_commercial_training_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "Records cleared for commercial model training without third-party copyright infringement risk (SRC-006, SRC-007, SRC-008).",
                "dimension": "commercial_training",
                "count": len(commercial_training_records),
                "record_ids": [r["id"] for r in commercial_training_records],
                "excluded_count": len(excluded_from_commercial),
                "excluded_details": excluded_from_commercial,
            }, f, indent=2)

        # Save Raw Redistribution Manifest
        with open(out_path / "release_raw_redistribution_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "Records cleared for public raw-text dataset redistribution under MIT / CC0 / Permissive public disclosure.",
                "dimension": "raw_text_redistribution",
                "count": len(raw_redistribution_records),
                "record_ids": [r["id"] for r in raw_redistribution_records],
                "excluded_count": len(excluded_from_raw_redist),
                "excluded_details": excluded_from_raw_redist,
            }, f, indent=2)

        # Save Standalone Metadata Manifest (Audit B Profile 3)
        with open(out_path / "release_metadata_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "Standalone annotation metadata (record IDs, character offsets, entity labels) completely devoid of underlying raw text strings, eligible for open redistribution under MIT.",
                "dimension": "derived_annotation_redistribution",
                "count": len(metadata_redistribution_records),
                "records": metadata_redistribution_records,
                "excluded_count": len(excluded_from_metadata),
                "excluded_details": excluded_from_metadata,
            }, f, indent=2)

        return manifests_meta
