# Critical Audit G: Privacy Screening & PII Protection Audit

**Audit Objective:** Independently review the privacy screening engine in `src/dataset_tools/privacy_screener.py`, evaluate screening results against defensible legal standards, and document limitations, false-positive risks, and false-negative risks.

---

## 1. Defensible Language & Compliance Findings

> [!IMPORTANT]
> **Defensible Privacy Standard:**
> Automated regex and algorithmic pattern matching **cannot prove the absolute absence of private personal data**. 
> Claims such as *"absolute privacy guaranteed"* or *"zero private leaks in existence"* are technically indefensible. 
> 
> The defensible and verified finding is:
> **Under comprehensive automated screening for known structured identifiers (MyKad, credit cards, telephone numbers, API tokens, and granular residential lot addresses), zero privacy violations were detected across the 1,000 canonical records.**

---

## 2. Verification of Screening Mechanisms

`PrivacyScreener` was audited against synthetic test fixtures across 5 primary threat categories:

| Target Category | Detection Method | Synthetic Whitelist Exemption | Audit Verification |
| :--- | :--- | :--- | :---: |
| **Malaysian MyKad (NRIC)** | 12-digit regex with state-code filtering | Explicit synthetic list (`950315-10-5231`, etc.) | **PASS** |
| **Live Mobile Numbers** | `+601[0-9]` and `01[0-9]` regex patterns | Reserved documentation prefixes (`012-345 6789`) | **PASS** |
| **Credit Card Numbers** | 13–19 digit patterns validated via Luhn checksum | None (All valid Luhn matches flagged) | **PASS** |
| **API Tokens & Credentials** | High-entropy strings (`ghp_`, `sk-`, `bearer`, passwords) | None | **PASS** |
| **Residential Addresses** | Explicit unit/lot numbers with residential street/taman | None | **PASS** |

### Automated Screening Result:
* Records Evaluated: 1,000
* Flagged Critical Violations: 0
* Flagged High/Medium Violations: 0
* Overall Screening Status: **PASS [CLEAN UNDER DEFINED HEURISTICS]**

---

## 3. Screening Limitations & Residual Risk Analysis

1. **False-Negative Risks (Unstructured or Obfuscated PII):**
   * *Spelled-out numbers:* If an individual wrote a phone number or ID in words (e.g. *"kosong satu dua tiga..."*), heuristic regex would fail to detect it.
   * *Obfuscated formatting:* Non-standard separators or intentional evasions (e.g. `012 [dot] 345 [dash] 6789`).
2. **Homonym Collision (Accidental Real Name Matching):**
   * Synthetically generated Malaysian names (e.g. combining common Malay, Chinese, or Indian given names and surnames) may coincidentally match living individuals. 
   * Under privacy frameworks (such as Malaysia's Personal Data Protection Act 2010 / PDPA), common personal names appearing in fictional synthetic contexts without accompanying identifying attributes (address, IC, biometric, or contact data) do not constitute actionable personal data breaches.
3. **Source-Level Governance Requirements:**
   * Public Hansard excerpts (`SRC-005`) and Bursa Malaysia disclosures (`SRC-006`) contain names of elected officials, ministers, and public corporate directors acting in their official public capacity. These are public regulatory records.
   * Independently authored (`SRC-007`) and synthetic (`SRC-008`) datasets use strictly invented roles, fictional docket codes, and generic project references.

---

## 4. Manual Review Status

A manual spot-check of 100 randomly sampled sentences across all 7 strata confirmed:
* No private residential home addresses.
* No personal banking credentials or passwords.
* All phone numbers and MyKad numbers present in the repository exist solely within documentation fixtures or test mock objects, with none present in the canonical training text.
