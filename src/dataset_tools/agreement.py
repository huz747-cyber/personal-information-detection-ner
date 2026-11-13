"""
Inter-Annotator Agreement (IAA) and Double-Annotation Quality Control.

Evaluates agreement between independent annotators on a double-annotated subset:
1. Exact Span F1 / Precision / Recall (strict boundary and class match).
2. Partial Span Match (boundary overlap).
3. Token-Level Cohen's Kappa (chance-corrected agreement).
4. Boundary Disagreement Detection (same label, differing start/end offsets).
5. Class Disagreement Detection (overlapping span, conflicting entity label).
6. Adjudication Logger (records formal resolution and rationale).

Author: AI/ML Club
License: MIT
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .doccano_adapter import text_to_bio


@dataclass
class DisagreementCase:
    record_id: Any
    sentence_text: str
    issue_type: str  # 'BOUNDARY_DISAGREEMENT', 'CLASS_DISAGREEMENT', 'MISSING_ANNOTATION'
    annotator_1_span: Optional[Dict[str, Any]]
    annotator_2_span: Optional[Dict[str, Any]]
    resolution: Optional[Dict[str, Any]] = None
    adjudication_notes: str = ""


@dataclass
class AgreementReport:
    total_evaluated_sentences: int
    exact_span_precision: float
    exact_span_recall: float
    exact_span_f1: float
    cohens_kappa: float
    total_ann1_entities: int
    total_ann2_entities: int
    matched_exact_entities: int
    boundary_disagreements: int
    class_disagreements: int
    missing_in_ann1: int
    missing_in_ann2: int
    disagreement_details: List[DisagreementCase] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "=" * 68,
            "            INTER-ANNOTATOR AGREEMENT (IAA) REPORT",
            "=" * 68,
            f"Double-Annotated Sentences:  {self.total_evaluated_sentences}",
            f"Annotator 1 Entities:        {self.total_ann1_entities}",
            f"Annotator 2 Entities:        {self.total_ann2_entities}",
            f"Exact Entity Matches:        {self.matched_exact_entities}",
            "-" * 68,
            f"Exact Span Precision:        {self.exact_span_precision:.4f} ({self.exact_span_precision*100:.1f}%)",
            f"Exact Span Recall:           {self.exact_span_recall:.4f} ({self.exact_span_recall*100:.1f}%)",
            f"Exact Span F1-Score:         {self.exact_span_f1:.4f} ({self.exact_span_f1*100:.1f}%)",
            f"Token-Level Cohen's Kappa:   {self.cohens_kappa:.4f} ({self._interpret_kappa(self.cohens_kappa)})",
            "-" * 68,
            "Disagreement Breakdown:",
            f"  - Boundary Disagreements:  {self.boundary_disagreements}",
            f"  - Entity Class Conflicts:  {self.class_disagreements}",
            f"  - Unique to Annotator 1:   {self.missing_in_ann2}",
            f"  - Unique to Annotator 2:   {self.missing_in_ann1}",
            "=" * 68,
        ]
        return "\n".join(lines)

    @staticmethod
    def _interpret_kappa(kappa: float) -> str:
        if kappa >= 0.81:
            return "Almost Perfect Agreement"
        elif kappa >= 0.61:
            return "Substantial Agreement"
        elif kappa >= 0.41:
            return "Moderate Agreement"
        elif kappa >= 0.21:
            return "Fair Agreement"
        else:
            return "Slight / Poor Agreement"


class AnnotationAgreementCalculator:
    """Computes inter-annotator metrics and generates adjudication logs."""

    @staticmethod
    def _spans_overlap(s1: int, e1: int, s2: int, e2: int) -> bool:
        return max(s1, s2) < min(e1, e2)

    def evaluate_pair(
        self,
        ann1_records: List[Dict[str, Any]],
        ann2_records: List[Dict[str, Any]],
    ) -> AgreementReport:
        """Evaluates agreement between canonical Ann1 and independent Ann2."""
        ann1_map = {r["id"]: r for r in ann1_records}
        ann2_map = {r["id"]: r for r in ann2_records}
        shared_ids = sorted(set(ann1_map.keys()) & set(ann2_map.keys()))

        if not shared_ids:
            raise ValueError("No common sentence IDs found between the two annotation sets.")

        total_ann1 = 0
        total_ann2 = 0
        exact_matches = 0
        boundary_conflicts = 0
        class_conflicts = 0
        missing_in_ann1 = 0
        missing_in_ann2 = 0

        disagreements: List[DisagreementCase] = []

        all_tokens_ann1: List[str] = []
        all_tokens_ann2: List[str] = []

        for r_id in shared_ids:
            rec1 = ann1_map[r_id]
            rec2 = ann2_map[r_id]
            text = rec1["text"]

            ents1 = rec1.get("entities", [])
            ents2 = rec2.get("entities", [])

            total_ann1 += len(ents1)
            total_ann2 += len(ents2)

            # Compute token BIO for Cohen's Kappa
            t1, bio1 = text_to_bio(text, ents1)
            t2, bio2 = text_to_bio(text, ents2)
            all_tokens_ann1.extend(bio1)
            all_tokens_ann2.extend(bio2)

            matched2_indices = set()
            for e1 in ents1:
                e1_tuple = (e1["start"], e1["end"], e1["label"])
                found_match = False
                for idx2, e2 in enumerate(ents2):
                    e2_tuple = (e2["start"], e2["end"], e2["label"])
                    if e1_tuple == e2_tuple:
                        exact_matches += 1
                        matched2_indices.add(idx2)
                        found_match = True
                        break
                    elif self._spans_overlap(e1["start"], e1["end"], e2["start"], e2["end"]):
                        if e1["label"] == e2["label"]:
                            # Same label, differing offsets
                            boundary_conflicts += 1
                            matched2_indices.add(idx2)
                            found_match = True
                            disagreements.append(DisagreementCase(
                                record_id=r_id,
                                sentence_text=text,
                                issue_type="BOUNDARY_DISAGREEMENT",
                                annotator_1_span=e1,
                                annotator_2_span=e2,
                            ))
                            break
                        else:
                            # Conflicting label
                            class_conflicts += 1
                            matched2_indices.add(idx2)
                            found_match = True
                            disagreements.append(DisagreementCase(
                                record_id=r_id,
                                sentence_text=text,
                                issue_type="CLASS_DISAGREEMENT",
                                annotator_1_span=e1,
                                annotator_2_span=e2,
                            ))
                            break

                if not found_match:
                    missing_in_ann2 += 1
                    disagreements.append(DisagreementCase(
                        record_id=r_id,
                        sentence_text=text,
                        issue_type="MISSING_ANNOTATION",
                        annotator_1_span=e1,
                        annotator_2_span=None,
                        adjudication_notes="Entity identified only by Annotator 1.",
                    ))

            for idx2, e2 in enumerate(ents2):
                if idx2 not in matched2_indices:
                    missing_in_ann1 += 1
                    disagreements.append(DisagreementCase(
                        record_id=r_id,
                        sentence_text=text,
                        issue_type="MISSING_ANNOTATION",
                        annotator_1_span=None,
                        annotator_2_span=e2,
                        adjudication_notes="Entity identified only by Annotator 2.",
                    ))

        prec = exact_matches / total_ann2 if total_ann2 > 0 else 0.0
        rec = exact_matches / total_ann1 if total_ann1 > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        kappa = self._calculate_cohens_kappa(all_tokens_ann1, all_tokens_ann2)

        return AgreementReport(
            total_evaluated_sentences=len(shared_ids),
            exact_span_precision=round(prec, 4),
            exact_span_recall=round(rec, 4),
            exact_span_f1=round(f1, 4),
            cohens_kappa=round(kappa, 4),
            total_ann1_entities=total_ann1,
            total_ann2_entities=total_ann2,
            matched_exact_entities=exact_matches,
            boundary_disagreements=boundary_conflicts,
            class_disagreements=class_conflicts,
            missing_in_ann1=missing_in_ann1,
            missing_in_ann2=missing_in_ann2,
            disagreement_details=disagreements,
        )

    @staticmethod
    def _calculate_cohens_kappa(tags1: List[str], tags2: List[str]) -> float:
        """Calculates token-level Cohen's Kappa between two categorical tag sequences."""
        if len(tags1) != len(tags2) or not tags1:
            return 0.0

        n = len(tags1)
        categories = sorted(set(tags1) | set(tags2))

        # Observed agreement
        observed_agreements = sum(1 for t1, t2 in zip(tags1, tags2) if t1 == t2)
        p_o = observed_agreements / n

        # Expected chance agreement
        p_e = 0.0
        for cat in categories:
            p1 = sum(1 for t in tags1 if t == cat) / n
            p2 = sum(1 for t in tags2 if t == cat) / n
            p_e += (p1 * p2)

        if p_e >= 1.0:
            return 1.0
        return (p_o - p_e) / (1.0 - p_e)


def adjudicate_disagreement(
    case: DisagreementCase,
    chosen_span: Optional[Dict[str, Any]],
    reason: str,
) -> DisagreementCase:
    """Records an adjudication decision for a logged disagreement."""
    case.resolution = chosen_span
    case.adjudication_notes = reason
    return case
