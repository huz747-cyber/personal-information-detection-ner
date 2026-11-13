# Phase 2.6.2 Audit E: Genuine Human Annotation Campaign Plan

**Campaign Objective:** Establish a rigorous, reproducible, double-blind human annotation protocol for independent evaluation of the Malaysian NER dataset, replacing simulated concordance with true human inter-annotator agreement.

---

## 1. Guiding Principles & Independence Mandate

* **No Synthetic Simulation:** Neither annotator shall be algorithmically perturbed or synthetically generated.
* **Double-Blind Separation:**
  - Annotator 1 and Annotator 2 must annotate identical raw text strings in complete isolation.
  - Neither annotator may see the other's annotations, pre-annotated labels, or canonical gold labels.
* **Standardized Schema:** Both annotators must strictly follow [data/ANNOTATION_GUIDELINES.md](file:///C:/Users/User/.gemini/antigravity/scratch/personal-information-detection-ner/data/ANNOTATION_GUIDELINES.md).

---

## 2. Stratified Sample Selection Protocol

A reproducible sample of **150 sentences (15.0% of canonical dataset)** will be extracted using a dedicated seed (`seed=101`) to prevent overlap with previous development samples:

| Linguistic Stratum | Total in Dataset | Sample Size | Proportion in Sample |
| :--- | :---: | :---: | :---: |
| **Formal Malay** | 240 | **36** | 24.0% |
| **Malaysian English** | 240 | **36** | 24.0% |
| **Manglish (Colloquial)** | 140 | **21** | 14.0% |
| **Mixed Malay-English** | 140 | **21** | 14.0% |
| **Malaysian Chinese Contexts** | 95 | **14** | 9.3% |
| **Malaysian Indian Contexts** | 95 | **14** | 9.3% |
| **International Baseline Anchor**| 50 | **8** | 5.3% |
| **TOTAL SAMPLE** | **1,000** | **150** | **100.0%** |

### Blind Sample Preparation:
Raw sentences are stripped of existing annotations and exported into unannotated JSONL:
```json
{"id": "campaign-001", "text": "Menteri Pertanian telah mengadakan pertemuan bersama Petronas di Putrajaya."}
```
Two separate projects are created in Doccano:
- Project A: Assigned to Human Annotator 1.
- Project B: Assigned to Human Annotator 2.

---

## 3. Human Annotator Onboarding & Guidelines

Each annotator undergoes a 30-minute calibration session covering:
1. **Scope Boundaries:**
   - Detect only `PERSON`, `ORGANIZATION`, `LOCATION`.
   - Structured PII (`MYKAD`, `PHONE`, `POSTCODE`) is left untagged.
2. **Patronymic Rules:**
   - Include patronymic indicators (`bin`, `binti`, `bt.`, `a/l`, `a/p`, `s/o`, `d/o`) as part of the full `PERSON` span.
   - Example: `[Ahmad Faiz bin Zulkifli]` (one span, not two).
3. **Honorific & Title Handling:**
   - Exclude political, royal, and professional titles (`Datuk Seri`, `Tan Sri`, `Dr.`, `Prof.`) from the entity span unless indivisible from the legal name.
4. **Institutional Polysemy Resolution:**
   - Healthcare and educational bodies acting as operational, legal, or commercial agents (`Hospital Kuala Lumpur`, `Universiti Malaya`) are tagged as `ORGANIZATION`. When serving purely as physical geographic points, tagged as `LOCATION`.
5. **Corporate Suffixes:**
   - Include `Berhad`, `Bhd`, `Sdn Bhd`, `Plc` within the `ORGANIZATION` span.

---

## 4. Evaluation Metrics & Agreement Calculator

Once both human annotators complete labeling, their exported JSONL files are ingested by `src/dataset_tools/agreement.py` to compute:

1. **Exact Span Metrics:**
   - Strict matching: Character `start`, `end`, and `label` must match exactly.
   - Outputs: Exact Span Precision, Recall, and $F_1$-Score.
2. **Per-Class Agreement:**
   - Span $F_1$ evaluated independently for `PERSON`, `ORGANIZATION`, and `LOCATION`.
3. **Token-Level Cohen's Kappa ($\kappa$):**
   - Word and symbol tokens aligned using `tokenize_with_offsets()`.
   - Chance-adjusted Cohen's Kappa computed across aligned sequences.
4. **Disagreement Isolation:**
   - Boundary Disagreements: Same label, conflicting character offsets.
   - Classification Disagreements: Overlapping character offsets, conflicting labels.
   - Missing Spans: Entities identified by one annotator but missed by the other.

---

## 5. Formal Adjudication Workflow

Disagreements are reviewed by a third-party Senior Lead Annotator:
* Each logged conflict is recorded with:
  - Sentence text and ID.
  - Annotator 1 span vs Annotator 2 span.
  - Final Adjudicated Label / Offsets.
  - Explicit rationale citing `ANNOTATION_GUIDELINES.md`.
* The resulting adjudicated dataset is stored as the definitive gold reference subset.
* Agreement scores are reported strictly on the pre-adjudication blind annotations to preserve scientific validity.
