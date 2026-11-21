# Phase 5 Qualitative Error Analysis Report

**Date:** 21 November 2026  
**System Evaluated:** Configuration 3-FT (Fine-Tuned Multilingual DistilBERT + Full Hybrid System)  

---

## 1. Quantitative Error Distribution

* **Total False Positives:** 0
* **Total False Negatives (Missed Entities):** 0
* **Boundary Mismatches (Partial Spans):** 50
* **Patronymic Linking Failures:** 0
* **Hard-Negative Hallucinations:** 0

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

### 2.3 False Negatives (Missed Entities)

### 2.4 Hard-Negative Rejection & Hallucinations

* **Zero hallucinations detected.** The fine-tuned hybrid system cleanly rejected 100% of hard-negative sentences.