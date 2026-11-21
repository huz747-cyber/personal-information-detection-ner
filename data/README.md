# Malaysian NER & Structured PII Dataset Architecture

This directory houses dataset resources, annotation schemas, validation pipelines, release manifests, and partition splits for Malaysian Named Entity Recognition (NER) and Structured PII detection.

---

## Directory Organization

```text
data/
├── ANNOTATION_GUIDELINES.md     # Authoritative IOB2 annotation guidelines (v1.0.0)
├── README.md                    # Architecture, schema, provenance, and split documentation
├── SOURCE_MANIFEST.csv          # Complete provenance and licensing register for all data sources
├── annotated/                   # Canonical annotated corpora (Doccano JSONLines)
│   ├── malaysian_ner_1000.jsonl # Expanded canonical 1,000-sentence Malaysian NER dataset
│   └── sample_malaysian_ner.jsonl # Initial 37-sentence prototype sample (Phase 2.5)
├── collection/                  # Sub-corpora by provenance channel
│   ├── public/                  # Publicly sourced data (Bursa disclosures, Hansard, CoNLL baseline)
│   ├── independent/             # Independently authored Malaysian conversational & corporate text
│   ├── synthetic/               # Template-generated combinatorial sentences
│   └── double_annotation/       # Dual-annotated subset for inter-annotator concordance auditing
├── manifests/                   # Scoped legal release manifests enforcing fail-closed compliance
│   ├── release_research_manifest.json            # 1,000 records cleared for academic research
│   ├── release_commercial_training_manifest.json # 855 records cleared for commercial training
│   ├── release_raw_redistribution_manifest.json  # 855 records cleared for public text download
│   └── release_metadata_manifest.json            # 950 records cleared for standalone metadata release
├── raw/                         # Decoupled structured PII & raw ingested datasets
│   └── structured_pii_sample.jsonl # 15 records with validated MyKad, phone, and postcode spans
├── reports/                     # Audit reports, release evaluations, and concordance metrics
└── splits/                      # Reproducible 70/15/15 partitioned splits
    ├── train.jsonl              # 705 sentences (70.5%)
    ├── val.jsonl                # 150 sentences (15.0%)
    ├── test.jsonl               # 145 sentences (14.5%)
    └── experimental_structure_isolated/ # Zero-structural-overlap diagnostic split (700/150/150)
```

---

## 1. Architectural Philosophy: Decoupled PII

In conventional NLP pipelines, numeric identifiers (e.g., identity card numbers, phone numbers, postcodes) are often forced into sequence labeling models alongside semantic entities (`PERSON`, `ORGANIZATION`, `LOCATION`). In practice, this causes substantial failure modes:

1. **Subword Tokenization Fragmentation:**  
   Pretrained transformer tokenizers (e.g., WordPiece, Byte-Pair Encoding) break 12-digit unhyphenated numbers like `950315105231` into 4 to 6 arbitrary subword tokens (`95`, `##03`, `##15`, `##10`, `##52`, `##31`). Standard sequence taggers struggle to learn long-range sequence grammar on fragmented subwords without massive labeled numeric data.

2. **Algorithmic Validation vs. Semantic Ambiguity:**  
   Malaysian NRIC (MyKad) numbers have strict deterministic rules (calendar dates + official JPN 2-digit state birth codes). Phone numbers follow MCMC-allocated telco blocks (`010`–`019`). Postcodes strictly correspond to POS Malaysia routing codes (`01xxx`–`98xxx`). Regex patterns paired with finite-state validation achieve near-100% precision on clean patterns, whereas language models frequently mistake order numbers or currency figures for identifiers.

3. **Regulatory Separation (PDPA 2010):**  
   Under Malaysia's Personal Data Protection Act 2010, national registration IDs and direct contact channels require strict access control, masking, and hashing. Decoupling them allows dedicated auditing, differential privacy, and independent redaction layers without retraining transformer backbones.

---

## 2. Dataset Composition & Stratification (1,000 Canonical Sentences)

The canonical dataset ([data/annotated/malaysian_ner_1000.jsonl](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/annotated/malaysian_ner_1000.jsonl)) contains exactly **1,000 unique sentences** capturing Malaysian sociolinguistic diversity, code-switching, and cultural naming patterns.

### 2.1 Linguistic Stratification Matrix

| Category / Stratum | Code | Sentence Count | Percentage | Description |
| :--- | :--- | :---: | :---: | :--- |
| **Standard Formal Malay** | `formal_malay` | 240 | 24.0% | Official administrative, parliamentary, legal, and news text. |
| **Malaysian English** | `malaysian_english` | 240 | 24.0% | Local corporate, professional, and commercial business English. |
| **Manglish & Conversational** | `manglish` | 140 | 14.0% | Colloquial Malaysian English featuring discourse particles (*lah*, *meh*, *kan*). |
| **Malay-English Code-Switching**| `mixed_code_switch`| 140 | 14.0% | Natural bilingual conversational exchanges and social dialogue. |
| **Malaysian Chinese Naming** | `chinese_naming` | 95 | 9.5% | Dialect romanization (Hokkien, Cantonese, Teochew) + Western-Chinese names. |
| **Malaysian Indian Naming** | `indian_naming` | 95 | 9.5% | Patronymics (`a/l`, `a/p`, `s/o`, `d/o`), Tamil, and Punjabi naming contexts. |
| **Western Baseline Regression** | `international_baseline` | 50 | 5.0% | International anchor sentences from CoNLL-2003 preventing catastrophic forgetting. |
| **TOTAL** | | **1,000** | **100.0%** | **Target 1,000 Verified Sentences** |

### 2.2 Hard-Negative Examples
* **Total Hard Negatives:** **105 sentences** (10.5% of corpus; exceeds the $\ge 100$ requirement).
* **Composition:** Contains distractor patterns including currency amounts (`RM 50,000`), calendar dates (`14hb Ogos 2024`), numerical order IDs, and legal terms without any `PERSON`, `ORGANIZATION`, or `LOCATION` entities.
* **Integrity Guarantee:** Verified via automated auditing to contain **zero entity annotations** (`len(entities) == 0`).

---

## 3. Entity Statistics & Class Distributions

The canonical dataset contains **2,230 named entities** mapped across 3 semantic categories:

| Entity Category | Tag (IOB2) | Total Spans | Percentage | Span Description |
| :--- | :--- | :---: | :---: | :--- |
| **`LOCATION`** | `B-LOC`, `I-LOC` | 830 | 37.2% | Geopolitical entities, states, federal territories, street addresses, and precincts. |
| **`PERSON`** | `B-PER`, `I-PER` | 823 | 36.9% | Proper personal names including patronymic particles (`bin`, `binti`, `a/l`, `a/p`). |
| **`ORGANIZATION`** | `B-ORG`, `I-ORG` | 577 | 25.9% | Statutory bodies, government ministries, registered corporations (`Sdn Bhd`), universities. |
| **TOTAL** | | **2,230** | **100.0%** | **Exact 1:1 Invariant: Total Entities == B-Tag Count** |

### BIO Token Distribution:
* `B-LOCATION`: 830 | `I-LOCATION`: 488
* `B-ORGANIZATION`: 577 | `I-ORGANIZATION`: 1,288
* `B-PERSON`: 823 | `I-PERSON`: 1,690
* `O`: 16,689 tokens

---

## 4. Provenance & Source Licensing Register

All 1,000 sentences are traceable to registered sources documented in [data/SOURCE_MANIFEST.csv](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/SOURCE_MANIFEST.csv):

| Source ID | Source Name | Primary Licence | Volume | Sourced / Synthetic | Commercial Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **`SRC-001`** | Mesolitica Malaya NER | MIT (Code) / News Fair Dealing | 47 | Public Sourced | `UNVERIFIED` (Research Only) |
| **`SRC-004`** | CoNLL-2003 English NER | Reuters Open Research License | 50 | Public Sourced | `VERIFIED_RESTRICTED` (Research Only) |
| **`SRC-005`** | Parliamentary Hansard | Public Record (Act 332 s. 13(2)(h)) | 48 | Public Sourced | `UNVERIFIED` (Research Only) |
| **`SRC-006`** | Bursa Malaysia Corporate | Public Regulatory Disclosures | 80 | Public Sourced | `VERIFIED_ALLOWED` (Commercial) |
| **`SRC-007`** | Independent Project Authorship | MIT License (Original Work) | 485 | Human-Authored | `VERIFIED_ALLOWED` (Commercial) |
| **`SRC-008`** | Combinatorial Synthetic Engine | MIT License / CC0 Dedication | 290 | Synthetic | `VERIFIED_ALLOWED` (Commercial) |

### Synthetic vs. Sourced Breakdown:
* **Human-Authored & Publicly Sourced Data:** **710 sentences (71.0%)** (`SRC-001`: 47, `SRC-004`: 50, `SRC-005`: 48, `SRC-006`: 80, `SRC-007`: 485).
* **Synthetic Generator Data:** **290 sentences (29.0%)** (`SRC-008`).

---

## 5. Partition Splits (Seed 42 / Knapsack Grouping)

To eliminate cross-split data leakage, partitioning was executed using **sentence-weighted knapsack bin packing** grouped by `document_id` and `template_id`:

| Split Partition | File Path | Sentence Count | Ratio | Entities | Hard Negatives |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Train** | `data/splits/train.jsonl` | **705** | 70.5% | 1,630 | 75 |
| **Validation** | `data/splits/val.jsonl` | **150** | 15.0% | 295 | 20 |
| **Test** | `data/splits/test.jsonl` | **145** | 14.5% | 305 | 10 |
| **TOTAL** | | **1,000** | **100.0%** | **2,230** | **105** |

### Leakage Audit Invariants:
* Cross-split exact text duplicates: **0 (Zero)**
* Cross-split normalized text duplicates: **0 (Zero)**
* Cross-split document ID leakage: **0 (Zero)**
* Cross-split template ID leakage: **0 (Zero)**

### Diagnostic Alternative Split:
An alternative experimental partition is available under `data/splits/experimental_structure_isolated/` (700 Train / 150 Val / 150 Test). It isolates all 303 abstract grammatical frames with **zero structural overlap**, serving as a diagnostic benchmark for zero-shot syntactic generalization.

---

## 6. Privacy & Security Safeguards

In compliance with the Malaysian Personal Data Protection Act 2010 (PDPA) and privacy engineering best practices:
1. **Zero Real PII:** All personal names in independent and synthetic text are fictional or historical.
2. **Deterministic Privacy Screening:** Every record was evaluated by [privacy_screener.py](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/src/dataset_tools/privacy_screener.py):
   * Zero API keys, private passwords, or security credentials.
   * Zero credit card or bank account numbers.
   * Zero live residential addresses or personal mobile numbers.
3. **Public Officeholders Only:** Parliamentary debate records retain only public ministerial designations and assembly titles.

---

## 7. Known Limitations

1. **Algorithmic Concordance Baseline:** Initial inter-annotator agreement was evaluated algorithmically ($F_1 = 0.9969$, $\kappa = 0.9978$) using simulated institutional annotation variance. Physical human annotation campaigns should be conducted prior to commercial high-stakes deployment using the protocol in [phase_2_6_2_human_annotation_plan.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_human_annotation_plan.md).
2. **Canonical Structural Overlap:** While the canonical split strictly eliminates entity and document leakage, 46 abstract sentence frames appear across Train and Test due to standard regulatory and corporate phrasing formulas.
3. **Government License Ambiguity:** Malaysian Parliamentary Hansard transcripts are protected from infringement for reporting purposes, but lack an explicit commercial Open Government License. Consequently, 48 Hansard records are excluded from commercial release manifests.

---

## 8. Dataset Tooling Commands

Run validation checks on the canonical dataset:
```bash
python -m src.dataset_tools.validator --file data/annotated/malaysian_ner_1000.jsonl
```

Verify zero cross-split leakage:
```bash
python -m src.dataset_tools.validator --train data/splits/train.jsonl --val data/splits/val.jsonl --test data/splits/test.jsonl
```

Generate release manifests enforcing fail-closed compliance:
```bash
python -c "from src.dataset_tools.release_checker import DatasetReleaseChecker; import json; recs=[json.loads(l) for l in open('data/annotated/malaysian_ner_1000.jsonl')]; DatasetReleaseChecker().generate_release_manifests(recs)"
```
