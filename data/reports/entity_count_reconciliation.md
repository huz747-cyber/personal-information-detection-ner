# Critical Audit A: Entity Count Reconciliation Report

**Audit Objective:** Independently investigate and reconcile the numerical discrepancy between reported named entities (2,230) and IOB2 beginning tags (previously reported as 2,241 total, with 588 `B-ORGANIZATION` vs 577 `ORGANIZATION` entities).

---

## 1. Executive Summary of Root Cause

* **The Discrepancy:** Previous Phase 2.6 reports indicated 577 `ORGANIZATION` entities but 588 `B-ORGANIZATION` tags—an inflation of exactly 11 tags.
* **The Root Cause:** The bug was traced directly to `text_to_bio()` in `src/dataset_tools/doccano_adapter.py`. 
  Line 81 previously contained:
  ```python
  if t_start >= e_start and (t_start == e_start or t_start - e_start < 2):
      assigned_tag = f"B-{label}"
  ```
  For corporate entities whose first token is a single character (such as `D` in `D&O Green Technologies Berhad`), the second token `&` begins at offset `e_start + 1`. Because `(e_start + 1) - e_start = 1 < 2` evaluated to `True`, the tokenizer assigned `B-ORGANIZATION` to **both** token `'D'` and token `'&'`.
* **The Exact 11 Affected Records:** Exactly 11 sentences in the dataset contained the corporate entity `D&O Green Technologies Berhad`:
  - `my-myaen-088` (Melaka)
  - `my-myaen-096` (Melaka)
  - `my-myaen-104` (Melaka)
  - `my-myaen-112` (Melaka)
  - `my-myaen-120` (Melaka)
  - `my-myaen-128` (Melaka)
  - `my-myaen-136` (Melaka)
  - `my-myaen-144` (Melaka)
  - `my-myaen-152` (Melaka)
  - `my-myaen-160` (Melaka)
  - `my-myaen-168` (Melaka)
  Each occurrence generated one duplicate `B-ORGANIZATION` tag ($577 + 11 = 588$).

---

## 2. Implementation Correction

The flawed heuristic was replaced with explicit entity-tracking in `src/dataset_tools/doccano_adapter.py`:
```python
first_token_seen = set()
for token, t_start, t_end in tokens_with_offsets:
    tokens.append(token)
    assigned_tag = "O"
    for ent_idx, ent in enumerate(sorted_entities):
        if max(t_start, ent["start"]) < min(t_end, ent["end"]):
            if ent_idx not in first_token_seen:
                assigned_tag = f"B-{ent['label']}"
                first_token_seen.add(ent_idx)
            else:
                assigned_tag = f"I-{ent['label']}"
            break
    bio_tags.append(assigned_tag)
```
This guarantees that **every entity span produces exactly one `B-` tag**, and all subsequent tokens within that entity span are assigned `I-` tags.

---

## 3. Reconciled Accounting Table

| Entity Class | Declared Character Spans | B-Tag Count | I-Tag Count | Status |
| :--- | :---: | :---: | :---: | :---: |
| **`PERSON`** | 823 | 823 | 1,690 | **MATCH (1:1)** |
| **`LOCATION`** | 830 | 830 | 488 | **MATCH (1:1)** |
| **`ORGANIZATION`** | 577 | 577 | 1,288 | **MATCH (1:1)** |
| **`O` (Outside Tokens)**| — | — | 16,689 | **VERIFIED** |
| **TOTAL NAMED ENTITIES** | **2,230** | **2,230** | **3,466** | **PERFECT INVARIANT MATCH** |

### Mathematical Invariant Verification:
$$\text{Total Entities} = B\text{-PERSON} + B\text{-LOCATION} + B\text{-ORGANIZATION} = 823 + 830 + 577 = 2,230$$

Every entity has:
- Valid integer `start` and `end` offsets ($0 \le \text{start} < \text{end} \le \text{len(text)}$).
- 100% text slice equality: `text[start:end] == entity_text`.
- Valid BIO transition sequence (no orphaned `I-` tags).
- Dedicated regression test: `tests/test_phase26_tools.py::test_text_to_bio_entity_invariant_and_punctuation` (**PASS**).
