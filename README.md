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
│   ├── __init__.py          # Package initialization
│   ├── entity_extractor.py  # Core NER detection, label mapping, and redaction logic
│   ├── predict.py           # Pretrained DistilBERT inference CLI & test suite
│   └── train.py             # Future CoNLL-2003 fine-tuning script with Trainer & seqeval
├── examples/
│   ├── __init__.py
│   ├── sample_texts.json    # Curated real-world test cases (corporate, medical, tech, etc.)
│   └── run_demo.py          # Runnable demo executing detection and PII redaction
└── tests/
    ├── __init__.py
    └── test_extractor.py    # Unit tests for schema validation, detection, and masking
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

## 🛡️ Privacy, Security & Ethics

- **Zero-Storage Rule**: The detection script runs entirely locally or in-memory; no processed text or personal data is uploaded to remote servers or logged.
- **Git Hygiene**: Model weights (`*.safetensors`, `*.bin`), virtual environments (`.venv/`), and environment files (`.env`) are strictly excluded via `.gitignore`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
