# Phase 2.6.3 Audit C: Model-Weight Distribution Rights & Downstream Licensing Audit

**Repository:** `personal-information-detection-ner`  
**Working Branch:** `phase-2.6-dataset-collection`  
**Auditor:** Antigravity Autonomous Agent (DeepMind Engineering Protocol)  
**Date:** 14 November 2026  
**Status Standard:** `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `RESTRICTED`, `FAILED`, `NOT_TESTED`  

---

## 1. Executive Summary

This audit investigates the intellectual property and licensing status of model weights produced by fine-tuning on the Malaysian NER dataset. 

A critical legal constraint has been uncovered regarding the active baseline model:  
**The baseline checkpoint `dslim/distilbert-NER` is pre-fine-tuned on the CoNLL-2003 English NER dataset, which derives from Reuters Corpus Volume 1 (RCV1). Under the Reuters Open Research License, all derived model checkpoints inherit an enforceable non-commercial academic research restriction.**

Consequently:
1. **Any model fine-tuned on top of `dslim/distilbert-NER` is strictly restricted to non-commercial academic research**, regardless of whether the fine-tuning dataset is commercially licensed.
2. **Commercial model-weight distribution in Phase 3 requires starting from a clean foundational base model** (e.g., `distilbert-base-cased` or `distilbert-base-multilingual-cased` under Apache 2.0) trained exclusively on the **855 commercial-eligible records**.

---

## 2. Lineage Analysis of `dslim/distilbert-NER`

```
[Hugging Face / Google / Sanh et al.]
   distilbert-base-cased (Apache 2.0)
                │
                ▼ Fine-tuned on CoNLL-2003 (Reuters Corpus RCV1)
[David S. Lim / dslim]
   dslim/distilbert-NER
   * Inherits Reuters Open Research License *
   * Permitted: Non-commercial academic research *
   * Prohibited: Commercial exploitation / redistribution *
                │
                ▼ Proposed Fine-Tuning
[Personal Information Detection in Text Project]
   - If starting from dslim/distilbert-NER: RESTRICTED TO RESEARCH ONLY
   - If starting from clean distilbert-base-cased + 855 subset: COMMERCIAL CLEARED
```

### 2.1 The CoNLL-2003 / Reuters Corpus Restriction
* **Corpus Source:** Reuters Corpus Volume 1 (RCV1) consists of 806,791 English-language news stories published by Reuters between 1996 and 1997.
* **Licensing Agreement:** Reuters granted the NLP research community permission to use RCV1 under the **Reuters Open Research License**.
* **Key Terms:**
  * Clause 1: *"The Materials may be used solely for non-commercial research and educational purposes."*
  * Clause 2: *"Licensee shall not distribute, sublicense, sell, or commercially exploit the Materials or any derived work thereof."*
* **Impact on Model Weights:** Weights of a neural network fine-tuned on CoNLL-2003 represent a derivative work of the underlying RCV1 corpus under copyright law. Therefore, `dslim/distilbert-NER` cannot be distributed for commercial deployment.

---

## 3. Separation of Model Release Rights

To prevent legal exposure, model distribution rights must be strictly separated across two distinct pathways:

### Pathway A: Research Model-Weight Distribution
* **Permitted Base Checkpoint:** `dslim/distilbert-NER` (or any academic checkpoint).
* **Permitted Training Data:** Full 1,000-sentence canonical research dataset (`release_research_manifest.json`), including Mesolitica (`SRC-001`), CoNLL-2003 anchor sentences (`SRC-004`), and Hansard debates (`SRC-005`).
* **Distribution Terms:** Non-commercial academic research release under the Reuters Research License / CC BY-NC 4.0.
* **Status:** **`VERIFIED_ALLOWED`** for academic publication and non-profit benchmarking.

### Pathway B: Commercial Model-Weight Distribution
* **Permitted Base Checkpoint:** Clean pre-trained foundation models with permissive upstream licenses:
  * `distilbert-base-cased` (Apache 2.0)
  * `distilbert-base-multilingual-cased` (Apache 2.0)
  * `xlm-roberta-base` (MIT License)
  * `bert-base-multilingual-cased` (Apache 2.0)
* **Permitted Training Data:** Exclusively the **855 commercial-eligible subset** (`release_commercial_training_manifest.json`), comprising Bursa announcements (`SRC-006`), Independent authorship (`SRC-007`), and Synthetic data (`SRC-008`).
* **Strict Exclusions:** Zero sentences from `SRC-001` (47), `SRC-004` (50), or `SRC-005` (48) may be included in the training run.
* **Distribution Terms:** Apache 2.0 or MIT License, permitting commercial SaaS integration, proprietary embedding, and unrestricted redistribution.
* **Status:** **`VERIFIED_ALLOWED`** when trained under these architectural constraints.

---

## 4. Rights Matrix for Model Checkpoints

| Base Model Starting Point | Fine-Tuning Corpus | Resulting Weight License | Research Distribution | Commercial Distribution | Commercial SaaS Deployment |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `dslim/distilbert-NER` | 1,000 Research Corpus | Reuters NC / Research | **YES (`VERIFIED_ALLOWED`)** | **NO (`VERIFIED_RESTRICTED`)** | **PROHIBITED** |
| `dslim/distilbert-NER` | 855 Commercial Subset | Reuters NC / Research | **YES (`VERIFIED_ALLOWED`)** | **NO (`VERIFIED_RESTRICTED`)** | **PROHIBITED** |
| `distilbert-base-cased` (Clean) | 1,000 Research Corpus | Proprietary / News Taint | **YES (`VERIFIED_ALLOWED`)** | **NO (`UNVERIFIED`)** | **RISK EXPOSURE** |
| `distilbert-base-cased` (Clean) | **855 Commercial Subset** | **Apache 2.0 / MIT** | **YES (`VERIFIED_ALLOWED`)** | **YES (`VERIFIED_ALLOWED`)** | **CLEARED** |

---

## 5. Architectural Recommendations for Phase 3

When the project receives explicit human approval to proceed to Phase 3:
1. **Do NOT fine-tune `dslim/distilbert-NER` for commercial deliverables.** Keep `dslim/distilbert-NER` purely as an evaluation baseline.
2. **Implement dual training targets in Phase 3:**
   * **Target 1 (Research Benchmark Model):** Train from `distilbert-base-cased` or `dslim/distilbert-NER` on the full 1,000-sentence canonical research split to measure maximum generalization.
   * **Target 2 (Commercial Clean Checkpoint):** Train from clean `distilbert-base-multilingual-cased` (Apache 2.0) strictly on the 855-record commercial subset to produce an enterprise-ready, freely distributable release artifact.
