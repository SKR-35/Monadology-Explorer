import json

import pytest

from monadology_explorer.loader import (
    DataLoadError,
    load_concepts,
    load_edges,
    load_paragraphs,
    load_themes,
)


def write_json(path, data):
    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def test_load_paragraphs(tmp_path):
    path = tmp_path / "paragraphs.json"

    write_json(
        path,
        [
            {
                "id": "p001",
                "number": 1,
                "text": "Example",
                "theme": "nature_of_monads",
            }
        ],
    )

    paragraphs = load_paragraphs(path)

    assert len(paragraphs) == 1
    assert paragraphs[0].id == "p001"
    assert paragraphs[0].number == 1


def test_load_concepts(tmp_path):
    path = tmp_path / "concepts.json"

    write_json(
        path,
        [{"id": "monad", "name": "Monad"}],
    )

    concepts = load_concepts(path)

    assert concepts[0].name == "Monad"


def test_load_edges(tmp_path):
    path = tmp_path / "edges.json"

    write_json(
        path,
        [
            {
                "source": "monad",
                "target": "p001",
                "relationship": "discusses",
                "note": None,
            }
        ],
    )

    edges = load_edges(path)

    assert edges[0].source == "monad"
    assert edges[0].target == "p001"


def test_load_themes_converts_starting_concepts_to_tuple(tmp_path):
    path = tmp_path / "themes.json"

    write_json(
        path,
        [
            {
                "id": "nature_of_monads",
                "name": "The Nature of Monads",
                "paragraph_start": 1,
                "paragraph_end": 18,
                "starting_concepts": ["monad", "perception"],
            }
        ],
    )

    themes = load_themes(path)

    assert themes[0].starting_concepts == ("monad", "perception")


def test_missing_file_raises_data_load_error(tmp_path):
    path = tmp_path / "missing.json"

    with pytest.raises(DataLoadError, match="Data file not found"):
        load_paragraphs(path)


def test_invalid_json_raises_data_load_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(DataLoadError, match="Invalid JSON"):
        load_paragraphs(path)
        
def test_paragraph_missing_required_field_raises_data_load_error(tmp_path):
    path = tmp_path / "paragraphs.json"
    write_json(
        path,
        [
            {
                "id": "p001",
                "number": 1,
                "theme": "nature_of_monads",
            }
        ],
    )

    with pytest.raises(DataLoadError):
        load_paragraphs(path)


def test_edge_with_malformed_record_raises_data_load_error(tmp_path):
    path = tmp_path / "edges.json"
    write_json(
        path,
        [
            {
                "source": "monad",
                "target": "p001",
                # relationship deliberately omitted
            }
        ],
    )

    with pytest.raises(DataLoadError):
        load_edges(path)