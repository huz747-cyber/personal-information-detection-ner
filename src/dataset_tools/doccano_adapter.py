"""
Doccano Import / Export and BIO Conversion Adapter.

Provides seamless bidirectional conversion between:
1. Standard Doccano JSONLines format (for annotation UI tooling):
   {"id": 1, "text": "...", "label": [[start, end, "LABEL"], ...], "meta": {...}}
2. Internal Entity Record schema (with explicit text slices and metadata):
   {"id": 1, "text": "...", "entities": [{"text": "...", "label": "...", "start": int, "end": int}], "metadata": {...}}
3. Token-level IOB2 / BIO tagging sequences:
   tokens: ["Ahmad", "Faiz", "bin", "Zulkifli", "ke", "Kuala", "Lumpur"]
   bio:    ["B-PERSON", "I-PERSON", "I-PERSON", "I-PERSON", "O", "B-LOCATION", "I-LOCATION"]

Author: AI/ML Club
License: MIT
"""

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def tokenize_with_offsets(text: str) -> List[Tuple[str, int, int]]:
    """Tokenizes a string into words/punctuation while preserving exact character offsets.

    Matches alphanumeric word sequences (including internal apostrophes/hyphens for names)
    and individual punctuation symbols, skipping pure whitespace.

    Args:
        text: Input text string.

    Returns:
        List of tuples: (token_text, start_offset, end_offset).
    """
    tokens: List[Tuple[str, int, int]] = []
    # Match words (with potential internal hyphens/apostrophes like Dato' or a/l) or individual symbols
    pattern = re.compile(r"\w+(?:['/]\w+)?|[^\w\s]")
    for match in pattern.finditer(text):
        tokens.append((match.group(0), match.start(), match.end()))
    return tokens


def text_to_bio(
    text: str,
    entities: List[Dict[str, Any]],
    tokenizer_fn: Optional[Callable[[str], List[Tuple[str, int, int]]]] = None,
) -> Tuple[List[str], List[str]]:
    """Converts a text string and entity character spans into tokens and IOB2 BIO tags.

    Args:
        text: Original sentence text.
        entities: List of entity dictionaries with 'start', 'end', and 'label'.
        tokenizer_fn: Optional custom tokenizer returning (token, start, end). Defaults to tokenize_with_offsets.

    Returns:
        Tuple of (tokens_list, bio_tags_list).
    """
    if tokenizer_fn is None:
        tokens_with_offsets = tokenize_with_offsets(text)
    else:
        tokens_with_offsets = tokenizer_fn(text)

    # Sort entities by start offset
    sorted_entities = sorted(entities, key=lambda e: (e["start"], e["end"]))

    tokens: List[str] = []
    bio_tags: List[str] = []

    for token, t_start, t_end in tokens_with_offsets:
        tokens.append(token)
        assigned_tag = "O"

        for ent in sorted_entities:
            e_start = ent["start"]
            e_end = ent["end"]
            label = ent["label"]

            # Token intersects with entity
            if max(t_start, e_start) < min(t_end, e_end):
                # If this token is the first token of the entity span, use B-
                if t_start >= e_start and (t_start == e_start or t_start - e_start < 2):
                    assigned_tag = f"B-{label}"
                else:
                    assigned_tag = f"I-{label}"
                break

        bio_tags.append(assigned_tag)

    return tokens, bio_tags


def bio_to_spans(
    tokens: List[str],
    bio_tags: List[str],
    text: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Converts tokens and IOB2 BIO tags back into entity character spans.

    If text is provided, aligns tokens against original text to reconstruct exact offsets.
    If text is not provided, reconstructs synthetic offsets assuming single space separator.

    Args:
        tokens: List of token strings.
        bio_tags: List of corresponding BIO tags.
        text: Optional original text.

    Returns:
        List of entity dictionaries with 'text', 'label', 'start', 'end'.
    """
    if len(tokens) != len(bio_tags):
        raise ValueError(f"Mismatch: {len(tokens)} tokens vs {len(bio_tags)} BIO tags")

    # Reconstruct token character offsets
    token_offsets: List[Tuple[int, int]] = []
    if text is not None:
        cursor = 0
        for token in tokens:
            idx = text.find(token, cursor)
            if idx == -1:
                # Fallback if whitespace/casing normalization occurred
                idx = cursor
            token_offsets.append((idx, idx + len(token)))
            cursor = idx + len(token)
    else:
        cursor = 0
        for token in tokens:
            token_offsets.append((cursor, cursor + len(token)))
            cursor += len(token) + 1

    entities: List[Dict[str, Any]] = []
    current_label: Optional[str] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None

    for i, (token, tag) in enumerate(zip(tokens, bio_tags)):
        t_start, t_end = token_offsets[i]

        if tag.startswith("B-"):
            if current_label is not None and span_start is not None and span_end is not None:
                ent_text = text[span_start:span_end] if text else " ".join(tokens)
                entities.append({
                    "text": ent_text,
                    "label": current_label,
                    "start": span_start,
                    "end": span_end,
                })
            current_label = tag[2:]
            span_start = t_start
            span_end = t_end

        elif tag.startswith("I-"):
            tag_label = tag[2:]
            if current_label == tag_label and span_start is not None:
                span_end = t_end
            else:
                # Handle orphaned I- tag as new span start
                if current_label is not None and span_start is not None and span_end is not None:
                    ent_text = text[span_start:span_end] if text else ""
                    entities.append({
                        "text": ent_text,
                        "label": current_label,
                        "start": span_start,
                        "end": span_end,
                    })
                current_label = tag_label
                span_start = t_start
                span_end = t_end

        else:  # 'O'
            if current_label is not None and span_start is not None and span_end is not None:
                ent_text = text[span_start:span_end] if text else ""
                entities.append({
                    "text": ent_text,
                    "label": current_label,
                    "start": span_start,
                    "end": span_end,
                })
                current_label = None
                span_start = None
                span_end = None

    if current_label is not None and span_start is not None and span_end is not None:
        ent_text = text[span_start:span_end] if text else ""
        entities.append({
            "text": ent_text,
            "label": current_label,
            "start": span_start,
            "end": span_end,
        })

    return entities


def export_to_doccano(
    records: List[Dict[str, Any]],
    output_path: Union[str, Path],
) -> int:
    """Exports dataset records to standard Doccano JSONLines format.

    Args:
        records: List of internal records with 'id', 'text', 'entities' or 'label', and optional 'metadata'.
        output_path: File path for destination .jsonl file.

    Returns:
        Number of records exported.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for idx, rec in enumerate(records, start=1):
            text = rec["text"]
            labels: List[List[Any]] = []

            if "entities" in rec:
                for ent in rec["entities"]:
                    labels.append([ent["start"], ent["end"], ent["label"]])
            elif "label" in rec:
                for item in rec["label"]:
                    if isinstance(item, list) and len(item) == 3:
                        labels.append(item)
                    elif isinstance(item, dict):
                        labels.append([item["start_offset"], item["end_offset"], item["label"]])

            # Sort labels by start offset
            labels.sort(key=lambda x: (x[0], x[1]))

            doccano_line = {
                "id": rec.get("id", idx),
                "text": text,
                "label": labels,
                "meta": rec.get("metadata", rec.get("meta", {})),
            }
            f.write(json.dumps(doccano_line, ensure_ascii=False) + "\n")
            count += 1

    return count


def import_from_doccano(
    input_path: Union[str, Path],
) -> List[Dict[str, Any]]:
    """Imports and validates records from a Doccano JSONLines file.

    Args:
        input_path: Path to the .jsonl file.

    Returns:
        List of standardized internal records with verified text slices.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Doccano file not found: {input_path}")

    records: List[Dict[str, Any]] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                raw = json.loads(line_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num} of {input_path}: {e}")

            text = raw.get("text", "")
            raw_labels = raw.get("label", [])
            meta = raw.get("meta", {})
            rec_id = raw.get("id", line_num)

            entities: List[Dict[str, Any]] = []
            for item in raw_labels:
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    start, end, label = int(item[0]), int(item[1]), str(item[2])
                elif isinstance(item, dict):
                    start = int(item.get("start_offset", item.get("start", 0)))
                    end = int(item.get("end_offset", item.get("end", 0)))
                    label = str(item.get("label", ""))
                else:
                    continue

                # Ensure boundaries within text length
                if start < 0 or end > len(text) or start >= end:
                    raise ValueError(
                        f"Line {line_num}: invalid offset span [{start}, {end}] for text length {len(text)}"
                    )

                slice_text = text[start:end]
                entities.append({
                    "text": slice_text,
                    "label": label,
                    "start": start,
                    "end": end,
                })

            # Sort entities by start offset
            entities.sort(key=lambda x: (x["start"], x["end"]))

            records.append({
                "id": rec_id,
                "text": text,
                "entities": entities,
                "metadata": meta,
            })

    return records
