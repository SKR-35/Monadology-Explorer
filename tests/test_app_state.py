from types import SimpleNamespace

import networkx as nx
import pytest

import app


class SessionState(dict):
    """Minimal Streamlit-like session state for application state tests."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def session_state(monkeypatch):
    state = SessionState()
    fake_streamlit = SimpleNamespace(session_state=state)
    monkeypatch.setattr(app, "st", fake_streamlit)
    return state


def test_initialize_session_sets_exploration_defaults(session_state):
    app.initialize_session(
        "nature_of_monads",
        {"monad", "perception"},
    )

    assert session_state.active_theme_id == "nature_of_monads"
    assert session_state.visible_nodes == {"monad", "perception"}
    assert session_state.selected_node is None
    assert session_state.search_query == ""
    assert session_state.search_result is None


def test_initialize_session_does_not_overwrite_existing_exploration(
    session_state,
):
    session_state.update(
        {
            "active_theme_id": "nature_of_monads",
            "visible_nodes": {"monad", "p001"},
            "selected_node": "p001",
            "search_query": "Monad",
            "search_result": "monad",
        }
    )

    app.initialize_session(
        "truth_reason_god",
        {"god"},
    )

    assert session_state.active_theme_id == "nature_of_monads"
    assert session_state.visible_nodes == {"monad", "p001"}
    assert session_state.selected_node == "p001"
    assert session_state.search_query == "Monad"
    assert session_state.search_result == "monad"


def test_switch_theme_starts_fresh_exploration(session_state):
    session_state.update(
        {
            "active_theme_id": "nature_of_monads",
            "visible_nodes": {"monad", "perception", "p001"},
            "selected_node": "p001",
            "search_query": "perception",
            "search_result": "perception",
        }
    )

    app.switch_theme(
        "truth_reason_god",
        {"god", "necessary_truth"},
    )

    assert session_state.active_theme_id == "truth_reason_god"
    assert session_state.visible_nodes == {"god", "necessary_truth"}
    assert session_state.selected_node is None
    assert session_state.search_query == ""
    assert session_state.search_result is None


def test_switching_to_current_theme_preserves_exploration(session_state):
    session_state.update(
        {
            "active_theme_id": "nature_of_monads",
            "visible_nodes": {"monad", "p001"},
            "selected_node": "p001",
            "search_query": "Monad",
            "search_result": "monad",
        }
    )

    app.switch_theme(
        "nature_of_monads",
        {"monad"},
    )

    assert session_state.visible_nodes == {"monad", "p001"}
    assert session_state.selected_node == "p001"
    assert session_state.search_query == "Monad"
    assert session_state.search_result == "monad"


def test_reset_exploration_restores_starting_nodes(session_state):
    session_state.update(
        {
            "visible_nodes": {"monad", "perception", "p001"},
            "selected_node": "p001",
            "search_query": "perception",
            "search_result": "perception",
        }
    )

    app.reset_exploration({"monad", "simple_substance"})

    assert session_state.visible_nodes == {"monad", "simple_substance"}
    assert session_state.selected_node is None
    assert session_state.search_query == ""
    assert session_state.search_result is None


def test_select_and_reveal_preserves_existing_nodes(session_state):
    graph = nx.Graph()
    graph.add_nodes_from(["monad", "perception", "p001"])
    graph.add_edge("monad", "p001")
    graph.add_edge("perception", "p001")

    session_state.visible_nodes = {"monad"}

    app.select_and_reveal(graph, "p001")

    assert session_state.visible_nodes == {"monad", "p001"}
    assert session_state.selected_node == "p001"


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        (
            SimpleNamespace(
                selection=SimpleNamespace(
                    points=[{"customdata": ["monad", 5, "Monad", ""]}]
                )
            ),
            "monad",
        ),
        (
            {
                "selection": {
                    "points": [
                        {"customdata": ["p035", 3, "§35", "Paragraph text"]}
                    ]
                }
            },
            "p035",
        ),
        ({"selection": {"points": []}}, None),
        ({"selection": {"points": [{}]}}, None),
        ({"selection": {"points": [{"customdata": []}]}}, None),
        ({"selection": {"points": [{"customdata": [123]}]}}, None),
        ({}, None),
        (None, None),
    ],
)
def test_selected_from_plotly_event(event, expected):
    assert app.selected_from_plotly_event(event) == expected