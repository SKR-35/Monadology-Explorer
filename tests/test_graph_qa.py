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


def build_complete_graph():
    return build_graph(
        load_paragraphs(DATA_DIR / "paragraphs.json"),
        load_concepts(DATA_DIR / "concepts.json"),
        load_edges(DATA_DIR / "edges.json"),
    )


def test_complete_curated_graph_has_no_isolated_nodes():
    graph = build_complete_graph()

    assert list(nx.isolates(graph)) == []
   
    
def test_complete_curated_graph_is_connected():
    graph = build_complete_graph()

    assert nx.number_connected_components(graph) == 1
    
    
def test_complete_curated_dataset_satisfies_validation_contract():
    paragraphs = load_paragraphs(DATA_DIR / "paragraphs.json")
    concepts = load_concepts(DATA_DIR / "concepts.json")
    edges = load_edges(DATA_DIR / "edges.json")
    themes = load_themes(DATA_DIR / "themes.json")

    validate_dataset(paragraphs, concepts, edges, themes)