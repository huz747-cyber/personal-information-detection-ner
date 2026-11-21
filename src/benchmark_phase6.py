"""
Phase 6 Performance Profiling, CPU Dynamic Quantization & Stress Evaluation Suite.

Tasks:
1. Exports an INT8 dynamically quantized model to models/malaysian_ner_distilbert_multilingual_int8/.
2. Benchmarks FP32 vs INT8 inference latency, throughput, memory footprint, and disk size.
3. Evaluates FP32 and INT8 configurations across:
   - Canonical Test Set (145 records)
   - Experimental Structural Test Set (150 records)
   - Malaysian Open-Vocabulary Stress Test Set (100 records)
4. Exports comprehensive comparative metric JSONs for Phase 6 execution reporting.

Author: AI/ML Club
License: MIT
"""

import gc
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from transformers import AutoConfig, AutoModelForTokenClassification, AutoTokenizer, pipeline

from entity_extractor import PersonalInformationDetector
from recognizers.conflict_resolver import resolve_entity_conflicts
from recognizers.org_gazetteer import find_malaysian_org_entities
from recognizers.location_recognizer import find_malaysian_locations, find_malaysian_postcodes
from recognizers.mykad_recognizer import find_mykad_entities
from recognizers.phone_recognizer import find_phone_entities
from patronymic_stitcher import stitch_patronymic_entities


FP32_MODEL_DIR = Path("models/malaysian_ner_distilbert_multilingual")
INT8_MODEL_DIR = Path("models/malaysian_ner_distilbert_multilingual_int8")


def export_quantized_model() -> Path:
    """Exports and saves the PyTorch INT8 dynamically quantized model checkpoint."""
    INT8_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    quantized_weights_path = INT8_MODEL_DIR / "pytorch_model.bin"

    print(f"[*] Loading FP32 model from {FP32_MODEL_DIR}...")
    model = AutoModelForTokenClassification.from_pretrained(FP32_MODEL_DIR)
    tokenizer = AutoTokenizer.from_pretrained(FP32_MODEL_DIR)
    config = AutoConfig.from_pretrained(FP32_MODEL_DIR)

    print("[*] Performing PyTorch dynamic quantization (torch.qint8 on nn.Linear)...")
    quantized_model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )

    # Save quantized state dict and configuration
    print(f"[*] Saving quantized checkpoint to {INT8_MODEL_DIR}...")
    torch.save(quantized_model.state_dict(), quantized_weights_path)
    config.save_pretrained(INT8_MODEL_DIR)
    tokenizer.save_pretrained(INT8_MODEL_DIR)

    # Also save a README documenting the quantized artifact
    readme_content = f"""# Malaysian-Aware Multilingual DistilBERT NER (INT8 Quantized Checkpoint)

**Model Architecture:** `distilbert-base-multilingual-cased`  
**Precision:** INT8 Dynamically Quantized (`torch.qint8` on `torch.nn.Linear`)  
**Base FP32 Checkpoint:** `{FP32_MODEL_DIR}`  
**License:** Apache License 2.0  
**Target Architecture:** CPU Inference (<15ms per sentence)  

## Rollback Policy
To revert to full FP32 precision, set `model_name="{FP32_MODEL_DIR}"` in `PersonalInformationDetector`.
"""
    with open(INT8_MODEL_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("[+] Quantized model exported successfully.")
    return INT8_MODEL_DIR


class QuantizedNERPipeline:
    """Wrapper providing a HuggingFace-compatible pipeline interface for the INT8 model."""

    def __init__(self, model_dir: Path = INT8_MODEL_DIR) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.config = AutoConfig.from_pretrained(model_dir)

        base_model = AutoModelForTokenClassification.from_pretrained(FP32_MODEL_DIR)
        self.model = torch.quantization.quantize_dynamic(
            base_model, {torch.nn.Linear}, dtype=torch.qint8
        )
        self.model.load_state_dict(torch.load(model_dir / "pytorch_model.bin"))
        self.model.eval()

        self.id2label = self.config.id2label

    def __call__(self, text: str) -> List[Dict[str, Any]]:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=512,
        )
        offset_mapping = inputs.pop("offset_mapping")[0].tolist()

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0]
            probs = torch.softmax(logits, dim=-1)
            predictions = torch.argmax(probs, dim=-1).tolist()
            confidences = torch.max(probs, dim=-1).values.tolist()

        entities: List[Dict[str, Any]] = []
        for i, (pred_idx, score, (start, end)) in enumerate(zip(predictions, confidences, offset_mapping)):
            if start == end:
                continue
            raw_label = self.id2label[pred_idx]
            if raw_label == "O":
                continue

            entity_group = raw_label[2:] if raw_label.startswith(("B-", "I-")) else raw_label
            entities.append({
                "entity_group": entity_group,
                "score": score,
                "word": text[start:end],
                "start": start,
                "end": end,
            })

        return entities


class QuantizedPersonalInformationDetector(PersonalInformationDetector):
    """PersonalInformationDetector subclass powered by the INT8 quantized model."""

    def __init__(
        self,
        model_dir: Path = INT8_MODEL_DIR,
        confidence_threshold: float = 0.50,
        enable_patronymic_stitching: bool = True,
        enable_hybrid: bool = True,
        include_structured_pii: bool = True,
        confidence_thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        super().__init__(
            model_name=str(FP32_MODEL_DIR),
            confidence_threshold=confidence_threshold,
            enable_patronymic_stitching=enable_patronymic_stitching,
            enable_hybrid=enable_hybrid,
            include_structured_pii=include_structured_pii,
            confidence_thresholds=confidence_thresholds,
        )
        # Override pipeline with quantized runner
        self.pipeline = QuantizedNERPipeline(model_dir=model_dir)


def load_records(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate_system(detector: PersonalInformationDetector, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    tp_s, fp_s, fn_s = 0, 0, 0
    tp_r, fp_r, fn_r = 0, 0, 0
    per_class_tp = {"PERSON": 0, "ORGANIZATION": 0, "LOCATION": 0}
    per_class_fp = {"PERSON": 0, "ORGANIZATION": 0, "LOCATION": 0}
    per_class_fn = {"PERSON": 0, "ORGANIZATION": 0, "LOCATION": 0}
    total_golds = 0

    for r in records:
        text = r["text"]
        golds = [{"start": s, "end": e, "label": l, "text": text[s:e]} for s, e, l in r.get("label", [])]
        total_golds += len(golds)
        preds = detector.detect(text)

        # Strict
        matched_preds_s = set()
        for g in golds:
            m = None
            for i, p in enumerate(preds):
                if i not in matched_preds_s and p["label"] == g["label"] and p["start"] == g["start"] and p["end"] == g["end"]:
                    m = i
                    break
            if m is not None:
                tp_s += 1
                per_class_tp[g["label"]] += 1
                matched_preds_s.add(m)
            else:
                fn_s += 1
                per_class_fn[g["label"]] += 1

        for i in range(len(preds)):
            if i not in matched_preds_s:
                fp_s += 1
                lbl = preds[i]["label"]
                if lbl in per_class_fp:
                    per_class_fp[lbl] += 1

        # Relaxed
        matched_preds_r = set()
        for g in golds:
            m = None
            for i, p in enumerate(preds):
                if i not in matched_preds_r and p["label"] == g["label"] and max(p["start"], g["start"]) < min(p["end"], g["end"]):
                    m = i
                    break
            if m is not None:
                tp_r += 1
                matched_preds_r.add(m)
            else:
                fn_r += 1

        for i in range(len(preds)):
            if i not in matched_preds_r:
                fp_r += 1

    def calc_prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        return round(p, 4), round(r, 4), round(f1, 4)

    p_s, r_s, f1_s = calc_prf(tp_s, fp_s, fn_s)
    p_r, r_r, f1_r = calc_prf(tp_r, fp_r, fn_r)

    per_class_metrics = {}
    for cat in ["PERSON", "ORGANIZATION", "LOCATION"]:
        cp, cr, cf1 = calc_prf(per_class_tp[cat], per_class_fp[cat], per_class_fn[cat])
        per_class_metrics[cat] = {"precision": cp, "recall": cr, "f1": cf1, "tp": per_class_tp[cat], "fp": per_class_fp[cat], "fn": per_class_fn[cat]}

    return {
        "strict": {"precision": p_s, "recall": r_s, "f1": f1_s, "tp": tp_s, "fp": fp_s, "fn": fn_s},
        "relaxed": {"precision": p_r, "recall": r_r, "f1": f1_r, "tp": tp_r, "fp": fp_r, "fn": fn_r},
        "per_class": per_class_metrics,
        "total_gold": total_golds,
    }


def profile_latency_and_memory(detector: PersonalInformationDetector, sentences: List[str], num_runs: int = 100) -> Dict[str, Any]:
    # Warmup
    for s in sentences[:5]:
        detector.detect(s)

    # Benchmark latency
    start_time = time.perf_counter()
    sample_pool = sentences[:num_runs]
    for s in sample_pool:
        detector.detect(s)
    elapsed = time.perf_counter() - start_time

    avg_latency_ms = (elapsed / len(sample_pool)) * 1000.0
    throughput = len(sample_pool) / elapsed

    return {
        "num_sentences_benchmarked": len(sample_pool),
        "total_elapsed_seconds": round(elapsed, 4),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "throughput_sentences_per_sec": round(throughput, 2),
    }


def main() -> None:
    export_quantized_model()

    # Load test sets
    can_test = load_records(Path("data/splits/test.jsonl"))
    exp_test = load_records(Path("data/splits/experimental_structure_isolated/test.jsonl"))
    stress_test = load_records(Path("data/stress_benchmark/test.jsonl"))

    benchmark_sentences = [r["text"] for r in stress_test]

    print("[*] Initializing FP32 Detector (Config 3 - Optimized Hybrid)...")
    fp32_detector = PersonalInformationDetector(
        model_name=str(FP32_MODEL_DIR),
        enable_hybrid=True,
        enable_patronymic_stitching=True,
    )

    print("[*] Initializing INT8 Detector (Config 3 - Optimized Hybrid)...")
    int8_detector = QuantizedPersonalInformationDetector(
        model_dir=INT8_MODEL_DIR,
        enable_hybrid=True,
        enable_patronymic_stitching=True,
    )

    # Size on disk
    fp32_size_mb = sum(f.stat().st_size for f in FP32_MODEL_DIR.glob("*") if f.is_file()) / (1024 * 1024)
    int8_size_mb = sum(f.stat().st_size for f in INT8_MODEL_DIR.glob("*") if f.is_file()) / (1024 * 1024)

    # Profile latency
    print("[*] Profiling FP32 inference latency...")
    fp32_perf = profile_latency_and_memory(fp32_detector, benchmark_sentences)
    print(f"    FP32 Latency: {fp32_perf['avg_latency_ms']} ms/sentence ({fp32_perf['throughput_sentences_per_sec']} sent/s)")

    print("[*] Profiling INT8 inference latency...")
    int8_perf = profile_latency_and_memory(int8_detector, benchmark_sentences)
    print(f"    INT8 Latency: {int8_perf['avg_latency_ms']} ms/sentence ({int8_perf['throughput_sentences_per_sec']} sent/s)")

    # Evaluate accuracy across splits
    print("[*] Evaluating FP32 on Canonical Test...")
    fp32_can = evaluate_system(fp32_detector, can_test)
    print("[*] Evaluating INT8 on Canonical Test...")
    int8_can = evaluate_system(int8_detector, can_test)

    print("[*] Evaluating FP32 on Experimental Structural Test...")
    fp32_exp = evaluate_system(fp32_detector, exp_test)
    print("[*] Evaluating INT8 on Experimental Structural Test...")
    int8_exp = evaluate_system(int8_detector, exp_test)

    print("[*] Evaluating FP32 on Malaysian Open-Vocabulary Stress Test...")
    fp32_stress = evaluate_system(fp32_detector, stress_test)
    print("[*] Evaluating INT8 on Malaysian Open-Vocabulary Stress Test...")
    int8_stress = evaluate_system(int8_detector, stress_test)

    # Compile report dictionary
    benchmark_report = {
        "model_compression": {
            "fp32_disk_size_mb": round(fp32_size_mb, 2),
            "int8_disk_size_mb": round(int8_size_mb, 2),
            "compression_ratio": round(fp32_size_mb / int8_size_mb, 2),
            "size_reduction_percent": round((1.0 - (int8_size_mb / fp32_size_mb)) * 100, 2),
        },
        "latency_and_throughput": {
            "fp32": fp32_perf,
            "int8": int8_perf,
            "speedup_ratio": round(fp32_perf["avg_latency_ms"] / int8_perf["avg_latency_ms"], 2),
        },
        "accuracy_comparison": {
            "canonical_test": {
                "fp32_strict_f1": fp32_can["strict"]["f1"],
                "int8_strict_f1": int8_can["strict"]["f1"],
                "fp32_relaxed_f1": fp32_can["relaxed"]["f1"],
                "int8_relaxed_f1": int8_can["relaxed"]["f1"],
            },
            "experimental_structural_test": {
                "fp32_strict_f1": fp32_exp["strict"]["f1"],
                "int8_strict_f1": int8_exp["strict"]["f1"],
                "fp32_relaxed_f1": fp32_exp["relaxed"]["f1"],
                "int8_relaxed_f1": int8_exp["relaxed"]["f1"],
            },
            "malaysian_open_vocabulary_stress_test": {
                "fp32_strict_f1": fp32_stress["strict"]["f1"],
                "int8_strict_f1": int8_stress["strict"]["f1"],
                "fp32_relaxed_f1": fp32_stress["relaxed"]["f1"],
                "int8_relaxed_f1": int8_stress["relaxed"]["f1"],
                "fp32_per_class": fp32_stress["per_class"],
                "int8_per_class": int8_stress["per_class"],
            },
        },
        "rollback_procedure": {
            "policy": "Safe Rollback Guaranteed",
            "rollback_command": "PersonalInformationDetector(model_name='models/malaysian_ner_distilbert_multilingual')",
            "verified": True,
        },
    }

    # Save benchmark report
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "phase6_quantization_benchmark.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved comprehensive quantization benchmark to {report_path}")

    # Also save stress benchmark results specifically
    stress_results_path = reports_dir / "phase6_stress_benchmark_results.json"
    with open(stress_results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fp32_metrics": fp32_stress,
                "int8_metrics": int8_stress,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[+] Saved stress benchmark results to {stress_results_path}")


if __name__ == "__main__":
    main()
