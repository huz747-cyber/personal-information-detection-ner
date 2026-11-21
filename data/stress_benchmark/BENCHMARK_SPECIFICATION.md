# Malaysian Open-Vocabulary Stress Benchmark Specification (Phase 6)

**Benchmark Name:** Malaysian Open-Vocabulary NER Stress Benchmark  
**Date Frozen:** 21 November 2026  
**Total Records:** 200 unique Malaysian sentences  
**Total Named Entities:** 600 entities (200 PERSON, 200 ORGANIZATION, 200 LOCATION)  
**License & Provenance:** CC-BY-4.0 / MIT (100% Unencumbered Synthetic + Public Knowledge)  

---

## 1. Objective & Purpose

The **Malaysian Open-Vocabulary Stress Benchmark** was constructed in Phase 6 to provide an independent, uncompromised evaluation set for measuring genuine out-of-vocabulary entity generalization.

### Zero-Overlap Guarantee
- **Training Set Entity Overlap:** **0.0%** (0 / 150 unique entity strings appeared in `data/splits/commercial/train.jsonl`).
- **Canonical Test Set Overlap:** **0.0%**.
- **Model Checkpoint Isolation:** This benchmark was created **after** Phase 5 model training was completed and frozen. Zero sentences or entities from this benchmark were ever exposed to model gradients, checkpoint selection, or hyperparameter tuning.

---

## 2. Partition Architecture

The benchmark is partitioned into two strictly separated sets:

| Partition File | Record Count | Total Entities | Target Usage |
|:---|:---:|:---:|:---|
| `data/stress_benchmark/dev.jsonl` | **100** | 300 | Calibration, confidence threshold tuning, error diagnosis |
| `data/stress_benchmark/test.jsonl` | **100** | 300 | Final frozen zero-shot evaluation, robustness verification |
| `data/stress_benchmark/malaysian_stress_200.jsonl` | **200** | 600 | Consolidated benchmark |

---

## 3. Linguistic Stratification Matrix

Both the Dev and Test partitions maintain an identical linguistic stratification profile:

| Linguistic Category | Dev Records | Test Records | Total | Description |
|:---|:---:|:---:|:---:|:---|
| **Standard Formal Bahasa Melayu** | 25 | 25 | 50 | Formal ministerial announcements, government circulars, and official administration |
| **Malaysian English** | 25 | 25 | 50 | Corporate news, executive appointments, and regional commerce |
| **Manglish & Conversational** | 20 | 20 | 40 | Informal speech featuring Malaysian colloquial discourse particles (*lah*, *meh*, *lor*, *leh*, *one*, *kan*, *wei*) |
| **Malay-English Code-Switching** | 20 | 20 | 40 | Natural bilingual workplace communication and conversational switching |
| **Informal Messaging** | 10 | 10 | 20 | WhatsApp/SMS-style text with abbreviations (*pls*, *dat*, *fyi*, *tq*) and minimal punctuation |
| **TOTAL** | **100** | **100** | **200** | Balanced multi-genre representation |

---

## 4. Entity Provenance & Multi-Ethnic Representation

### 4.1 PERSON Entities (200 instances, 50 unique names)
- **Malay Patronymic Traditions:** Full patronymic constructs using `bin` and `binti` (e.g. *Khairul Amri bin Jamaluddin*, *Nur Farhana binti Mohamad Noor*, *Zulkifli bin Mohamad Al-Bakri*, *Nurul Izzah binti Anwar*).
- **Malaysian Chinese Traditions:** Three-character dialect-specific surnames and given names (e.g. *Tan Boon Heong*, *Chong Wei Feng*, *Lim Guan Seng*, *Wee Ka Siong*, *Loke Siew Fook*).
- **Malaysian Indian Traditions:** Classical Tamil and Malaysian Indian patronymic formats using `a/l`, `a/p`, and `s/o` (e.g. *Anand s/o Subramaniam*, *Kavitha a/p Ramasamy*, *Vimalraj a/l Murugan*, *M. Kulasegaran a/l V. Murugeson*).
- **Sabah & Sarawak Traditions:** Indigenous Dayak, Kadazan-Dusun, and Sarawakian naming conventions (e.g. *Stephen Kalong Ningkan*, *Roland Sagah Wee Inn*, *Ewon Benedick*, *Arthur Joseph Kurup*).

### 4.2 ORGANIZATION Entities (200 instances, 50 unique entities)
- **Statutory Bodies & Agencies:** Unseen federal commissions and boards (e.g. *Suruhanjaya Tenaga Malaysia*, *Lembaga Lada Malaysia*, *Perbadanan Produktiviti Malaysia*, *Agensi Antidadah Kebangsaan*, *Pihak Berkuasa Peranti Perubatan*).
- **Malaysian Corporates & GLCs:** Unseen Bursa Malaysia listed entities, SMEs, and PLTs (e.g. *Solarvest Holdings Berhad*, *Farm Fresh Berhad*, *Econframe Berhad*, *Coraza Integrated Technology Berhad*, *Vortex Logistics PLT*).
- **Local Councils & Universities:** Regional municipal councils and public universities (e.g. *Majlis Bandaraya Iskandar Puteri*, *Majlis Bandaraya Pasir Gudang*, *Universiti Malaysia Pahang Al-Sultan Abdullah*, *Universiti Malaysia Kelantan*).

### 4.3 LOCATION Entities (200 instances, 50 unique locations)
- **Secondary Towns & Districts:** Unseen Malaysian administrative centers and towns across Peninsular Malaysia, Sabah, and Sarawak (e.g. *Bagan Datuk*, *Batu Gajah*, *Tanjung Malim*, *Pontian Kechil*, *Banting*, *Tangkak*, *Mersing*, *Sitiawan*, *Kuala Kangsar*, *Raub*, *Pekan*, *Bachok*, *Keningau*, *Beaufort*, *Mukah*, *Sarikei*, *Kapit*, *Limbang*).

---

## 5. Automated Validation & Quality Sign-Off

The dataset was strictly audited and verified using `src/dataset_tools/validator.py`:
- **Syntax & Schema:** 100% compliant with standard JSONL Doccano specification.
- **Span Boundaries:** 100% exact match between character offsets `[start, end]` and substring text.
- **Token Alignment:** Validated IOB2 tagging across all 600 entity spans.
- **Zero Cross-Split Contamination:** Validated disjoint entity sets between benchmark and commercial training partitions.
