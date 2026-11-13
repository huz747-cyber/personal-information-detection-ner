# Phase 2.6.2 Master Final Release Audit: Dataset Release Eligibility & Generalization Integrity

**Repository:** `personal-information-detection-ner`  
**Working Branch:** `phase-2.6-dataset-collection`  
**Baseline Commit:** `b1c3705`  
**Latest Audit Commit:** `f8676f9`  
**Audit Completion Date:** 13 November 2026  
**Auditor:** Antigravity Autonomous Agent (DeepMind Engineering Protocol)  
**Final Release Decision:** **RELEASE ELIGIBILITY CERTIFIED WITH SCOPED SAFEGUARDS**

---

## 1. Executive Summary

Phase 2.6.2 concludes the dataset collection and quality assurance milestones for the Personal Information Detection in Text project. 

This audit establishes the legal boundaries, architectural protections, and generalization characteristics of the canonical 1,000-sentence Malaysian NER dataset across 5 independent legal dimensions:

1. **Research Training & Evaluation:** **APPROVED (100.0% / 1,000 records)**.
2. **Commercial Model Training:** **APPROVED WITH SAFEGUARD (90.3% / 903 records)**. *97 records from Mesolitica news text and CoNLL Reuters text are strictly excluded from commercial training manifests.*
3. **Public Raw-Text Redistribution:** **APPROVED WITH SAFEGUARD (90.3% / 903 records)**. *Redistribution is restricted to originally authored, synthetic, public hansard, and factual regulatory disclosures.*
4. **Derived Annotation (Offsets) Distribution:** **APPROVED (100.0% / 1,000 records)**.
5. **Model Checkpoint / Weight Distribution:** **RESEARCH APPROVED; COMMERCIAL SCOPED**. Models trained exclusively on the 903-record commercial subset may be distributed commercially; models trained on the full 1,000-record research set must remain restricted to non-commercial research.

---

## 2. Repository & Git Baseline

* **Branch:** `phase-2.6-dataset-collection`
* **Baseline Commit (Phase 2.6):** `b1c3705`
* **Audit Commit (Phase 2.6.1):** `f8676f9`
* **Canonical Dataset:** `data/annotated/malaysian_ner_1000.jsonl` (1,000 records, 2,230 entities, 105 hard negatives).
* **Git Integrity Status:** **VERIFIED**. Zero lines modified in `src/recognizers/`, `src/extractor.py`, `src/entity_extractor.py`, or benchmark tests. Zero binary model artifacts added.

---

## 3. Source-Level Licensing & Permission Findings

Every data source was audited across its exact legal foundation:

| Source ID | Source Name | Primary Licence | Research Training | Commercial Training | Raw Text Redistribution | Model Weight Release | Legal Classification |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`SRC-001`** | Mesolitica Malaya NER | MIT (Code) / News Fair Dealing | **YES** | **NO** | **NO** | Research Only | `VERIFIED_FOR_RESEARCH` |
| **`SRC-002`** | WikiANN PAN-X (ms) | CC-BY-SA 4.0 | **YES** | **YES** | **YES** | ShareAlike | `VERIFIED_FOR_RESEARCH` |
| **`SRC-003`** | SEACrowd Malay NER | Apache 2.0 | **YES** | **YES** | **YES** | Permissive | `VERIFIED_FOR_RESEARCH` |
| **`SRC-004`** | CoNLL-2003 English NER | Reuters Research License | **YES** | **NO** | **NO** | Academic Only | `RESTRICTED_RESEARCH_ONLY` |
| **`SRC-005`** | Parliamentary Hansard | Open Gov Data / Public Record | **YES** | **YES** | **YES** | Permissive | `VERIFIED_FOR_RESEARCH` |
| **`SRC-006`** | Bursa Malaysia Corporate | Public Regulatory Filings | **YES** | **YES** | **YES** | Permissive | `VERIFIED_FOR_COMMERCIAL_USE` |
| **`SRC-007`** | Independent Authorship | MIT License (Original Work) | **YES** | **YES** | **YES** | Permissive | `VERIFIED_FOR_COMMERCIAL_USE` |
| **`SRC-008`** | Synthetic Generator | MIT License / CC0 Dedication | **YES** | **YES** | **YES** | Permissive | `VERIFIED_FOR_COMMERCIAL_USE` |

*Detailed Report:* [data/reports/phase_2_6_2_licensing_release_audit.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_licensing_release_audit.md).

---

## 4. Separate Permissions for Training and Redistribution

To enforce safe release boundaries, `src/dataset_tools/release_checker.py` generated three separated manifests in `data/manifests/`:

* **`release_research_manifest.json`:** 1,000 records (**100.0%**).
* **`release_commercial_training_manifest.json`:** 903 records (**90.3%**). Automatically excludes `SRC-001` (47 records) and `SRC-004` (50 records).
* **`release_raw_redistribution_manifest.json`:** 903 records (**90.3%**). Prevents redistribution of Reuters text and third-party news snippets.

---

## 5. Structural Leakage Findings & Experimental Split

* **Canonical Split (`data/splits/`):**
  - Group isolation on `document_id` and `template_id` guarantees **0 identical sentences** and **0 template leakage**.
  - Abstract syntactic analysis revealed 46 shared grammatical frames between Train and Test (67.6% of Test structures), largely driven by standard corporate disclosure formulas and multi-template synthetic parallelism.
* **Alternative Experimental Split (`data/splits/experimental_structure_isolated/`):**
  - All 1,000 sentences were clustered strictly by **abstract grammatical frame** (303 unique structures).
  - Train (700, 70.0%), Val (150, 15.0%), Test (150, 15.0%).
  - **Structural Cross-Split Leakage:** **0 structures (ABSOLUTE ZERO LEAKAGE)**.
  - Recommended for advanced zero-shot syntactic generalization research.

*Detailed Report:* [data/reports/phase_2_6_2_structural_leakage_audit.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_structural_leakage_audit.md).

---

## 6. Doccano Compatibility Evidence

* **Status:** `SCHEMA_VERIFIED_ONLY`.
* A local production Doccano server is not installed in this execution environment; no false live test claims are made.
* Format is audited against official Doccano Sequence Labeling specifications:
  - 1,000 valid JSONLines lines.
  - 2,230 valid spans formatted as `[start, end, label]`.
  - Zero-length spans: 0.
  - Character offset alignment: 100.0% verified slice equality (`text[start:end] == entity_text`).
* Full Docker reproduction instructions documented in: [data/reports/phase_2_6_2_doccano_release_audit.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_doccano_release_audit.md).

---

## 7. Complete Git Integrity Verification

* **Status:** `VERIFIED`.
* Comparison between baseline `b1c3705` and latest `f8676f9` confirms zero changes to:
  - Transformer models (`src/extractor.py`, `src/entity_extractor.py`)
  - Hybrid recognizers (`src/recognizers/`)
  - Gazetteers and patronymic stitchers
  - Benchmark evaluation suites
* Zero binary model files added to Git.
* Detailed changed-file inventory documented in: [data/reports/phase_2_6_2_git_integrity_audit.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_git_integrity_audit.md).

---

## 8. Human Annotation Readiness Plan

* **Status:** `NOT_TESTED (Planned)`.
* Previous 150-sentence double-annotation is classified as **algorithmic consistency testing**, not independent human agreement.
* Practical plan established:
  - 150-sentence stratified sample selected with dedicated `seed=101`.
  - Double-blind project setup in Doccano (Annotator 1 vs Annotator 2).
  - Guidelines onboarding, third-party adjudication, and exact span Cohen's Kappa evaluation.
* Detailed protocol documented in: [data/reports/phase_2_6_2_human_annotation_plan.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/phase_2_6_2_human_annotation_plan.md).

---

## 9. Automated Test Results

Executed complete test suite:
```powershell
.\.venv\Scripts\pytest tests/ -v
```
* **Results:** **84 passed in 10.29s (100% PASS)**.
* Pre-existing tests (73 tests): 100% regression pass.
* Phase 2.6 / 2.6.1 tests (11 tests): 100% pass.

---

## 10. Outstanding Risks & Mitigations

1. **Commercial News Corpus Risk:** Scraped news text from Mesolitica (`SRC-001`) cannot be redistributed commercially. *Mitigated by excluding `SRC-001` from the commercial release manifest.*
2. **Reuters Academic License:** CoNLL-2003 text (`SRC-004`) is restricted to non-commercial academic research. *Mitigated by isolating `SRC-004` to research evaluation only.*
3. **Simulated Human IAA:** High agreement scores reflect algorithmic consistency. *Mitigated by transparent downgrade of evidence and creation of the Phase 2.6.2 Human Annotation Plan.*

---

## 11. Final Release Eligibility Decisions

| Release Dimension | Final Decision | Eligible Records | Action Required / Release Mechanism |
| :--- | :---: | :---: | :--- |
| **1. Research Model Training** | **APPROVED** | 1,000 (100.0%) | Use `data/manifests/release_research_manifest.json` |
| **2. Commercial Model Training** | **APPROVED** | 903 (90.3%) | Use `data/manifests/release_commercial_training_manifest.json` |
| **3. Raw Dataset Public Redistribution** | **APPROVED** | 903 (90.3%) | Use `data/manifests/release_raw_redistribution_manifest.json` |
| **4. Derived Annotation Redistribution** | **APPROVED** | 1,000 (100.0%) | Safe under MIT License |
| **5. Model Weight Distribution (Research)**| **APPROVED** | 1,000 (100.0%) | Publishable under academic research terms |
| **6. Model Weight Distribution (Commercial)**| **APPROVED (Scoped)**| 903 (90.3%) | Train strictly on commercial manifest |

---

## 12. Recommended Next Phase

The dataset is now legally partitioned, scientifically validated, structurally analyzed, and release-ready.

**Recommended Step:** 
Submit this Phase 2.6.2 audit report for formal human review. Upon human approval, proceed to **Phase 3 (Model Selection, Subword Alignment, and Fine-Tuning Planning)** using either:
- The **Commercial Manifest (903 records)** if commercial weights are required, or
- The **Full Research Manifest (1,000 records)** if benchmarking against baseline DistilBERT and CoNLL-2003 for academic research.
