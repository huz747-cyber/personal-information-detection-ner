"""
Dataset Release and Licensing Eligibility Checker.

Evaluates dataset sources across 5 distinct legal release dimensions:
1. Research Use (Non-commercial training and academic evaluation)
2. Commercial Training (Model weights trained on data used in commercial software)
3. Raw-Text Redistribution (Redistributing raw sentence text in public download)
4. Derived Annotation Redistribution (Redistributing character offsets and labels)
5. Model-Weight Distribution (Publishing model checkpoint trained on this corpus)

Generates separated release manifests to guarantee zero ineligible records leak into
commercial or public redistribution releases.

Author: AI/ML Club
License: MIT
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from .doccano_adapter import import_from_doccano


@dataclass
class SourceEligibilityProfile:
    source_id: str
    source_name: str
    licence: str
    research_use: bool
    commercial_training: bool
    raw_text_redistribution: bool
    derived_annotation_redistribution: bool
    model_weight_distribution: bool
    rationale: str


SOURCE_PROFILES: Dict[str, SourceEligibilityProfile] = {
    "SRC-001": SourceEligibilityProfile(
        source_id="SRC-001",
        source_name="Mesolitica Malaya NER Dataset",
        licence="MIT (Repository Code) / News Fair Dealing (Text)",
        research_use=True,
        commercial_training=False,
        raw_text_redistribution=False,
        derived_annotation_redistribution=True,
        model_weight_distribution=False,
        rationale="Underlying Malay news text belongs to Malaysian publishers; Fair Dealing covers non-profit research, but commercial training and raw text redistribution carry copyright risk.",
    ),
    "SRC-002": SourceEligibilityProfile(
        source_id="SRC-002",
        source_name="WikiANN PAN-X Malay Subset (ms)",
        licence="CC-BY-SA 4.0",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Permissive under CC-BY-SA 4.0 with attribution and ShareAlike provisions.",
    ),
    "SRC-003": SourceEligibilityProfile(
        source_id="SRC-003",
        source_name="SEACrowd Malay NER Benchmark",
        licence="Apache 2.0",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Permissive open-source benchmark under Apache 2.0.",
    ),
    "SRC-004": SourceEligibilityProfile(
        source_id="SRC-004",
        source_name="CoNLL-2003 English NER",
        licence="Reuters Open Research License",
        research_use=True,
        commercial_training=False,
        raw_text_redistribution=False,
        derived_annotation_redistribution=False,
        model_weight_distribution=False,
        rationale="Reuters corpus is strictly limited to non-commercial academic research; commercial training and raw text redistribution are strictly prohibited.",
    ),
    "SRC-005": SourceEligibilityProfile(
        source_id="SRC-005",
        source_name="Malaysian Parliamentary Hansard Excerpts",
        licence="Open Government Data / Public Record",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Official transcripts of parliamentary proceedings are non-infringing public records under Section 13(2)(h) of the Malaysian Copyright Act 1987.",
    ),
    "SRC-006": SourceEligibilityProfile(
        source_id="SRC-006",
        source_name="Bursa Malaysia Corporate Disclosures",
        licence="Public Regulatory Disclosure",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Factual public announcements (director appointments, registered addresses, dividends) lack copyrightable artistic expression under copyright law.",
    ),
    "SRC-007": SourceEligibilityProfile(
        source_id="SRC-007",
        source_name="Independent Project Authorship",
        licence="MIT License",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Originally authored fictional and administrative sentences by project contributors; released unconditionally under MIT License.",
    ),
    "SRC-008": SourceEligibilityProfile(
        source_id="SRC-008",
        source_name="Combinatorial Synthetic Engine",
        licence="MIT License / CC0 Public Domain",
        research_use=True,
        commercial_training=True,
        raw_text_redistribution=True,
        derived_annotation_redistribution=True,
        model_weight_distribution=True,
        rationale="Algorithmically generated via grammar templates and public domain slot entities; dedicated under MIT License.",
    ),
}


class DatasetReleaseChecker:
    """Audits records and produces dimension-specific release manifests."""

    def __init__(self, profiles: Dict[str, SourceEligibilityProfile] = SOURCE_PROFILES):
        self.profiles = profiles

    def check_record(self, record: Dict[str, Any]) -> Dict[str, bool]:
        """Returns boolean eligibility across all 5 dimensions for a single record."""
        meta = record.get("metadata", record.get("meta", {}))
        src_id = meta.get("source_id", "UNKNOWN")
        profile = self.profiles.get(src_id)
        if profile is None:
            return {
                "research_use": False,
                "commercial_training": False,
                "raw_text_redistribution": False,
                "derived_annotation_redistribution": False,
                "model_weight_distribution": False,
            }
        return {
            "research_use": profile.research_use,
            "commercial_training": profile.commercial_training,
            "raw_text_redistribution": profile.raw_text_redistribution,
            "derived_annotation_redistribution": profile.derived_annotation_redistribution,
            "model_weight_distribution": profile.model_weight_distribution,
        }

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
        model_weight_records = []

        excluded_from_commercial = []
        excluded_from_redistribution = []

        for r in records:
            elig = self.check_record(r)
            r_id = r.get("id")
            src_id = r.get("metadata", r.get("meta", {})).get("source_id")

            if elig["research_use"]:
                research_records.append(r)

            if elig["commercial_training"]:
                commercial_training_records.append(r)
            else:
                excluded_from_commercial.append((r_id, src_id))

            if elig["raw_text_redistribution"]:
                raw_redistribution_records.append(r)
            else:
                excluded_from_redistribution.append((r_id, src_id))

            if elig["model_weight_distribution"]:
                model_weight_records.append(r)

        manifests_meta = {
            "total_canonical_records": len(records),
            "research_eligible_count": len(research_records),
            "commercial_training_eligible_count": len(commercial_training_records),
            "raw_redistribution_eligible_count": len(raw_redistribution_records),
            "model_weight_distribution_eligible_count": len(model_weight_records),
            "excluded_from_commercial_count": len(excluded_from_commercial),
            "excluded_from_redistribution_count": len(excluded_from_redistribution),
        }

        # Write manifest lists of record IDs
        with open(out_path / "release_research_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "All records eligible for non-commercial academic research and benchmarking.",
                "count": len(research_records),
                "record_ids": [r["id"] for r in research_records],
            }, f, indent=2)

        with open(out_path / "release_commercial_training_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "Records cleared for commercial model training without third-party copyright infringement.",
                "count": len(commercial_training_records),
                "record_ids": [r["id"] for r in commercial_training_records],
                "excluded_count": len(excluded_from_commercial),
                "excluded_details": [{"id": i, "source": s} for i, s in excluded_from_commercial],
            }, f, indent=2)

        with open(out_path / "release_raw_redistribution_manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "description": "Records cleared for public raw-text dataset redistribution.",
                "count": len(raw_redistribution_records),
                "record_ids": [r["id"] for r in raw_redistribution_records],
                "excluded_count": len(excluded_from_redistribution),
                "excluded_details": [{"id": i, "source": s} for i, s in excluded_from_redistribution],
            }, f, indent=2)

        return manifests_meta
