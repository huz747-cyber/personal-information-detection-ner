"""
Deduplication and Near-Duplicate Detection Engine.

Provides multi-stage deduplication:
1. Exact String Match: Identical text strings.
2. Normalized Match: Text with stripped whitespace, case normalization, and punctuation stripping.
3. Near-Duplicate Fuzzy Match: Character n-gram Jaccard similarity to catch template echoes
   where sentences share 85%+ lexical similarity.

Author: AI/ML Club
License: MIT
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class DuplicateCluster:
    primary_id: Any
    duplicate_ids: List[Any]
    match_type: str  # 'EXACT', 'NORMALIZED', 'NEAR_DUPLICATE'
    similarity: float
    representative_text: str


class DatasetDeduplicator:
    """Detects and clusters duplicate and near-duplicate sentences."""

    def __init__(self, near_duplicate_threshold: float = 0.85, ngram_size: int = 3):
        self.threshold = near_duplicate_threshold
        self.ngram_size = ngram_size

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes text by lowercasing, stripping punctuation, and collapsing whitespace."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(cleaned.split())

    def get_ngrams(self, text: str) -> Set[str]:
        """Extracts character n-grams from normalized text."""
        norm = self.normalize_text(text)
        if len(norm) < self.ngram_size:
            return {norm}
        return {norm[i : i + self.ngram_size] for i in range(len(norm) - self.ngram_size + 1)}

    def jaccard_similarity(self, ngrams_a: Set[str], ngrams_b: Set[str]) -> float:
        """Computes Jaccard index between two n-gram sets."""
        if not ngrams_a or not ngrams_b:
            return 0.0
        intersection = len(ngrams_a & ngrams_b)
        union = len(ngrams_a | ngrams_b)
        return intersection / union if union > 0 else 0.0

    def find_duplicates(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[DuplicateCluster], List[Dict[str, Any]]]:
        """Scans records for duplicates and returns (clusters, unique_records).

        Args:
            records: List of records containing 'id' and 'text'.

        Returns:
            Tuple of:
                - List of DuplicateCluster objects describing duplicate relationships.
                - Filtered list of unique records (keeping only the primary instance).
        """
        exact_map: Dict[str, Any] = {}
        norm_map: Dict[str, Any] = {}
        unique_records: List[Dict[str, Any]] = []
        clusters: List[DuplicateCluster] = []

        # Track processed ngrams for near-duplicate screening
        unique_ngrams: List[Tuple[Any, str, Set[str]]] = []

        for rec in records:
            r_id = rec.get("id", "UNKNOWN")
            text = rec.get("text", "")
            norm = self.normalize_text(text)

            # 1. Exact Match
            if text in exact_map:
                clusters.append(DuplicateCluster(
                    primary_id=exact_map[text],
                    duplicate_ids=[r_id],
                    match_type="EXACT",
                    similarity=1.0,
                    representative_text=text,
                ))
                continue

            # 2. Normalized Match
            if norm in norm_map:
                clusters.append(DuplicateCluster(
                    primary_id=norm_map[norm],
                    duplicate_ids=[r_id],
                    match_type="NORMALIZED",
                    similarity=1.0,
                    representative_text=text,
                ))
                continue

            # 3. Near-Duplicate Fuzzy Match
            current_ngrams = self.get_ngrams(text)
            is_near_dup = False

            for u_id, u_text, u_ngrams in unique_ngrams:
                sim = self.jaccard_similarity(current_ngrams, u_ngrams)
                if sim >= self.threshold:
                    clusters.append(DuplicateCluster(
                        primary_id=u_id,
                        duplicate_ids=[r_id],
                        match_type="NEAR_DUPLICATE",
                        similarity=round(sim, 3),
                        representative_text=text,
                    ))
                    is_near_dup = True
                    break

            if not is_near_dup:
                exact_map[text] = r_id
                norm_map[norm] = r_id
                unique_ngrams.append((r_id, text, current_ngrams))
                unique_records.append(rec)

        return clusters, unique_records
