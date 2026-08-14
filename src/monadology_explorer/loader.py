"""Load repository-controlled graph data."""

import json
from pathlib import Path
from typing import Any

from monadology_explorer.models import Concept, Edge, Paragraph, Theme


class DataLoadError(ValueError):
    """Raised when curated project data cannot be loaded."""


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise DataLoadError(f"Data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataLoadError(f"Invalid JSON in data file: {path}") from exc


def load_paragraphs(path: Path) -> list[Paragraph]:
    data = _load_json(path)

    try:
        return [Paragraph(**item) for item in data]
    except (TypeError, KeyError) as exc:
        raise DataLoadError(f"Invalid paragraph data in: {path}") from exc


def load_concepts(path: Path) -> list[Concept]:
    data = _load_json(path)

    try:
        return [Concept(**item) for item in data]
    except (TypeError, KeyError) as exc:
        raise DataLoadError(f"Invalid concept data in: {path}") from exc


def load_edges(path: Path) -> list[Edge]:
    data = _load_json(path)

    try:
        return [Edge(**item) for item in data]
    except (TypeError, KeyError) as exc:
        raise DataLoadError(f"Invalid edge data in: {path}") from exc


def load_themes(path: Path) -> list[Theme]:
    data = _load_json(path)

    try:
        return [
            Theme(
                id=item["id"],
                name=item["name"],
                paragraph_start=item["paragraph_start"],
                paragraph_end=item["paragraph_end"],
                starting_concepts=tuple(item["starting_concepts"]),
            )
            for item in data
        ]
    except (TypeError, KeyError) as exc:
        raise DataLoadError(f"Invalid theme data in: {path}") from exc