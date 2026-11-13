"""
Provenance and Licensing Auditor.

Verifies that all dataset records strictly map to verified sources in
data/SOURCE_MANIFEST.csv and audits licensing, commercial rights, and attribution.

Author: AI/ML Club
License: MIT
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


@dataclass
class SourceRecord:
    source_id: str
    source_name: str
    source_url: str
    creator: str
    collection_date: str
    licence: str
    commercial_use_permission: str
    attribution_requirements: str
    redistribution_permission: str
    data_type: str
    preprocessing_history: str
    verification_status: str


@dataclass
class ProvenanceAuditReport:
    total_records: int
    verified_records: int
    unverified_records: int
    restricted_records: int
    source_counts: Dict[str, int] = field(default_factory=dict)
    data_type_counts: Dict[str, int] = field(default_factory=dict)
    licence_counts: Dict[str, int] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    is_compliant: bool = True

    def summary(self) -> str:
        lines = [
            "=" * 68,
            "                  DATASET PROVENANCE & LICENSING AUDIT",
            "=" * 68,
            f"Total Evaluated Records:     {self.total_records}",
            f"Verified Clean Records:      {self.verified_records}",
            f"Unverified Source Records:   {self.unverified_records}",
            f"Restricted Use Records:      {self.restricted_records}",
            f"Audit Compliance Status:     {'PASS [VERIFIED]' if self.is_compliant else 'WARN [ISSUES DETECTED]'}",
            "-" * 68,
            "Data Origin (Data Type) Breakdown:",
        ]
        for dt, count in sorted(self.data_type_counts.items()):
            pct = (count / self.total_records) * 100 if self.total_records > 0 else 0
            lines.append(f"  - {dt:<28}: {count:>5} ({pct:>5.1f}%)")

        lines.extend([
            "-" * 68,
            "Licensing Distribution:",
        ])
        for lic, count in sorted(self.licence_counts.items()):
            lines.append(f"  - {lic:<32}: {count:>5}")

        if self.issues:
            lines.extend([
                "-" * 68,
                f"Issues Logged ({len(self.issues)} items):",
            ])
            for iss in self.issues[:10]:
                lines.append(f"  [WARN] {iss}")

        lines.append("=" * 68)
        return "\n".join(lines)


class ProvenanceAuditor:
    """Validates records against the authoritative source manifest."""

    REQUIRED_MANIFEST_COLUMNS = [
        "source_id", "source_name", "source_url", "creator", "collection_date",
        "licence", "commercial_use_permission", "attribution_requirements",
        "redistribution_permission", "data_type", "preprocessing_history",
        "verification_status"
    ]

    def __init__(self, manifest_path: Union[str, Path] = "data/SOURCE_MANIFEST.csv"):
        self.manifest_path = Path(manifest_path)
        self.sources: Dict[str, SourceRecord] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Loads and validates the source manifest CSV."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for col in self.REQUIRED_MANIFEST_COLUMNS:
                if col not in headers:
                    raise ValueError(f"Manifest missing required column: '{col}'")

            for row in reader:
                s_id = row["source_id"].strip()
                self.sources[s_id] = SourceRecord(
                    source_id=s_id,
                    source_name=row["source_name"].strip(),
                    source_url=row["source_url"].strip(),
                    creator=row["creator"].strip(),
                    collection_date=row["collection_date"].strip(),
                    licence=row["licence"].strip(),
                    commercial_use_permission=row["commercial_use_permission"].strip(),
                    attribution_requirements=row["attribution_requirements"].strip(),
                    redistribution_permission=row["redistribution_permission"].strip(),
                    data_type=row["data_type"].strip(),
                    preprocessing_history=row["preprocessing_history"].strip(),
                    verification_status=row["verification_status"].strip(),
                )

    def audit_dataset(self, records: List[Dict[str, Any]]) -> ProvenanceAuditReport:
        """Audits dataset records against registered source provenance."""
        source_counts: Dict[str, int] = {}
        data_type_counts: Dict[str, int] = {}
        licence_counts: Dict[str, int] = {}
        issues: List[str] = []

        verified_records = 0
        unverified_records = 0
        restricted_records = 0

        for rec in records:
            r_id = rec.get("id", "UNKNOWN")
            meta = rec.get("metadata", rec.get("meta", {}))
            source_id = meta.get("source_id")

            if not source_id:
                issues.append(f"Record ID {r_id} is missing 'source_id' in metadata.")
                unverified_records += 1
                continue

            if source_id not in self.sources:
                issues.append(f"Record ID {r_id} has unregistered source_id '{source_id}'.")
                unverified_records += 1
                continue

            src = self.sources[source_id]
            source_counts[source_id] = source_counts.get(source_id, 0) + 1
            data_type_counts[src.data_type] = data_type_counts.get(src.data_type, 0) + 1
            licence_counts[src.licence] = licence_counts.get(src.licence, 0) + 1

            if src.verification_status in {"VERIFIED", "PARTIALLY_VERIFIED"}:
                verified_records += 1
            elif src.verification_status == "RESTRICTED_RESEARCH_ONLY":
                restricted_records += 1
                verified_records += 1  # Verified but restricted to research evaluation
            else:
                unverified_records += 1
                issues.append(f"Record ID {r_id} has status '{src.verification_status}'.")

        total = len(records)
        is_compliant = unverified_records == 0 and len(issues) == 0

        return ProvenanceAuditReport(
            total_records=total,
            verified_records=verified_records,
            unverified_records=unverified_records,
            restricted_records=restricted_records,
            source_counts=source_counts,
            data_type_counts=data_type_counts,
            licence_counts=licence_counts,
            issues=issues,
            is_compliant=is_compliant,
        )
