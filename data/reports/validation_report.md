# Malaysian NER 1,000-Sentence Quality Assurance Report

```text
====================================================================
               MALAYSIAN NER DATASET VALIDATION REPORT
====================================================================
Total Sentences Evaluated:   1000
Fully Valid Sentences:       1000
Sentences with Errors:       0
Total Errors:                0
Total Warnings:              22
Hard Negatives Verified:     105
Validation Status:           PASS [CLEAN]
--------------------------------------------------------------------
Entity Class Breakdown:
  - LOCATION            :    830
  - ORGANIZATION        :    577
  - PERSON              :    823
--------------------------------------------------------------------
BIO Token Tag Breakdown:
  - B-LOCATION          :    830
  - B-ORGANIZATION      :    588
  - B-PERSON            :    823
  - I-LOCATION          :    488
  - I-ORGANIZATION      :   1277
  - I-PERSON            :   1690
  - O                   :  16689
--------------------------------------------------------------------
Linguistic Stratum Distribution:
  - chinese_naming              :    95 (  9.5%)
  - formal_malay                :   240 ( 24.0%)
  - indian_naming               :    95 (  9.5%)
  - international_baseline      :    50 (  5.0%)
  - malaysian_english           :   240 ( 24.0%)
  - manglish                    :   140 ( 14.0%)
  - mixed_code_switch           :   140 ( 14.0%)
--------------------------------------------------------------------
Sentences by Entity Count:
  - 0 entities in sentence:   105 sentences
  - 2 entities in sentence:   455 sentences
  - 3 entities in sentence:   440 sentences
--------------------------------------------------------------------
Issues Logged (First 15 of 22):
  [WARNING] ID my-malay-230 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-malay-232 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-malay-233 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-222 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-227 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-229 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-233 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-234 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-myaen-236 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mang-130 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mang-131 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mang-139 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mixcs-129 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mixcs-131 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
  [WARNING] ID my-mixcs-138 (HARD_NEGATIVE): Hard-negative sentence contains no recognizable distractor pattern (currency, date, ID).
====================================================================
Cross-Split Contamination:   0 errors (PASS)
```
