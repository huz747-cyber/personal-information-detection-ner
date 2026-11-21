"""
Phase 5 — Malaysian-Aware NER Model Fine-Tuning Pipeline.

Fine-tunes a multilingual transformer (default: 'distilbert-base-multilingual-cased')
on Malaysian semantic Named Entity Recognition (PERSON, ORGANIZATION, LOCATION).

Features:
- Reproducible subword-to-IOB2 span alignment with offset mapping.
- Special-token and ignored-token (-100) handling.
- Deterministic training with fixed random seeds.
- Dynamic batch padding and AdamW optimizer with linear warmup scheduler.
- Validation tracking (loss, strict F1, relaxed F1).
- Best-model checkpointing and configuration export.

Author: AI/ML Club
License: Apache-2.0
"""

import argparse
import json
import os
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoConfig,
    AutoModelForTokenClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

# Standard IOB2 schema for Malaysian semantic NER
LABELS: List[str] = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-ORGANIZATION",
    "I-ORGANIZATION",
    "B-LOCATION",
    "I-LOCATION",
]

ID2LABEL: Dict[int, str] = {i: l for i, l in enumerate(LABELS)}
LABEL2ID: Dict[str, int] = {l: i for i, l in enumerate(LABELS)}


def set_seed(seed: int = 42) -> None:
    """Sets random seeds across standard library, NumPy, and PyTorch for deterministic training."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Loads JSONLines records."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class MalaysianNERDataset(Dataset):
    """PyTorch Dataset for Token Classification with subword offset alignment."""

    def __init__(
        self,
        records: List[Dict[str, Any]],
        tokenizer: Any,
        max_length: int = 128,
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.features = [self._process_record(r) for r in records]

    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        text = record["text"]
        raw_labels = record.get("label", record.get("entities", []))

        # Standardize gold entities
        gold_entities = []
        for item in raw_labels:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                gold_entities.append({"start": item[0], "end": item[1], "label": item[2]})
            elif isinstance(item, dict):
                gold_entities.append({"start": item["start"], "end": item["end"], "label": item["label"]})

        encoding = self.tokenizer(
            text,
            return_offsets_mapping=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors=None,
        )

        offsets = encoding["offset_mapping"]
        labels = []

        for start, end in offsets:
            # Special tokens ([CLS], [SEP], padding) have offset (0, 0)
            if start == 0 and end == 0:
                labels.append(-100)
                continue

            matched_label = "O"
            for ent in gold_entities:
                s, e, l = ent["start"], ent["end"], ent["label"]
                if max(start, s) < min(end, e):
                    # Subword token falls within or overlaps with the entity
                    if start == s:
                        matched_label = f"B-{l}"
                    else:
                        matched_label = f"I-{l}"
                    break

            labels.append(LABEL2ID.get(matched_label, 0))

        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": labels,
            "text": text,
            "gold_entities": gold_entities,
        }

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.features[idx]


def collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    """Dynamically pads input_ids, attention_mask, and labels to the max length in batch."""
    max_len = max(len(item["input_ids"]) for item in batch)

    batch_input_ids = []
    batch_attention_mask = []
    batch_labels = []

    for item in batch:
        pad_len = max_len - len(item["input_ids"])
        batch_input_ids.append(item["input_ids"] + [0] * pad_len)
        batch_attention_mask.append(item["attention_mask"] + [0] * pad_len)
        batch_labels.append(item["labels"] + [-100] * pad_len)

    return {
        "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(batch_attention_mask, dtype=torch.long),
        "labels": torch.tensor(batch_labels, dtype=torch.long),
    }


def predict_entities(
    model: Any,
    tokenizer: Any,
    text: str,
    device: torch.device,
    max_length: int = 128,
) -> List[Dict[str, Any]]:
    """Predicts named entities from raw text, reconstructing character spans from subword offsets."""
    model.eval()
    encoding = tokenizer(
        text,
        return_offsets_mapping=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    offsets = encoding.pop("offset_mapping")[0].tolist()
    inputs = {k: v.to(device) for k, v in encoding.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[0]
        probs = torch.softmax(logits, dim=-1)
        pred_ids = torch.argmax(logits, dim=-1).tolist()
        pred_scores = probs.max(dim=-1).values.tolist()

    entities: List[Dict[str, Any]] = []
    curr: Optional[Dict[str, Any]] = None

    for (s, e), lab_id, score in zip(offsets, pred_ids, pred_scores):
        if s == 0 and e == 0:
            continue
        lab = ID2LABEL.get(lab_id, "O")

        if lab.startswith("B-"):
            if curr:
                entities.append(curr)
            curr = {
                "start": s,
                "end": e,
                "label": lab[2:],
                "scores": [score],
            }
        elif lab.startswith("I-"):
            ent_type = lab[2:]
            if curr and curr["label"] == ent_type:
                curr["end"] = e
                curr["scores"].append(score)
            else:
                if curr:
                    entities.append(curr)
                curr = {
                    "start": s,
                    "end": e,
                    "label": ent_type,
                    "scores": [score],
                }
        else:  # "O"
            if curr:
                entities.append(curr)
                curr = None

    if curr:
        entities.append(curr)

    for ent in entities:
        ent["text"] = text[ent["start"]:ent["end"]]
        ent["score"] = round(float(sum(ent["scores"]) / len(ent["scores"])), 4)
        del ent["scores"]

    return entities


def evaluate_dataset(
    model: Any,
    tokenizer: Any,
    records: List[Dict[str, Any]],
    device: torch.device,
    max_length: int = 128,
) -> Dict[str, Any]:
    """Runs evaluation across records and computes strict and relaxed Precision, Recall, and F1."""
    total_strict_tp = 0
    total_strict_fp = 0
    total_strict_fn = 0

    total_relaxed_tp = 0
    total_relaxed_fp = 0
    total_relaxed_fn = 0

    for r in records:
        text = r["text"]
        raw_labels = r.get("label", r.get("entities", []))
        golds = []
        for item in raw_labels:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                golds.append({"start": item[0], "end": item[1], "label": item[2]})
            elif isinstance(item, dict):
                golds.append({"start": item["start"], "end": item["end"], "label": item["label"]})

        preds = predict_entities(model, tokenizer, text, device=device, max_length=max_length)

        # Strict matching
        unmatched_golds = list(golds)
        for p in preds:
            match = None
            for g in unmatched_golds:
                if p["label"] == g["label"] and p["start"] == g["start"] and p["end"] == g["end"]:
                    match = g
                    break
            if match:
                total_strict_tp += 1
                unmatched_golds.remove(match)
            else:
                total_strict_fp += 1
        total_strict_fn += len(unmatched_golds)

        # Relaxed matching
        unmatched_golds_rel = list(golds)
        for p in preds:
            match = None
            for g in unmatched_golds_rel:
                if p["label"] == g["label"] and max(p["start"], g["start"]) < min(p["end"], g["end"]):
                    match = g
                    break
            if match:
                total_relaxed_tp += 1
                unmatched_golds_rel.remove(match)
            else:
                total_relaxed_fp += 1
        total_relaxed_fn += len(unmatched_golds_rel)

    strict_p = total_strict_tp / (total_strict_tp + total_strict_fp) if (total_strict_tp + total_strict_fp) > 0 else 0.0
    strict_r = total_strict_tp / (total_strict_tp + total_strict_fn) if (total_strict_tp + total_strict_fn) > 0 else 0.0
    strict_f1 = 2 * strict_p * strict_r / (strict_p + strict_r) if (strict_p + strict_r) > 0 else 0.0

    relaxed_p = total_relaxed_tp / (total_relaxed_tp + total_relaxed_fp) if (total_relaxed_tp + total_relaxed_fp) > 0 else 0.0
    relaxed_r = total_relaxed_tp / (total_relaxed_tp + total_relaxed_fn) if (total_relaxed_tp + total_relaxed_fn) > 0 else 0.0
    relaxed_f1 = 2 * relaxed_p * relaxed_r / (relaxed_p + relaxed_r) if (relaxed_p + relaxed_r) > 0 else 0.0

    return {
        "strict_precision": round(strict_p, 4),
        "strict_recall": round(strict_r, 4),
        "strict_f1": round(strict_f1, 4),
        "relaxed_precision": round(relaxed_p, 4),
        "relaxed_recall": round(relaxed_r, 4),
        "relaxed_f1": round(relaxed_f1, 4),
    }


def train_model(
    train_path: Path,
    val_path: Path,
    output_dir: Path,
    reports_dir: Path,
    model_name: str = "distilbert-base-multilingual-cased",
    batch_size: int = 16,
    lr: float = 3e-5,
    epochs: int = 6,
    max_length: int = 128,
    seed: int = 42,
    weight_decay: float = 0.01,
    warmup_ratio: float = 0.1,
) -> Dict[str, Any]:
    """Fine-tunes the multilingual transformer model for Malaysian NER."""
    set_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Training device: {device}")
    print(f"[*] Base model: {model_name}")

    print(f"[*] Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print(f"[*] Configuring classification head ({len(LABELS)} classes)...")
    config = AutoConfig.from_pretrained(
        model_name,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model = AutoModelForTokenClassification.from_pretrained(model_name, config=config)
    model.to(device)

    # Load records
    train_records = load_jsonl(train_path)
    val_records = load_jsonl(val_path)
    print(f"[*] Loaded {len(train_records)} training records from {train_path}")
    print(f"[*] Loaded {len(val_records)} validation records from {val_path}")

    train_dataset = MalaysianNERDataset(train_records, tokenizer, max_length=max_length)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
    )

    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * warmup_ratio)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    training_history = []
    best_val_f1 = -1.0
    best_epoch = -1

    start_time = time.time()

    print("\n" + "=" * 70)
    print("BEGINNING MULTILINGUAL TRANSFORMER FINE-TUNING")
    print("=" * 70)

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        step_count = 0

        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            step_count += 1

        avg_train_loss = epoch_loss / step_count if step_count > 0 else 0.0

        # Validation evaluation
        val_metrics = evaluate_dataset(model, tokenizer, val_records, device=device, max_length=max_length)

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "val_strict_precision": val_metrics["strict_precision"],
            "val_strict_recall": val_metrics["strict_recall"],
            "val_strict_f1": val_metrics["strict_f1"],
            "val_relaxed_f1": val_metrics["relaxed_f1"],
            "learning_rate": round(scheduler.get_last_lr()[0], 8),
        }
        training_history.append(epoch_record)

        print(
            f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_train_loss:.4f} | "
            f"Val Strict F1: {val_metrics['strict_f1']*100:.2f}% (P: {val_metrics['strict_precision']*100:.1f}%, R: {val_metrics['strict_recall']*100:.1f}%) | "
            f"Val Relaxed F1: {val_metrics['relaxed_f1']*100:.2f}%"
        )

        # Checkpoint if best strict F1 (or relaxed F1 if tie)
        if val_metrics["strict_f1"] > best_val_f1:
            best_val_f1 = val_metrics["strict_f1"]
            best_epoch = epoch
            print(f"  [*] New best validation Strict F1: {best_val_f1*100:.2f}%. Saving checkpoint to {output_dir}...")
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

    total_duration = time.time() - start_time
    print("=" * 70)
    print(f"[+] Fine-tuning completed in {total_duration:.2f}s ({total_duration/60:.2f}m). Best Epoch: {best_epoch} (Strict F1: {best_val_f1*100:.2f}%)")

    # Save training config
    training_config = {
        "model_name": model_name,
        "base_model_license": "Apache-2.0",
        "train_dataset": str(train_path),
        "train_record_count": len(train_records),
        "val_dataset": str(val_path),
        "val_record_count": len(val_records),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "weight_decay": weight_decay,
        "warmup_ratio": warmup_ratio,
        "max_length": max_length,
        "seed": seed,
        "best_epoch": best_epoch,
        "best_val_strict_f1": best_val_f1,
        "training_duration_seconds": round(total_duration, 2),
        "device": str(device),
        "output_dir": str(output_dir),
    }

    config_file = reports_dir / "phase5_training_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(training_config, f, indent=2)
    print(f"[+] Saved training configuration to {config_file}")

    history_file = reports_dir / "phase5_training_history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2)
    print(f"[+] Saved training history to {history_file}")

    return {
        "config": training_config,
        "history": training_history,
        "best_model_dir": str(output_dir),
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 5 Malaysian NER Multilingual Fine-Tuning Runner.")
    parser.add_argument("--train-path", type=str, default="data/splits/commercial/train.jsonl")
    parser.add_argument("--val-path", type=str, default="data/splits/commercial/val.jsonl")
    parser.add_argument("--output-dir", type=str, default="models/malaysian_ner_distilbert_multilingual")
    parser.add_argument("--reports-dir", type=str, default="data/reports")
    parser.add_argument("--model-name", type=str, default="distilbert-base-multilingual-cased")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)

    args = parser.parse_args()

    train_model(
        train_path=Path(args.train_path),
        val_path=Path(args.val_path),
        output_dir=Path(args.output_dir),
        reports_dir=Path(args.reports_dir),
        model_name=args.model_name,
        batch_size=args.batch_size,
        lr=args.lr,
        epochs=args.epochs,
        max_length=args.max_length,
        seed=args.seed,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
    )


if __name__ == "__main__":
    main()
