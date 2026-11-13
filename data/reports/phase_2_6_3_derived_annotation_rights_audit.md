# Phase 2.6.3 Audit B: Derived Annotation Rights & Multi-Profile Licensing Audit

**Repository:** `personal-information-detection-ner`  
**Working Branch:** `phase-2.6-dataset-collection`  
**Auditor:** Antigravity Autonomous Agent (DeepMind Engineering Protocol)  
**Date:** 14 November 2026  
**Status Standard:** `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `RESTRICTED`, `FAILED`, `NOT_TESTED`  

---

## 1. Executive Summary

In Phase 2.6.2, it was asserted that *"all 1,000 derived annotations can be redistributed under the MIT License."* This audit decomposes this claim across established intellectual property doctrine regarding derivative works, factual compilations, and underlying text rights.

Under copyright law, **a downstream annotator's license (e.g., MIT) cannot extinguish or expand the rights of underlying third-party text**. When annotation metadata is inextricably bound to copyrighted source text, the resulting composite asset inherits the restrictions of the underlying text.

To ensure strict legal compliance and intellectual property hygiene, derived annotation rights are formally divided into **four independent release profiles**:

1. **Profile 1 (Software Code):** **`VERIFIED_ALLOWED`** under MIT License.
2. **Profile 2 (Annotation Schema & Guidelines):** **`VERIFIED_ALLOWED`** under CC BY 4.0 / MIT.
3. **Profile 3 (Standalone Annotation Metadata without Text):** **`VERIFIED_ALLOWED`** under MIT (950 records cleared; 50 excluded under Reuters fail-closed safeguards).
4. **Profile 4 (Complete Composite Annotated Dataset):** **`SCOPED / HYBRID`** (855 records cleared under MIT; 145 records restricted to research-only distribution).

---

## 2. Legal Analysis of Derivative Annotations

### 2.1 The Derivative Work Principle
A composite annotated record consists of two separable elements:
1. **The Underlying Expression:** The verbatim sentence text string created by the original author or publisher.
2. **The Annotation Metadata:** The character offsets `[start, end]`, categorical entity tags (`PERSON`, `ORGANIZATION`, `LOCATION`), token BIO boundaries, and synthetic attributes.

Under Section 8(1) of the Malaysian Copyright Act 1987 and international copyright conventions (Berne Convention Art. 2(3)):
> *"Derivative works... shall be protected as original works without prejudice to the copyright in any pre-existing work utilized for such purpose."*

The phrase **"without prejudice to the copyright in any pre-existing work"** establishes that adding original annotations to a copyrighted sentence does not grant the annotator the legal authority to relicense the underlying sentence under MIT. Doing so would constitute copyright infringement of the original author's exclusive distribution rights.

### 2.2 Factual Offsets vs. Literary Expression
Standalone annotation metadata (character start, character end, entity label) contains **zero creative literary expression** from the underlying text. An offset tuple such as `[21, 50, "ORGANIZATION"]` is a factual numerical indexing coordinate. In accordance with the merger doctrine and the idea-expression dichotomy, factual coordinates alone do not infringe underlying literary copyright.

---

## 3. The Four Release Profiles

```
+-----------------------------------------------------------------------------------+
|                           PROJECT INTELLECTUAL PROPERTY                           |
+-----------------------------------------------------------------------------------+
           |                                                      |
           v                                                      v
  [STANDALONE ASSETS]                                   [DATASET ASSETS]
  - Profile 1: Tools & Code (MIT)                       - Profile 3: Standalone Metadata
  - Profile 2: Guidelines & Schema (CC BY 4.0)            (Offsets & Labels ONLY - MIT)
                                                        - Profile 4: Composite Records
                                                          (Text + Labels - Scoped)
```

### Profile 1: Ingestion & Quality Tooling (Software Code)
* **Assets:** All Python scripts under `src/dataset_tools/` (`doccano_adapter.py`, `validator.py`, `splitter.py`, `release_checker.py`, `privacy_screener.py`, `agreement.py`).
* **Authorship:** 100% original source code authored by project contributors.
* **Licensing:** **MIT License**.
* **Release Eligibility:** **`VERIFIED_ALLOWED`**. Freely redistributable, modifiable, and commercially reusable without restriction.

### Profile 2: Annotation Schema & Guidelines (Conceptual Framework)
* **Assets:** `data/ANNOTATION_GUIDELINES.md`, BIO tagging definitions, Malaysian patronymic guidelines, multi-ethnic entity taxonomy.
* **Authorship:** Project contributors.
* **Licensing:** **Creative Commons Attribution 4.0 International (CC BY 4.0)** and/or **MIT License**.
* **Release Eligibility:** **`VERIFIED_ALLOWED`**. May be referenced, cited, and extended by external academic or commercial research teams with standard attribution.

### Profile 3: Standalone Annotation Metadata (Without Source Text)
* **Assets:** `data/manifests/release_metadata_manifest.json`.
* **Asset Contents:** Sentence IDs, character offsets `[start, end]`, entity classification labels, character counts, token lengths, and document IDs. **Zero underlying sentence strings are included.**
* **Licensing:** **MIT License** / **CC0 Public Domain Dedication**.
* **Release Eligibility:**
  * `SRC-001` (Mesolitica): **`VERIFIED_ALLOWED`** (47 records — offsets do not reproduce news text).
  * `SRC-004` (CoNLL-2003 Reuters): **`VERIFIED_RESTRICTED`** (50 records — excluded under fail-closed standard due to strict Reuters Open Research License derivative provisions).
  * `SRC-005` (Hansard): **`VERIFIED_ALLOWED`** (48 records — metadata indexes factual debate records).
  * `SRC-006` (Bursa Malaysia): **`VERIFIED_ALLOWED`** (80 records).
  * `SRC-007` (Independent): **`VERIFIED_ALLOWED`** (485 records).
  * `SRC-008` (Synthetic): **`VERIFIED_ALLOWED`** (290 records).
* **Summary Count:** **950 records cleared**; 50 excluded under strict Reuters fail-closed safeguards.

### Profile 4: Complete Composite Annotated Dataset (Text + Annotations)
* **Assets:** `data/annotated/malaysian_ner_1000.jsonl` and split files under `data/splits/`.
* **Legal Status:** Composite derivative works governed by the underlying text rights.
* **Release Scopes:**
  * **Research Release (`release_research_manifest.json`):** **1,000 records (100.0%)**. Cleared for academic and research evaluation under Fair Dealing (Act 332 s. 13(2)(a)), non-profit educational exceptions, and the Reuters Research License.
  * **Commercial & Public Raw Redistribution (`release_commercial_training_manifest.json`):** **855 records (85.5%)**. Exclusively contains `SRC-006` (80), `SRC-007` (485), and `SRC-008` (290). Released under MIT / CC0 / Permissive Regulatory Filings.
  * **Excluded from Public Raw Redistribution:** **145 records (14.5%)** (`SRC-001`: 47, `SRC-004`: 50, `SRC-005`: 48).

---

## 4. Multi-Profile Release Matrix

| Asset Component | Profile ID | Permitted License | Release Scope | Cleared Count | Ineligible / Restricted Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Python Tooling Code** | Profile 1 | MIT License | Universal Public | 100% of code | 0 |
| **Annotation Guidelines** | Profile 2 | CC BY 4.0 / MIT | Universal Public | 100% of schema | 0 |
| **Standalone Offset Metadata** | Profile 3 | MIT License | Universal Public | **950 records** | **50 records** (`SRC-004`) |
| **Commercial Composite Dataset** | Profile 4 | MIT / CC0 / Public | Commercial & Open | **855 records** | **145 records** (`SRC-001`, `004`, `005`) |
| **Research Composite Dataset** | Profile 4 | Research Fair Dealing | Academic Research | **1,000 records** | 0 |

---

## 5. Audit Conclusion

The assertion in Phase 2.6.2 that *"all 1,000 derived annotations can be redistributed under MIT"* is **PARTIALLY_VERIFIED**:
* It is **VERIFIED** for Profile 1 (Code), Profile 2 (Schema), and Profile 3 (Standalone metadata for 950 records).
* It is **RESTRICTED** for Profile 4 (Composite dataset), where only the **855-record commercial subset** may be redistributed under MIT, while 145 records remain restricted to research use.
