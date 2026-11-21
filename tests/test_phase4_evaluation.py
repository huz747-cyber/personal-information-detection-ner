"""
Unit and regression tests for Phase 4 baseline evaluation metrics and logic.
"""

import pytest
from src.evaluate_phase4 import (
    compute_metrics,
    compute_confusion_matrix,
    evaluate_hard_negatives,
    evaluate_gazetteer_leakage,
    collect_error_cases,
    extract_gold_entities,
)


def test_compute_metrics_strict_exact_match():
    preds = [[{"start": 0, "end": 10, "label": "PERSON", "text": "Ali Hassan"}]]
    golds = [[{"start": 0, "end": 10, "label": "PERSON", "text": "Ali Hassan"}]]
    res = compute_metrics(preds, golds, relaxed=False)
    assert res["tp"] == 1
    assert res["fp"] == 0
    assert res["fn"] == 0
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0
    assert res["f1"] == 1.0


def test_compute_metrics_strict_boundary_mismatch():
    # Boundary mismatch should be 0 TP under strict evaluation
    preds = [[{"start": 0, "end": 3, "label": "PERSON", "text": "Ali"}]]
    golds = [[{"start": 0, "end": 10, "label": "PERSON", "text": "Ali Hassan"}]]
    res = compute_metrics(preds, golds, relaxed=False)
    assert res["tp"] == 0
    assert res["fp"] == 1
    assert res["fn"] == 1
    assert res["f1"] == 0.0


def test_compute_metrics_relaxed_boundary_match():
    # Overlapping boundary should be 1 TP under relaxed evaluation
    preds = [[{"start": 0, "end": 3, "label": "PERSON", "text": "Ali"}]]
    golds = [[{"start": 0, "end": 10, "label": "PERSON", "text": "Ali Hassan"}]]
    res = compute_metrics(preds, golds, relaxed=True)
    assert res["tp"] == 1
    assert res["fp"] == 0
    assert res["fn"] == 0
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0
    assert res["f1"] == 1.0


def test_compute_metrics_empty():
    res = compute_metrics([], [], relaxed=False)
    assert res["precision"] == 0.0
    assert res["recall"] == 0.0
    assert res["f1"] == 0.0


def test_compute_confusion_matrix():
    # Pred PERSON, Gold ORGANIZATION -> confusion ORG -> PERSON
    preds = [[{"start": 0, "end": 8, "label": "PERSON", "text": "Petronas"}]]
    golds = [[{"start": 0, "end": 8, "label": "ORGANIZATION", "text": "Petronas"}]]
    cm = compute_confusion_matrix(preds, golds)
    assert cm["ORGANIZATION"]["PERSON"] == 1
    assert cm["ORGANIZATION"]["ORGANIZATION"] == 0
    assert cm["PERSON"]["PERSON"] == 0


def test_evaluate_hard_negatives():
    records = [
        {"id": "hn-1", "label": []},
        {"id": "hn-2", "label": []},
        {"id": "reg-1", "label": [[0, 5, "PERSON"]]},
    ]
    # Predict 0 on hn-1, spurious entity on hn-2
    preds = [
        [],
        [{"start": 2, "end": 8, "label": "PERSON", "text": "Distractor"}],
        [{"start": 0, "end": 5, "label": "PERSON", "text": "Najib"}],
    ]
    res = evaluate_hard_negatives(records, preds)
    assert res["total_hard_negatives"] == 2
    assert res["clean_sentences_count"] == 1
    assert res["total_hallucinations"] == 1
    assert res["rejection_accuracy"] == 0.5


def test_evaluate_gazetteer_leakage():
    records = [
        {
            "id": "s1",
            "text": "Petronas and Grab are in Kuala Lumpur and Cyberjaya.",
            "label": [
                [0, 8, "ORGANIZATION"],
                [13, 17, "ORGANIZATION"],
                [25, 37, "LOCATION"],
                [42, 51, "LOCATION"],
            ],
        }
    ]
    golds = [extract_gold_entities(r) for r in records]
    preds_dict = {
        "Config 3 (Hybrid)": [
            [
                {"start": 0, "end": 8, "label": "ORGANIZATION", "text": "Petronas"},
                {"start": 13, "end": 17, "label": "ORGANIZATION", "text": "Grab"},
                {"start": 25, "end": 37, "label": "LOCATION", "text": "Kuala Lumpur"},
                {"start": 42, "end": 51, "label": "LOCATION", "text": "Cyberjaya"},
            ]
        ]
    }
    analysis = evaluate_gazetteer_leakage(records, preds_dict, golds)
    assert analysis["total_gold_entities"] == 4
    assert analysis["known_in_gazetteer_count"] >= 2
    assert analysis["unseen_entities_count"] >= 1
    assert "Config 3 (Hybrid)" in analysis["config_comparison"]


def test_collect_error_cases():
    records = [
        {"id": "err-1", "text": "Ahmad bin Ali went to KL", "label": [[0, 13, "PERSON"], [22, 24, "LOCATION"]]},
    ]
    golds = [extract_gold_entities(r) for r in records]
    # Predict only KL, completely missing Ahmad bin Ali
    preds = [
        [
            {"start": 22, "end": 24, "label": "LOCATION", "text": "KL", "score": 0.8},
        ]
    ]
    errors = collect_error_cases(records, preds, golds)
    assert len(errors["false_negatives"]) == 1
    assert len(errors["patronymic_errors"]) == 1
