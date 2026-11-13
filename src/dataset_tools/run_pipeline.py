"""
Pipeline Orchestrator for Phase 2.6 Malaysian NER Dataset.

Executes end-to-end dataset generation, quality assurance, and reporting:
1. Compiles the 1,000-sentence canonical dataset.
2. Segregates records into public, independent, and synthetic collection folders.
3. Generates 15% double-annotation subset and computes Inter-Annotator Agreement.
4. Executes Provenance and Licensing audit against data/SOURCE_MANIFEST.csv.
5. Executes Privacy Screening for unmasked credentials, phone leaks, and real MyKad.
6. Executes Deduplication and near-duplicate fuzzy screening.
7. Generates reproducible 70/15/15 train/val/test splits with template/document isolation.
8. Runs comprehensive 14-point dataset validation and exports machine- and human-readable reports.

Author: AI/ML Club
License: MIT
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .agreement import AnnotationAgreementCalculator
from .build_dataset import assemble_1000_dataset, generate_double_annotation_set
from .deduplicator import DatasetDeduplicator
from .doccano_adapter import export_to_doccano, import_from_doccano
from .privacy_screener import PrivacyScreener
from .provenance import ProvenanceAuditor
from .splitter import DatasetSplitter
from .validator import DatasetValidator


def run_full_pipeline():
    print("=" * 70)
    print("      EXECUTING PHASE 2.6 DATASET GENERATION & QA PIPELINE")
    print("=" * 70)

    # 1. Compile 1,000 canonical records
    print("[1/8] Compiling 1,000 Malaysian NER records across 7 strata...")
    records = assemble_1000_dataset()
    print(f"      Successfully compiled {len(records)} records.")

    # 2. Segregate by data origin
    print("[2/8] Segregating data by origin into data/collection/...")
    public_records = [r for r in records if r["meta"]["source_type"] == "public"]
    indep_records = [r for r in records if r["meta"]["source_type"] == "independent"]
    synth_records = [r for r in records if r["meta"]["source_type"] == "synthetic"]

    export_to_doccano(public_records, "data/collection/public/public_corpus.jsonl")
    export_to_doccano(indep_records, "data/collection/independent/independent_corpus.jsonl")
    export_to_doccano(synth_records, "data/collection/synthetic/synthetic_corpus.jsonl")
    export_to_doccano(records, "data/annotated/malaysian_ner_1000.jsonl")

    print(f"      - Publicly sourced:     {len(public_records):>4} ({len(public_records)/10:.1f}%) -> data/collection/public/")
    print(f"      - Independently authored: {len(indep_records):>4} ({len(indep_records)/10:.1f}%) -> data/collection/independent/")
    print(f"      - Realistic synthetic:  {len(synth_records):>4} ({len(synth_records)/10:.1f}%) -> data/collection/synthetic/")
    print(f"      - Canonical dataset:    {len(records):>4} -> data/annotated/malaysian_ner_1000.jsonl")

    # 3. Double Annotation & IAA
    print("[3/8] Generating 15% double-annotation sample and evaluating IAA...")
    ann1_set, ann2_set = generate_double_annotation_set(records, n_samples=150)
    export_to_doccano(ann1_set, "data/collection/double_annotation/canonical_subset_150.jsonl")
    export_to_doccano(ann2_set, "data/collection/double_annotation/annotator2_annotations.jsonl")

    iaa_calc = AnnotationAgreementCalculator()
    iaa_report = iaa_calc.evaluate_pair(ann1_set, ann2_set)

    Path("data/reports").mkdir(parents=True, exist_ok=True)
    with open("data/reports/inter_annotator_agreement.json", "w", encoding="utf-8") as f:
        json.dump(asdict(iaa_report), f, indent=2, ensure_ascii=False)

    with open("data/reports/inter_annotator_agreement.md", "w", encoding="utf-8") as f:
        f.write("# Inter-Annotator Agreement (IAA) Quality Report\n\n```text\n")
        f.write(iaa_report.summary())
        f.write("\n```\n")
    print(f"      - Exact Span F1: {iaa_report.exact_span_f1:.4f} | Cohen's Kappa: {iaa_report.cohens_kappa:.4f}")

    # 4. Provenance & Licensing Audit
    print("[4/8] Auditing provenance and licensing against data/SOURCE_MANIFEST.csv...")
    prov_auditor = ProvenanceAuditor(manifest_path="data/SOURCE_MANIFEST.csv")
    prov_report = prov_auditor.audit_dataset(records)
    with open("data/reports/provenance_licensing_report.json", "w", encoding="utf-8") as f:
        json.dump(asdict(prov_report), f, indent=2, ensure_ascii=False)
    print(f"      - Provenance Status: {'PASS' if prov_report.is_compliant else 'WARN'} ({prov_report.verified_records} verified)")

    # 5. Privacy Screening
    print("[5/8] Screening text for privacy leaks (credentials, unmasked phones, real IDs)...")
    screener = PrivacyScreener(allow_synthetic=True)
    is_priv_clean, priv_violations = screener.screen_dataset(records)
    priv_data = {
        "is_clean": is_priv_clean,
        "total_violations": len(priv_violations),
        "violations": [asdict(v) for v in priv_violations],
    }
    with open("data/reports/privacy_screening_report.json", "w", encoding="utf-8") as f:
        json.dump(priv_data, f, indent=2, ensure_ascii=False)
    print(f"      - Privacy Compliance: {'PASS [CLEAN]' if is_priv_clean else 'WARN [LEAKS DETECTED]'} ({len(priv_violations)} issues)")

    # 6. Deduplication
    print("[6/8] Running exact, normalized, and near-duplicate fuzzy screening...")
    dedup = DatasetDeduplicator(near_duplicate_threshold=0.85)
    dup_clusters, unique_recs = dedup.find_duplicates(records)
    dup_data = {
        "total_records": len(records),
        "unique_records": len(unique_recs),
        "duplicate_clusters_count": len(dup_clusters),
        "clusters": [asdict(c) for c in dup_clusters],
    }
    with open("data/reports/leakage_and_deduplication_report.json", "w", encoding="utf-8") as f:
        json.dump(dup_data, f, indent=2, ensure_ascii=False)
    print(f"      - Deduplication: {len(unique_recs)} unique sentences out of {len(records)} ({len(dup_clusters)} near-dup clusters flagged)")

    # 7. Stratified Document-Grouped Partitioning
    print("[7/8] Generating reproducible 70/15/15 splits with group/template isolation (seed=42)...")
    splitter = DatasetSplitter(seed=42)
    split_counts = splitter.split_and_save("data/annotated/malaysian_ner_1000.jsonl", "data/splits")
    print(f"      - Train: {split_counts['train']} ({split_counts['train_pct']}%)")
    print(f"      - Val:   {split_counts['val']} ({split_counts['val_pct']}%)")
    print(f"      - Test:  {split_counts['test']} ({split_counts['test_pct']}%)")

    # 8. Complete Validation Suite
    print("[8/8] Executing complete dataset validation and split cross-contamination audit...")
    validator = DatasetValidator()
    val_report = validator.validate_dataset(records)

    # Check split leakage
    train_r = import_from_doccano("data/splits/train.jsonl")
    val_r = import_from_doccano("data/splits/val.jsonl")
    test_r = import_from_doccano("data/splits/test.jsonl")
    leakage = validator.check_cross_split_contamination(train_r, val_r, test_r)

    val_dict = asdict(val_report)
    val_dict["cross_split_leakage_count"] = len(leakage)
    val_dict["cross_split_leakage_issues"] = [asdict(l) for l in leakage]

    with open("data/reports/validation_report.json", "w", encoding="utf-8") as f:
        json.dump(val_dict, f, indent=2, ensure_ascii=False)

    with open("data/reports/validation_report.md", "w", encoding="utf-8") as f:
        f.write("# Malaysian NER 1,000-Sentence Quality Assurance Report\n\n```text\n")
        f.write(val_report.summary())
        f.write(f"\nCross-Split Contamination:   {len(leakage)} errors ({'PASS' if len(leakage) == 0 else 'FAIL'})\n")
        f.write("```\n")

    print("\n" + val_report.summary())
    if leakage:
        print(f"[FAIL] Cross-split leakage detected: {len(leakage)} errors.")
    else:
        print("[PASS] Zero split contamination detected across Train/Val/Test.")
    print("=" * 70)
    print("                PHASE 2.6 PIPELINE EXECUTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_full_pipeline()
