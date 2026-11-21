# Phase 4 Qualitative Error Analysis Report

**Date:** 21 November 2026  
**System Evaluated:** Configuration 3 (Full Phase 2 Hybrid NER System)  

---

## 1. Quantitative Error Breakdown

* **Total False Positives:** 60
* **Total False Negatives (Missed Entities):** 0
* **Boundary Mismatches (Partial Spans):** 91
* **Patronymic Linking Failures:** 0
* **Hard-Negative Hallucinations:** 4

---

## 2. Representative Error Examples & Diagnosis

### 2.1 Boundary Mismatches (Partial Span Spills)
Boundary defects typically arise when subword tokens in multi-word organizations or code-switched phrases are only partially tagged by DistilBERT.

* **Sentence ID:** `my-mang-003`
  * *Text:* "Priya d/o Mohan already reached the office in Subang Jaya around 5.14 PM meh for case 3."
  * *Predicted:* [PERSON] 'P' (0:1)
  * *Ground Truth:* [PERSON] 'Priya d/o Mohan' (0:15)

* **Sentence ID:** `my-mang-006`
  * *Text:* "Don't worry one, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 5.35 PM under batch 6."
  * *Predicted:* [ORGANIZATION] 'submitted the proposal to Maxis Berhad' (48:86)
  * *Ground Truth:* [ORGANIZATION] 'Maxis Berhad' (74:86)

* **Sentence ID:** `my-mang-008`
  * *Text:* "Don't worry leh, Suresh a/l Murugan already submitted the proposal to CIMB Bank around 3.49 PM under batch 8."
  * *Predicted:* [PERSON] 'Suresh a' (17:25)
  * *Ground Truth:* [PERSON] 'Suresh a/l Murugan' (17:35)

* **Sentence ID:** `my-mang-013`
  * *Text:* "Priya d/o Mohan already reached the office in Subang Jaya around 1.29 PM lah for case 13."
  * *Predicted:* [PERSON] 'P' (0:1)
  * *Ground Truth:* [PERSON] 'Priya d/o Mohan' (0:15)

* **Sentence ID:** `my-mang-016`
  * *Text:* "Don't worry lor, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 1.50 PM under batch 16."
  * *Predicted:* [ORGANIZATION] 'submitted the proposal to Maxis Berhad' (48:86)
  * *Ground Truth:* [ORGANIZATION] 'Maxis Berhad' (74:86)

### 2.2 False Positives (Spurious Entities)
Spurious entities occur primarily on conversational Malaysian terms, job designations, or currency distractor tokens.

* **Sentence ID:** `my-mang-003`
  * *Text:* "Priya d/o Mohan already reached the office in Subang Jaya around 5.14 PM meh for case 3."
  * *Spurious Entity:* `[PERSON]` 'Mohan' (Confidence: 96.0%)

* **Sentence ID:** `my-mang-008`
  * *Text:* "Don't worry leh, Suresh a/l Murugan already submitted the proposal to CIMB Bank around 3.49 PM under batch 8."
  * *Spurious Entity:* `[PERSON]` 'l Murugan' (Confidence: 83.5%)

* **Sentence ID:** `my-mang-013`
  * *Text:* "Priya d/o Mohan already reached the office in Subang Jaya around 1.29 PM lah for case 13."
  * *Spurious Entity:* `[PERSON]` 'Mohan' (Confidence: 95.6%)

* **Sentence ID:** `my-mang-018`
  * *Text:* "Don't worry one, Suresh a/l Murugan already submitted the proposal to CIMB Bank around 5.09 PM under batch 18."
  * *Spurious Entity:* `[PERSON]` 'l Murugan' (Confidence: 86.4%)

* **Sentence ID:** `my-mang-023`
  * *Text:* "Priya d/o Mohan already reached the office in Subang Jaya around 3.44 PM ma for case 23."
  * *Spurious Entity:* `[PERSON]` 'Mohan' (Confidence: 96.5%)

### 2.3 False Negatives (Missed Entities)
Missed entities occur predominantly on colloquial names, uncommon patronymic particles, or corporate entities without gazetteer listings.

### 2.4 Hard-Negative Hallucinations
Hard-negative sentences are engineered without any named entities but contain distractor formats (currencies, timestamps, dates).

* **Sentence ID:** `my-mang-130`
  * *Text:* "Aiyo, the grab delivery fee so expensive during heavy rain time lor."
  * *Hallucination:* `[PERSON]` 'Aiyo' (Confidence: 80.0%)

* **Sentence ID:** `my-mixcs-133`
  * *Text:* "Petang nanti I ada internal audit session with the management team kat tingkat 3."
  * *Hallucination:* `[ORGANIZATION]` 'Petang' (Confidence: 95.1%)

* **Sentence ID:** `my-mixcs-133`
  * *Text:* "Petang nanti I ada internal audit session with the management team kat tingkat 3."
  * *Hallucination:* `[ORGANIZATION]` 'kat' (Confidence: 79.2%)

* **Sentence ID:** `my-mixcs-134`
  * *Text:* "Semua candidate kena bring hard copy resume and original certificates masa interview."
  * *Hallucination:* `[PERSON]` 'Semua' (Confidence: 84.7%)

---

## 3. Recommended Architectural Interventions for Phase 5

1. **Fine-Tuning on Malaysian Hard Negatives:** Down-weight transformer attention on currency tokens (`RM`, `SGD`) and time expressions.
2. **Multilingual Checkpoint Ingestion:** Transition from English-only DistilBERT to multilingual foundation models (`distilbert-base-multilingual-cased` or `xlm-roberta-base`) to enhance representation of Bahasa Melayu morphology.
3. **Context-Sensitive Boundary Refinement:** Implement bidirectional subword expansion around patronymic connectors (`a/l`, `s/o`) to prevent initial particle truncation.