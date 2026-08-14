"""Domain models for the curated Monadology graph."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Paragraph:
    id: str
    number: int
    text: str
    theme: str


@dataclass(frozen=True, slots=True)
class Concept:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    relationship: str
    note: str | None = None


@dataclass(frozen=True, slots=True)
class Theme:
    id: str
    name: str
    paragraph_start: int
    paragraph_end: int
    starting_concepts: tuple[str, ...]