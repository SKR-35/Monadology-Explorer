"""Inspect connectivity and structural quality of the curated graph."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import networkx as nx

from monadology_explorer.graph import build_graph
from monadology_explorer.loader import (
    load_concepts,
    load_edges,
    load_paragraphs,
    load_themes,
)
from monadology_explorer.validation import validate_dataset

DATA_DIR = Path("data")


def node_label(graph: nx.Graph, node_id: str) -> str:
    attributes = graph.nodes[node_id]
    return f"{node_id} ({attributes['label']})"


def main() -> None:
    paragraphs = load_paragraphs(DATA_DIR / "paragraphs.json")
    concepts = load_concepts(DATA_DIR / "concepts.json")
    edges = load_edges(DATA_DIR / "edges.json")
    themes = load_themes(DATA_DIR / "themes.json")

    validate_dataset(paragraphs, concepts, edges, themes)
    graph = build_graph(paragraphs, concepts, edges)

    components = sorted(
        nx.connected_components(graph),
        key=len,
        reverse=True,
    )

    print("Monadology Explorer — Graph QA")
    print("=" * 56)
    print(f"Nodes               : {graph.number_of_nodes()}")
    print(f"Edges               : {graph.number_of_edges()}")
    print(f"Connected components: {len(components)}")

    for index, component in enumerate(components, start=1):
        paragraph_count = sum(
            graph.nodes[node]["node_type"] == "paragraph"
            for node in component
        )
        concept_count = len(component) - paragraph_count

        print(f"\nComponent {index}")
        print("-" * 56)
        print(f"Nodes      : {len(component)}")
        print(f"Paragraphs : {paragraph_count}")
        print(f"Concepts   : {concept_count}")

        if index > 1 or len(component) <= 20:
            print("Members:")
            for node_id in sorted(component):
                print(f"  {node_label(graph, node_id)}")

    print("\nArticulation points")
    print("-" * 56)
    articulation_points = sorted(
        nx.articulation_points(graph),
        key=lambda node: (-graph.degree[node], node),
    )
    if articulation_points:
        for node_id in articulation_points[:20]:
            print(
                f"{node_label(graph, node_id):<48} "
                f"degree={graph.degree[node_id]}"
            )
    else:
        print("None")

    print("\nConcept degree distribution")
    print("-" * 56)
    concept_degrees = Counter(
        graph.degree[node_id]
        for node_id, attributes in graph.nodes(data=True)
        if attributes["node_type"] == "concept"
    )
    for degree in sorted(concept_degrees):
        print(f"degree {degree:>2}: {concept_degrees[degree]:>2} concepts")

    print("\nPotential hubs")
    print("-" * 56)
    concept_nodes = [
        node_id
        for node_id, attributes in graph.nodes(data=True)
        if attributes["node_type"] == "concept"
    ]
    ranked = sorted(
        concept_nodes,
        key=lambda node: (-graph.degree[node], node),
    )
    for node_id in ranked[:15]:
        print(
            f"{node_label(graph, node_id):<48} "
            f"degree={graph.degree[node_id]}"
        )


if __name__ == "__main__":
    main()
