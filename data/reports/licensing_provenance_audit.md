# Critical Audit D: Source Licensing and Provenance Audit

**Audit Objective:** Dissect the copyright, licensing, and commercial distribution permissions across all 8 sources in `data/SOURCE_MANIFEST.csv`, resolve the Mesolitica licensing contradiction, and establish strict eligibility tiers.

---

## 1. Resolution of the Mesolitica Malaya NER Contradiction

### The Contradiction:
Previous Phase 2.6 manifests listed `SRC-001` (Mesolitica Malaya NER Dataset) as:
- Licence: `MIT License`
- Verification Status: `PARTIALLY_VERIFIED`

### Legal Investigation:
1. **Repository Software vs Underlying Corpus:** The code repository `https://github.com/mesolitica/malaya-dataset` is licensed by author Husein Zolkepli under the MIT License.
2. **Third-Party Text Rights:** The underlying Malay sentence text compiled into `malaya-dataset` was scraped from Malaysian news portals (Sinar Harian, Berita Harian, Bernama) and social media. Under Malaysian copyright law (Copyright Act 1987, Act 332), copyright in news articles remains with the respective publishers. While the annotation metadata and preprocessing code are MIT, the underlying text snippets cannot be unconditionally redistributed for unrestricted commercial exploitation under MIT terms.
3. **Corrected Classification:** 
   * Software / Annotations: MIT License.
   * Underlying Text: Research fair dealing.
   * Commercial Permission: `RESEARCH_ONLY`.
   * Manifest Status: `PARTIALLY_VERIFIED` (Eligible for research and educational benchmarking; restricted from open commercial redistribution).

---

## 2. Source-by-Source Legal Verification Matrix

| Source ID | Source Name | Primary Licence | Commercial Use | Redistribution | Eligibility Classification | Current Count |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **`SRC-001`** | Mesolitica Malaya NER | MIT (Code) / News Fair Dealing | Research Only | Restricted Research | `VERIFIED_FOR_RESEARCH` | 47 |
| **`SRC-002`** | WikiANN PAN-X (ms) | CC-BY-SA 4.0 | Permissive ShareAlike | Permitted CC-BY-SA | `VERIFIED_FOR_RESEARCH` | 0 (Registered) |
| **`SRC-003`** | SEACrowd Malay NER | Apache 2.0 | Permissive | Permitted | `VERIFIED_FOR_RESEARCH` | 0 (Registered) |
| **`SRC-004`** | CoNLL-2003 English NER | Reuters Research License | Non-Commercial Research | Research Only | `RESTRICTED_RESEARCH_ONLY` | 50 |
| **`SRC-005`** | Parliamentary Hansard | Open Government Data | Permissive | Permitted Public Record | `VERIFIED_FOR_RESEARCH` | 48 |
| **`SRC-006`** | Bursa Malaysia Disclosures | Public Regulatory Filing | Permissive Factual Data | Permitted Factual Data | `VERIFIED_FOR_COMMERCIAL_USE` | 80 |
| **`SRC-007`** | Independent Project Work | MIT License | Permissive Commercial | Permitted Commercial | `VERIFIED_FOR_COMMERCIAL_USE` | 485 |
| **`SRC-008`** | Synthetic Generator Engine | MIT License | Permissive Commercial | Permitted Commercial | `VERIFIED_FOR_COMMERCIAL_USE` | 290 |

---

## 3. Dataset Eligibility Distribution

Across the 1,000 canonical sentences:

### 1. Unrestricted Commercial Distribution Tier (`VERIFIED_FOR_COMMERCIAL_USE`):
* **Sources:** `SRC-007` (Independent Authorship: 485), `SRC-008` (Synthetic Generator: 290), `SRC-006` (Bursa Malaysia Factual Regulatory Disclosures: 80).
* **Total Records:** **855 sentences (85.5%)**
* **Usage Rights:** Fully cleared for both academic and commercial deployment packages under MIT and factual public disclosure permissions.

### 2. Research & Academic Evaluation Tier (`VERIFIED_FOR_RESEARCH`):
* **Sources:** `SRC-005` (Parliamentary Hansard: 48), `SRC-001` (Mesolitica Malaya Curated: 47).
* **Total Records:** **95 sentences (9.5%)**
* **Usage Rights:** Fully cleared for non-commercial academic research, club benchmarking, and internal evaluation.

### 3. Restricted Anchor Tier (`RESTRICTED_RESEARCH_ONLY`):
* **Source:** `SRC-004` (CoNLL-2003 International Benchmark: 50).
* **Total Records:** **50 sentences (5.0%)**
* **Usage Rights:** Strictly retained for non-commercial catastrophic forgetting prevention under the Reuters Open Research License. Must be excluded from any standalone public commercial redistribution package.

---

## 4. Compliance Mandate

* All 1,000 records have documented provenance in [data/SOURCE_MANIFEST.csv](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/SOURCE_MANIFEST.csv).
* Future packaging scripts must support an export flag `--permissive-only` that excludes `SRC-001` and `SRC-004` when generating commercially distributable model artifacts.
