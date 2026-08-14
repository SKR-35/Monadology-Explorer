"""Pure exploration logic for Monadology Explorer."""

from __future__ import annotations

import re
from collections.abc import Iterable

import networkx as nx

from monadology_explorer.models import Concept, Paragraph, Theme

_PARAGRAPH_QUERY = re.compile(r"^\s*§?\s*(\d{1,2})\s*$")


def initial_visible_nodes(theme: Theme) -> set[str]:
    """Return the curated starting concepts for a theme."""
    return set(theme.starting_concepts)


def expand_one_hop(
    graph: nx.Graph,
    visible_nodes: Iterable[str],
    node_id: str,
) -> set[str]:
    """Reveal a node and its immediate neighbors without hiding prior discoveries."""
    if node_id not in graph:
        raise KeyError(f"Unknown graph node: {node_id}")

    visible = set(visible_nodes)
    visible.add(node_id)
    visible.update(graph.neighbors(node_id))
    return visible


def reveal_node(
    graph: nx.Graph,
    visible_nodes: Iterable[str],
    node_id: str,
) -> set[str]:
    """Reveal one known node while preserving the current exploration."""
    if node_id not in graph:
        raise KeyError(f"Unknown graph node: {node_id}")

    visible = set(visible_nodes)
    visible.add(node_id)
    return visible


def search_nodes(
    query: str,
    paragraphs: Iterable[Paragraph],
    concepts: Iterable[Concept],
) -> list[str]:
    """Search paragraphs by number or concepts by case-insensitive name."""
    normalized = query.strip()
    if not normalized:
        return []

    paragraph_match = _PARAGRAPH_QUERY.match(normalized)
    if paragraph_match:
        number = int(paragraph_match.group(1))
        if 1 <= number <= 90:
            return [f"p{number:03d}"]
        return []

    lowered = normalized.casefold()
    matches = [
        concept
        for concept in concepts
        if lowered in concept.name.casefold()
    ]

    return [
        concept.id
        for concept in sorted(
            matches,
            key=lambda concept: (
                concept.name.casefold() != lowered,
                concept.name.casefold(),
            ),
        )
    ]


def adjacent_paragraph_id(
    number: int,
    *,
    direction: int,
) -> str | None:
    """Return the previous/next canonical paragraph identifier."""
    if direction not in {-1, 1}:
        raise ValueError("direction must be -1 or 1")

    candidate = number + direction
    if not 1 <= candidate <= 90:
        return None
    return f"p{candidate:03d}"


def connected_relationships(
    graph: nx.Graph,
    node_id: str,
) -> list[tuple[str, str, str]]:
    """Return connected node ID, label, and relationship for a node."""
    if node_id not in graph:
        raise KeyError(f"Unknown graph node: {node_id}")

    rows: list[tuple[str, str, str]] = []

    for neighbor_id in graph.neighbors(node_id):
        edge = graph.edges[node_id, neighbor_id]
        rows.append(
            (
                neighbor_id,
                graph.nodes[neighbor_id]["label"],
                edge["relationship"],
            )
        )

    return sorted(rows, key=lambda row: (row[1].casefold(), row[0]))


def discovery_counts(
    graph: nx.Graph,
    visible_nodes: Iterable[str],
) -> tuple[int, int]:
    """Return visible paragraph and concept counts."""
    paragraphs = 0
    concepts = 0

    for node_id in set(visible_nodes):
        if node_id not in graph:
            continue

        node_type = graph.nodes[node_id]["node_type"]
        if node_type == "paragraph":
            paragraphs += 1
        elif node_type == "concept":
            concepts += 1

    return paragraphs, concepts
