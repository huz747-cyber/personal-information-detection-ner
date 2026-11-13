# Personal Information Detection in Text using NER

An NLP and Named Entity Recognition (NER) project for detecting people, organizations, and locations in text. Developed as an AI/ML Club project.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Transformers-yellow)](https://huggingface.co/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Project Overview

In the era of privacy compliance (GDPR, HIPAA, PDPA), identifying Personally Identifiable Information (PII) before storing, processing, or transmitting unstructured text is critical.

This project implements a **Named Entity Recognition (NER)** pipeline using **DistilBERT** (a lightweight, fast Transformer model) to detect and redact sensitive entity types:
- **`PERSON`**: Names of individuals (e.g., *Dr. Sarah Connor*, *Alice Smith*)
- **`ORGANIZATION`**: Companies, agencies, and institutions (e.g., *Google*, *Red Cross*, *United Nations*)
- **`LOCATION`**: Cities, countries, and geographical regions (e.g., *Geneva*, *Tokyo*, *Zurich*)

### Key Design Principle: Inference vs. Fine-Tuning Separation
To keep the codebase maintainable and accessible:
- **`src/predict.py` & `src/entity_extractor.py`**: Prototype inference using the pretrained `dslim/distilbert-NER` model. Runs immediately out-of-the-box without requiring any model training.
- **`src/train.py`**: A dedicated, fully prepared training and fine-tuning pipeline using the standard **CoNLL-2003** dataset from Hugging Face Datasets and evaluation via **seqeval**. Ready to be launched whenever fine-tuning is required.

---

## 📂 Repository Structure

```
personal-information-detection-ner/
├── .gitignore               # Excludes virtual environments, models, caches & secrets
├── README.md                # Project documentation and quickstart guide
├── requirements.txt         # Core dependencies (torch, transformers, datasets, seqeval)
├── src/
│   ├── __init__.py          # Package initialization & exports
│   ├── entity_extractor.py  # Core NER detection, hybrid pipeline coordinator & redaction
│   ├── patronymic_stitcher.py # Malaysian patronymic consolidator (bin, binti, bt., a/l, a/p, s/o, d/o)
│   ├── evaluate_benchmark.py# 3-Tier benchmark evaluation tool computing Precision, Recall, Strict & Relaxed F1
│   ├── predict.py           # Pretrained DistilBERT inference CLI & test suite
│   ├── train.py             # Future CoNLL-2003 fine-tuning script with Trainer & seqeval
│   └── recognizers/         # Phase 2: Modular Malaysian Recognizers & Gazetteers
│       ├── __init__.py
│       ├── mykad_recognizer.py      # Malaysian NRIC / MyKad pattern & JPN routing validator
│       ├── phone_recognizer.py      # Malaysian mobile and landline (+60 / 0) pattern recognizer
│       ├── org_gazetteer.py         # Statutory agencies, public bodies, and corporate gazetteer
│       ├── title_recognizer.py      # Malaysian honorific detector & false-positive purger
│       ├── location_recognizer.py   # Malaysian postcodes & geographic location gazetteer
│       └── conflict_resolver.py     # Multi-tier entity deduplication & span conflict resolver
├── examples/
│   ├── __init__.py
│   ├── sample_texts.json    # Curated real-world test cases (corporate, medical, tech, etc.)
│   ├── malaysian_benchmark.json # Ground-truth annotated 22-case Malaysian synthetic benchmark dataset
│   └── run_demo.py          # Runnable demo executing detection and PII redaction
└── tests/
    ├── __init__.py
    ├── test_extractor.py          # Unit tests for baseline schema validation, detection, and masking
    ├── test_malaysian_entities.py # Unit tests for Malaysian patronymics & score non-inflation
    └── test_hybrid_recognizers.py # Dedicated unit tests for Phase 2 MyKad, Phone, Postcode, and Gazetteers
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Git

### 2. Environment Setup

Create and activate a virtual environment:

```bash
# Clone the repository
git clone https://github.com/huz747-cyber/personal-information-detection-ner.git
cd personal-information-detection-ner

# Create a virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Or on Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔍 Running Inference (Pretrained Prototype)

The initial prototype uses `dslim/distilbert-NER` for fast, CPU/GPU-friendly inference.

### Run Sample Benchmark Sentences
```bash
python src/predict.py
```

### Analyze Custom Text via CLI
```bash
python src/predict.py --text "Dr. Sarah Connor met with Cyberdyne Systems in Los Angeles."
```

**Output:**
```
Input Text: "Dr. Sarah Connor met with Cyberdyne Systems in Los Angeles."
----------------------------------------------------------------------
Entity                    | Type            | Confidence | Offsets   
----------------------------------------------------------------------
Sarah Connor              | PERSON          | 99.4%      | 4:16      
Cyberdyne Systems         | ORGANIZATION    | 98.7%      | 26:43     
Los Angeles               | LOCATION        | 99.1%      | 47:58     
----------------------------------------------------------------------
```

### Mask / Redact Sensitive Information
Use the `--redact` flag to automatically sanitize text:
```bash
python src/predict.py --text "Elena Rostova joined Microsoft in Zurich." --redact
```

**Output:**
```
Redacted: "[PERSON] joined [ORGANIZATION] in [LOCATION]."
```

### Interactive CLI Mode
```bash
python src/predict.py --interactive
```

### Run Full Multi-Domain Demo
```bash
python examples/run_demo.py
```

---

## 💻 Python API Usage

You can easily embed `PersonalInformationDetector` into any Python application:

```python
from src.entity_extractor import PersonalInformationDetector

# Initialize detector
detector = PersonalInformationDetector(confidence_threshold=0.50)

# Detect entities
text = "Satya Nadella visited Microsoft offices in Redmond."
entities = detector.detect(text)

for ent in entities:
    print(f"Found {ent['label']}: '{ent['text']}' (Score: {ent['score']})")

# Sanitize text
clean_text = detector.redact(text)
print(clean_text)
# Output: "[PERSON] visited [ORGANIZATION] offices in [LOCATION]."
```

---

## 🏋️ Fine-Tuning on CoNLL-2003 (Future Training)

`src/train.py` provides a complete training pipeline ready for fine-tuning on the gold-standard CoNLL-2003 dataset.

### Pipeline Features:
- Subword alignment with PyTorch ignore index (`-100`) for special tokens and continuations.
- Entity-level evaluation metrics via `seqeval` (Precision, Recall, F1, Accuracy).
- Checkpointing and automatic selection of the best model based on F1 score.

### Running a Quick Verification Smoke Test
```bash
python src/train.py --max_train_samples 200 --max_eval_samples 50 --epochs 1
```

### Running Full Fine-Tuning
```bash
python src/train.py --epochs 3 --batch_size 16 --learning_rate 2e-5 --output_dir ./models/distilbert-ner-finetuned
```

> **Note:** The initial prototype currently uses the pretrained checkpoint. No local fine-tuning is required until you wish to train your own custom model weights.

---

## 🧪 Running Unit Tests

Verify that entity extraction and redaction behave as expected:

```bash
pytest tests/ -v
```

---

## 🇲🇾 Malaysian-Aware NER & Hybrid Recognizer Layer (Phase 1 & Phase 2)

This repository incorporates a modular, multi-tier hybrid architecture combining Transformer deep learning with deterministic recognizers and domain gazetteers:

### 1. Architectural Tiers:
- **Tier 1 (Deterministic Recognizers & Gazetteers)**:
  - `MYKAD`: Validates 12-digit Malaysian NRICs against birth date logic and official JPN place-of-birth routing codes.
  - `PHONE`: Mobile (`+6010`-`+6019`, `010`-`019`) and landline (`03`-`09`, `082`-`089`) formats with false-positive rejection for dates, currency, and IP addresses.
  - `POSTCODE`: 5-digit POS Malaysia routing validation requiring nearby address context keywords to reject currency numbers.
  - `ORGANIZATION`: Curated gazetteer of statutory bodies (`LHDN`, `KWSP`, `PDRM`, `SPRM`, `JPJ`, `SSM`, `KKM`), public universities (`Universiti Malaya`), major banks (`Maybank`, `CIMB`), GLCs (`TNB`, `Petronas`), and registered company suffixes (`Sdn. Bhd.`, `Bhd.`, `PLT`).
  - `LOCATION`: Gazetteers for all Malaysian states, federal territories, major cities, tech corridors (`Cyberjaya`), and street prefixes (`Jalan ...`).
- **Tier 2 (Contextual Transformer Model)**:
  - `dslim/distilbert-NER` provides general open-vocabulary entity classification.
- **Tier 3 (Post-Processing & Conflict Resolution)**:
  - `src/patronymic_stitcher.py`: Consolidates Malaysian patronymic names (`bin`, `binti`, `bt.`, `a/l`, `a/p`, `s/o`, `d/o`).
  - `src/recognizers/title_recognizer.py`: Purges false-positive model predictions where Malaysian honorifics (`Dato' Seri`, `Tan Sri`) were tagged as organizations.
  - `src/recognizers/conflict_resolver.py`: Overlap arbitration and greedy deduplication prioritizing structured PII and curated gazetteers.

### 2. Benchmark Comparison (Baseline ➔ Phase 1 ➔ Phase 2)
Run the ground-truth benchmark comparison tool across the annotated synthetic benchmark:

```bash
python src/evaluate_benchmark.py
```

**Empirical 3-Tier Results (on 22 Validated Synthetic Cases):**
| Metric Class | Baseline (Raw DistilBERT) | Phase 1 (Patronymic Stitching) | Phase 2 (Full Hybrid Layer) | Total Gain ($\Delta$) |
| :--- | :---: | :---: | :---: | :---: |
| **Overall Strict F1** | 48.1% | 66.1% | **90.5%** | **+42.4%** |
| **Overall Relaxed F1**| 72.2% | 77.4% | **93.7%** | **+21.5%** |
| `PERSON` F1 | 40.0% | 87.0% | **90.9%** | **+50.9%** |
| `ORGANIZATION` F1 | 38.7% | 38.7% | **78.6%** | **+39.9%** |
| `LOCATION` F1 | 75.0% | 75.0% | **95.0%** | **+20.0%** |
| `MYKAD` F1 | 0.0% | 0.0% | **100.0%** | **+100.0%** |
| `PHONE` F1 | 0.0% | 0.0% | **100.0%** | **+100.0%** |
| `POSTCODE` F1 | 0.0% | 0.0% | **100.0%** | **+100.0%** |

---

## 🛡️ Privacy, Security & Ethics

- **Zero Identity Verification Claim**: Pattern detection validates algorithmic and syntactic formatting rules only; it does NOT verify actual identity status with the National Registration Department (JPN) or any official database.
- **Synthetic Test Data Only**: All benchmarks, examples, and test cases use strictly synthetic, fictional names and identifiers to respect privacy.
- **Zero-Storage Rule**: The detection script runs entirely locally or in-memory; no processed text or personal data is uploaded to remote servers or logged.
- **Git Hygiene**: Model weights (`*.safetensors`, `*.bin`), virtual environments (`.venv/`), and environment files (`.env`) are strictly excluded via `.gitignore`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
