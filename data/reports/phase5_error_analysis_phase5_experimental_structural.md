# Phase 5 Qualitative Error Analysis Report

**Date:** 21 November 2026  
**System Evaluated:** Configuration 3-FT (Fine-Tuned Multilingual DistilBERT + Full Hybrid System)  

---

## 1. Quantitative Error Distribution

* **Total False Positives:** 1
* **Total False Negatives (Missed Entities):** 3
* **Boundary Mismatches (Partial Spans):** 38
* **Patronymic Linking Failures:** 0
* **Hard-Negative Hallucinations:** 1

---

## 2. Representative Error Cases & Root-Cause Diagnosis

### 2.1 Boundary Mismatches

* **Sentence ID:** `my-malay-019`
  * *Text:* "Menteri Kementerian Belia dan Sukan, Saifuddin bin Nasution menghadiri majlis dialog awam mengenai pengurusan sisa pepejal di Ipoh pada 19 Julai 2024 sempena program siri 19."
  * *Predicted:* [ORGANIZATION] 'Belia dan Sukan' (20:35)
  * *Ground Truth:* [ORGANIZATION] 'Kementerian Belia dan Sukan' (8:35)

* **Sentence ID:** `my-malay-028`
  * *Text:* "Menteri Kementerian Kemajuan Desa dan Wilayah, Fadillah bin Yusof melancarkan inisiatif pendigitalan perkhidmatan kaunter di Kuala Terengganu pada 28 April 2024 sempena program siri 28."
  * *Predicted:* [ORGANIZATION] 'Kemajuan Desa dan Wilayah' (20:45)
  * *Ground Truth:* [ORGANIZATION] 'Kementerian Kemajuan Desa dan Wilayah' (8:45)

* **Sentence ID:** `my-malay-037`
  * *Text:* "Menteri Kementerian Perpaduan Negara, Mohamad Sabu bin Mahmood mengadakan sesi libat urus bersama pemimpin komuniti setempat di Shah Alam pada 9 Januari 2024 sempena program siri 37."
  * *Predicted:* [ORGANIZATION] 'Perpaduan Negara' (20:36)
  * *Ground Truth:* [ORGANIZATION] 'Kementerian Perpaduan Negara' (8:36)

* **Sentence ID:** `my-malay-040`
  * *Text:* "Menteri Kementerian Sumber Asli dan Kelestarian Alam, Rafizi bin Ramli merumuskan usul persidangan perpaduan antara kaum di Johor Bahru pada 12 April 2024 sempena program siri 40."
  * *Predicted:* [ORGANIZATION] 'Sumber Asli dan Kelestarian Alam' (20:52)
  * *Ground Truth:* [ORGANIZATION] 'Kementerian Sumber Asli dan Kelestarian Alam' (8:52)

* **Sentence ID:** `my-malay-049`
  * *Text:* "Menteri Kementerian Belia dan Sukan, Saifuddin bin Nasution menghadiri majlis dialog awam mengenai pengurusan sisa pepejal di Ipoh pada 21 Januari 2024 sempena program siri 49."
  * *Predicted:* [ORGANIZATION] 'Belia dan Sukan' (20:35)
  * *Ground Truth:* [ORGANIZATION] 'Kementerian Belia dan Sukan' (8:35)

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
