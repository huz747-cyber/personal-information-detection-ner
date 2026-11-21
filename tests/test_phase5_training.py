"""
Unit and regression tests for Phase 5 fine-tuning pipeline and evaluation.
"""

from pathlib import Path
import pytest
import torch
from transformers import AutoTokenizer

from src.train_phase5 import (
    LABELS,
    ID2LABEL,
    LABEL2ID,
    MalaysianNERDataset,
    collate_fn,
    predict_entities,
    evaluate_dataset,
    set_seed,
)


@pytest.fixture(scope="module")
def tokenizer():
    return AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")


def test_label_schema_invariants():
    assert len(LABELS) == 7
    assert LABELS[0] == "O"
    assert "B-PERSON" in LABELS and "I-PERSON" in LABELS
    assert "B-ORGANIZATION" in LABELS and "I-ORGANIZATION" in LABELS
    assert "B-LOCATION" in LABELS and "I-LOCATION" in LABELS
    assert len(ID2LABEL) == 7
    assert len(LABEL2ID) == 7


def test_subword_iob2_alignment(tokenizer):
    record = {
        "text": "Ahmad bin Ali melawat Menara Maybank di Kuala Lumpur.",
        "label": [
            [0, 13, "PERSON"],
            [22, 36, "ORGANIZATION"],
            [40, 52, "LOCATION"],
        ],
    }

    dataset = MalaysianNERDataset([record], tokenizer, max_length=64)
    item = dataset[0]

    input_ids = item["input_ids"]
    labels = item["labels"]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # First token [CLS] and last token [SEP] should be ignored (-100)
    assert labels[0] == -100
    assert labels[-1] == -100

    # Token "Ahmad" (0:5) should be B-PERSON
    ahmad_idx = tokens.index("Ahmad")
    assert labels[ahmad_idx] == LABEL2ID["B-PERSON"]

    # Token "bin" (6:9) should be I-PERSON
    bin_idx = tokens.index("bin")
    assert labels[bin_idx] == LABEL2ID["I-PERSON"]

    # Token "Ali" (10:13) should be I-PERSON
    ali_idx = tokens.index("Ali")
    assert labels[ali_idx] == LABEL2ID["I-PERSON"]


def test_collate_fn_dynamic_padding(tokenizer):
    rec1 = {"text": "Short sentence.", "label": []}
    rec2 = {"text": "A much longer sentence containing multiple words for padding check.", "label": []}

    dataset = MalaysianNERDataset([rec1, rec2], tokenizer, max_length=64)
    batch = collate_fn([dataset[0], dataset[1]])

    assert batch["input_ids"].shape[0] == 2
    assert batch["attention_mask"].shape[0] == 2
    assert batch["labels"].shape[0] == 2
    # Ensure second dimension is equal (padded to max length in batch)
    assert batch["input_ids"].shape[1] == batch["labels"].shape[1]
    # Check that padded labels have value -100
    assert (batch["labels"][0] == -100).any()


def test_deterministic_seed_setting():
    set_seed(42)
    t1 = torch.rand(5)
    set_seed(42)
    t2 = torch.rand(5)
    assert torch.equal(t1, t2)


def test_commercial_dataset_isolation():
    comm_train = Path("data/splits/commercial/train.jsonl")
    assert comm_train.exists()

    with open(comm_train, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 560

    # Ensure no prohibited sources leaked into commercial train
    for line in lines:
        assert '"SRC-001"' not in line
        assert '"SRC-004"' not in line
        assert '"SRC-005"' not in line
