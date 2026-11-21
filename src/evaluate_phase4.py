"""
Phase 4 Baseline Evaluation & Generalisation Testing Suite.

Comprehensive evaluation tool comparing:
1. Configuration 1: Raw pretrained transformer ('dslim/distilbert-NER')
2. Configuration 2: Transformer with patronymic stitching (Phase 1)
3. Configuration 3: Complete Phase 2 hybrid NER system (stitcher + gazetteers + rules)
4. Configuration 4: Structured PII recognizers (MYKAD, PHONE, POSTCODE) evaluated separately.

Computes:
- Strict & relaxed Precision, Recall, F1 (Overall and per-class)
- Confusion matrices, False Positive Rates, False Negative Rates
- Hard-negative rejection accuracy
- Category-level breakdown across all 7 sociolinguistic strata
- Gazetteer leakage & unseen entity generalisation analysis
- Cross-split structural generalisation (Canonical vs. Structurally-Isolated)
- Concrete error analysis

Author: AI/ML Club
License: MIT
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Support imports whether executed from root or src/
try:
    from entity_extractor import PersonalInformationDetector
    from recognizers.mykad_recognizer import find_mykad_entities
    from recognizers.phone_recognizer import find_phone_entities
    from recognizers.location_recognizer import (
        find_malaysian_locations,
        find_malaysian_postcodes,
        MALAYSIAN_LOCATION_NAMES,
    )
    from recognizers.org_gazetteer import (
        find_malaysian_org_entities,
        MALAYSIAN_ORG_NAMES,
        MALAYSIAN_ORG_ACRONYMS,
    )
except ImportError:
    from src.entity_extractor import PersonalInformationDetector
    from src.recognizers.mykad_recognizer import find_mykad_entities
    from src.recognizers.phone_recognizer import find_phone_entities
    from src.recognizers.location_recognizer import (
        find_malaysian_locations,
        find_malaysian_postcodes,
        MALAYSIAN_LOCATION_NAMES,
    )
    from src.recognizers.org_gazetteer import (
        find_malaysian_org_entities,
        MALAYSIAN_ORG_NAMES,
        MALAYSIAN_ORG_ACRONYMS,
    )


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Loads records from a JSONLines dataset file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def extract_gold_entities(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts standardized gold entity dictionaries from record."""
    entities = []
    text = record["text"]
    raw_labels = record.get("label", record.get("entities", []))
    for item in raw_labels:
        if isinstance(item, (list, tuple)) and len(item) == 3:
            s, e, l = item
            entities.append({
                "start": s,
                "end": e,
                "label": l,
                "text": text[s:e],
            })
        elif isinstance(item, dict):
            s, e, l = item["start"], item["end"], item["label"]
            entities.append({
                "start": s,
                "end": e,
                "label": l,
                "text": text[s:e] if "text" not in item else item["text"],
            })
    return entities


def compute_metrics(
    predictions_per_sample: List[List[Dict[str, Any]]],
    ground_truth_per_sample: List[List[Dict[str, Any]]],
    relaxed: bool = False,
    target_labels: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Computes Precision, Recall, and F1 score across all samples."""
    total_tp = 0
    total_fp = 0
    total_fn = 0

    class_counts: Dict[str, Dict[str, int]] = {}

    for preds, targets in zip(predictions_per_sample, ground_truth_per_sample):
        # Filter target labels if specified
        filtered_preds = [p for p in preds if target_labels is None or p["label"] in target_labels]
        filtered_targets = [t for t in targets if target_labels is None or t["label"] in target_labels]

        unmatched_targets = list(filtered_targets)

        for p in filtered_preds:
            p_label = p["label"]
            if p_label not in class_counts:
                class_counts[p_label] = {"tp": 0, "fp": 0, "fn": 0}

            matched = False
            for idx, t in enumerate(unmatched_targets):
                if p_label != t["label"]:
                    continue

                if relaxed:
                    is_match = max(p["start"], t["start"]) < min(p["end"], t["end"])
                else:
                    is_match = (p["start"] == t["start"]) and (p["end"] == t["end"])

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

    def calc_prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return round(prec, 4), round(rec, 4), round(f1, 4)

    overall_prec, overall_rec, overall_f1 = calc_prf(total_tp, total_fp, total_fn)

    per_class_metrics = {}
    for label, counts in sorted(class_counts.items()):
        p, r, f = calc_prf(counts["tp"], counts["fp"], counts["fn"])
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
        "total_gold": total_tp + total_fn,
        "total_pred": total_tp + total_fp,
        "false_positive_rate": round(total_fp / (total_tp + total_fp), 4) if (total_tp + total_fp) > 0 else 0.0,
        "false_negative_rate": round(total_fn / (total_tp + total_fn), 4) if (total_tp + total_fn) > 0 else 0.0,
        "per_class": per_class_metrics,
    }


def compute_confusion_matrix(
    predictions_per_sample: List[List[Dict[str, Any]]],
    ground_truth_per_sample: List[List[Dict[str, Any]]],
    target_labels: List[str] = ["PERSON", "ORGANIZATION", "LOCATION"],
) -> Dict[str, Dict[str, int]]:
    """Builds an entity-level confusion matrix between Gold and Predicted categories."""
    labels_with_o = target_labels + ["O"]
    matrix = {g: {p: 0 for p in labels_with_o} for g in labels_with_o}

    for preds, targets in zip(predictions_per_sample, ground_truth_per_sample):
        unmatched_preds = list(preds)
        unmatched_targets = list(targets)

        # Match targets with overlapping predictions
        for t in list(unmatched_targets):
            best_match = None
            best_overlap = 0

            for p in unmatched_preds:
                overlap = max(0, min(p["end"], t["end"]) - max(p["start"], t["start"]))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = p

            if best_match and best_overlap > 0:
                matrix[t["label"]][best_match["label"]] += 1
                unmatched_targets.remove(t)
                unmatched_preds.remove(best_match)
            else:
                # Missed entity (predicted as O)
                matrix[t["label"]]["O"] += 1

        # Remaining predictions without any overlapping target are predicted from O
        for p in unmatched_preds:
            if p["label"] in matrix["O"]:
                matrix["O"][p["label"]] += 1

    return matrix


def evaluate_hard_negatives(
    records: List[Dict[str, Any]],
    predictions_per_sample: List[List[Dict[str, Any]]],
    target_labels: Set[str] = {"PERSON", "ORGANIZATION", "LOCATION"},
) -> Dict[str, Any]:
    """Evaluates false positive hallucinations on hard-negative sentences."""
    total_hn = 0
    clean_hn = 0
    hallucinated_entities = []

    for r, preds in zip(records, predictions_per_sample):
        is_hn = r.get("meta", {}).get("is_hard_negative", False) or len(r.get("label", [])) == 0
        if not is_hn:
            continue

        total_hn += 1
        filtered_preds = [p for p in preds if p["label"] in target_labels]
        if len(filtered_preds) == 0:
            clean_hn += 1
        else:
            for p in filtered_preds:
                hallucinated_entities.append({
                    "sentence_id": r.get("id"),
                    "text": r.get("text"),
                    "entity": p.get("text"),
                    "label": p.get("label"),
                    "score": p.get("score"),
                })

    rejection_accuracy = clean_hn / total_hn if total_hn > 0 else 1.0

    return {
        "total_hard_negatives": total_hn,
        "clean_sentences_count": clean_hn,
        "rejection_accuracy": round(rejection_accuracy, 4),
        "total_hallucinations": len(hallucinated_entities),
        "hallucinated_details": hallucinated_entities,
    }


def evaluate_gazetteer_leakage(
    records: List[Dict[str, Any]],
    predictions_per_config: Dict[str, List[List[Dict[str, Any]]]],
    ground_truth: List[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Analyzes performance on entities explicitly present in gazetteers vs. unseen entities."""
    known_org_exact = {s.lower() for s in MALAYSIAN_ORG_NAMES} | {s.lower() for s in MALAYSIAN_ORG_ACRONYMS}
    known_loc_exact = {s.lower() for s in MALAYSIAN_LOCATION_NAMES}

    total_entities = 0
    known_entities_count = 0
    unseen_entities_count = 0

    known_targets_per_sample = []
    unseen_targets_per_sample = []

    unseen_org_targets = []
    unseen_loc_targets = []
    unseen_per_targets = []

    for item, targets in zip(records, ground_truth):
        k_t = []
        u_t = []
        u_org = []
        u_loc = []
        u_per = []

        for t in targets:
            total_entities += 1
            t_text_norm = t["text"].strip().lower()
            lbl = t["label"]

            is_known = False
            if lbl == "ORGANIZATION" and t_text_norm in known_org_exact:
                is_known = True
            elif lbl == "LOCATION" and t_text_norm in known_loc_exact:
                is_known = True

            if is_known:
                known_entities_count += 1
                k_t.append(t)
            else:
                unseen_entities_count += 1
                u_t.append(t)
                if lbl == "ORGANIZATION":
                    u_org.append(t)
                elif lbl == "LOCATION":
                    u_loc.append(t)
                elif lbl == "PERSON":
                    u_per.append(t)

        known_targets_per_sample.append(k_t)
        unseen_targets_per_sample.append(u_t)
        unseen_org_targets.append(u_org)
        unseen_loc_targets.append(u_loc)
        unseen_per_targets.append(u_per)

    # Evaluate configurations on Unseen Entities
    comparison = {}
    for cfg_name, preds in predictions_per_config.items():
        # Overall unseen
        unseen_strict = compute_metrics(preds, unseen_targets_per_sample, relaxed=False)
        unseen_relaxed = compute_metrics(preds, unseen_targets_per_sample, relaxed=True)
        # Known entities
        known_strict = compute_metrics(preds, known_targets_per_sample, relaxed=False)
        # Unseen Org
        unseen_org_m = compute_metrics(preds, unseen_org_targets, relaxed=False, target_labels={"ORGANIZATION"})
        # Unseen Loc
        unseen_loc_m = compute_metrics(preds, unseen_loc_targets, relaxed=False, target_labels={"LOCATION"})
        # Unseen Person
        unseen_per_m = compute_metrics(preds, unseen_per_targets, relaxed=False, target_labels={"PERSON"})

        comparison[cfg_name] = {
            "unseen_strict_f1": unseen_strict["f1"],
            "unseen_strict_prec": unseen_strict["precision"],
            "unseen_strict_rec": unseen_strict["recall"],
            "unseen_relaxed_f1": unseen_relaxed["f1"],
            "known_strict_f1": known_strict["f1"],
            "unseen_org_f1": unseen_org_m["f1"],
            "unseen_loc_f1": unseen_loc_m["f1"],
            "unseen_person_f1": unseen_per_m["f1"],
        }

    return {
        "total_gold_entities": total_entities,
        "known_in_gazetteer_count": known_entities_count,
        "unseen_entities_count": unseen_entities_count,
        "unseen_percentage": round(unseen_entities_count / total_entities * 100, 2) if total_entities > 0 else 0,
        "config_comparison": comparison,
    }


def evaluate_structured_pii_recognizers(pii_path: Path) -> Dict[str, Any]:
    """Evaluates Configuration 4: Structured PII recognizers (MYKAD, PHONE, POSTCODE)."""
    if not pii_path.exists():
        return {"error": f"PII dataset not found at {pii_path}"}

    records = load_jsonl(pii_path)
    mykad_preds, mykad_targets = [], []
    phone_preds, phone_targets = [], []
    postcode_preds, postcode_targets = [], []

    for r in records:
        text = r["text"]
        spans = r.get("pii_spans", [])

        # Gold targets
        m_t = [{"start": s["start"], "end": s["end"], "label": "MYKAD", "text": s.get("raw_value", text[s["start"]:s["end"]])} for s in spans if s["type"] == "MYKAD"]
        p_t = [{"start": s["start"], "end": s["end"], "label": "PHONE", "text": s.get("raw_value", text[s["start"]:s["end"]])} for s in spans if s["type"] == "PHONE"]
        pc_t = [{"start": s["start"], "end": s["end"], "label": "POSTCODE", "text": s.get("raw_value", text[s["start"]:s["end"]])} for s in spans if s["type"] == "POSTCODE"]

        mykad_targets.append(m_t)
        phone_targets.append(p_t)
        postcode_targets.append(pc_t)

        # Predictions
        mykad_preds.append(find_mykad_entities(text))
        phone_preds.append(find_phone_entities(text))
        postcode_preds.append(find_malaysian_postcodes(text))

    mykad_m = compute_metrics(mykad_preds, mykad_targets, relaxed=False)
    phone_m = compute_metrics(phone_preds, phone_targets, relaxed=False)
    postcode_m = compute_metrics(postcode_preds, postcode_targets, relaxed=False)

    return {
        "records_evaluated": len(records),
        "mykad": mykad_m,
        "phone": phone_m,
        "postcode": postcode_m,
    }


def collect_error_cases(
    records: List[Dict[str, Any]],
    predictions: List[List[Dict[str, Any]]],
    targets: List[List[Dict[str, Any]]],
    target_labels: Set[str] = {"PERSON", "ORGANIZATION", "LOCATION"},
) -> Dict[str, List[Dict[str, Any]]]:
    """Categorizes qualitative prediction errors for actionable diagnosis."""
    errors = {
        "false_positives": [],
        "false_negatives": [],
        "boundary_mismatches": [],
        "patronymic_errors": [],
        "hard_negative_hallucinations": [],
    }

    patronymic_keywords = {"bin", "binti", "bt.", "a/l", "a/p", "s/o", "d/o"}

    for r, preds, golds in zip(records, predictions, targets):
        filtered_preds = [p for p in preds if p["label"] in target_labels]
        filtered_golds = [g for g in golds if g["label"] in target_labels]
        is_hn = r.get("meta", {}).get("is_hard_negative", False) or len(filtered_golds) == 0

        if is_hn and len(filtered_preds) > 0:
            for p in filtered_preds:
                errors["hard_negative_hallucinations"].append({
                    "sentence_id": r.get("id"),
                    "text": r.get("text"),
                    "pred_text": p["text"],
                    "pred_label": p["label"],
                    "score": p["score"],
                })

        unmatched_golds = list(filtered_golds)

        for p in filtered_preds:
            matched_gold = None
            exact_match = False
            for g in unmatched_golds:
                if p["label"] == g["label"] and p["start"] == g["start"] and p["end"] == g["end"]:
                    exact_match = True
                    matched_gold = g
                    break
                elif max(p["start"], g["start"]) < min(p["end"], g["end"]):
                    matched_gold = g

            if exact_match:
                unmatched_golds.remove(matched_gold)
            elif matched_gold:
                # Boundary defect or category confusion
                errors["boundary_mismatches"].append({
                    "sentence_id": r.get("id"),
                    "text": r.get("text"),
                    "pred": f"[{p['label']}] '{p['text']}' ({p['start']}:{p['end']})",
                    "gold": f"[{matched_gold['label']}] '{matched_gold['text']}' ({matched_gold['start']}:{matched_gold['end']})",
                })
                unmatched_golds.remove(matched_gold)
            else:
                # Spurious false positive
                errors["false_positives"].append({
                    "sentence_id": r.get("id"),
                    "text": r.get("text"),
                    "pred_text": p["text"],
                    "pred_label": p["label"],
                    "score": p["score"],
                })

        for g in unmatched_golds:
            errors["false_negatives"].append({
                "sentence_id": r.get("id"),
                "text": r.get("text"),
                "gold_text": g["text"],
                "gold_label": g["label"],
            })
            # Check if this missed entity contains patronymics
            if any(f" {pk} " in g["text"].lower() for pk in patronymic_keywords):
                errors["patronymic_errors"].append({
                    "sentence_id": r.get("id"),
                    "text": r.get("text"),
                    "patronymic_entity": g["text"],
                })

    return errors


def run_comprehensive_evaluation(
    dataset_path: Path,
    output_dir: Path,
    threshold: float = 0.50,
    file_prefix: str = "phase4_baseline",
) -> Dict[str, Any]:
    """Orchestrates comprehensive evaluation of all 4 configurations on given dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records = load_jsonl(dataset_path)
    print(f"[*] Loaded {len(records)} records from {dataset_path}")

    ground_truth = [extract_gold_entities(r) for r in records]

    # Initialize detectors
    print("\n[*] Initializing Configuration 1: Raw Pretrained Transformer (DistilBERT)...")
    c1_detector = PersonalInformationDetector(
        confidence_threshold=threshold,
        enable_patronymic_stitching=False,
        enable_hybrid=False,
        include_structured_pii=False,
    )

    print("\n[*] Initializing Configuration 2: Transformer + Patronymic Stitching (Phase 1)...")
    c2_detector = PersonalInformationDetector(
        confidence_threshold=threshold,
        enable_patronymic_stitching=True,
        enable_hybrid=False,
        include_structured_pii=False,
    )

    print("\n[*] Initializing Configuration 3: Full Phase 2 Hybrid NER System...")
    c3_detector = PersonalInformationDetector(
        confidence_threshold=threshold,
        enable_patronymic_stitching=True,
        enable_hybrid=True,
        include_structured_pii=False,
    )

    print("\n[*] Running predictions across all samples...")
    c1_preds = [c1_detector.detect(r["text"]) for r in records]
    c2_preds = [c2_detector.detect(r["text"]) for r in records]
    c3_preds = [c3_detector.detect(r["text"]) for r in records]

    # 1. Configuration Metrics
    configs_metrics = {}
    for name, preds in [
        ("Config 1: Raw DistilBERT", c1_preds),
        ("Config 2: DistilBERT + Stitcher (Phase 1)", c2_preds),
        ("Config 3: Full Hybrid (Phase 2)", c3_preds),
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

    # 2. Per-Category Breakdown (using Config 3)
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
            "strict_precision": sub_strict["precision"],
            "strict_recall": sub_strict["recall"],
            "strict_f1": sub_strict["f1"],
            "relaxed_f1": sub_relaxed["f1"],
            "per_class": sub_strict["per_class"],
            "hard_negatives": sub_hn,
        }

    # 3. Gazetteer Leakage Analysis
    preds_dict = {
        "Config 1 (Raw)": c1_preds,
        "Config 2 (Stitcher)": c2_preds,
        "Config 3 (Hybrid)": c3_preds,
    }
    gazetteer_analysis = evaluate_gazetteer_leakage(records, preds_dict, ground_truth)

    # 4. Error Analysis
    error_cases = collect_error_cases(records, c3_preds, ground_truth)

    # 5. Configuration 4: Structured PII
    pii_path = Path("data/raw/structured_pii_sample.jsonl")
    pii_metrics = evaluate_structured_pii_recognizers(pii_path)

    # Compile Full Output Dictionary
    evaluation_summary = {
        "dataset_path": str(dataset_path),
        "total_records": len(records),
        "configurations": configs_metrics,
        "per_category": per_category_metrics,
        "gazetteer_leakage": gazetteer_analysis,
        "structured_pii": pii_metrics,
        "error_summary": {k: len(v) for k, v in error_cases.items()},
    }

    # Save outputs
    metrics_file = output_dir / f"{file_prefix}_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_summary, f, indent=2)
    print(f"[+] Saved evaluation metrics to {metrics_file}")

    per_cat_file = output_dir / f"{file_prefix}_per_category_metrics.json"
    with open(per_cat_file, "w", encoding="utf-8") as f:
        json.dump(per_category_metrics, f, indent=2)
    print(f"[+] Saved per-category metrics to {per_cat_file}")

    gaz_file = output_dir / f"{file_prefix}_gazetteer_leakage.json"
    with open(gaz_file, "w", encoding="utf-8") as f:
        json.dump(gazetteer_analysis, f, indent=2)
    print(f"[+] Saved gazetteer leakage report to {gaz_file}")

    # Save raw predictions
    preds_dump_file = output_dir / f"phase4_predictions_{dataset_path.stem}.jsonl"
    with open(preds_dump_file, "w", encoding="utf-8") as f:
        for r, p1, p2, p3 in zip(records, c1_preds, c2_preds, c3_preds):
            f.write(json.dumps({
                "id": r.get("id"),
                "text": r.get("text"),
                "gold": extract_gold_entities(r),
                "pred_config1_raw": p1,
                "pred_config2_stitcher": p2,
                "pred_config3_hybrid": p3,
            }) + "\n")
    print(f"[+] Saved raw predictions to {preds_dump_file}")

    return evaluation_summary


def generate_error_analysis_markdown(error_cases: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
    """Generates an extensive markdown error analysis report."""
    md_lines = [
        "# Phase 4 Qualitative Error Analysis Report",
        "",
        "**Date:** 21 November 2026  ",
        "**System Evaluated:** Configuration 3 (Full Phase 2 Hybrid NER System)  ",
        "",
        "---",
        "",
        "## 1. Quantitative Error Breakdown",
        "",
        f"* **Total False Positives:** {len(error_cases['false_positives'])}",
        f"* **Total False Negatives (Missed Entities):** {len(error_cases['false_negatives'])}",
        f"* **Boundary Mismatches (Partial Spans):** {len(error_cases['boundary_mismatches'])}",
        f"* **Patronymic Linking Failures:** {len(error_cases['patronymic_errors'])}",
        f"* **Hard-Negative Hallucinations:** {len(error_cases['hard_negative_hallucinations'])}",
        "",
        "---",
        "",
        "## 2. Representative Error Examples & Diagnosis",
        "",
        "### 2.1 Boundary Mismatches (Partial Span Spills)",
        "Boundary defects typically arise when subword tokens in multi-word organizations or code-switched phrases are only partially tagged by DistilBERT.",
        "",
    ]

    for item in error_cases["boundary_mismatches"][:5]:
        md_lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        md_lines.append(f"  * *Text:* \"{item['text']}\"")
        md_lines.append(f"  * *Predicted:* {item['pred']}")
        md_lines.append(f"  * *Ground Truth:* {item['gold']}")
        md_lines.append("")

    md_lines.extend([
        "### 2.2 False Positives (Spurious Entities)",
        "Spurious entities occur primarily on conversational Malaysian terms, job designations, or currency distractor tokens.",
        "",
    ])

    for item in error_cases["false_positives"][:5]:
        md_lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        md_lines.append(f"  * *Text:* \"{item['text']}\"")
        md_lines.append(f"  * *Spurious Entity:* `[{item['pred_label']}]` '{item['pred_text']}' (Confidence: {item['score']*100:.1f}%)")
        md_lines.append("")

    md_lines.extend([
        "### 2.3 False Negatives (Missed Entities)",
        "Missed entities occur predominantly on colloquial names, uncommon patronymic particles, or corporate entities without gazetteer listings.",
        "",
    ])

    for item in error_cases["false_negatives"][:5]:
        md_lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
        md_lines.append(f"  * *Text:* \"{item['text']}\"")
        md_lines.append(f"  * *Missed Entity:* `[{item['gold_label']}]` '{item['gold_text']}'")
        md_lines.append("")

    md_lines.extend([
        "### 2.4 Hard-Negative Hallucinations",
        "Hard-negative sentences are engineered without any named entities but contain distractor formats (currencies, timestamps, dates).",
        "",
    ])

    if not error_cases["hard_negative_hallucinations"]:
        md_lines.append("* **Zero hallucinations detected.** The hybrid system achieved 100% rejection accuracy on hard negatives.")
    else:
        for item in error_cases["hard_negative_hallucinations"][:5]:
            md_lines.append(f"* **Sentence ID:** `{item['sentence_id']}`")
            md_lines.append(f"  * *Text:* \"{item['text']}\"")
            md_lines.append(f"  * *Hallucination:* `[{item['pred_label']}]` '{item['pred_text']}' (Confidence: {item['score']*100:.1f}%)")
            md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 3. Recommended Architectural Interventions for Phase 5",
        "",
        "1. **Fine-Tuning on Malaysian Hard Negatives:** Down-weight transformer attention on currency tokens (`RM`, `SGD`) and time expressions.",
        "2. **Multilingual Checkpoint Ingestion:** Transition from English-only DistilBERT to multilingual foundation models (`distilbert-base-multilingual-cased` or `xlm-roberta-base`) to enhance representation of Bahasa Melayu morphology.",
        "3. **Context-Sensitive Boundary Refinement:** Implement bidirectional subword expansion around patronymic connectors (`a/l`, `s/o`) to prevent initial particle truncation.",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"[+] Saved error analysis report to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Baseline Evaluation & Generalisation Runner.")
    parser.add_argument(
        "--test-split",
        type=str,
        default="data/splits/test.jsonl",
        help="Path to canonical test split.",
    )
    parser.add_argument(
        "--experimental-split",
        type=str,
        default="data/splits/experimental_structure_isolated/test.jsonl",
        help="Path to alternative experimental structural test split.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/reports",
        help="Directory to save generated evaluation reports and raw predictions.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Confidence threshold for predictions (default: 0.50).",
    )

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    canonical_test_path = Path(args.test_split)
    exp_test_path = Path(args.experimental_split)

    print("=" * 80)
    print("PHASE 4: EVALUATING CANONICAL HELD-OUT TEST SPLIT")
    print("=" * 80)
    canonical_summary = run_comprehensive_evaluation(canonical_test_path, out_dir, threshold=args.threshold)

    # Collect errors on canonical test split
    records = load_jsonl(canonical_test_path)
    golds = [extract_gold_entities(r) for r in records]
    c3_preds = [PersonalInformationDetector(confidence_threshold=args.threshold, enable_patronymic_stitching=True, enable_hybrid=True, include_structured_pii=False).detect(r["text"]) for r in records]
    error_cases = collect_error_cases(records, c3_preds, golds)
    generate_error_analysis_markdown(error_cases, out_dir / "phase4_error_analysis.md")

    if exp_test_path.exists():
        print("\n" + "=" * 80)
        print("PHASE 4: EVALUATING EXPERIMENTAL STRUCTURAL-ISOLATED TEST SPLIT")
        print("=" * 80)
        exp_summary = run_comprehensive_evaluation(
            exp_test_path,
            out_dir,
            threshold=args.threshold,
            file_prefix="phase4_experimental_structural",
        )
        print(f"[+] Saved experimental structural metrics with prefix 'phase4_experimental_structural'")

    print("\n[+] Phase 4 comprehensive baseline evaluation completed successfully.")


if __name__ == "__main__":
    main()
