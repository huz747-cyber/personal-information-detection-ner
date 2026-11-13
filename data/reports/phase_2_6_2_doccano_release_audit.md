# Phase 2.6.2 Audit C: Doccano Release Compatibility Audit

**Audit Objective:** Inspect the official import and export schema specifications for Doccano Sequence Labeling projects, verify formatting compliance, and provide reproduction instructions for live verification.

---

## 1. Compliance Status

> [!NOTE]
> **Audit Classification: `SCHEMA_VERIFIED_ONLY`**
> 
> A local production Doccano server (requiring PostgreSQL/SQLite backend, Node.js frontend, and Celery workers) is not installed in this execution environment. 
> In accordance with strict audit integrity rules, **no claim of a live UI import test is made**. 
> The dataset format was rigorously audited against the official Doccano open-source Sequence Labeling schema documentation.

---

## 2. Doccano Sequence Labeling Schema Specifications

Doccano's official specification for Sequence Labeling / Named Entity Recognition (`JSONL` upload format) mandates:

```json
{"id": 1, "text": "Sentence string", "label": [[start_int, end_int, "LABEL_STRING"]], "meta": {}}
```

### Verification Against Canonical Dataset (`data/annotated/malaysian_ner_1000.jsonl`):
| Schema Field | Official Doccano Specification | Dataset Implementation | Audit Result |
| :--- | :--- | :--- | :---: |
| **`text`** | Non-empty UTF-8 string | Exact raw sentence string | **MATCH (1,000 / 1,000)** |
| **`label`** | List of `[start, end, label]` | List of 3-element lists: integer start, integer end, string label | **MATCH (2,230 / 2,230 spans)** |
| **Offset Semantics** | 0-indexed character offsets ($0 \le \text{start} < \text{end} \le \text{len(text)}$) | Exact character slicing: `text[start:end] == entity_text` | **MATCH (100.0% verified)** |
| **Zero-Length Spans**| Disallowed / causes UI parsing error | Zero zero-length spans present | **MATCH (0 errors)** |
| **`meta`** | JSON object holding user metadata | Holds `stratum`, `source_id`, `document_id`, `is_hard_negative` | **MATCH (Valid JSON)** |
| **Encoding** | Strict UTF-8 without BOM | UTF-8 encoded | **MATCH** |
| **Label Palette** | Set of recognized category names | `PERSON`, `ORGANIZATION`, `LOCATION` | **MATCH** |

---

## 3. Reproduction Instructions for Future Live Doccano Verification

To run a live test on a machine with Docker:

1. **Launch Doccano:**
   ```bash
   docker pull doccano/doccano
   docker run -d --name doccano -p 8000:8000 doccano/doccano
   ```
2. **Initialize Admin User & Create Project:**
   - Navigate to `http://localhost:8000/`.
   - Log in with default credentials or run: `docker exec -it doccano doccano createuser --username admin --password password`.
   - Click **Create Project** $\rightarrow$ Select project type: **Sequence Labeling** $\rightarrow$ Name: `"Malaysian NER Benchmark"`.
3. **Configure Label Palette:**
   - In Settings $\rightarrow$ Labels, add:
     - `PERSON` (Shortcut: `p`)
     - `ORGANIZATION` (Shortcut: `o`)
     - `LOCATION` (Shortcut: `l`)
4. **Import Dataset:**
   - In Dataset $\rightarrow$ Import Dataset $\rightarrow$ File Format: **JSONL**.
   - Upload file: `data/annotated/malaysian_ner_1000.jsonl`.
   - Verify that 1,000 records import with highlighted entity spans and populated metadata panels.
5. **Export & Verify:**
   - In Dataset $\rightarrow$ Export Dataset $\rightarrow$ Format: **JSONL**.
   - Compare exported spans against original character offsets using `tests/test_phase26_tools.py::test_doccano_schema_and_roundtrip_fidelity`.
