from pathlib import Path

from monadology_explorer.graph import (
    build_graph,
    forceatlas2_layout,
)
from monadology_explorer.loader import (
    load_concepts,
    load_edges,
    load_paragraphs,
)

DATA_DIR = Path("data")


def test_forceatlas2_layout_is_deterministic_for_same_seed():
    graph = build_graph(
        load_paragraphs(DATA_DIR / "paragraphs.json"),
        load_concepts(DATA_DIR / "concepts.json"),
        load_edges(DATA_DIR / "edges.json"),
    )

    first = forceatlas2_layout(graph, seed=42)
    second = forceatlas2_layout(graph, seed=42)

    assert first == second
    assert set(first) == set(graph.nodes)