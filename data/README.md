# Malaysian NER & Structured PII Dataset Architecture

This directory houses dataset resources, annotation schemas, validation pipelines, and split partitions for Malaysian Named Entity Recognition and Structured PII detection.

---

## Directory Organization

```text
data/
├── ANNOTATION_GUIDELINES.md     # Authoritative IOB2 annotation guidelines
├── README.md                    # Architecture and schema documentation
├── annotated/                   # Canonical annotated corpora (Doccano JSONLines)
│   └── sample_malaysian_ner.jsonl
├── raw/                         # Decoupled structured PII & raw ingested datasets
│   └── structured_pii_sample.jsonl
└── splits/                      # Reproducible 70/15/15 partitioned splits
    ├── train.jsonl
    ├── val.jsonl
    └── test.jsonl
```

---

## 1. Architectural Philosophy: Decoupled PII

In conventional NLP pipelines, numeric identifiers (e.g., identity card numbers, phone numbers, postcodes) are often forced into sequence labeling models alongside semantic entities (`PERSON`, `ORGANIZATION`, `LOCATION`). In practice, this causes substantial failure modes:

1. **Subword Tokenization Fragmentation:**  
   Pretrained transformer tokenizers (e.g. WordPiece, Byte-Pair Encoding) break 12-digit unhyphenated numbers like `950315105231` into 4 to 6 arbitrary subword tokens (`95`, `##03`, `##15`, `##10`, `##52`, `##31`). Standard sequence taggers struggle to learn long-range sequence grammar on fragmented subwords without massive labeled numeric data.

2. **Algorithmic Validation vs. Semantic Ambiguity:**  
   Malaysian NRIC (MyKad) numbers have strict deterministic rules (calendar dates + official JPN 2-digit state birth codes). Phone numbers follow MCMC-allocated telco blocks (`010`–`019`). Postcodes strictly correspond to POS Malaysia routing codes (`01xxx`–`98xxx`). Regex patterns paired with finite-state validation achieve near-100% precision on clean patterns, whereas language models frequently mistake order numbers or currency figures for identifiers.

3. **Regulatory Separation (PDPA 2010):**  
   Under Malaysia's Personal Data Protection Act 2010, national registration IDs and direct contact channels require strict access control, masking, and hashing. Decoupling them allows dedicated auditing, differential privacy, and independent redaction layers without retraining transformer backbones.

---

## 2. Data Schemas

### 2.1 General NER Schema (`data/annotated/*.jsonl`)
Standard Doccano JSONLines format:

```json
{
  "id": "my-ner-001",
  "text": "Ahmad Faiz bin Zulkifli telah dilantik sebagai pengarah di Universiti Malaya di Kuala Lumpur.",
  "label": [
    [0, 23, "PERSON"],
    [58, 75, "ORGANIZATION"],
    [79, 91, "LOCATION"]
  ],
  "meta": {
    "language": "ms",
    "stratum": "formal_malay",
    "domain": "higher_education",
    "source_type": "synthetic_curated"
  }
}
```

### 2.2 Decoupled Structured PII Schema (`data/raw/*.jsonl`)
Dedicated structured record format for algorithmic validation:

```json
{
  "id": "my-pii-001",
  "text": "Sila hubungi Ahmad Faiz (No. K/P: 950315-10-5231) di talian +6012-345 6789 atau poskod 50250.",
  "pii_spans": [
    {
      "type": "MYKAD",
      "start": 34,
      "end": 48,
      "raw_value": "950315-10-5231",
      "masked_value": "950315-10-****",
      "is_valid_format": true,
      "metadata": {
        "birth_date": "1995-03-15",
        "jpn_state_code": "10",
        "state_name": "Selangor"
      }
    },
    {
      "type": "PHONE",
      "start": 60,
      "end": 74,
      "raw_value": "+6012-345 6789",
      "masked_value": "+6012-*** ****",
      "is_valid_format": true,
      "metadata": {
        "network": "Mobile",
        "telco_prefix": "012"
      }
    },
    {
      "type": "POSTCODE",
      "start": 88,
      "end": 93,
      "raw_value": "50250",
      "masked_value": "50250",
      "is_valid_format": true,
      "metadata": {
        "state_routing": "Kuala Lumpur",
        "prefix": "50"
      }
    }
  ],
  "metadata": {
    "is_synthetic": true
  }
}
```

---

## 3. Dataset Tooling Commands

Run validation checks on any dataset file:
```bash
python -m src.dataset_tools.validator --file data/annotated/sample_malaysian_ner.jsonl
```

Verify zero cross-split leakage:
```bash
python -m src.dataset_tools.validator --train data/splits/train.jsonl --val data/splits/val.jsonl --test data/splits/test.jsonl
```

Generate reproducible 70/15/15 splits:
```bash
python -m src.dataset_tools.splitter --input data/annotated/sample_malaysian_ner.jsonl --output-dir data/splits --seed 42
```
