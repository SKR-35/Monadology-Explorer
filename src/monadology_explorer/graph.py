"""Graph construction and layout helpers for Monadology Explorer."""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

from monadology_explorer.models import Concept, Edge, Paragraph

NODE_TYPE_PARAGRAPH = "paragraph"
NODE_TYPE_CONCEPT = "concept"


def build_graph(
    paragraphs: Iterable[Paragraph],
    concepts: Iterable[Concept],
    edges: Iterable[Edge],
) -> nx.Graph:
    """Build the curated Monadology graph.

    The graph is intentionally undirected for v1 exploration because the
    current semantic relations describe association/development rather than
    a formal causal or proof direction.
    """
    graph = nx.Graph()

    for paragraph in paragraphs:
        graph.add_node(
            paragraph.id,
            node_type=NODE_TYPE_PARAGRAPH,
            label=f"§{paragraph.number}",
            number=paragraph.number,
            text=paragraph.text,
            theme=paragraph.theme,
        )

    for concept in concepts:
        graph.add_node(
            concept.id,
            node_type=NODE_TYPE_CONCEPT,
            label=concept.name,
            name=concept.name,
        )

    for edge in edges:
        graph.add_edge(
            edge.source,
            edge.target,
            relationship=edge.relationship,
            note=edge.note,
        )

    return graph


def spring_layout(
    graph: nx.Graph,
    *,
    seed: int = 42,
) -> dict[str, tuple[float, float]]:
    """Return deterministic spring-layout coordinates."""
    raw_positions = nx.spring_layout(graph, seed=seed)

    return {
        node_id: (float(position[0]), float(position[1]))
        for node_id, position in raw_positions.items()
    }


def forceatlas2_layout(
    graph: nx.Graph,
    *,
    seed: int = 42,
) -> dict[str, tuple[float, float]]:
    """Return a deterministic Gephi-style ForceAtlas2 layout.

    A deterministic spring layout provides stable initial coordinates before
    ForceAtlas2 refines the network structure.
    """
    initial_positions = nx.spring_layout(
        graph,
        seed=seed,
        iterations=50,
    )

    raw_positions = nx.forceatlas2_layout(
        graph,
        pos=initial_positions,
        max_iter=500,
        scaling_ratio=3.0,
        gravity=0.9,
        strong_gravity=False,
        linlog=False,
        seed=seed,
    )

    return {
        node_id: (float(position[0]), float(position[1]))
        for node_id, position in raw_positions.items()
    }


def node_degree_summary(
    graph: nx.Graph,
    *,
    limit: int = 15,
) -> list[tuple[str, int]]:
    """Return highest-degree nodes for inspection."""
    ranked = sorted(
        graph.degree,
        key=lambda item: (-item[1], item[0]),
    )
    return ranked[:limit]
