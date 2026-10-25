"""R6 — every phrasing we expect on stage or in the test set extracts the right object."""

import csv
from pathlib import Path

import pytest

from remem.answer.extract import extract

TEST_SET = Path(__file__).resolve().parents[1] / "eval" / "test_set.csv"
RECALL_IDS = {"T37", "T38", "T39", "T40"}
SYNONYMS = {"keychain": "keys"}  # phrasings that share no word with expected_object


@pytest.mark.parametrize(
    ("question", "kind", "obj"),
    [
        # demo rows 2-5, typed and dictated
        ("Where are my keys?", "find", "keys"),
        ("where are my keys.", "find", "keys"),
        ("Where are the sunglasses?", "find", "sunglasses"),
        ("Where is my passport?", "find", "passport"),
        ("When was I at the whiteboard?", "recall", "whiteboard"),
        # phrasings from the test set and iOS quirks
        ("Where’s my wallet?", "find", "wallet"),
        ("wheres my wallet", "find", "wallet"),
        ("Have you seen my keychain?", "find", "keychain"),
        ("Where did I leave my earbuds case?", "find", "earbuds case"),
        ("where did I put my mug", "find", "mug"),
        ("Where is my water bottle now?", "find", "water bottle"),
        ("where are my keys at", "find", "keys"),
        ("Where's my phone charger again?", "find", "phone charger"),
        ("find my notebook", "find", "notebook"),
        ("keys", "find", "keys"),
    ],
)
def test_extract(question: str, kind: str, obj: str) -> None:
    query = extract(question)
    assert query is not None
    assert (query.kind, query.object) == (kind, obj)
    assert query.text == f"a photo of {obj}"


@pytest.mark.parametrize("question", ["", "   ", "?", "where is my", "where are my ?"])
def test_extract_nothing(question: str) -> None:
    assert extract(question) is None


def _rows() -> list[dict[str, str]]:
    with TEST_SET.open(newline="") as f:
        return list(csv.DictReader(f))


def test_test_set_shape() -> None:
    rows = _rows()
    assert len(rows) == 40
    assert [r["id"] for r in rows] == [f"T{i:02d}" for i in range(1, 41)]
    assert sum(r["expected_band"] == "none" for r in rows) == 8


@pytest.mark.parametrize("row", _rows(), ids=lambda r: r["id"])
def test_test_set_extracts(row: dict[str, str]) -> None:
    query = extract(row["query"])
    assert query is not None
    assert query.kind == ("recall" if row["id"] in RECALL_IDS else "find")
    # Synonyms ("keychain" for keys, "coffee mug" for mug) are left to the embedding,
    # so the extracted object only has to share a word with the expected one.
    obj = SYNONYMS.get(query.object, query.object)
    assert set(obj.split()) & set(row["expected_object"].split())
