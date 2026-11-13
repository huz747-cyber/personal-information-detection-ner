"""
Benchmark Evaluation Tool for Named Entity Recognition.

Evaluates NER model predictions against a ground-truth annotated benchmark dataset
(e.g., `examples/malaysian_benchmark.json`). Computes Precision, Recall, and F1
scores for both Strict Match (exact span boundaries) and Relaxed Match (overlapping spans),
with per-class breakdowns.

Supports comparative evaluation:
    Runs the baseline model (stitching disabled) vs. Phase 1 (patronymic stitching enabled)
    to quantify the empirical impact of Malaysian patronymic consolidation.

Usage:
    python src/evaluate_benchmark.py
    python src/evaluate_benchmark.py --benchmark examples/malaysian_benchmark.json
    python src/evaluate_benchmark.py --compare
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

# Support direct script execution
try:
    from entity_extractor import PersonalInformationDetector
except ImportError:
    from src.entity_extractor import PersonalInformationDetector


def compute_metrics(
    predictions_per_sample: List[List[Dict[str, Any]]],
    ground_truth_per_sample: List[List[Dict[str, Any]]],
    relaxed: bool = False,
) -> Dict[str, Any]:
    """Computes Precision, Recall, and F1 score across all samples.

    Args:
        predictions_per_sample: Predicted entities for each benchmark sentence.
        ground_truth_per_sample: Annotated ground-truth entities for each sentence.
        relaxed: If True, considers a match if spans overlap; if False, requires exact span match.

    Returns:
        Dict containing micro-averaged overall metrics and per-class breakdowns.
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0

    class_counts: Dict[str, Dict[str, int]] = {}

    for preds, targets in zip(predictions_per_sample, ground_truth_per_sample):
        unmatched_targets = list(targets)

        for p in preds:
            p_label = p["label"]
            if p_label not in class_counts:
                class_counts[p_label] = {"tp": 0, "fp": 0, "fn": 0}

            matched = False
            for idx, t in enumerate(unmatched_targets):
                if p_label != t["label"]:
                    continue

                if relaxed:
                    # Overlap match: spans overlap by at least 1 character
                    is_match = max(p["start"], t["start"]) < min(p["end"], t["end"])
                else:
                    # Strict match: exact character offsets
                    is_match = p["start"] == t["start"] and p["end"] == t["end"]

                if is_match:
                    matched = True
                    unmatched_targets.pop(idx)
                    total_tp += 1
                    class_counts[p_label]["tp"] += 1
                    break

            if not matched:
                total_fp += 1
                class_counts[p_label]["fp"] += 1

        for t in unmatched_targets:
            t_label = t["label"]
            if t_label not in class_counts:
                class_counts[t_label] = {"tp": 0, "fp": 0, "fn": 0}
            total_fn += 1
            class_counts[t_label]["fn"] += 1

    def calc_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return round(prec, 4), round(rec, 4), round(f1, 4)

    overall_prec, overall_rec, overall_f1 = calc_f1(total_tp, total_fp, total_fn)

    per_class_metrics = {}
    for label, counts in class_counts.items():
        p, r, f = calc_f1(counts["tp"], counts["fp"], counts["fn"])
        per_class_metrics[label] = {
            "precision": p,
            "recall": r,
            "f1": f,
            "tp": counts["tp"],
            "fp": counts["fp"],
            "fn": counts["fn"],
        }

    return {
        "precision": overall_prec,
        "recall": overall_rec,
        "f1": overall_f1,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "per_class": per_class_metrics,
    }


def print_evaluation_table(title: str, strict: Dict[str, Any], relaxed: Dict[str, Any]) -> None:
    """Renders a formatted ASCII summary of evaluation metrics."""
    print("\n" + "=" * 70)
    print(f"EVALUATION REPORT: {title.upper()}")
    print("=" * 70)
    print(f"{'Evaluation Mode':<20} | {'Precision':<12} | {'Recall':<12} | {'F1 Score':<12}")
    print("-" * 70)
    print(f"{'Strict (Exact Spans)':<20} | {strict['precision']*100:<11.1f}% | {strict['recall']*100:<11.1f}% | {strict['f1']*100:<11.1f}%")
    print(f"{'Relaxed (Overlap)':<20} | {relaxed['precision']*100:<11.1f}% | {relaxed['recall']*100:<11.1f}% | {relaxed['f1']*100:<11.1f}%")
    print("-" * 70)

    print("\n[Per-Class Breakdown (Strict Match)]")
    print(f"{'Entity Class':<18} | {'Precision':<12} | {'Recall':<12} | {'F1 Score':<12} | {'TP/FP/FN'}")
    print("-" * 70)
    for cls_name, vals in sorted(strict["per_class"].items()):
        counts_str = f"{vals['tp']}/{vals['fp']}/{vals['fn']}"
        print(f"{cls_name:<18} | {vals['precision']*100:<11.1f}% | {vals['recall']*100:<11.1f}% | {vals['f1']*100:<11.1f}% | {counts_str}")
    print("=" * 70)


def evaluate(
    detector: PersonalInformationDetector,
    benchmark_data: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Runs predictions on all samples and calculates strict and relaxed metrics."""
    all_preds = []
    all_targets = []

    for item in benchmark_data:
        text = item["text"]
        preds = detector.detect(text)
        all_preds.append(preds)
        all_targets.append(item["entities"])

    strict = compute_metrics(all_preds, all_targets, relaxed=False)
    relaxed = compute_metrics(all_preds, all_targets, relaxed=True)
    return strict, relaxed


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate NER predictions on annotated benchmark.")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="examples/malaysian_benchmark.json",
        help="Path to the JSON benchmark file with ground-truth entity spans.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Entity confidence threshold (default: 0.50).",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        default=True,
        help="Run comparative evaluation between Baseline (no stitching) and Phase 1 (stitching).",
    )

    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    if not benchmark_path.exists():
        # Fallback to repo relative path if executed from nested dir
        benchmark_path = Path(__file__).resolve().parent.parent / args.benchmark

    if not benchmark_path.exists():
        print(f"Error: Benchmark file '{args.benchmark}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)

    print(f"[*] Loaded {len(benchmark_data)} test cases from '{benchmark_path}'.")

    if args.compare:
        print("\n[*] 1. Evaluating BASELINE (stitching disabled, hybrid disabled)...")
        baseline_detector = PersonalInformationDetector(
            confidence_threshold=args.threshold,
            enable_patronymic_stitching=False,
            enable_hybrid=False,
        )
        base_strict, base_relaxed = evaluate(baseline_detector, benchmark_data)
        print_evaluation_table("Baseline Model (Raw DistilBERT Only)", base_strict, base_relaxed)

        print("\n[*] 2. Evaluating PHASE 1 (patronymic stitching enabled, hybrid disabled)...")
        phase1_detector = PersonalInformationDetector(
            confidence_threshold=args.threshold,
            enable_patronymic_stitching=True,
            enable_hybrid=False,
        )
        p1_strict, p1_relaxed = evaluate(phase1_detector, benchmark_data)
        print_evaluation_table("Phase 1 Model (Patronymic Stitching Only)", p1_strict, p1_relaxed)

        print("\n[*] 3. Evaluating PHASE 2 (full hybrid recognizer layer enabled)...")
        phase2_detector = PersonalInformationDetector(
            confidence_threshold=args.threshold,
            enable_patronymic_stitching=True,
            enable_hybrid=True,
        )
        p2_strict, p2_relaxed = evaluate(phase2_detector, benchmark_data)
        print_evaluation_table("Phase 2 Model (Full Hybrid Recognizer Layer)", p2_strict, p2_relaxed)

        # Delta comparisons
        p1_strict_delta = (p1_strict["f1"] - base_strict["f1"]) * 100
        p2_strict_delta = (p2_strict["f1"] - base_strict["f1"]) * 100
        print("\n" + "#" * 70)
        print("EMPIRICAL COMPARISON SUMMARY (BASELINE ➔ PHASE 1 ➔ PHASE 2)")
        print("#" * 70)
        print(f"Overall Strict F1:  Baseline = {base_strict['f1']*100:.1f}% ➔ Phase 1 = {p1_strict['f1']*100:.1f}% ➔ Phase 2 = {p2_strict['f1']*100:.1f}% (Total Δ {p2_strict_delta:+.1f}%)")
        print(f"Relaxed F1:         Baseline = {base_relaxed['f1']*100:.1f}% ➔ Phase 1 = {p1_relaxed['f1']*100:.1f}% ➔ Phase 2 = {p2_relaxed['f1']*100:.1f}%")
        print("#" * 70 + "\n")
    else:
        detector = PersonalInformationDetector(
            confidence_threshold=args.threshold,
            enable_patronymic_stitching=True,
        )
        strict, relaxed = evaluate(detector, benchmark_data)
        print_evaluation_table("Benchmark Evaluation", strict, relaxed)


if __name__ == "__main__":
    main()
