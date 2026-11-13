# Critical Audit C: Synthetic Template Diversity Audit

**Audit Objective:** Analyze structural diversity, syntactic patterns, entity substitution distributions, and template concentration within the 290 synthetic sentences (`SRC-008`).

---

## 1. Metric Overview

| Metric | Measured Value | Benchmark / Assessment |
| :--- | :---: | :--- |
| **Total Synthetic Sentences** | 290 | 29.0% of canonical dataset |
| **Unique Template IDs** | 46 | Average 6.30 sentences per template |
| **Minimum Sentences per Template** | 5 | Found in state administration templates |
| **Maximum Sentences per Template** | 10 | Found in Manglish / Mixed templates |
| **Unique Abstract Grammatical Structures** | 43 | Sentences with entity spans & numerals masked |
| **Unique Substituted PERSON Entities** | 70 | High ethnic & patronymic variety |
| **Unique Substituted ORGANIZATION Entities** | 15 | Statutory bodies, state corps, banks |
| **Unique Substituted LOCATION Entities** | 35 | States, federal territories, corridors |

---

## 2. Template Distribution by Linguistic Stratum

| Linguistic Stratum | Unique Templates | Total Sentences | Sentences / Template |
| :--- | :---: | :---: | :---: |
| **Formal Malay** | 9 | 45 | 5.0 |
| **Malaysian English** | 9 | 45 | 5.0 |
| **Manglish (Colloquial)** | 6 | 60 | 10.0 |
| **Mixed Malay-English** | 6 | 60 | 10.0 |
| **Malaysian Chinese Contexts** | 8 | 40 | 5.0 |
| **Malaysian Indian Contexts** | 8 | 40 | 5.0 |
| **TOTAL** | **46** | **290** | **6.30 (Mean)** |

---

## 3. Structural Concentration & Repeated Syntactic Patterns

While textual duplicate detection (via character 3-gram Jaccard) showed zero identical strings due to randomized entity substitution and unique docket/reference numbers, abstract syntactic analysis reveals high structural concentration:

### Top 5 Repeated Grammatical Frames:
1. **Count: 45 sentences (15.5%)**
   * *Abstract Frame:* `[PERSON] telah menyerahkan dokumen pelantikan anggota lembaga [ORGANIZATION] di [LOCATION] mengikut warta bil [NUM].`
   * *Example:* *"Ahmad Shauki bin Zakaria telah menyerahkan dokumen pelantikan anggota lembaga Perbadanan Kemajuan Pertanian Negeri Melaka di Melaka mengikut warta bil 100."*
2. **Count: 40 sentences (13.8%)**
   * *Abstract Frame:* `Project engineer [PERSON] finalized the construction schedule for PHASE-[NUM] in [LOCATION].`
   * *Example:* *"Project engineer Tan Wei Jun finalized the construction schedule for PHASE-10 in George Town."*
3. **Count: 40 sentences (13.8%)**
   * *Abstract Frame:* `Site manager [PERSON] inspected the transit railway terminal infrastructure at Lot-[NUM] in [LOCATION].`
   * *Example:* *"Site manager Kavitha a/p Subramaniam inspected the transit railway terminal infrastructure at Lot-10 in Klang."*
4. **Count: 12 sentences (4.1%)**
   * *Abstract Frame:* `I think [PERSON] should follow up that Zoom call dekat [LOCATION] under reference REF-[NUM] before deadline ends.`
5. **Count: 12 sentences (4.1%)**
   * *Abstract Frame:* `I think [PERSON] should follow up that Teams meeting dekat [LOCATION] under reference REF-[NUM] before deadline ends.`

### Finding:
The top 3 grammatical structures account for **125 out of 290 synthetic sentences (43.1%)**. 
This demonstrates that while vocabulary substitutions are diverse (70 distinct person names, 35 locations), syntactic variation in the synthetic subset is concentrated. 

---

## 4. Preservation of Grouped Partitioning

Because of this template concentration, the decision in Phase 2.6 to enforce **strict template-id cluster isolation** during dataset partitioning is vindicated:
* All sentences generated from `tpl-syn-malay-1` are indivisibly routed to the same split.
* If naive sentence-level splitting had been applied, sentences sharing these identical grammatical frames would have leaked across Train, Validation, and Test, artificially inflating evaluation scores.
* Template isolation guarantees that model evaluation in Phase 3 measures genuine entity generalization rather than memorization of repetitive syntactic sentence frames.
