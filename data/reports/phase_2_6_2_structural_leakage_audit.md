# Phase 2.6.2 Audit B: Abstract Structural Leakage Audit & Experimental Split

**Audit Objective:** Quantify syntactic and abstract grammatical structure overlap between dataset splits, analyze the mechanisms of structural leakage, and establish an alternative experimental split with zero structural overlap.

---

## 1. Abstract Structure Representation

To evaluate syntactic leakage independent of entity substitution, every sentence is transformed into its **abstract grammatical frame**:
* Named entity spans are replaced with their category tokens: `[PERSON]`, `[LOCATION]`, `[ORGANIZATION]`.
* Reference codes and docket IDs are replaced with `[REF_ID]`.
* Currencies and numeric values are replaced with `[CURRENCY]` and `[NUM]`.
* Whitespace and punctuation are normalized.

*Example:*
* *Raw Sentence:* `"Investment partner Lee Siew Ling structured the syndicated green financing facility with Maybank Islamic Berhad in Bangsar South under tranche Series-A."`
* *Abstract Frame:* `"Investment partner [PERSON] structured the syndicated green financing facility with [ORGANIZATION] in [LOCATION] under tranche [REF_ID]."`

---

## 2. Canonical Split Structural Leakage Analysis

In the canonical partition (`data/splits/`), sentences are grouped by `document_id` and `template_id` before partitioning:

| Metric | Measured Value | Analysis / Assessment |
| :--- | :---: | :--- |
| **Unique Structures (Full Dataset)** | 303 | From 1,000 sentences (Averaging 3.3 sentences/structure) |
| **Unique Structures in Train** | 251 | From 705 sentences |
| **Unique Structures in Validation** | 78 | From 150 sentences |
| **Unique Structures in Test** | 68 | From 145 sentences |
| **Train & Validation Structure Overlap** | 41 structures | 52.6% of Val structures seen in Train |
| **Train & Test Structure Overlap** | 46 structures | 67.6% of Test structures seen in Train |
| **Validation & Test Structure Overlap** | 48 structures | 70.6% of Test structures seen in Val |
| **Structures Present in All Three Splits**| 41 structures | High-frequency legal & corporate patterns |

### Why Did Structural Overlap Occur Despite Template Grouping?
1. **Multi-Template Syntactic Parallelism:** In synthetic generation (`SRC-008`), multiple template IDs (e.g. `tpl-syn-myaen-1` through `tpl-syn-myaen-9`) implemented identical syntactic grammar with different randomized slot permutations. Grouping by `template_id` isolated individual template IDs, but allowed identical syntactic frames to land across splits.
2. **Statutory Corporate Language:** In Bursa announcements (`SRC-006`), multiple distinct disclosures utilize standard legal formulas mandated by listing rules (e.g., `"[ORGANIZATION] announced the appointment of [PERSON] as independent director in [LOCATION]."`).
3. **Common Natural Language Frames:** In independently authored sentences (`SRC-007`), standard conversational and administrative phrasing (e.g., `"Encik [PERSON] dah confirm booking venue dekat [LOCATION]..."`) was independently used across different authors.

---

## 3. Alternative Experimental Split: Pure Structure Isolation

To provide researchers with an ultra-strict generalization benchmark, an alternative experimental partition was generated under:
`data/splits/experimental_structure_isolated/`

### Grouping Method:
* All 1,000 sentences were clustered directly by **Abstract Syntactic Structure** (303 unique structural clusters).
* Knapsack bin packing was executed to partition these 303 structural clusters into 700 Train / 150 Val / 150 Test.

### Experimental Split Metrics:
| Split Partition | Sentence Count | Percentage | Unique Structures | Structural Cross-Split Leakage |
| :--- | :---: | :---: | :---: | :---: |
| **Train Split** | **700** | **70.0%** | 201 | **0 overlap with Val or Test** |
| **Validation Split** | **150** | **15.0%** | 52 | **0 overlap with Train or Test** |
| **Test Split** | **150** | **15.0%** | 50 | **0 overlap with Train or Val** |
| **TOTAL** | **1,000** | **100.0%** | **303** | **ABSOLUTE ZERO STRUCTURAL LEAKAGE** |

---

## 4. Benchmark Recommendations

* **Canonical Split (`data/splits/`):** Best suited for standard evaluation where entity generalization is tested in realistic linguistic domains that mirror real-world corporate and conversational distribution.
* **Experimental Split (`data/splits/experimental_structure_isolated/`):** Best suited for zero-shot syntactic generalization research, testing whether a transformer model can extract Malaysian entities when presented with completely novel, previously unseen sentence frames.
