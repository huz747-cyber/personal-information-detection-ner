"""
Fine-Tuning Script for DistilBERT on the CoNLL-2003 Named Entity Recognition Dataset.

NOTE: This script is prepared for future model training and fine-tuning.
The initial project prototype runs pretrained inference via `src/predict.py`.

Dataset Overview:
    CoNLL-2003 is a standard benchmark for Named Entity Recognition containing
    news stories annotated with 4 entity types:
      - PER (Person)
      - ORG (Organization)
      - LOC (Location)
      - MISC (Miscellaneous)

Key Concepts for Beginners:
    1. Token Classification: Each subword token is classified into an entity tag.
    2. Subword Alignment: Models like DistilBERT split words into subwords (e.g.,
       'Washington' -> 'Wash', '##ington'). We align labels by assigning -100
       (PyTorch ignore index) to special tokens and continuation subwords.
    3. Seqeval: The gold-standard evaluation library that computes strict F1,
       Precision, and Recall at the entity-span level, not just per-token accuracy.

Usage Examples:
    # 1. Quick test run with a small sample (verifies pipeline end-to-end):
    python src/train.py --max_train_samples 200 --max_eval_samples 50 --epochs 1

    # 2. Full fine-tuning run:
    python src/train.py --epochs 3 --batch_size 16 --learning_rate 2e-5 --output_dir ./models/distilbert-ner-finetuned
"""

import argparse
import os
from typing import Dict, List, Tuple
import evaluate
import numpy as np
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    """Parses command line arguments for training configuration."""
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT on CoNLL-2003 NER.")
    parser.add_argument(
        "--model_name",
        type=str,
        default="distilbert-base-cased",
        help="Base pretrained model checkpoint to fine-tune (default: 'distilbert-base-cased').",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./models/distilbert-ner-finetuned",
        help="Directory where the trained model weights and tokenizer will be saved.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3).",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Batch size per device for training and evaluation (default: 16).",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-5,
        help="Initial learning rate for AdamW optimizer (default: 2e-5).",
    )
    parser.add_argument(
        "--weight_decay",
        type=float,
        default=0.01,
        help="Weight decay for regularization (default: 0.01).",
    )
    parser.add_argument(
        "--max_train_samples",
        type=int,
        default=None,
        help="Truncate training dataset to this number of samples (useful for fast smoke tests).",
    )
    parser.add_argument(
        "--max_eval_samples",
        type=int,
        default=None,
        help="Truncate evaluation dataset to this number of samples.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="If set, only downloads data and validates tokenization without starting training.",
    )
    return parser.parse_args()


def tokenize_and_align_labels(
    examples: Dict[str, List],
    tokenizer: AutoTokenizer,
    label_all_tokens: bool = False,
) -> Dict[str, List]:
    """Tokenizes text and aligns CoNLL-2003 word-level labels with subword tokens.

    When words are broken down into subwords (e.g. 'Amsterdam' -> ['Am', '##ster', '##dam']),
    the first subword retains the entity label, while continuation subwords can either
    be assigned -100 (ignored by PyTorch CrossEntropyLoss) or the same label.

    Args:
        examples: Batch of raw dataset records containing 'tokens' and 'ner_tags'.
        tokenizer: Hugging Face tokenizer instance.
        label_all_tokens: Whether to propagate the tag to all subwords or only the first.

    Returns:
        Dict of tokenized inputs with properly aligned 'labels'.
    """
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []

        for word_idx in word_ids:
            if word_idx is None:
                # Special tokens like [CLS], [SEP] get -100 so loss is not computed on them
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # First subword token for this word
                label_ids.append(label[word_idx])
            else:
                # Continuation subword token (e.g. '##dam')
                label_ids.append(label[word_idx] if label_all_tokens else -100)
            previous_word_idx = word_idx

        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs


def build_compute_metrics(label_list: List[str]):
    """Builds the evaluation metric function using seqeval.

    Args:
        label_list: List of class names indexed by label ID.

    Returns:
        Callable function suitable for `Trainer(compute_metrics=...)`.
    """
    seqeval_metric = evaluate.load("seqeval")

    def compute_metrics(p: Tuple[np.ndarray, np.ndarray]) -> Dict[str, float]:
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (-100) and convert IDs to string labels
        true_predictions = [
            [label_list[p_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [label_list[l_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
            for prediction, label in zip(predictions, labels)
        ]

        results = seqeval_metric.compute(predictions=true_predictions, references=true_labels)
        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    return compute_metrics


def main() -> None:
    args = parse_args()
    print("=" * 70)
    print("CoNLL-2003 DISTILBERT NER FINE-TUNING PIPELINE")
    print("=" * 70)
    print(f"Base model:     {args.model_name}")
    print(f"Output dir:     {args.output_dir}")
    print(f"Epochs:         {args.epochs}")
    print(f"Batch size:     {args.batch_size}")
    print(f"Learning rate:  {args.learning_rate}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device:     {torch.cuda.get_device_name(0)}")
    print("=" * 70)

    # 1. Load dataset
    print("[*] Loading CoNLL-2003 dataset from Hugging Face Datasets...")
    dataset = load_dataset("conll2003")
    label_list = dataset["train"].features["ner_tags"].feature.names
    print(f"[+] Loaded dataset successfully. Label classes: {label_list}")

    # Build ID <-> Label mappings
    id2label = {i: label for i, label in enumerate(label_list)}
    label2id = {label: i for i, label in enumerate(label_list)}

    # 2. Load tokenizer and model
    print(f"[*] Initializing tokenizer and base model '{args.model_name}'...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
    )

    # 3. Tokenize datasets
    print("[*] Preprocessing and aligning subwords with entity labels...")
    tokenized_datasets = dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
    )

    train_data = tokenized_datasets["train"]
    eval_data = tokenized_datasets["validation"]

    if args.max_train_samples:
        train_data = train_data.select(range(min(args.max_train_samples, len(train_data))))
    if args.max_eval_samples:
        eval_data = eval_data.select(range(min(args.max_eval_samples, len(eval_data))))

    print(f"[+] Ready for training: {len(train_data)} train samples, {len(eval_data)} eval samples.")

    if args.dry_run:
        print("[!] Dry-run enabled. Dataset verified. Skipping training execution.")
        return

    # 4. Data collator & metrics
    data_collator = DataCollatorForTokenClassification(tokenizer)
    compute_metrics_fn = build_compute_metrics(label_list)

    # 5. Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=args.weight_decay,
        logging_dir=os.path.join(args.output_dir, "logs"),
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=2,
        report_to="none",  # Do not require wandb or external logging
    )

    # 6. Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics_fn,
    )

    # 7. Execute training
    print("\n[*] Starting training loop...")
    trainer.train()

    # 8. Final evaluation and saving
    print("\n[*] Evaluating best model on validation split...")
    eval_results = trainer.evaluate()
    print("Evaluation Results:", eval_results)

    print(f"[*] Saving fine-tuned model and tokenizer to '{args.output_dir}'...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[+] Model training complete! Saved to '{args.output_dir}'.")


if __name__ == "__main__":
    main()
