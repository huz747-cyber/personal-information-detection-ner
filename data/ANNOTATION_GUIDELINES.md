# Malaysian Named Entity Recognition (NER) Annotation Guidelines

**Version:** 1.0.0  
**Scheme:** IOB2 / BIO (Begin, Inside, Outside)  
**Target Entity Classes:** `PERSON`, `ORGANIZATION`, `LOCATION`  
**Governing Standard:** CoNLL-2003 / OntoNotes 5.0 adapted for Malaysian Multilingual & Sociolinguistic Contexts  
**Security/Compliance:** Malaysian Personal Data Protection Act 2010 (PDPA) & Synthetic Data Standard  

---

## 1. Overview & Objectives

These guidelines establish standardized rules for annotating named entities in multilingual Malaysian text (Bahasa Melayu, Malaysian English, Manglish, and code-switched text).

### Core Tagging Scheme (IOB2)
- **`B-PER` / `I-PER`**: Named persons (real or synthetic).
- **`B-ORG` / `I-ORG`**: Formal organizations, statutory bodies, government agencies, registered companies, public institutions.
- **`B-LOC` / `I-LOC`**: Physical, geographic, and geopolitical locations, administrative districts, and street addresses.
- **`O`**: Outside any entity. All punctuation, conjunctions, job titles, honorifics, and structured numeric identifiers are tagged as `O` in general NER.

> [!IMPORTANT]
> **Decoupled PII Rule**: Structured personal identifiers (`MYKAD`, `PHONE`, `POSTCODE`) are **NOT** tagged as PERSON or LOCATION in the general NER dataset. They are maintained in a dedicated, decoupled structured PII corpus to prevent subword tokenization fragmentation in language models.

---

## 2. Entity Class Definitions & Boundary Rules

### 2.1 PERSON (`B-PER`, `I-PER`)

A `PERSON` is defined as the proper name of an individual human being.

#### Malaysian Patronymic Names (MANDATORY INCLUSION)
Unlike Western naming conventions (Given Name + Family Name), Malaysian Malay and Indian names frequently use patronymic connectors indicating lineage. **The patronymic connector and the father's name MUST be included within the single contiguous `PERSON` entity span.**

| Patronymic Particle | Origin / Context | Example Sentence | Correct Span |
| :--- | :--- | :--- | :--- |
| **`bin`** | Malay male (son of) | `Ahmad Faiz bin Zulkifli hadir.` | `[Ahmad Faiz bin Zulkifli]` |
| **`binti`** | Malay female (daughter of) | `Siti Hajar binti Osman dilantik.` | `[Siti Hajar binti Osman]` |
| **`bt.` / `bt`** | Abbreviated Malay female | `Nurul Huda bt. Razali bersetuju.` | `[Nurul Huda bt. Razali]` |
| **`a/l`** | Indian Malaysian male (*anak lelaki*) | `Ravi a/l Chandran menandatangani.` | `[Ravi a/l Chandran]` |
| **`a/p`** | Indian Malaysian female (*anak perempuan*) | `Kavitha a/p Subramaniam berucap.` | `[Kavitha a/p Subramaniam]` |
| **`s/o`** | Malaysian Indian / Sikh (*son of*) | `Dinesh s/o Anand tiba di pejabat.` | `[Dinesh s/o Anand]` |
| **`d/o`** | Malaysian Indian / Sikh (*daughter of*) | `Priya d/o Mohan mendaftar firma.` | `[Priya d/o Mohan]` |

#### Honorifics and Titles (STRICT EXCLUSION)
Honorifics, royal titles, state awards, religious titles, and professional prefixes are **NEVER** part of the `PERSON` span. They must be tagged as `O`.

- **State & Federal Titles:** `Tun`, `Tan Sri`, `Puan Sri`, `Dato'`, `Datuk`, `Dato' Seri`, `Datin`, `Datin Seri`.
- **Religious & Professional Titles:** `Haji`, `Hajah`, `Ustaz`, `Ustazah`, `Dr.`, `Prof.`, `Prof. Madya`, `Ir.`, `Ts.`.
- **Example:**
  - Text: `Dato' Seri Dr. Wan Azizah binti Wan Ismail merasmikan dewan.`
  - Annotation: `Dato'` (O), `'` (O), `Seri` (O), `Dr.` (O), `[Wan Azizah binti Wan Ismail]` (**PERSON**).

#### Chinese Malaysian Naming Conventions
- Include both Western given names and Chinese dialect/Mandarin romanized names in a single contiguous span:
  - `[Tan Wei Jun]` (**PERSON**)
  - `[Dr. Michelle Lim Hui Min]` -> `Dr.` (O), `[Michelle Lim Hui Min]` (**PERSON**)
  - `[Wong Ah Fook]` (**PERSON**)

#### Negative PERSON Rules
- Do **NOT** annotate mythological figures, brand names, or software algorithms (e.g. `ChatGPT`, `Siri`).
- Do **NOT** merge two people connected by conjunctions:
  - `Ali dan Abu` -> `[Ali]` (**PERSON**), `dan` (O), `[Abu]` (**PERSON**).

---

### 2.2 ORGANIZATION (`B-ORG`, `I-ORG`)

An `ORGANIZATION` represents an institutional body, government agency, statutory authority, corporation, educational establishment, or non-profit entity.

#### Statutory Bodies and Government Agencies
Annotate both acronyms and full official names as `ORGANIZATION`:
- Acronyms: `[LHDN]`, `[KWSP]`, `[PERKESO]`, `[PDRM]`, `[SPRM]`, `[JPJ]`, `[BNM]`, `[Bomba]`, `[DOSM]`.
- Full Titles: `[Lembaga Hasil Dalam Negeri]`, `[Kumpulan Wang Simpanan Pekerja]`, `[Polis Diraja Malaysia]`, `[Bank Negara Malaysia]`.

#### Corporate Legal Suffixes (MANDATORY INCLUSION)
Malaysian corporate legal identifiers indicate legal entity registration and must be included inside the `ORGANIZATION` span:
- Suffixes: `Sdn. Bhd.`, `Sdn Bhd`, `Bhd.`, `Bhd`, `Sendirian Berhad`, `Berhad`, `PLT` (Perkongsian Liabiliti Terhad).
- Examples:
  - `[Tenaga Nasional Berhad]` (**ORGANIZATION**)
  - `[Megah Holdings Sdn. Bhd.]` (**ORGANIZATION**)
  - `[Maybank Islamic Berhad]` (**ORGANIZATION**)
  - `[Petronas Dagangan Berhad]` (**ORGANIZATION**)

#### Educational Institutions & Healthcare Facilities
- Universities: `[Universiti Malaya]`, `[Universiti Kebangsaan Malaysia]`, `[Universiti Teknologi MARA]`.
- Hospitals: `[Hospital Kuala Lumpur]`, `[Pusat Perubatan Universiti Malaya]`.
- *Arbitration Note*: Even though `Kuala Lumpur` or `Malaya` appears in the name, do **not** split into a nested `LOCATION`. The entire institution is an `ORGANIZATION`.

---

### 2.3 LOCATION (`B-LOC`, `I-LOC`)

A `LOCATION` represents a defined geographical, administrative, or infrastructural space.

#### Geopolitical & Administrative Entities
- Federal Territories: `[Kuala Lumpur]`, `[Putrajaya]`, `[Labuan]`, `[Wilayah Persekutuan Kuala Lumpur]`.
- States: `[Selangor]`, `[Johor]`, `[Pulau Pinang]`, `[Perak]`, `[Sabah]`, `[Sarawak]`, `[Kedah]`, etc.
- Cities & Urban Centers: `[Petaling Jaya]`, `[Subang Jaya]`, `[Shah Alam]`, `[George Town]`, `[Johor Bahru]`, `[Ipoh]`, `[Kuching]`, `[Kota Kinabalu]`.
- Tech Hubs & Corridors: `[Cyberjaya]`, `[Bandar Sunway]`, `[Bangsar South]`, `[Mont Kiara]`.

#### Street Names & Addresses
Annotate named thoroughfares and precincts as `LOCATION`:
- `[Jalan Sultan Ismail]` (**LOCATION**)
- `[Lebuhraya Damansara-Puchong]` (**LOCATION**)
- `[Presint 2]` (**LOCATION**)
- `[Taman Tun Dr Ismail]` (**LOCATION**)

#### Negative LOCATION Rules
- **Postcodes (5 digits)**: `50250` or `47301` are **NOT** tagged as LOCATION in core NER (they are tagged as `O`). They belong to the structured PII layer.
- **Room/Floor numbers**: `Tingkat 4`, `Bilik 302` are **NOT** locations (tagged as `O`).
- **Organizations containing place names**: `[Universiti Malaya]` is `ORGANIZATION`, **not** `LOCATION`.

---

## 3. Boundary & Formatting Conventions

1. **Whitespace Invariance**: Span boundaries must strictly encompass alphanumeric characters and internal punctuation. Never include preceding or trailing spaces (`" Putrajaya "` is an offset defect; `"Putrajaya"` is correct).
2. **Punctuation Attachment**:
   - Periods that are part of abbreviations (`bt.`, `Sdn. Bhd.`, `Dr.`) must be preserved within the span if the abbreviation itself is part of the entity.
   - Sentence-ending periods, commas, quotation marks, and parentheses must remain **outside** the entity span.
3. **No Overlapping Entities**: A token cannot belong to multiple classes simultaneously. In case of institutional naming conflicts, follow Section 2 arbitration rules.

---

## 4. Quality Control & Acceptance Checklist

Before any batch is promoted to the canonical dataset, it must pass automated validation:
- [ ] Offset verification: `sentence_text[start:end] == declared_text` for 100% of spans.
- [ ] Valid IOB2 transition grammar: zero orphaned `I-` tags.
- [ ] No duplicate sentences across train/val/test splits.
- [ ] Patronymic span completeness: no split patronymic tokens (`bin` left as `O` while names are tagged).
- [ ] Honorific exclusion: no state titles (`Dato'`, `Tan Sri`) included inside `PERSON` spans.
