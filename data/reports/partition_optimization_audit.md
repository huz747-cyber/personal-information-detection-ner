# Critical Audit E: Grouped Dataset Partition Optimization Audit

**Audit Objective:** Optimize the document-grouped and template-isolated dataset partition algorithm in `src/dataset_tools/splitter.py` to minimize deviations from the target 70% Train / 15% Val / 15% Test distribution while strictly guaranteeing zero cross-split leakage.

---

## 1. Baseline vs Optimized Partition Comparison

### Previous Phase 2.6 Partition:
* **Train:** 590 sentences (59.0%) — *110 sentences under target (11.0% deviation)*
* **Validation:** 175 sentences (17.5%) — *25 sentences over target*
* **Test:** 235 sentences (23.5%) — *85 sentences over target (8.5% deviation)*
* *Cause:* Cluster allocation was executed by count of clusters rather than sum of sentences, causing multi-sentence synthetic templates (e.g. 10 sentences each) to overweight the Test partition.

### Optimized Phase 2.6.1 Partition:
* **Train:** **705 sentences (70.5%)** — *Deviation: +0.5% (5 sentences)*
* **Validation:** **150 sentences (15.0%)** — *Deviation: 0.0% (Exact match)*
* **Test:** **145 sentences (14.5%)** — *Deviation: -0.5% (5 sentences)*
* *Mathematical constraint:* All 115 clusters in the dataset are indivisible units of size 5, 10, or 15 sentences. Allocating indivisible discrete bins of size 5 to match continuous target proportions achieves a near-perfect partition with only $\pm 0.5\%$ residual variance.

---

## 2. Multi-Factor Stratification Balance Across Splits

| Category / Stratum | Train Split (705) | Val Split (150) | Test Split (145) | Total (1,000) |
| :--- | :---: | :---: | :---: | :---: |
| **Linguistic Strata:** | | | | |
| - Formal Malay | 170 (24.1%) | 35 (23.3%) | 35 (24.1%) | 240 |
| - Malaysian English | 170 (24.1%) | 35 (23.3%) | 35 (24.1%) | 240 |
| - Manglish (Colloquial) | 100 (14.2%) | 15 (10.0%) | 25 (17.2%) | 140 |
| - Mixed Malay-English | 100 (14.2%) | 20 (13.3%) | 20 (13.8%) | 140 |
| - Malaysian Chinese Contexts | 65 (9.2%) | 15 (10.0%) | 15 (10.3%) | 95 |
| - Malaysian Indian Contexts | 65 (9.2%) | 15 (10.0%) | 15 (10.3%) | 95 |
| - International Baseline | 35 (5.0%) | 15 (10.0%) | 0 (0.0%) | 50 |
| **Data Origin:** | | | | |
| - Independently Authored (`SRC-007`) | 340 (48.2%) | 75 (50.0%) | 70 (48.3%) | 485 |
| - Combinatorial Synthetic (`SRC-008`) | 205 (29.1%) | 45 (30.0%) | 40 (27.6%) | 290 |
| - Publicly Sourced (`SRC-001,4,5,6`) | 160 (22.7%) | 30 (20.0%) | 35 (24.1%) | 225 |
| **Named Entity Classes:** | | | | |
| - `PERSON` | 585 | 125 | 113 | 823 |
| - `LOCATION` | 585 | 124 | 121 | 830 |
| - `ORGANIZATION` | 408 | 91 | 78 | 577 |
| **Hard Negatives (0 Entities):** | **70 (9.9%)** | **15 (10.0%)** | **20 (13.8%)** | **105 (10.5%)** |

---

## 3. Strict Group Isolation & Cross-Split Contamination Audit

The upgraded splitter preserves absolute group isolation:
* **Total Document Groups:** 69 multi-sentence document clusters.
* **Total Template Groups:** 46 synthetic template clusters.
* **Total Indivisible Clusters:** 115 clusters.

### Cross-Split Leakage Checks:
1. **Sentence Text Overlap:** Checked exact and normalized lowercase strings.
   * Train $\cap$ Validation: **0 records**
   * Train $\cap$ Test: **0 records**
   * Validation $\cap$ Test: **0 records**
2. **Template ID Cross-Split Overlap:**
   * Train $\cap$ Validation: **0 templates**
   * Train $\cap$ Test: **0 templates**
   * Validation $\cap$ Test: **0 templates**
3. **Document ID Cross-Split Overlap:**
   * Train $\cap$ Validation: **0 documents**
   * Train $\cap$ Test: **0 documents**
   * Validation $\cap$ Test: **0 documents**

### Deterministic Reproducibility:
The algorithm was executed 10 consecutive times with fixed seed `42`. In all 10 runs, the generated SHA-256 hashes of `data/splits/train.jsonl`, `val.jsonl`, and `test.jsonl` were bit-for-bit identical.
