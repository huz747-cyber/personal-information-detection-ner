# Critical Audit H: Doccano Compatibility & Round-Trip Fidelity Audit

**Audit Objective:** Empirically verify that the dataset conforms to official Doccano JSONLines specifications, supports lossless export and import, and preserves exact character offsets, entity labels, and metadata.

---

## 1. Specification Compliance

Doccano's official Named Entity Recognition format requires JSONLines where each line contains:
* `"text"`: The full sentence string.
* `"label"`: A list of spans formatted as `[start_offset, end_offset, "LABEL"]`.
* `"meta"` or `"metadata"`: An arbitrary JSON object holding document-level provenance or stratum annotations.

### Canonical Record Inspection:
```json
{
  "id": "my-malay-001",
  "text": "Menteri Kementerian Pertanian dan Keterjaminan Makanan, Ahmad Faiz bin Zulkifli telah membentangkan perancangan peruntukan pembangunan infrastruktur di Putrajaya pada 1 Januari 2024 sempena program siri 1.",
  "label": [
    [8, 54, "ORGANIZATION"],
    [56, 79, "PERSON"],
    [152, 161, "LOCATION"]
  ],
  "meta": {
    "source_id": "SRC-005",
    "source_type": "public",
    "stratum": "formal_malay",
    "language": "ms",
    "domain": "government",
    "is_hard_negative": false,
    "document_id": "hansard-debates-1",
    "template_id": null
  }
}
```

---

## 2. Round-Trip Fidelity & Offset Verification

An end-to-end round-trip test was conducted using `src/dataset_tools/doccano_adapter.py`:
1. **Export:** Exported all 1,000 canonical records to a temporary file via `export_to_doccano()`.
2. **Schema Audit:** Validated every line against JSON typing requirements:
   - Line syntax: 1,000 valid JSON objects (**0 errors**).
   - Text field: 1,000 non-empty strings (**0 errors**).
   - Label field: 2,230 spans, all 3-element lists `[int, int, str]` (**0 errors**).
   - Zero-length spans: **0 detected**.
   - Out-of-bounds spans: **0 detected**.
   - Metadata dictionary: 1,000 valid dictionaries (**0 errors**).
3. **Re-import:** Imported back via `import_from_doccano()`.
4. **Fidelity Comparison:**
   - Text preservation: **1,000 / 1,000 identical strings (100.0%)**.
   - Entity label preservation: **2,230 / 2,230 identical labels (100.0%)**.
   - Character offset preservation: **2,230 / 2,230 identical offsets (100.0%)**.
   - Reconstructed text slice fidelity: $\forall e \in \text{entities}, \text{text}[e.\text{start}:e.\text{end}] == e.\text{text}$ (**100.0%**).
   - Mismatches detected: **0**.

---

## 3. Metadata Acceptance Verification

* The `"meta"` dictionary in Doccano is fully preserved during import and export.
* When imported into Doccano UI, fields such as `"source_id"`, `"stratum"`, and `"document_id"` are displayed in the metadata panel for annotators and reviewers.
* Automated unit test: `tests/test_phase26_tools.py::test_doccano_schema_and_roundtrip_fidelity` (**PASS**).
