import networkx as nx
import pytest

from monadology_explorer.exploration import (
    adjacent_paragraph_id,
    connected_relationships,
    discovery_counts,
    expand_one_hop,
    initial_visible_nodes,
    reveal_node,
    search_nodes,
)
from monadology_explorer.models import Concept, Paragraph, Theme


def sample_graph():
    graph = nx.Graph()
    graph.add_node("monad", label="Monad", node_type="concept")
    graph.add_node("perception", label="Perception", node_type="concept")
    graph.add_node("p001", label="§1", node_type="paragraph")
    graph.add_edge("monad", "p001", relationship="discusses")
    graph.add_edge("monad", "perception", relationship="related to")
    return graph


def test_initial_visible_nodes_uses_theme_starting_concepts():
    theme = Theme(
        id="nature",
        name="Nature",
        paragraph_start=1,
        paragraph_end=18,
        starting_concepts=("monad", "perception"),
    )

    assert initial_visible_nodes(theme) == {"monad", "perception"}


def test_expand_one_hop_preserves_discovered_nodes():
    graph = sample_graph()

    visible = expand_one_hop(
        graph,
        {"perception"},
        "monad",
    )

    assert visible == {"perception", "monad", "p001"}


def test_expand_one_hop_is_idempotent():
    graph = sample_graph()

    first = expand_one_hop(graph, {"monad"}, "monad")
    second = expand_one_hop(graph, first, "monad")

    assert second == first


def test_reveal_node_does_not_expand_neighbors():
    graph = sample_graph()

    visible = reveal_node(graph, {"perception"}, "p001")

    assert visible == {"perception", "p001"}


def test_search_nodes_supports_paragraph_number_forms():
    paragraphs = [
        Paragraph(
            id="p035",
            number=35,
            text="Example",
            theme="truth_reason_god",
        )
    ]

    assert search_nodes("§35", paragraphs, []) == ["p035"]
    assert search_nodes("35", paragraphs, []) == ["p035"]


def test_search_nodes_rejects_out_of_range_paragraph():
    assert search_nodes("91", [], []) == []


def test_search_nodes_matches_concepts_case_insensitively():
    concepts = [
        Concept(id="perception", name="Perception"),
        Concept(
            id="unconscious_perception",
            name="Unconscious Perception",
        ),
    ]

    assert search_nodes("perception", [], concepts) == [
        "perception",
        "unconscious_perception",
    ]


def test_adjacent_paragraph_id_respects_boundaries():
    assert adjacent_paragraph_id(1, direction=-1) is None
    assert adjacent_paragraph_id(1, direction=1) == "p002"
    assert adjacent_paragraph_id(90, direction=-1) == "p089"
    assert adjacent_paragraph_id(90, direction=1) is None


def test_adjacent_paragraph_id_rejects_invalid_direction():
    with pytest.raises(ValueError, match="direction must be -1 or 1"):
        adjacent_paragraph_id(35, direction=0)


def test_connected_relationships_returns_semantic_labels():
    graph = sample_graph()

    relationships = connected_relationships(graph, "monad")

    assert set(relationships) == {
        ("p001", "§1", "discusses"),
        ("perception", "Perception", "related to"),
    }


def test_discovery_counts_separates_paragraphs_and_concepts():
    graph = sample_graph()

    assert discovery_counts(
        graph,
        {"monad", "perception", "p001"},
    ) == (1, 2)
