# Phase 5 Qualitative Error Analysis Report

**Date:** 21 November 2026  
**System Evaluated:** Configuration 3-FT (Fine-Tuned Multilingual DistilBERT + Full Hybrid System)  

---

## 1. Quantitative Error Distribution

* **Total False Positives:** 1
* **Total False Negatives (Missed Entities):** 3
* **Boundary Mismatches (Partial Spans):** 88
* **Patronymic Linking Failures:** 0
* **Hard-Negative Hallucinations:** 1

---

## 2. Representative Error Cases & Root-Cause Diagnosis

### 2.1 Boundary Mismatches

* **Sentence ID:** `my-mang-006`
  * *Text:* "Don't worry one, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 5.35 PM under batch 6."
  * *Predicted:* [ORGANIZATION] 'submitted the proposal to Maxis Berhad' (48:86)
  * *Ground Truth:* [ORGANIZATION] 'Maxis Berhad' (74:86)

* **Sentence ID:** `my-mang-016`
  * *Text:* "Don't worry lor, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 1.50 PM under batch 16."
  * *Predicted:* [ORGANIZATION] 'submitted the proposal to Maxis Berhad' (48:86)
  * *Ground Truth:* [ORGANIZATION] 'Maxis Berhad' (74:86)

* **Sentence ID:** `my-mang-026`
  * *Text:* "Don't worry leh, Siti Hajar binti Osman already submitted the proposal to Maxis Berhad around 3.10 PM under batch 26."
  * *Predicted:* [ORGANIZATION] 'submitted the proposal to Maxis Berhad' (48:86)
  * *Ground Truth:* [ORGANIZATION] 'Maxis Berhad' (74:86)

* **Sentence ID:** `my-mang-077`
  * *Text:* "Aiyo, Priya Mohan stuck in jam near Pavilion Kuala Lumpur because of accident on route 12 one!"
  * *Predicted:* [LOCATION] 'Kuala Lumpur' (45:57)
  * *Ground Truth:* [LOCATION] 'Pavilion Kuala Lumpur' (36:57)

* **Sentence ID:** `my-mang-107`
  * *Text:* "Aiyo, Priya Mohan stuck in jam near Pavilion Kuala Lumpur because of accident on route 42 one!"
  * *Predicted:* [LOCATION] 'Kuala Lumpur' (45:57)
  * *Ground Truth:* [LOCATION] 'Pavilion Kuala Lumpur' (36:57)

### 2.2 False Positives (Spurious Detections)

* **Sentence ID:** `my-malay-230`
  * *Text:* "Semua kenderaan barangan berat dilarang melalui laluan jalan persekutuan tersebut pada waktu puncak."
  * *Spurious Entity:* `[LOCATION]` 'jalan persekutuan tersebut pada waktu puncak' (Confidence: 95.0%)

### 2.3 False Negatives (Missed Entities)

* **Sentence ID:** `my-malay-125`
  * *Text:* "Pengarah Kamarul bin Baharin bersama perwakilan Hospital Sungai Buloh meninjau kemudahan makmal penyelidikan termaju bertempat di Kluang pada Jun 2024 di bawah inisiatif 30."
  * *Missed Entity:* `[ORGANIZATION]` 'Hospital Sungai Buloh'

* **Sentence ID:** `my-malay-149`
  * *Text:* "Pengarah Ahmad Fikri bin Mansor bersama perwakilan Hospital Sungai Buloh mempengerusikan mesyuarat perancangan tata kelola kewangan di Kluang pada Jun 2024 di bawah inisiatif 54."
  * *Missed Entity:* `[ORGANIZATION]` 'Hospital Sungai Buloh'

* **Sentence ID:** `my-malay-165`
  * *Text:* "Pengarah Kamarul bin Baharin bersama perwakilan Hospital Sungai Buloh meninjau kemudahan makmal penyelidikan termaju bertempat di Muar pada Oktober 2024 di bawah inisiatif 70."
  * *Missed Entity:* `[ORGANIZATION]` 'Hospital Sungai Buloh'

### 2.4 Hard-Negative Rejection & Hallucinations

* **Sentence ID:** `my-malay-230`
  * *Text:* "Semua kenderaan barangan berat dilarang melalui laluan jalan persekutuan tersebut pada waktu puncak."
  * *Hallucination:* `[LOCATION]` 'jalan persekutuan tersebut pada waktu puncak' (Confidence: 95.0%)
