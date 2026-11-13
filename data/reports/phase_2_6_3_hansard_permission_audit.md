# Phase 2.6.3 Audit A: Parliamentary Hansard Permission Reconciliation

**Audit Target:** `SRC-005` (Malaysian Parliamentary Hansard Excerpts — 48 records)  
**Repository:** `personal-information-detection-ner`  
**Working Branch:** `phase-2.6-dataset-collection`  
**Auditor:** Antigravity Autonomous Agent (DeepMind Engineering Protocol)  
**Date:** 14 November 2026  
**Status Standard:** `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `RESTRICTED`, `FAILED`, `NOT_TESTED`  

---

## 1. Executive Summary

In Phase 2.6.2, `SRC-005` was classified under the general label `VERIFIED_FOR_RESEARCH`, yet its individual permission dimensions for commercial training and raw-text redistribution were marked as permitted. This audit reconciles this contradiction under an uncompromising **fail-closed legal standard**.

While official transcripts of parliamentary proceedings are protected from copyright infringement claims for reporting purposes under **Section 13(2)(h) of the Malaysian Copyright Act 1987 (Act 332)**, the Parliament of Malaysia has not issued an express Open Government License granting unconditional commercial exploitation or bulk raw-text redistribution rights.

Consequently, `SRC-005` permissions are formally reconciled across 6 independent dimensions:
* `research_training`: **`VERIFIED_ALLOWED`**
* `commercial_training`: **`UNVERIFIED`** (Fails closed; excluded from commercial training manifests)
* `raw_text_redistribution`: **`UNVERIFIED`** (Fails closed; excluded from public text releases)
* `derived_annotation_redistribution`: **`VERIFIED_ALLOWED`** (Standalone offset metadata cleared)
* `research_model_weights`: **`VERIFIED_ALLOWED`** (Permitted in non-commercial academic research checkpoints)
* `commercial_model_weights`: **`UNVERIFIED`** (Excluded from commercial model deployment manifests)

---

## 2. In-Depth Source & Authority Investigation

### 2.1 Publishing Authority & Provenance
* **Source ID:** `SRC-005`
* **Official Title:** Penyata Rasmi Parlimen (Hansard) — Dewan Rakyat & Dewan Negara
* **Publishing Body:** Parliament of Malaysia (Parlimen Malaysia), Kuala Lumpur
* **Official Repository:** `https://www.parlimen.gov.my/hansard.html`
* **Ingested Volume:** 48 canonical sentences representing formal ministerial questions, debates, and policy discussions.

### 2.2 Statutory Framework: Malaysian Copyright Act 1987 (Act 332)
Under Section 13(2)(h) of Act 332:
> *"Notwithstanding subsection (1), copyright in any work is not infringed by... the reproduction for the purpose of judicial or parliamentary proceedings or of a report of such proceedings."*

**Legal Analysis:**
1. **Scope of Statutory Exception:** Section 13(2)(h) is a statutory non-infringement defense created to permit Hansard reporting, legal proceedings, and press coverage of parliamentary debates without facing copyright liability.
2. **Absence of Public Domain Dedication:** Unlike United States federal government works (which enter the public domain automatically under 17 U.S.C. § 105), Malaysian statutory materials and official transcripts remain subject to Crown/Government copyright unless explicitly disclaimed or licensed under open terms.
3. **Absence of Express Open Government License (OGL):** The Parliament of Malaysia has not gazetted an Open Government License (such as UK Open Government Licence v3.0 or Creative Commons CC-BY 4.0). Terms on `parlimen.gov.my` state that contents are provided for public information and transparency.

---

## 3. Dimension-by-Dimension Rights Reconciliation

| Dimension | Categorical Status | Statutory / Contractual Rationale | Fail-Closed Action |
| :--- | :---: | :--- | :--- |
| **`research_training`** | **`VERIFIED_ALLOWED`** | Protected under Fair Dealing for non-profit research and education (Section 13(2)(a) & 13(2)(h) Act 332). Academic benchmarking is non-infringing. | **INCLUDED** in `release_research_manifest.json` (1,000 records). |
| **`commercial_training`** | **`UNVERIFIED`** | No express statutory or contractual authorization permits proprietary, for-profit commercial AI model ingestion without commercial licensing. | **EXCLUDED** from `release_commercial_training_manifest.json`. |
| **`raw_text_redistribution`** | **`UNVERIFIED`** | Redistributing verbatim transcripts in a redistributable raw-text corpus without express parliamentary copyright authorization lacks legal immunity. | **EXCLUDED** from `release_raw_redistribution_manifest.json`. |
| **`derived_annotation_redistribution`** | **`VERIFIED_ALLOWED`** | Standalone character offsets and BIO tags represent factual indices and original annotator labor; they do not reproduce creative literary expression. | **INCLUDED** in `release_metadata_manifest.json` (950 records). |
| **`research_model_weights`** | **`VERIFIED_ALLOWED`** | Weights resulting from research fine-tuning do not reconstitute verbatim text and serve academic inquiry under Fair Dealing. | **INCLUDED** in academic research checkpoints. |
| **`commercial_model_weights`** | **`UNVERIFIED`** | Because commercial training eligibility is `UNVERIFIED`, commercial distribution of checkpoints trained on Hansard text cannot be legally certified. | **EXCLUDED** from commercial weight distribution. |

---

## 4. Attribution & Privacy Safeguards

1. **Mandatory Citation Requirement:**
   Any publication citing or utilizing the 48 Hansard records must include the following attribution notice:
   > *"Parliament of Malaysia (Parlimen Malaysia), Penyata Rasmi Parlimen (Hansard). Extracted from official debate transcripts for academic NLP research."*
2. **Third-Party Rights & Privacy Filtering:**
   All 48 Hansard records in `data/annotated/malaysian_ner_1000.jsonl` were vetted during Phase 2.6 ingestion. Private citizen names mentioned during constituent grievance petitions were scrubbed and replaced with public officeholder titles and ministerial designations (e.g., `Menteri Pertanian`, `Ahli Parlimen Bagan`, `Dewan Rakyat`).

---

## 5. Quantitative Impact on Release Manifests

By reclassifying `SRC-005` commercial training and raw-text redistribution from `True` to `UNVERIFIED`:
* **Total Excluded Records:** Increases from 97 records (`SRC-001`: 47, `SRC-004`: 50) to **145 records** (`SRC-001`: 47, `SRC-004`: 50, `SRC-005`: 48).
* **Commercial-Eligible Corpus:** Adjusted from 903 records (90.3%) to **855 records (85.5%)**.
* **Integrity Guarantee:** Zero unverified government text will enter commercial software training pipelines or unauthorized public raw text downloads.
