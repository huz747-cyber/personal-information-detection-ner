# Critical Audit F: Hard-Negative Validation & Distractor Audit

**Audit Objective:** Independently verify that every hard-negative sentence contains zero target entities, contains valid non-entity distractors, and does not accidentally contain unannotated real Malaysian entities.

---

## 1. Audit Summary

* **Total Hard-Negative Sentences:** 105 sentences (10.5% of canonical dataset).
* **Target Entity Count:** **0 entities** across all 105 sentences. (Every record has `entities: []` and `label: []`).
* **Unannotated Entity Intrusion Scan:** Cross-referenced all 105 texts against comprehensive gazetteers:
  - 16 Malaysian States & Federal Territories
  - 50+ Major Cities and Districts
  - 40+ Statutory Bodies and Agencies (`MALAYSIAN_ORG_NAMES`)
  - 25+ Corporate and Bank Acronyms (`MALAYSIAN_ORG_ACRONYMS`)
  * **Result:** **0 accidental gazetteer entity matches**.

---

## 2. Distractor Category Coverage

Hard-negative examples are designed to challenge future models and prevent over-triggering on capitalization, currency symbols, and local vocabulary:

| Distractor Category | Description & Patterns | Count in Hard Negatives | Representation |
| :--- | :--- | :---: | :---: |
| **Malaysian Currency** | Explicit `RM`, `MYR`, `$` amounts (e.g. `RM 50000`, `MYR 250,000.00`, `RM 1200`) | 20 | 19.0% |
| **Dates & Calendar** | Formal day/month terms (`15 Disember 2024`, `12 Mei 2025`, `Jumaat`, `Isnin`) | 9 | 8.6% |
| **Transaction / Invoice IDs** | Administrative reference codes (`TXN950315105231`, `PV-88190`, `POL-99210`, `ACT-302`) | 9 | 8.6% |
| **Generic Facilities & Infrastructure**| Common nouns for buildings (`dewan serbaguna`, `kaunter`, `pejabat`, `terminal`, `makmal`) | 13 | 12.4% |
| **Food & Cultural Vocabulary** | Local foods and cultural items (`nasi lemak`, `roti canai`, `teh tarik`, `baju kurung`) | 3 | 2.9% |
| **Colloquial Discourse / Manglish** | Informal discourse particles and slang (`jom lunch`, `confirm settle`, `lah`, `boss`) | 5 | 4.8% |
| **Standard Administrative Prose** | Generic regulatory sentences with ordinary capitalized legal/policy terms | 46 | 43.8% |
| **TOTAL HARD NEGATIVES** | **Zero PERSON, ORGANIZATION, or LOCATION entities** | **105** | **100.0%** |

---

## 3. Representative Verified Hard-Negative Examples

1. **Financial & Currency Distractor:**
   * *Text:* `"Jumlah peruntukan modal yang diluluskan adalah sebanyak MYR 250,000.00 untuk suku pertama tahun ini."`
   * *ID:* `my-malay-229`
   * *Challenge:* Contains uppercase currency identifier `MYR` and high-value numbers; model must not tag as `ORGANIZATION`.
2. **Transaction Identifier Distractor:**
   * *Text:* `"Nombor rujukan transaksi rasmi bagi pembayaran cukai tanah ini ialah TXN950315105231."`
   * *ID:* `my-malay-226`
   * *Challenge:* Alphanumeric transaction code resembles a serial/MyKad string; model must not tag as `PERSON`.
3. **Generic Facility Distractor:**
   * *Text:* `"Borang tempahan sewaan dewan serbaguna boleh dimuat turun daripada portal rasmi jabatan."`
   * *ID:* `my-malay-231`
   * *Challenge:* Contains generic municipal facility noun `dewan serbaguna` and `jabatan`; model must not tag as `LOCATION` or `ORGANIZATION`.
4. **Colloquial Manglish Distractor:**
   * *Text:* `"Better double check the delivery manifest so everything will settle properly without delay."`
   * *ID:* `my-mang-128`
   * *Challenge:* Informal workplace phrasing with zero entities.

---

## 4. Assessment

The hard-negative subset satisfies all quality criteria. It provides realistic non-entity linguistic contexts across all 7 strata, establishing a robust defense against false positives during model fine-tuning.
