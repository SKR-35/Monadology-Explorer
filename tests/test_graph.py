import networkx as nx

from monadology_explorer.graph import (
    NODE_TYPE_CONCEPT,
    NODE_TYPE_PARAGRAPH,
    build_graph,
    spring_layout,
)
from monadology_explorer.models import Concept, Edge, Paragraph


def sample_graph():
    paragraphs = [
        Paragraph(
            id="p001",
            number=1,
            text="Example paragraph",
            theme="nature_of_monads",
        )
    ]
    concepts = [
        Concept(id="monad", name="Monad"),
        Concept(id="perception", name="Perception"),
    ]
    edges = [
        Edge(
            source="p001",
            target="monad",
            relationship="discusses",
        ),
        Edge(
            source="monad",
            target="perception",
            relationship="related to",
        ),
    ]

    return build_graph(paragraphs, concepts, edges)


def test_build_graph_preserves_node_types_and_metadata():
    graph = sample_graph()

    assert graph.nodes["p001"]["node_type"] == NODE_TYPE_PARAGRAPH
    assert graph.nodes["p001"]["number"] == 1
    assert graph.nodes["monad"]["node_type"] == NODE_TYPE_CONCEPT
    assert graph.nodes["monad"]["label"] == "Monad"


def test_build_graph_preserves_relationship_metadata():
    graph = sample_graph()

    assert graph.edges["p001", "monad"]["relationship"] == "discusses"
    assert graph.edges["monad", "perception"]["relationship"] == "related to"


def test_build_graph_contains_expected_topology():
    graph = sample_graph()

    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2
    assert nx.is_connected(graph)


def test_spring_layout_is_deterministic_for_same_seed():
    graph = sample_graph()

    first = spring_layout(graph, seed=42)
    second = spring_layout(graph, seed=42)

    assert first == second
