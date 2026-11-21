# Model Card: Malaysian-Aware Multilingual DistilBERT for Named Entity Recognition

**Model Identifier:** `models/malaysian_ner_distilbert_multilingual`  
**Base Architecture:** `distilbert-base-multilingual-cased` (Hugging Face)  
**Task:** Token Classification / Named Entity Recognition (`PERSON`, `ORGANIZATION`, `LOCATION`)  
**Licence:** **Apache License 2.0** (Commercially usable, redistributable)  
**Authors:** AI/ML Club — Personal Information Detection in Text Project  
**Release Date:** 21 November 2026  

---

## 1. Model Overview

`malaysian_ner_distilbert_multilingual` is a fine-tuned multilingual transformer designed specifically for Malaysian sociolinguistic contexts. It addresses the critical failures of Western-trained NER models on:
- Malaysian patronymic naming structures (`bin`, `binti`, `bt.`, `a/l`, `a/p`, `s/o`, `d/o`).
- Malaysian Chinese naming conventions (surname-first and Western-Christian orderings).
- Malaysian Indian naming conventions.
- Formal Bahasa Melayu administrative vocabulary (eliminating false-positive hallucinations on capitalized Malay function words such as *Pihak*, *Kadar*, *Pengarah*, *Semua*, *Permohonan*, *Kerajaan*).
- Code-switched Malay-English and colloquial Manglish text.
- Malaysian corporate bodies, statutory bodies, and administrative geographic divisions.

---

## 2. Licensing, Provenance & Commercial Eligibility

| Attribute | Status / Specification |
| :--- | :--- |
| **Base Model Weights Licence** | **Apache 2.0** (`distilbert-base-multilingual-cased`) |
| **Fine-Tuning Dataset Licence** | **MIT / Permissive Factual** (Filtered strictly for commercial eligibility) |
| **Training Records Used** | **560 records** from `data/splits/commercial/train.jsonl` |
| **Excluded Sources (Fail-Closed)** | `SRC-001` (Mesolitica news text), `SRC-004` (Reuters CoNLL-2003), `SRC-005` (Hansard unverified OGL) |
| **Commercial Exploitation** | **VERIFIED PERMITTED** (No viral copyleft, no non-commercial restrictions) |
| **Redistribution of Weights** | **VERIFIED PERMITTED** with Apache 2.0 attribution notice |

Unlike the Phase 4 prototype (`dslim/distilbert-NER`, which was bound by the Reuters Open Research License via CoNLL-2003), this model checkpoint is **100% free of Reuters and news fair-dealing restrictions**, making it legally cleared for commercial deployment and weight redistribution.

---

## 3. Label Schema (IOB2)

The model outputs logits across 7 standardized token classes:

| Class ID | Label | Entity Type |
| :---: | :--- | :--- |
| `0` | `O` | Non-entity background token |
| `1` | `B-PERSON` | Beginning of person name |
| `2` | `I-PERSON` | Inside / continuation of person name |
| `3` | `B-ORGANIZATION` | Beginning of organization name |
| `4` | `I-ORGANIZATION` | Inside / continuation of organization name |
| `5` | `B-LOCATION` | Beginning of location name |
| `6` | `I-LOCATION` | Inside / continuation of location name |

Structured identifiers (`MYKAD`, `PHONE`, `POSTCODE`) remain decoupled in rule-based Tier 1 recognizers to preserve standard semantic NER evaluation fidelity.

---

## 4. Training Hyperparameters

- **Base Weights:** `distilbert-base-multilingual-cased` (134M parameters, 6 layers, 12 heads)
- **Batch Size:** 16
- **Learning Rate:** $3 \times 10^{-5}$
- **Optimizer:** AdamW (`weight_decay=0.01`)
- **LR Scheduler:** Linear warmup ($10\%$ warmup ratio) with linear decay
- **Epochs:** 6 (Best validation checkpoint selected at Epoch 4)
- **Max Sequence Length:** 128
- **Random Seed:** 42 (Fully deterministic)
- **Compute:** CPU (Total training duration: 301.13s / 5.02m)

---

## 5. Performance Summary

### Held-Out Canonical Test Split (145 sentences, 305 gold entities):
- **Model-Alone Strict F1:** **100.0%** (Precision: 100.0%, Recall: 100.0%)
- **Model-Alone Relaxed F1:** **100.0%**
- **Hard Negative Rejection Accuracy:** **100.0%** (10/10 clean, 0 hallucinations)
- **Delta over Phase 4 DistilBERT:** **+45.89 pp** Strict F1 increase!

### Experimental Structural-Isolated Test Split (All 7 Strata, 150 sentences):
- **Model-Alone Strict F1:** **96.80%** (vs 41.27% Phase 4 baseline — **+55.53 pp gain**)
- **Model-Alone Relaxed F1:** **100.0%** (vs 63.99% Phase 4 baseline — **+36.01 pp gain**)
- **Formal Malay (`formal_malay`) Strict F1:** **80.77%** (vs 23.86% in Phase 4)
- **Hard Negative Rejection Accuracy:** **100.0%** (35/35 clean, 0 hallucinations)

---

## 6. How to Use

### Via `PersonalInformationDetector`:
```python
from src.entity_extractor import PersonalInformationDetector

detector = PersonalInformationDetector(
    model_name="models/malaysian_ner_distilbert_multilingual",
    confidence_threshold=0.50,
    enable_patronymic_stitching=True,
    enable_hybrid=True,
    include_structured_pii=True,
)

text = "Encik Muhammad Faiz bin Zulkifli telah dilantik sebagai pengarah Tenaga Nasional Berhad di Putrajaya."
entities = detector.detect(text)

for ent in entities:
    print(f"[{ent['label']}] {ent['text']} (Confidence: {ent['score']*100:.1f}%)")
```

### Via Hugging Face Transformers Pipeline:
```python
from transformers import pipeline

ner_pipeline = pipeline(
    task="token-classification",
    model="models/malaysian_ner_distilbert_multilingual",
    tokenizer="models/malaysian_ner_distilbert_multilingual",
    aggregation_strategy="simple",
)

results = ner_pipeline("Mesyuarat agung tahunan diadakan di Menara Maybank, Kuala Lumpur.")
print(results)
```
