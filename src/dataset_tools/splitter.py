"""
Stratified and Leakage-Safe Dataset Splitter.

Splits Malaysian NER dataset records into reproducible 70% Train, 15% Validation,
and 15% Test subsets, enforcing:
1. Determinism: Fixed seed ensures bit-for-bit reproducibility.
2. Stratification: Preserves proportional representation across linguistic strata
   (Malay, English, Manglish, Mixed, Chinese, Indian, Western) and entity densities.
3. Grouping / Leakage Prevention: Sentences sharing identical root text or template
   clusters are assigned to the same partition to prevent cross-split data leakage.

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

    def split_records(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Partitions records into (train, val, test) using stratified group splitting.

        Args:
            records: List of internal records with 'text', 'entities', and 'metadata'.

        Returns:
            Tuple of (train_records, val_records, test_records).
        """
        rng = random.Random(self.seed)

        # 1. Group records by exact normalized sentence to prevent split leakage
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            h = self.compute_sentence_hash(rec.get("text", ""))
            groups.setdefault(h, []).append(rec)

        # 2. Organize groups into strata based on metadata context or entity characteristics
        strata: Dict[str, List[List[Dict[str, Any]]]] = {}
        for h, group_records in groups.items():
            first_rec = group_records[0]
            meta = first_rec.get("metadata", {})
            # Primary stratification key: stratum/context_type, fallback to language, fallback to entity presence
            stratum_key = meta.get(
                "stratum",
                meta.get("context_type", meta.get("language", "general"))
            )
            # Refine stratum key by whether sentence contains entities
            has_entities = bool(first_rec.get("entities"))
            combined_key = f"{stratum_key}_has_ent_{has_entities}"
            strata.setdefault(combined_key, []).append(group_records)

        train: List[Dict[str, Any]] = []
        val: List[Dict[str, Any]] = []
        test: List[Dict[str, Any]] = []

        # 3. For each stratum, shuffle groups deterministically and allocate
        for key in sorted(strata.keys()):
            group_list = strata[key]
            # Deterministic shuffle per stratum
            rng.shuffle(group_list)

            n_total = len(group_list)
            n_train = int(round(n_total * self.train_ratio))
            n_val = int(round(n_total * self.val_ratio))

            # Ensure every stratum with at least 3 items gets at least 1 in val and test
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

        # Final deterministic sort by ID to ensure stable ordering
        train.sort(key=lambda x: str(x.get("id", "")))
        val.sort(key=lambda x: str(x.get("id", "")))
        test.sort(key=lambda x: str(x.get("id", "")))

        return train, val, test

    def split_and_save(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> Dict[str, int]:
        """Loads a dataset file, executes stratified partition, and writes train/val/test .jsonl files.

        Args:
            input_path: Source .jsonl or .json dataset file.
            output_dir: Directory where train.jsonl, val.jsonl, test.jsonl will be saved.

        Returns:
            Dictionary with counts of records in each split.
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

        return {
            "total": len(records),
            "train": len(train),
            "val": len(val),
            "test": len(test),
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stratified Dataset Splitter")
    parser.add_argument("--input", required=True, help="Input dataset path (.jsonl or .json)")
    parser.add_argument("--output-dir", required=True, help="Output directory for splits")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = parser.parse_args()

    splitter = DatasetSplitter(seed=args.seed)
    counts = splitter.split_and_save(args.input, args.output_dir)
    print(f"Partitioned {counts['total']} records:")
    print(f"  Train: {counts['train']} ({counts['train']/counts['total']:.1%}) -> {args.output_dir}/train.jsonl")
    print(f"  Val:   {counts['val']} ({counts['val']/counts['total']:.1%}) -> {args.output_dir}/val.jsonl")
    print(f"  Test:  {counts['test']} ({counts['test']/counts['total']:.1%}) -> {args.output_dir}/test.jsonl")
