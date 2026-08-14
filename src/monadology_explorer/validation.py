"""Validation for the curated Monadology graph dataset."""

from collections import Counter

from monadology_explorer.models import Concept, Edge, Paragraph, Theme


class DatasetValidationError(ValueError):
    """Raised when curated graph data violates the dataset contract."""


def validate_dataset(
    paragraphs: list[Paragraph],
    concepts: list[Concept],
    edges: list[Edge],
    themes: list[Theme],
) -> None:
    """Validate the complete curated dataset.

    Raises:
        DatasetValidationError: If one or more validation rules fail.
    """
    errors: list[str] = []

    _validate_paragraphs(paragraphs, errors)
    _validate_node_ids(paragraphs, concepts, errors)
    _validate_themes(paragraphs, concepts, themes, errors)
    _validate_edges(paragraphs, concepts, edges, errors)

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise DatasetValidationError(
            f"Dataset validation failed:\n{details}"
        )


def _validate_paragraphs(
    paragraphs: list[Paragraph],
    errors: list[str],
) -> None:
    numbers = [paragraph.number for paragraph in paragraphs]

    if len(paragraphs) != 90:
        errors.append(
            f"Expected exactly 90 paragraphs, found {len(paragraphs)}."
        )

    expected_numbers = set(range(1, 91))
    actual_numbers = set(numbers)

    missing = sorted(expected_numbers - actual_numbers)
    unexpected = sorted(actual_numbers - expected_numbers)

    if missing:
        errors.append(f"Missing paragraph numbers: {missing}.")

    if unexpected:
        errors.append(f"Invalid paragraph numbers: {unexpected}.")

    duplicate_numbers = sorted(
        number
        for number, count in Counter(numbers).items()
        if count > 1
    )

    if duplicate_numbers:
        errors.append(
            f"Duplicate paragraph numbers: {duplicate_numbers}."
        )

    empty_text = sorted(
        paragraph.number
        for paragraph in paragraphs
        if not paragraph.text.strip()
    )

    if empty_text:
        errors.append(f"Paragraphs with empty text: {empty_text}.")


def _validate_node_ids(
    paragraphs: list[Paragraph],
    concepts: list[Concept],
    errors: list[str],
) -> None:
    node_ids = [
        *(paragraph.id for paragraph in paragraphs),
        *(concept.id for concept in concepts),
    ]

    duplicates = sorted(
        node_id
        for node_id, count in Counter(node_ids).items()
        if count > 1
    )

    if duplicates:
        errors.append(f"Duplicate graph node IDs: {duplicates}.")

    empty_concept_names = sorted(
        concept.id
        for concept in concepts
        if not concept.name.strip()
    )

    if empty_concept_names:
        errors.append(
            f"Concepts with empty names: {empty_concept_names}."
        )

def _validate_themes(
    paragraphs: list[Paragraph],
    concepts: list[Concept],
    themes: list[Theme],
    errors: list[str],
) -> None:
    theme_ids = [theme.id for theme in themes]

    duplicate_theme_ids = sorted(
        theme_id
        for theme_id, count in Counter(theme_ids).items()
        if count > 1
    )

    if duplicate_theme_ids:
        errors.append(f"Duplicate theme IDs: {duplicate_theme_ids}.")

    known_theme_ids = set(theme_ids)
    concept_ids = {concept.id for concept in concepts}

    covered_numbers: list[int] = []

    for theme in themes:
        if not theme.starting_concepts:
            errors.append(
                f"Theme '{theme.id}' has no starting concepts."
            )

        if not 1 <= theme.paragraph_start <= theme.paragraph_end <= 90:
            errors.append(
                f"Theme '{theme.id}' has invalid paragraph range "
                f"{theme.paragraph_start}-{theme.paragraph_end}."
            )
        else:
            covered_numbers.extend(
                range(theme.paragraph_start, theme.paragraph_end + 1)
            )

        for concept_id in theme.starting_concepts:
            if concept_id not in concept_ids:
                errors.append(
                    f"Theme '{theme.id}' references unknown starting "
                    f"concept '{concept_id}'."
                )

    coverage_counts = Counter(covered_numbers)

    missing_coverage = [
        number
        for number in range(1, 91)
        if coverage_counts[number] == 0
    ]

    overlapping_coverage = [
        number
        for number in range(1, 91)
        if coverage_counts[number] > 1
    ]

    if missing_coverage:
        errors.append(
            f"Paragraphs not covered by any theme: {missing_coverage}."
        )

    if overlapping_coverage:
        errors.append(
            f"Paragraphs covered by multiple themes: "
            f"{overlapping_coverage}."
        )

    themes_by_id = {theme.id: theme for theme in themes}

    for paragraph in paragraphs:
        if paragraph.theme not in known_theme_ids:
            errors.append(
                f"Paragraph {paragraph.id} references unknown theme "
                f"'{paragraph.theme}'."
            )
            continue

        theme = themes_by_id[paragraph.theme]

        if not (
            theme.paragraph_start
            <= paragraph.number
            <= theme.paragraph_end
        ):
            errors.append(
                f"Paragraph {paragraph.id} is assigned to theme "
                f"'{paragraph.theme}' but falls outside its configured "
                f"range."
            )


def _validate_edges(
    paragraphs: list[Paragraph],
    concepts: list[Concept],
    edges: list[Edge],
    errors: list[str],
) -> None:
    node_ids = {
        *(paragraph.id for paragraph in paragraphs),
        *(concept.id for concept in concepts),
    }

    for index, edge in enumerate(edges, start=1):
        if edge.source not in node_ids:
            errors.append(
                f"Edge {index} references unknown source "
                f"'{edge.source}'."
            )

        if edge.target not in node_ids:
            errors.append(
                f"Edge {index} references unknown target "
                f"'{edge.target}'."
            )

        if not edge.relationship.strip():
            errors.append(
                f"Edge {index} has an empty relationship."
            )