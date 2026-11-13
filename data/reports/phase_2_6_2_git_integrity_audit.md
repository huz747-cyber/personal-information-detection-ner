# Phase 2.6.2 Audit D: Complete Git Integrity & Protection Verification

**Audit Objective:** Perform an exhaustive Git diff and integrity comparison between baseline commit `b1c3705` and latest audit commit `f8676f9`, proving that protected models, weights, recognizers, gazetteers, and benchmarks remain untouched.

---

## 1. Commit Baseline & Scope

* **Baseline Commit (Phase 2.6 Completion):** `b1c3705`
* **Audit Commit (Phase 2.6.1 QA):** `f8676f9`
* **Target Protected Scope:**
  - Active transformer model code and configurations (`src/extractor.py`, `src/entity_extractor.py`)
  - Phase 2 hybrid recognizers (`src/recognizers/`)
  - Malaysian gazetteers and acronym sets (`src/recognizers/org_gazetteer.py`, `location_recognizer.py`, `title_recognizer.py`)
  - Structured PII pattern recognizers (`mykad_recognizer.py`, `phone_recognizer.py`)
  - Conflict resolution engine (`conflict_resolver.py`)
  - Core benchmark evaluation tests (`tests/test_extractor.py`, `tests/test_hybrid_recognizers.py`, `tests/test_malaysian_entities.py`)

---

## 2. Protected Files Diff Verification

Command executed:
```powershell
git diff b1c3705 f8676f9 -- src/extractor.py src/entity_extractor.py src/recognizers/ tests/test_extractor.py tests/test_hybrid_recognizers.py tests/test_malaysian_entities.py
```

* **Output:** `(EMPTY)`
* **Lines Added to Protected Files:** **0**
* **Lines Deleted from Protected Files:** **0**
* **Lines Modified in Protected Files:** **0**
* **Status:** **PASS [100% UNTOUCHED]**

---

## 3. Complete Changed Files Inventory (b1c3705 $\rightarrow$ f8676f9)

| Git Status | File Path | Category | Purpose of Modification |
| :---: | :--- | :--- | :--- |
| **`M`** | `src/dataset_tools/doccano_adapter.py` | Dataset Tool | Fixed `text_to_bio()` B-tag assignment on punctuation |
| **`M`** | `src/dataset_tools/splitter.py` | Dataset Tool | Sentence-weighted knapsack partition optimization |
| **`M`** | `src/dataset_tools/provenance.py` | Dataset Tool | Added `eligibility_classification` loading |
| **`M`** | `tests/test_phase26_tools.py` | Test Suite | Added entity invariant & doccano roundtrip unit tests |
| **`M`** | `data/SOURCE_MANIFEST.csv` | Metadata | Clarified Mesolitica news copyright & added eligibility |
| **`M`** | `data/splits/train.jsonl` | Partitions | Re-partitioned to 705 sentences (70.5%) |
| **`M`** | `data/splits/val.jsonl` | Partitions | Re-partitioned to 150 sentences (15.0%) |
| **`M`** | `data/splits/test.jsonl` | Partitions | Re-partitioned to 145 sentences (14.5%) |
| **`M`** | `data/reports/validation_report.json` | Report | Updated validation report with reconciled 577 B-ORGs |
| **`M`** | `data/reports/validation_report.md` | Report | Markdown validation summary |
| **`M`** | `data/reports/provenance_licensing_report.json` | Report | Machine-readable provenance data |
| **`A`** | `data/reports/PHASE_2_6_1_FINAL_AUDIT.md` | Audit Report | Phase 2.6.1 Master Final Audit Report |
| **`A`** | `data/reports/entity_count_reconciliation.md` | Audit Report | Critical Audit A Report |
| **`A`** | `data/reports/annotation_agreement_audit.md` | Audit Report | Critical Audit B Report |
| **`A`** | `data/reports/synthetic_diversity_audit.md` | Audit Report | Critical Audit C Report |
| **`A`** | `data/reports/licensing_provenance_audit.md` | Audit Report | Critical Audit D Report |
| **`A`** | `data/reports/partition_optimization_audit.md` | Audit Report | Critical Audit E Report |
| **`A`** | `data/reports/hard_negative_audit.md` | Audit Report | Critical Audit F Report |
| **`A`** | `data/reports/privacy_audit.md` | Audit Report | Critical Audit G Report |
| **`A`** | `data/reports/doccano_compatibility_audit.md` | Audit Report | Critical Audit H Report |

---

## 4. Binary & Large File Audit

* Checked repository for `.bin`, `.pt`, `.onnx`, `.h5`, or `.safetensors` files:
  * **Result:** **0 binary model files added or tracked in Git**.
* Working tree cleanly preserves standard repository footprint.
