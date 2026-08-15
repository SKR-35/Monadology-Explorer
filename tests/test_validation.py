from dataclasses import replace

import pytest

from monadology_explorer.models import Concept, Edge, Paragraph, Theme
from monadology_explorer.validation import (
    DatasetValidationError,
    validate_dataset,
)


def make_valid_dataset():
    paragraphs = [
        Paragraph(
            id=f"p{number:03d}",
            number=number,
            text=f"Paragraph {number}",
            theme="theme_1",
        )
        for number in range(1, 91)
    ]

    concepts = [
        Concept(id="monad", name="Monad"),
    ]

    edges = [
        Edge(
            source="monad",
            target="p001",
            relationship="discusses",
        ),
    ]

    themes = [
        Theme(
            id="theme_1",
            name="Test Theme",
            paragraph_start=1,
            paragraph_end=90,
            starting_concepts=("monad",),
        ),
    ]

    return paragraphs, concepts, edges, themes


def test_valid_dataset_passes():
    validate_dataset(*make_valid_dataset())


def test_missing_paragraph_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    paragraphs.pop()

    with pytest.raises(
        DatasetValidationError,
        match="Expected exactly 90 paragraphs",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_duplicate_node_id_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    concepts.append(Concept(id="p001", name="Duplicate"))

    with pytest.raises(
        DatasetValidationError,
        match="Duplicate graph node IDs",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_edge_with_unknown_target_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    edges.append(
        Edge(
            source="monad",
            target="does_not_exist",
            relationship="discusses",
        )
    )

    with pytest.raises(
        DatasetValidationError,
        match="unknown target",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_theme_without_starting_concepts_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    themes[0] = Theme(
        id="theme_1",
        name="Test Theme",
        paragraph_start=1,
        paragraph_end=90,
        starting_concepts=(),
    )

    with pytest.raises(
        DatasetValidationError,
        match="has no starting concepts",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)
        
def test_paragraph_outside_assigned_theme_range_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()

    themes[0] = Theme(
        id="theme_1",
        name="Test Theme",
        paragraph_start=2,
        paragraph_end=90,
        starting_concepts=("monad",),
    )

    with pytest.raises(
        DatasetValidationError,
        match="Paragraphs not covered by any theme",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)
        
def test_empty_paragraph_text_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    paragraphs[0] = replace(paragraphs[0], text="   ")

    with pytest.raises(
        DatasetValidationError,
        match="Paragraphs with empty text",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_duplicate_paragraph_number_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    paragraphs[-1] = replace(
        paragraphs[-1],
        number=89,
    )

    with pytest.raises(
        DatasetValidationError,
        match="Duplicate paragraph numbers",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_unknown_theme_on_paragraph_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    paragraphs[0] = replace(
        paragraphs[0],
        theme="does_not_exist",
    )

    with pytest.raises(
        DatasetValidationError,
        match="references unknown theme",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_theme_with_unknown_starting_concept_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    themes[0] = replace(
        themes[0],
        starting_concepts=("monad", "does_not_exist"),
    )

    with pytest.raises(
        DatasetValidationError,
        match="references unknown starting concept",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_overlapping_theme_ranges_are_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()

    themes[:] = [
        Theme(
            id="theme_1",
            name="First Theme",
            paragraph_start=1,
            paragraph_end=50,
            starting_concepts=("monad",),
        ),
        Theme(
            id="theme_2",
            name="Second Theme",
            paragraph_start=50,
            paragraph_end=90,
            starting_concepts=("monad",),
        ),
    ]

    with pytest.raises(
        DatasetValidationError,
        match="Paragraphs covered by multiple themes",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_edge_with_unknown_source_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    edges.append(
        Edge(
            source="does_not_exist",
            target="p001",
            relationship="discusses",
        )
    )

    with pytest.raises(
        DatasetValidationError,
        match="unknown source",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)


def test_edge_with_empty_relationship_is_rejected():
    paragraphs, concepts, edges, themes = make_valid_dataset()
    edges.append(
        Edge(
            source="monad",
            target="p001",
            relationship="   ",
        )
    )

    with pytest.raises(
        DatasetValidationError,
        match="has an empty relationship",
    ):
        validate_dataset(paragraphs, concepts, edges, themes)