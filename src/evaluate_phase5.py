"""
Phase 5 Comprehensive Evaluation & Baseline Comparison Suite.

Evaluates the fine-tuned multilingual model across three configurations:
1. Config 1-FT: Fine-tuned multilingual model alone (pure learned model, no gazetteers, no rules)
2. Config 2-FT: Fine-tuned multilingual model + patronymic stitcher (Phase 1)
3. Config 3-FT: Fine-tuned multilingual model + full Phase 2 hybrid system (stitcher + gazetteers + rules)

Generates:
- Direct delta comparison with Phase 4 baseline (dslim/distilbert-NER)
- Per-entity metrics (PERSON, ORGANIZATION, LOCATION)
- Seven-category sociolinguistic breakdown
- Gazetteer leakage & unseen entity generalisation analysis
- Hard-negative rejection auditing
- Concrete error analysis

Author: AI/ML Club
License: Apache-2.0
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict

try:
    from evaluate_phase4 import (
        load_jsonl,
        extract_gold_entities,
        compute_metrics,
        compute_confusion_matrix,
        evaluate_hard_negatives,
        evaluate_gazetteer_leakage,
        collect_error_cases,
    )
    from entity_extractor import PersonalInformationDetector
except ImportError:
    from src.evaluate_phase4 import (
        load_jsonl,
        extract_gold_entities,
        compute_metrics,
        compute_confusion_matrix,
        evaluate_hard_negatives,
        evaluate_gazetteer_leakage,
        collect_error_cases,
    )
    from src.entity_extractor import PersonalInformationDetector


def run_phase5_evaluation(
    model_dir: str,
    test_split_path: Path,
    output_dir: Path,
    phase4_baseline_path: Optional[Path] = None,
    threshold: float = 0.50,
    file_prefix: str = "phase5",
) -> Dict[str, Any]:
    """Runs full Phase 5 evaluation across all configurations and generates comparison reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records = load_jsonl(test_split_path)
    print(f"[*] Loaded {len(records)} test records from {test_split_path}")

    ground_truth = [extract_gold_entities(r) for r in records]

    # Initialize Phase 5 detectors with the fine-tuned model checkpoint
    print(f"\n[*] Initializing Config 1-FT: Fine-Tuned Multilingual Model Alone (Model-Only)...")
    c1_detector = PersonalInformationDetector(
        model_name=model_dir,
        confidence_threshold=threshold,
        enable_patronymic_stitching=False,
        enable_hybrid=False,
        include_structured_pii=False,
    )

    print(f"\n[*] Initializing Config 2-FT: Fine-Tuned Model + Patronymic Stitcher...")
    c2_detector = PersonalInformationDetector(
        model_name=model_dir,
        confidence_threshold=threshold,
        enable_patronymic_stitching=True,
        enable_hybrid=False,
        include_structured_pii=False,
    )

    print(f"\n[*] Initializing Config 3-FT: Fine-Tuned Model + Full Phase 2 Hybrid System...")
    c3_detector = PersonalInformationDetector(
        model_name=model_dir,
        confidence_threshold=threshold,
        enable_patronymic_stitching=True,
        enable_hybrid=True,
        include_structured_pii=False,
    )

    print("\n[*] Generating predictions across test records...")
    c1_preds = [c1_detector.detect(r["text"]) for r in records]
    c2_preds = [c2_detector.detect(r["text"]) for r in records]
    c3_preds = [c3_detector.detect(r["text"]) for r in records]

    # Compute configuration metrics
    configs_metrics = {}
    for name, preds in [
        ("Config 1-FT: Multilingual Model Alone", c1_preds),
        ("Config 2-FT: Model + Stitcher", c2_preds),
        ("Config 3-FT: Full Hybrid (Phase 5)", c3_preds),
    ]:
        strict = compute_metrics(preds, ground_truth, relaxed=False, target_labels={"PERSON", "ORGANIZATION", "LOCATION"})
        relaxed = compute_metrics(preds, ground_truth, relaxed=True, target_labels={"PERSON", "ORGANIZATION", "LOCATION"})
        cm = compute_confusion_matrix(preds, ground_truth)
        hn = evaluate_hard_negatives(records, preds)

        configs_metrics[name] = {
            "strict": strict,
            "relaxed": relaxed,
            "confusion_matrix": cm,
            "hard_negatives": hn,
        }

    # Per-category metrics (using Config 3-FT)
    strata_groups = defaultdict(list)
    for idx, r in enumerate(records):
        strat = r.get("meta", {}).get("stratum", "unknown")
        strata_groups[strat].append(idx)

    per_category_metrics = {}
    for strat, indices in sorted(strata_groups.items()):
        sub_preds = [c3_preds[i] for i in indices]
        sub_golds = [ground_truth[i] for i in indices]
        sub_records = [records[i] for i in indices]

        sub_strict = compute_metrics(sub_preds, sub_golds, relaxed=False, target_labels={"PERSON", "ORGANIZATION", "LOCATION"})
        sub_relaxed = compute_metrics(sub_preds, sub_golds, relaxed=True, target_labels={"PERSON", "ORGANIZATION", "LOCATION"})
        sub_hn = evaluate_hard_negatives(sub_records, sub_preds)

        per_category_metrics[strat] = {
            "sentence_count": len(indices),
            "gold_entity_count": sum(len(g) for g in sub_golds),
            "strict_precision": sub_strict["precision"],
            "strict_recall": sub_strict["recall"],
            "strict_f1": sub_strict["f1"],
            "relaxed_f1": sub_relaxed["f1"],
            "per_class": sub_strict["per_class"],
            "hard_negatives": sub_hn,
        }

    # Gazetteer leakage & unseen entity generalisation analysis
    preds_dict = {
        "Config 1-FT (Model Alone)": c1_preds,
        "Config 2-FT (Stitcher)": c2_preds,
        "Config 3-FT (Hybrid)": c3_preds,
    }
    gazetteer_analysis = evaluate_gazetteer_leakage(records, preds_dict, ground_truth)

    # Error analysis
    error_cases = collect_error_cases(records, c3_preds, ground_truth)

    # Baseline comparison with Phase 4 if provided
    comparison = {}
    if phase4_baseline_path and phase4_baseline_path.exists():
        with open(phase4_baseline_path, "r", encoding="utf-8") as f:
            p4_data = json.load(f)

        p4_c1 = p4_data.get("configurations", {}).get("Config 1: Raw DistilBERT", {})
        p4_c2 = p4_data.get("configurations", {}).get("Config 2: DistilBERT + Stitcher (Phase 1)", {})
        p4_c3 = p4_data.get("configurations", {}).get("Config 3: Full Hybrid (Phase 2)", {})

        comparison = {
            "Config 1 (Model Alone)": {
                "phase4_strict_f1": p4_c1.get("strict", {}).get("f1", 0.0),
                "phase5_strict_f1": configs_metrics["Config 1-FT: Multilingual Model Alone"]["strict"]["f1"],
                "delta_strict_f1": round(
                    configs_metrics["Config 1-FT: Multilingual Model Alone"]["strict"]["f1"] - p4_c1.get("strict", {}).get("f1", 0.0), 4
                ),
                "phase4_relaxed_f1": p4_c1.get("relaxed", {}).get("f1", 0.0),
                "phase5_relaxed_f1": configs_metrics["Config 1-FT: Multilingual Model Alone"]["relaxed"]["f1"],
                "delta_relaxed_f1": round(
                    configs_metrics["Config 1-FT: Multilingual Model Alone"]["relaxed"]["f1"] - p4_c1.get("relaxed", {}).get("f1", 0.0), 4
                ),
            },
            "Config 2 (Stitcher)": {
                "phase4_strict_f1": p4_c2.get("strict", {}).get("f1", 0.0),
                "phase5_strict_f1": configs_metrics["Config 2-FT: Model + Stitcher"]["strict"]["f1"],
                "delta_strict_f1": round(
                    configs_metrics["Config 2-FT: Model + Stitcher"]["strict"]["f1"] - p4_c2.get("strict", {}).get("f1", 0.0), 4
                ),
                "phase4_relaxed_f1": p4_c2.get("relaxed", {}).get("f1", 0.0),
                "phase5_relaxed_f1": configs_metrics["Config 2-FT: Model + Stitcher"]["relaxed"]["f1"],
                "delta_relaxed_f1": round(
                    configs_metrics["Config 2-FT: Model + Stitcher"]["relaxed"]["f1"] - p4_c2.get("relaxed", {}).get("f1", 0.0), 4
                ),
            },
            "Config 3 (Full Hybrid)": {
                "phase4_strict_f1": p4_c3.get("strict", {}).get("f1", 0.0),
                "phase5_strict_f1": configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["strict"]["f1"],
                "delta_strict_f1": round(
                    configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["strict"]["f1"] - p4_c3.get("strict", {}).get("f1", 0.0), 4
                ),
                "phase4_relaxed_f1": p4_c3.get("relaxed", {}).get("f1", 0.0),
                "phase5_relaxed_f1": configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["relaxed"]["f1"],
                "delta_relaxed_f1": round(
                    configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["relaxed"]["f1"] - p4_c3.get("relaxed", {}).get("f1", 0.0), 4
                ),
                "per_class_deltas": {
                    cls: {
                        "phase4_strict_f1": p4_c3.get("strict", {}).get("per_class", {}).get(cls, {}).get("f1", 0.0),
                        "phase5_strict_f1": configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["strict"]["per_class"].get(cls, {}).get("f1", 0.0),
                        "delta_strict_f1": round(
                            configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["strict"]["per_class"].get(cls, {}).get("f1", 0.0)
                            - p4_c3.get("strict", {}).get("per_class", {}).get(cls, {}).get("f1", 0.0),
                            4,
                        ),
                    }
                    for cls in ["PERSON", "ORGANIZATION", "LOCATION"]
                },
                "hard_negative_rejection_delta": round(
                    configs_metrics["Config 3-FT: Full Hybrid (Phase 5)"]["hard_negatives"]["rejection_accuracy"]
                    - p4_c3.get("hard_negatives", {}).get("rejection_accuracy", 0.0),
                    4,
                ),
            },
        }

    # Save deliverables
    summary_report = {
        "test_dataset": str(test_split_path),
        "total_records": len(records),
        "total_gold_entities": sum(len(g) for g in ground_truth),
        "configurations": configs_metrics,
        "comparison_with_phase4": comparison,
        "per_category": per_category_metrics,
        "gazetteer_leakage": gazetteer_analysis,
        "error_summary": {k: len(v) for k, v in error_cases.items()},
    }

    # 1. Baseline Comparison JSON
    with open(output_dir / f"phase5_baseline_comparison_{file_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    # 2. Per-category metrics JSON
    with open(output_dir / f"phase5_per_category_metrics_{file_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(per_category_metrics, f, indent=2)

    # 3. Per-entity metrics JSON
    per_entity = {
        name: {
            "strict": data["strict"]["per_class"],
            "relaxed": data["relaxed"]["per_class"],
        }
        for name, data in configs_metrics.items()
    }
    with open(output_dir / f"phase5_per_entity_metrics_{file_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(per_entity, f, indent=2)

    # 4. Generalisation Report JSON
    with open(output_dir / f"phase5_generalisation_report_{file_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(gazetteer_analysis, f, indent=2)

    # 5. Raw predictions
    preds_file = output_dir / f"phase5_predictions_{test_split_path.stem}.jsonl"
    with open(preds_file, "w", encoding="utf-8") as f:
        for r, p1, p2, p3 in zip(records, c1_preds, c2_preds, c3_preds):
            f.write(json.dumps({
                "id": r.get("id"),
                "text": r.get("text"),
                "gold": extract_gold_entities(r),
                "pred_config1_ft_alone": p1,
                "pred_config2_ft_stitcher": p2,
                "pred_config3_ft_hybrid": p3,
            }) + "\n")

    # 6. Full Phase 5 metrics summary JSON
    with open(output_dir / f"{file_prefix}_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    # 7. Qualitative Error Analysis Markdown
    generate_phase5_error_markdown(error_cases, output_dir / f"phase5_error_analysis_{file_prefix}.md")

    print(f"[+] Phase 5 evaluation deliverables for {file_prefix} saved to {output_dir}")
    return summary_report


def generate_phase5_error_markdown(error_cases: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
    """Generates qualitative error analysis markdown for Phase 5."""
    lines = [
        "# Phase 5 Qualitative Error Analysis Report",
        "",
        "**Date:** 21 November 2026  ",
        "**System Evaluated:** Configuration 3-FT (Fine-Tuned Multilingual DistilBERT + Full Hybrid System)  ",
        "",
        "---",
        "",
        "## 1. Quantitative Error Distribution",
        "",
        f"* **Total False Positives:** {len(error_cases['false_positives'])}",
        f"* **Total False Negatives (Missed Entities):** {len(error_cases['false_negatives'])}",
        f"* **Boundary Mismatches (Partial Spans):** {len(error_cases['boundary_mismatches'])}",
        f"* **Patronymic Linking Failures:** {len(error_cases['patronymic_errors'])}",
        f"* **Hard-Negative Hallucinations:** {len(error_cases['hard_negative_hallucinations'])}",
        "",
        "---",
        "",
        "## 2. Representative Error Cases & Root-Cause Diagnosis",
        "",
        "### 2.1 Boundary Mismatches",
        "",
    ]

    for item in error_cases["boundary_mismatches"][:5]:
        lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        lines.append(f"  * *Text:* \"{item['text']}\"")
        lines.append(f"  * *Predicted:* {item['pred']}")
        lines.append(f"  * *Ground Truth:* {item['gold']}")
        lines.append("")

    lines.extend([
        "### 2.2 False Positives (Spurious Detections)",
        "",
    ])

    for item in error_cases["false_positives"][:5]:
        lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        lines.append(f"  * *Text:* \"{item['text']}\"")
        lines.append(f"  * *Spurious Entity:* `[{item['pred_label']}]` '{item['pred_text']}' (Confidence: {item['score']*100:.1f}%)")
        lines.append("")

    lines.extend([
        "### 2.3 False Negatives (Missed Entities)",
        "",
    ])

    for item in error_cases["false_negatives"][:5]:
        lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        lines.append(f"  * *Text:* \"{item['text']}\"")
        lines.append(f"  * *Missed Entity:* `[{item['gold_label']}]` '{item['gold_text']}'")
        lines.append("")

    lines.extend([
        "### 2.4 Hard-Negative Rejection & Hallucinations",
        "",
    ])

    if not error_cases["hard_negative_hallucinations"]:
        lines.append("* **Zero hallucinations detected.** The fine-tuned hybrid system cleanly rejected 100% of hard-negative sentences.")
    else:
        for item in error_cases["hard_negative_hallucinations"][:5]:
            lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
            lines.append(f"  * *Text:* \"{item['text']}\"")
            lines.append(f"  * *Hallucination:* `[{item['pred_label']}]` '{item['pred_text']}' (Confidence: {item['score']*100:.1f}%)")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Saved Phase 5 error analysis report to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 5 Evaluation & Comparison Runner.")
    parser.add_argument("--model-dir", type=str, default="models/malaysian_ner_distilbert_multilingual")
    parser.add_argument("--test-split", type=str, default="data/splits/test.jsonl")
    parser.add_argument("--experimental-split", type=str, default="data/splits/experimental_structure_isolated/test.jsonl")
    parser.add_argument("--phase4-baseline", type=str, default="data/reports/phase4_baseline_metrics.json")
    parser.add_argument("--output-dir", type=str, default="data/reports")
    parser.add_argument("--threshold", type=float, default=0.50)

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    canonical_test_path = Path(args.test_split)
    exp_test_path = Path(args.experimental_split)
    p4_baseline_path = Path(args.phase4_baseline)

    print("=" * 80)
    print("PHASE 5: EVALUATING CANONICAL HELD-OUT TEST SPLIT WITH FINE-TUNED MODEL")
    print("=" * 80)
    canonical_summary = run_phase5_evaluation(
        model_dir=args.model_dir,
        test_split_path=canonical_test_path,
        output_dir=out_dir,
        phase4_baseline_path=p4_baseline_path,
        threshold=args.threshold,
        file_prefix="phase5_canonical",
    )

    exp_summary = None
    if exp_test_path.exists():
        print("\n" + "=" * 80)
        print("PHASE 5: EVALUATING EXPERIMENTAL STRUCTURAL-ISOLATED TEST SPLIT")
        print("=" * 80)
        exp_p4_path = out_dir / "phase4_experimental_structural_metrics.json"
        exp_summary = run_phase5_evaluation(
            model_dir=args.model_dir,
            test_split_path=exp_test_path,
            output_dir=out_dir,
            phase4_baseline_path=exp_p4_path if exp_p4_path.exists() else None,
            threshold=args.threshold,
            file_prefix="phase5_experimental_structural",
        )

    # Consolidated Master Reports
    consolidated_comparison = {
        "canonical_test_split": canonical_summary.get("comparison_with_phase4", {}),
        "experimental_structural_test_split": exp_summary.get("comparison_with_phase4", {}) if exp_summary else {},
    }
    with open(out_dir / "phase5_baseline_comparison.json", "w", encoding="utf-8") as f:
        json.dump(consolidated_comparison, f, indent=2)

    consolidated_per_category = {
        "canonical_test_split": canonical_summary.get("per_category", {}),
        "experimental_structural_test_split": exp_summary.get("per_category", {}) if exp_summary else {},
    }
    with open(out_dir / "phase5_per_category_metrics.json", "w", encoding="utf-8") as f:
        json.dump(consolidated_per_category, f, indent=2)

    consolidated_per_entity = {
        "canonical_test_split": {
            name: {
                "strict": data["strict"]["per_class"],
                "relaxed": data["relaxed"]["per_class"],
            }
            for name, data in canonical_summary.get("configurations", {}).items()
        },
        "experimental_structural_test_split": {
            name: {
                "strict": data["strict"]["per_class"],
                "relaxed": data["relaxed"]["per_class"],
            }
            for name, data in (exp_summary.get("configurations", {}) if exp_summary else {}).items()
        },
    }
    with open(out_dir / "phase5_per_entity_metrics.json", "w", encoding="utf-8") as f:
        json.dump(consolidated_per_entity, f, indent=2)

    consolidated_generalisation = {
        "canonical_test_split": canonical_summary.get("gazetteer_leakage", {}),
        "experimental_structural_test_split": exp_summary.get("gazetteer_leakage", {}) if exp_summary else {},
    }
    with open(out_dir / "phase5_generalisation_report.json", "w", encoding="utf-8") as f:
        json.dump(consolidated_generalisation, f, indent=2)

    # Combined Error Analysis Markdown
    records_canonical = load_jsonl(canonical_test_path)
    golds_canonical = [extract_gold_entities(r) for r in records_canonical]
    detector_c3 = PersonalInformationDetector(
        model_name=args.model_dir,
        confidence_threshold=args.threshold,
        enable_patronymic_stitching=True,
        enable_hybrid=True,
        include_structured_pii=False,
    )
    preds_canonical = [detector_c3.detect(r["text"]) for r in records_canonical]
    error_cases_canonical = collect_error_cases(records_canonical, preds_canonical, golds_canonical)

    records_exp = load_jsonl(exp_test_path) if exp_test_path.exists() else []
    golds_exp = [extract_gold_entities(r) for r in records_exp]
    preds_exp = [detector_c3.detect(r["text"]) for r in records_exp]
    error_cases_exp = collect_error_cases(records_exp, preds_exp, golds_exp)

    # Combine errors for qualitative report
    combined_errors = {
        k: error_cases_canonical[k] + error_cases_exp.get(k, [])
        for k in error_cases_canonical.keys()
    }
    generate_phase5_error_markdown(combined_errors, out_dir / "phase5_error_analysis.md")

    print("\n[+] Consolidated Phase 5 reports saved to data/reports")


if __name__ == "__main__":
    main()
