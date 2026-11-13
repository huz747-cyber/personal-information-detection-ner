# Phase 2.6.2 Audit A: Source Licensing and Release Eligibility Audit

**Audit Objective:** Independently evaluate legal permissions, copyright risks, commercial training rights, and redistribution parameters across all dataset sources, establishing separate release manifests.

---

## 1. Executive Summary & Legal Principles

To prevent legal exposure and copyright infringement in downstream model deployment, this audit decouples distinct permission dimensions:
1. **Research & Educational Benchmarking Use**
2. **Commercial Model Training Rights**
3. **Raw Sentence Text Redistribution**
4. **Derived Annotation (Offsets & Labels) Redistribution**
5. **Model Checkpoint / Weight Distribution**

> [!IMPORTANT]
> **Key Legal Distinctions Enforced:**
> - An open-source software license (such as MIT on a GitHub repository) **does not automatically grant copyright clearance over scraped third-party text** included in the repository.
> - Public availability on the internet does not constitute public domain dedication or commercial redistribution permission.
> - Fair Dealing under Section 13(2)(a) of the Malaysian Copyright Act 1987 permits non-commercial research and private study, but does not grant commercial redistribution or proprietary model commercialization rights.

---

## 2. Source-by-Source Investigation Matrix

| Source ID | Source Name | Primary Licence | Commercial Training | Raw Text Redistribution | Model Weight Distribution | Eligibility Classification | Sentence Count |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **`SRC-001`** | Mesolitica Malaya NER | MIT (Code) / News Fair Dealing | **NO (Unverified)** | **NO (Restricted)** | **Research Only** | `VERIFIED_FOR_RESEARCH` | 47 (4.7%) |
| **`SRC-002`** | WikiANN PAN-X (ms) | CC-BY-SA 4.0 | **YES (ShareAlike)** | **YES (CC-BY-SA)** | **YES (ShareAlike)**| `VERIFIED_FOR_RESEARCH` | 0 (Registered) |
| **`SRC-003`** | SEACrowd Malay NER | Apache 2.0 | **YES (Permissive)** | **YES (Permissive)** | **YES (Permissive)**| `VERIFIED_FOR_RESEARCH` | 0 (Registered) |
| **`SRC-004`** | CoNLL-2003 English NER | Reuters Research License | **NO (Forbidden)** | **NO (Forbidden)** | **NO (Academic Only)**| `RESTRICTED_RESEARCH_ONLY` | 50 (5.0%) |
| **`SRC-005`** | Parliamentary Hansard | Open Gov Data / Public Record | **YES (Public Record)**| **YES (Public Record)**| **YES (Permissive)**| `VERIFIED_FOR_RESEARCH` | 48 (4.8%) |
| **`SRC-006`** | Bursa Malaysia Corporate | Public Regulatory Filings | **YES (Factual Data)** | **YES (Factual Data)** | **YES (Permissive)**| `VERIFIED_FOR_COMMERCIAL_USE`| 80 (8.0%) |
| **`SRC-007`** | Independent Project Authorship | MIT License (Original Work) | **YES (Permissive)** | **YES (Permissive)** | **YES (Permissive)**| `VERIFIED_FOR_COMMERCIAL_USE`| 485 (48.5%) |
| **`SRC-008`** | Combinatorial Synthetic Engine | MIT License / CC0 Dedication | **YES (Permissive)** | **YES (Permissive)** | **YES (Permissive)**| `VERIFIED_FOR_COMMERCIAL_USE`| 290 (29.0%) |

---

## 3. Detailed Source Legal Assessments

### 1. `SRC-001`: Mesolitica Malaya NER Dataset (47 sentences)
* **Creator / Repository:** Husein Zolkepli / Mesolitica (`https://github.com/mesolitica/malaya-dataset`).
* **Copyright Nature:** Software scripts are MIT licensed; underlying news text originates from Malaysian media portals (Sinar Harian, Berita Harian, Bernama).
* **Legal Assessment:** Under Section 13(2)(a) of the Malaysian Copyright Act 1987, fair dealing covers non-profit research and private study. However, redistributing raw commercial news text or training commercial models without publisher consent is legally disputed.
* **Release Determination:** Cleared for academic research; **excluded** from commercial training and raw text redistribution packages.

### 2. `SRC-004`: CoNLL-2003 English NER Benchmark (50 sentences)
* **Creator / Repository:** Tjong Kim Sang & De Meulder (2003) / Hugging Face.
* **Underlying Data:** Reuters Corpus Volume 1 (RCV1) news stories from 1996–1997.
* **License:** Reuters Open Research License strictly forbids commercial exploitation and public raw text redistribution.
* **Release Determination:** Retained strictly as an internal academic anchor to measure catastrophic forgetting; **strictly excluded** from commercial training and raw text redistribution manifests.

### 3. `SRC-005`: Malaysian Parliamentary Hansard (48 sentences)
* **Publisher:** Parliament of Malaysia (Parlimen Malaysia).
* **Copyright Nature:** Official transcripts of parliamentary proceedings (Penyata Rasmi Parlimen).
* **Legal Assessment:** Under Section 13(2)(h) of the Malaysian Copyright Act 1987, reproduction of legislative proceedings is a non-infringing act. Factual parliamentary statements are open government public records.
* **Release Determination:** Cleared for research and public analysis.

### 4. `SRC-006`: Bursa Malaysia Corporate Disclosures (80 sentences)
* **Publisher:** Bursa Malaysia Securities Berhad & Public Listed Companies.
* **Nature:** Factual statutory filings (director appointments, registered addresses, AGM dates) mandated by the Capital Markets and Services Act 2007.
* **Legal Assessment:** Factual statutory announcements lack copyrightable expressive authorship under copyright law (*Feist Publications* doctrine). Factual data points are permissible for model training and reporting.
* **Release Determination:** Cleared for commercial training and reporting.

### 5. `SRC-007` & `SRC-008`: Independent Project Authorship & Synthetic Engine (775 sentences, 77.5%)
* **Creators:** AI/ML Club Project Contributors and Synthetic Multi-Template Engine.
* **Copyright Nature:** Original fictional and administrative sentences drafted specifically for this open-source project, and algorithmically generated combinatorial sentences.
* **License:** MIT License / CC0 dedication.
* **Release Determination:** **100% cleared** across all 5 dimensions (commercial training, redistribution, weight release).

---

## 4. Generated Release Manifests & Safeguards

The automated release checker `src/dataset_tools/release_checker.py` generated three separated release manifests in `data/manifests/`:

1. **`release_research_manifest.json`:**
   * **Total Records:** **1,000 sentences (100.0%)**
   * **Purpose:** Internal non-commercial academic research, benchmark evaluation, and catastrophic forgetting testing.
2. **`release_commercial_training_manifest.json`:**
   * **Total Records:** **903 sentences (90.3%)**
   * **Safeguard:** Automatically excludes 97 sentences (`SRC-001`: 47, `SRC-004`: 50) to guarantee zero third-party news or Reuters research-only text is included in commercial training runs.
3. **`release_raw_redistribution_manifest.json`:**
   * **Total Records:** **903 sentences (90.3%)**
   * **Safeguard:** Automatically excludes 97 sentences with redistribution restrictions, allowing safe public download releases.

Machine-readable legal profiles generated in: [data/reports/source_release_eligibility.json](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/reports/source_release_eligibility.json).
