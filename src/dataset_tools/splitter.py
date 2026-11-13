"""
Stratified, Document-Grouped, and Leakage-Safe Dataset Splitter.

Splits Malaysian NER dataset records into reproducible 70% Train, 15% Validation,
and 15% Test subsets, enforcing:
1. Determinism: Fixed seed ensures bit-for-bit reproducibility.
2. Group Isolation: Sentences sharing the same document_id or synthetic template_id
   are clustered into an indivisible unit so that no related sentences or templates
   can ever cross partition boundaries.
3. Multi-Factor Stratification: Balances partitions proportionally across:
   - 7 Linguistic Strata (Formal Malay, English, Manglish, Mixed, Chinese, Indian, Baseline).
   - Data Origin (Publicly sourced, Independently written, Synthetic).
   - Entity Distributions & Hard Negatives.

Author: AI/ML Club
License: MIT
"""

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .doccano_adapter import export_to_doccano, import_from_doccano


class DatasetSplitter:
    """Partitions dataset records into Train, Validation, and Test splits."""

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ):
        if not abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5:
            raise ValueError(
                f"Ratios must sum to 1.0 (got {train_ratio} + {val_ratio} + {test_ratio} = {train_ratio + val_ratio + test_ratio})"
            )
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    @staticmethod
    def compute_sentence_hash(text: str) -> str:
        """Computes a normalized MD5 hash of the sentence text for deduplication grouping."""
        norm = " ".join(text.lower().split())
        return hashlib.md5(norm.encode("utf-8")).hexdigest()

    def get_cluster_key(self, record: Dict[str, Any]) -> str:
        """Determines the indivisible grouping key for a record to prevent split leakage.

        Priority:
        1. document_id (if part of a multi-sentence public document)
        2. template_id (if derived from a parameterized synthetic template)
        3. Normalized sentence text hash (exact / normalized duplicate grouping)
        """
        meta = record.get("metadata", record.get("meta", {}))
        if meta.get("document_id"):
            return f"doc_{meta['document_id']}"
        if meta.get("template_id"):
            return f"tpl_{meta['template_id']}"
        return f"hash_{self.compute_sentence_hash(record.get('text', ''))}"

    def get_stratum_key(self, record: Dict[str, Any]) -> str:
        """Computes multi-factor stratification key based on linguistic stratum, origin, and entity profile."""
        meta = record.get("metadata", record.get("meta", {}))
        stratum = meta.get("stratum", meta.get("language", "general"))
        source_type = meta.get("source_type", meta.get("data_type", "synthetic"))
        is_hard_negative = meta.get("is_hard_negative", meta.get("hard_negative", False))

        entities = record.get("entities", [])
        has_per = any(e.get("label") == "PERSON" for e in entities)
        has_org = any(e.get("label") == "ORGANIZATION" for e in entities)
        has_loc = any(e.get("label") == "LOCATION" for e in entities)

        ent_profile = "neg" if is_hard_negative or not entities else f"P{int(has_per)}O{int(has_org)}L{int(has_loc)}"
        return f"{stratum}|{source_type}|{ent_profile}"

    def split_records(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Partitions records into (train, val, test) using stratified document-group splitting.

        Args:
            records: List of internal records with 'text', 'entities', and 'metadata'.

        Returns:
            Tuple of (train_records, val_records, test_records).
        """
        rng = random.Random(self.seed)

        # 1. Cluster records by document_id / template_id / text hash
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            key = self.get_cluster_key(rec)
            clusters.setdefault(key, []).append(rec)

        # 2. Assign clusters to strata based on representative record characteristics
        strata: Dict[str, List[List[Dict[str, Any]]]] = {}
        for cluster_key, group_records in clusters.items():
            first_rec = group_records[0]
            stratum_key = self.get_stratum_key(first_rec)
            strata.setdefault(stratum_key, []).append(group_records)

        train: List[Dict[str, Any]] = []
        val: List[Dict[str, Any]] = []
        test: List[Dict[str, Any]] = []

        # 3. For each stratum, shuffle clusters deterministically and allocate
        for key in sorted(strata.keys()):
            group_list = strata[key]
            rng.shuffle(group_list)

            n_total = len(group_list)
            n_train = int(round(n_total * self.train_ratio))
            n_val = int(round(n_total * self.val_ratio))

            if n_total >= 3:
                if n_val == 0:
                    n_val = 1
                    n_train = max(1, n_train - 1)
                if (n_total - n_train - n_val) == 0:
                    n_test = 1
                    n_train = max(1, n_train - 1)
                else:
                    n_test = n_total - n_train - n_val
            else:
                n_test = n_total - n_train - n_val

            train_groups = group_list[:n_train]
            val_groups = group_list[n_train : n_train + n_val]
            test_groups = group_list[n_train + n_val :]

            for g in train_groups:
                train.extend(g)
            for g in val_groups:
                val.extend(g)
            for g in test_groups:
                test.extend(g)

        # Deterministic sort by record ID for reproducibility
        train.sort(key=lambda x: str(x.get("id", "")))
        val.sort(key=lambda x: str(x.get("id", "")))
        test.sort(key=lambda x: str(x.get("id", "")))

        return train, val, test

    def split_and_save(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> Dict[str, Any]:
        """Loads a dataset file, executes stratified partition, and writes train/val/test .jsonl files.

        Args:
            input_path: Source .jsonl or .json dataset file.
            output_dir: Directory where train.jsonl, val.jsonl, test.jsonl will be saved.

        Returns:
            Dictionary with counts and proportions of records in each split.
        """
        in_p = Path(input_path)
        out_d = Path(output_dir)
        out_d.mkdir(parents=True, exist_ok=True)

        if in_p.suffix in {".jsonl", ".txt"}:
            records = import_from_doccano(in_p)
        elif in_p.suffix == ".json":
            with open(in_p, "r", encoding="utf-8") as f:
                records = json.load(f)
        else:
            raise ValueError(f"Unsupported format: {in_p.suffix}")

        train, val, test = self.split_records(records)

        export_to_doccano(train, out_d / "train.jsonl")
        export_to_doccano(val, out_d / "val.jsonl")
        export_to_doccano(test, out_d / "test.jsonl")

        total = len(records)
        return {
            "total": total,
            "train": len(train),
            "train_pct": round((len(train) / total) * 100, 2) if total > 0 else 0,
            "val": len(val),
            "val_pct": round((len(val) / total) * 100, 2) if total > 0 else 0,
            "test": len(test),
            "test_pct": round((len(test) / total) * 100, 2) if total > 0 else 0,
        }
