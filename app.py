"""Streamlit application for Monadology Explorer."""

from __future__ import annotations

import logging
from html import escape
from pathlib import Path
from textwrap import wrap

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from monadology_explorer.exploration import (
    adjacent_paragraph_id,
    connected_relationships,
    discovery_counts,
    expand_one_hop,
    initial_visible_nodes,
    reveal_node,
    search_nodes,
)
from monadology_explorer.graph import (
    NODE_TYPE_CONCEPT,
    NODE_TYPE_PARAGRAPH,
    build_graph,
    forceatlas2_layout,
)
from monadology_explorer.loader import (
    DataLoadError,
    load_concepts,
    load_edges,
    load_paragraphs,
    load_themes,
)
from monadology_explorer.validation import (
    DatasetValidationError,
    validate_dataset,
)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

DATA_DIR = Path("data")


DEFAULT_THEME_COLORS = {
    "nature_of_monads": "#6BAED6",
    "natural_psychic_hierarchy": "#74C476",
    "truth_reason_god": "#9E9AC8",
    "creation_harmony": "#FD8D3C",
    "bodies_souls_nature": "#E377C2",
    "conclusion": "#FDD0A2",
}


def contrast_text_color(hex_color: str) -> str:
    """Return a readable light/dark foreground for a hexadecimal background."""
    value = hex_color.lstrip("#")
    red, green, blue = (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )
    luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
    return "#111111" if luminance > 160 else "#F7F7F7"


def initialize_appearance(themes) -> None:
    defaults = {
        "concept_color": "#F6A6A6",
        "paragraph_color": "#FF4B4B",
        "edge_color": "#6E7D91",
        "background_color": "#c6d0e6",
        "dashboard_background_color": "#1F2937",
        "selected_edge_color": "#E63946",
        "theme_coloring": True,
        "graph_fit_nonce": 0,
        "fit_dashboard": True,
    }

    appearance_defaults_version = 3

    if (
        st.session_state.get("appearance_defaults_version")
        != appearance_defaults_version
    ):
        for key, value in defaults.items():
            st.session_state[key] = value

        for theme in themes:
            st.session_state[f"theme_color_{theme.id}"] = (
                DEFAULT_THEME_COLORS.get(theme.id, "#BDBDBD")
            )

        st.session_state.appearance_defaults_version = (
            appearance_defaults_version
        )

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    for theme in themes:
        key = f"theme_color_{theme.id}"
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_THEME_COLORS.get(
                theme.id,
                "#BDBDBD",
            )


def reset_appearance(themes) -> None:
    st.session_state.concept_color = "#F6A6A6"
    st.session_state.paragraph_color = "#FF4B4B"
    st.session_state.edge_color = "#6E7D91"
    st.session_state.background_color = "#c6d0e6"
    st.session_state.dashboard_background_color = "#1F2937"
    st.session_state.selected_edge_color = "#E63946"
    st.session_state.theme_coloring = True

    for theme in themes:
        st.session_state[f"theme_color_{theme.id}"] = (
            DEFAULT_THEME_COLORS.get(theme.id, "#BDBDBD")
        )



def apply_dashboard_background() -> None:
    """Apply runtime dashboard colors and derive all control surfaces from it."""
    background = st.session_state.dashboard_background_color
    foreground = contrast_text_color(background)

    def mix_hex(base: str, target: str, amount: float) -> str:
        """Blend two hex colors; amount=0 keeps base, amount=1 gives target."""
        base_value = base.lstrip("#")
        target_value = target.lstrip("#")

        base_rgb = [
            int(base_value[index : index + 2], 16)
            for index in (0, 2, 4)
        ]
        target_rgb = [
            int(target_value[index : index + 2], 16)
            for index in (0, 2, 4)
        ]

        mixed = [
            round(start + ((end - start) * amount))
            for start, end in zip(base_rgb, target_rgb, strict=True)
        ]
        return "#" + "".join(f"{channel:02X}" for channel in mixed)

    # Controls should always be visibly distinct from the dashboard, but they
    # must follow it automatically when the user changes the dashboard color.
    if foreground == "#F7F7F7":
        control_background = mix_hex(background, "#FFFFFF", 0.10)
        control_hover = mix_hex(background, "#FFFFFF", 0.16)
        control_border = mix_hex(background, "#FFFFFF", 0.22)
        placeholder = mix_hex(foreground, background, 0.34)
    else:
        control_background = mix_hex(background, "#000000", 0.06)
        control_hover = mix_hex(background, "#000000", 0.10)
        control_border = mix_hex(background, "#000000", 0.16)
        placeholder = mix_hex(foreground, background, 0.42)

    st.markdown(
        f"""
        <style>
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background-color: {background} !important;
            color: {foreground} !important;
        }}

        /* Remove Streamlit's remaining white header / toolbar strip. */
        [data-testid="stHeader"],
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {{
            background-color: {background} !important;
            color: {foreground} !important;
        }}

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div {{
            background-color: {background} !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {foreground};
        }}

        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp p,
        .stApp label,
        .stApp span {{
            color: {foreground};
        }}

        /*
        Streamlit's exact wrapper markup varies by widget/version, so style
        both Streamlit test IDs and BaseWeb primitives. All colors are derived
        from the selected dashboard background rather than hard-coded.
        */
        .stButton > button,
        [data-testid="stBaseButton-secondary"],
        [data-testid="stBaseButton-primary"],
        [data-testid="stExpander"],
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        [data-testid="stTextInput"] > div > div {{
            background-color: {control_background} !important;
            border-color: {control_border} !important;
            color: {foreground} !important;
        }}

        .stButton > button *,
        [data-testid="stBaseButton-secondary"] *,
        [data-testid="stBaseButton-primary"] *,
        [data-testid="stExpander"] *,
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="base-input"] * {{
            color: {foreground} !important;
        }}

        /* All selectboxes, including search results, follow the dashboard palette. */
        [data-testid="stSelectbox"] div[data-baseweb="select"],
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
        [data-testid="stSelectbox"] [role="combobox"],
        div[data-baseweb="select"] [role="combobox"] {{
            background-color: {control_background} !important;
            border-color: {control_border} !important;
            box-shadow: none !important;
            color: {foreground} !important;
        }}

        [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
        [data-testid="stSelectbox"] [role="combobox"]:focus,
        [data-testid="stSelectbox"] [role="combobox"]:focus-visible {{
            background-color: {control_background} !important;
            border-color: {control_border} !important;
            box-shadow: 0 0 0 1px {control_border} !important;
            outline: none !important;
        }}

        div[data-baseweb="select"] input,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg,
        [data-testid="stSelectbox"] span,
        [data-testid="stSelectbox"] svg {{
            color: {foreground} !important;
            fill: {foreground} !important;
            -webkit-text-fill-color: {foreground} !important;
        }}

        /* Search/text inputs: keep both wrapper and actual input transparent. */
        [data-testid="stTextInput"] input,
        .stTextInput input,
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input {{
            background-color: transparent !important;
            color: {foreground} !important;
            -webkit-text-fill-color: {foreground} !important;
            caret-color: {foreground} !important;
        }}

        [data-testid="stTextInput"] input::placeholder,
        .stTextInput input::placeholder,
        div[data-baseweb="input"] input::placeholder,
        div[data-baseweb="base-input"] input::placeholder {{
            color: {placeholder} !important;
            -webkit-text-fill-color: {placeholder} !important;
            opacity: 1 !important;
        }}

        .stButton > button:hover,
        [data-testid="stBaseButton-secondary"]:hover,
        [data-testid="stBaseButton-primary"]:hover {{
            background-color: {control_hover} !important;
            border-color: {control_border} !important;
        }}

        /* Dropdown menus opened from selectboxes should follow the theme too. */
        ul[data-baseweb="menu"],
        [role="listbox"],
        [data-baseweb="popover"] {{
            background-color: {control_background} !important;
            color: {foreground} !important;
        }}

        [role="option"] {{
            background-color: {control_background} !important;
            color: {foreground} !important;
        }}

        [role="option"]:hover {{
            background-color: {control_hover} !important;
        }}

        div[data-testid="stMetric"] {{
            background: {control_background} !important;
            border: 1px solid {control_border};
        }}

        div[data-testid="stMetric"] *,
        div[data-testid="stDataFrame"] * {{
            color: {foreground};
        }}

        [data-testid="stCaptionContainer"] * {{
            color: {foreground};
            opacity: 0.78;
        }}

        .paragraph-reader {{
            max-height: 210px;
            overflow-y: auto;
            padding-right: 0.35rem;
            line-height: 1.38;
            font-size: 0.94rem;
            color: {foreground};
        }}

        .relationship-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid {control_border};
            border-radius: 0.55rem;
            background-color: {control_background};
            color: {foreground};
            font-size: 0.90rem;
        }}

        .relationship-table th,
        .relationship-table td {{
            padding: 0.48rem 0.60rem;
            border-bottom: 1px solid {control_border};
            background-color: {control_background};
            color: {foreground} !important;
            text-align: left;
        }}

        .relationship-table th {{
            font-weight: 600;
            background-color: {control_hover};
        }}

        .relationship-table tr:last-child td {{
            border-bottom: none;
        }}

        .block-container {{
            padding-top: 1.05rem !important;
            padding-bottom: 0.35rem !important;
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 0.55rem !important;
            padding-bottom: 0.35rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_appearance_controls(themes) -> dict[str, str]:
    st.sidebar.subheader("Appearance")

    with st.sidebar.expander("Colors & graph display", expanded=False):
        st.color_picker("Concept nodes", key="concept_color")
        st.color_picker("Paragraph nodes", key="paragraph_color")
        st.color_picker("Relationships", key="edge_color")
        st.color_picker("Selected relationships", key="selected_edge_color")
        st.color_picker("Graph background", key="background_color")
        st.color_picker(
            "Dashboard background",
            key="dashboard_background_color",
        )
        st.checkbox("Color paragraphs by theme", key="theme_coloring")

        if st.session_state.theme_coloring:
            st.caption("Theme colors")
            for theme in themes:
                st.color_picker(
                    theme.name,
                    key=f"theme_color_{theme.id}",
                )

        st.button(
            "Reset appearance",
            use_container_width=True,
            on_click=reset_appearance,
            args=(themes,),
        )

    if st.sidebar.button("Fit to screen", use_container_width=True):
        st.session_state.fit_dashboard = True
        st.session_state.graph_fit_nonce += 1
        st.rerun()

    return {
        theme.id: st.session_state[f"theme_color_{theme.id}"]
        for theme in themes
    }


@st.cache_data
def load_data():
    paragraphs = load_paragraphs(DATA_DIR / "paragraphs.json")
    concepts = load_concepts(DATA_DIR / "concepts.json")
    edges = load_edges(DATA_DIR / "edges.json")
    themes = load_themes(DATA_DIR / "themes.json")

    validate_dataset(paragraphs, concepts, edges, themes)
    return paragraphs, concepts, edges, themes


@st.cache_resource
def make_graph(paragraphs, concepts, edges):
    return build_graph(paragraphs, concepts, edges)


@st.cache_data
def make_layout(node_ids, edge_pairs):
    """Build stable full-graph coordinates so nodes do not jump when revealed."""
    graph = nx.Graph()
    graph.add_nodes_from(node_ids)
    graph.add_edges_from(edge_pairs)
    return forceatlas2_layout(graph)


def initialize_session(theme_id: str, starting_nodes: set[str]) -> None:
    """Initialize exploration-related session state once."""
    defaults = {
        "active_theme_id": theme_id,
        "visible_nodes": set(starting_nodes),
        "selected_node": None,
        "search_query": "",
        "search_result": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def switch_theme(theme_id: str, starting_nodes: set[str]) -> None:
    """Start a fresh exploration when the editorial theme changes."""
    if st.session_state.active_theme_id == theme_id:
        return

    st.session_state.active_theme_id = theme_id
    st.session_state.visible_nodes = set(starting_nodes)
    st.session_state.selected_node = None
    st.session_state.search_query = ""
    st.session_state.search_result = None


def reset_exploration(starting_nodes: set[str]) -> None:
    st.session_state.visible_nodes = set(starting_nodes)
    st.session_state.selected_node = None
    st.session_state.search_query = ""
    st.session_state.search_result = None


def select_and_reveal(graph: nx.Graph, node_id: str) -> None:
    """Use one state transition for search, dropdown and sequential navigation."""
    st.session_state.visible_nodes = reveal_node(
        graph,
        st.session_state.visible_nodes,
        node_id,
    )
    st.session_state.selected_node = node_id


def node_marker_size(graph: nx.Graph, node_id: str, selected: bool) -> float:
    """Scale nodes by degree while keeping paragraph nodes visually subordinate."""
    degree = graph.degree[node_id]
    if graph.nodes[node_id]["node_type"] == NODE_TYPE_CONCEPT:
        size = 11 + (degree ** 0.5) * 3.2
    else:
        size = 7 + (degree ** 0.5) * 1.8

    return size + 7 if selected else size


def paragraph_hover_text(text: str, *, width: int = 72) -> str:
    """Format canonical paragraph text for a readable Plotly hover card."""
    return "<br>".join(
        escape(line)
        for line in wrap(
            text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )


def graph_figure(
    full_graph: nx.Graph,
    visible_nodes: set[str],
    positions: dict[str, tuple[float, float]],
    selected_node: str | None,
    *,
    show_all: bool,
    theme_colors: dict[str, str],
) -> go.Figure:
    graph = full_graph if show_all else full_graph.subgraph(visible_nodes)

    normal_edge_x: list[float | None] = []
    normal_edge_y: list[float | None] = []
    selected_edge_x: list[float | None] = []
    selected_edge_y: list[float | None] = []

    edge_hover_x: list[float] = []
    edge_hover_y: list[float] = []
    edge_hover_text: list[str] = []

    for source, target, attributes in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]

        is_selected_edge = (
            selected_node is not None
            and selected_node in {source, target}
        )

        target_x = selected_edge_x if is_selected_edge else normal_edge_x
        target_y = selected_edge_y if is_selected_edge else normal_edge_y

        target_x.extend([x0, x1, None])
        target_y.extend([y0, y1, None])

        edge_hover_x.append((x0 + x1) / 2)
        edge_hover_y.append((y0 + y1) / 2)
        edge_hover_text.append(
            f"{graph.nodes[source]['label']} "
            f"— {attributes['relationship']} — "
            f"{graph.nodes[target]['label']}"
        )

    normal_edge_trace = go.Scatter(
        x=normal_edge_x,
        y=normal_edge_y,
        mode="lines",
        hoverinfo="none",
        line={
            "width": 1.45,
            "color": st.session_state.edge_color,
        },
        opacity=0.62,
        name="Relationships",
    )

    selected_edge_trace = go.Scatter(
        x=selected_edge_x,
        y=selected_edge_y,
        mode="lines",
        hoverinfo="none",
        line={
            "width": 2.8,
            "color": st.session_state.selected_edge_color,
        },
        opacity=0.95,
        name="Selected relationships",
        showlegend=False,
    )

    edge_hover_trace = go.Scatter(
        x=edge_hover_x,
        y=edge_hover_y,
        mode="markers",
        marker={"size": 12, "opacity": 0},
        text=edge_hover_text,
        hovertemplate="%{text}<extra>Relationship</extra>",
        showlegend=False,
    )

    traces: list[go.Scatter] = [
        normal_edge_trace,
        selected_edge_trace,
        edge_hover_trace,
    ]

    for node_type, name, symbol in (
        (NODE_TYPE_PARAGRAPH, "Paragraphs", "square"),
        (NODE_TYPE_CONCEPT, "Concepts", "circle"),
    ):
        x_values = []
        y_values = []
        display_labels = []
        customdata = []
        sizes = []
        colors = []

        for node_id, attributes in graph.nodes(data=True):
            if attributes["node_type"] != node_type:
                continue

            x, y = positions[node_id]
            x_values.append(x)
            y_values.append(y)
            display_labels.append(
                attributes["label"]
                if (
                    node_id == selected_node
                    or (
                        not show_all
                        and attributes["node_type"] == NODE_TYPE_CONCEPT
                    )
                )
                else ""
            )
            customdata.append(
                [
                    node_id,
                    full_graph.degree[node_id],
                    attributes["label"],
                    (
                        paragraph_hover_text(attributes["text"])
                        if node_type == NODE_TYPE_PARAGRAPH
                        else ""
                    ),
                ]
            )
            sizes.append(
                node_marker_size(
                    full_graph,
                    node_id,
                    selected=node_id == selected_node,
                )
            )

            if node_type == NODE_TYPE_CONCEPT:
                colors.append(st.session_state.concept_color)
            elif st.session_state.theme_coloring:
                colors.append(
                    theme_colors.get(
                        attributes["theme"],
                        st.session_state.paragraph_color,
                    )
                )
            else:
                colors.append(st.session_state.paragraph_color)

        traces.append(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers+text",
                text=display_labels,
                textposition="top center",
                customdata=customdata,
                hovertemplate=(
                    (
                        "<b>%{customdata[2]}</b><br>"
                        "ID: %{customdata[0]} · Degree: %{customdata[1]}"
                        "<br><br>%{customdata[3]}"
                        "<extra>Paragraph</extra>"
                    )
                    if node_type == NODE_TYPE_PARAGRAPH
                    else (
                        "<b>%{customdata[2]}</b><br>"
                        "ID: %{customdata[0]}<br>"
                        "Degree: %{customdata[1]}"
                        "<extra>Concept</extra>"
                    )
                ),
                marker={
                    "size": sizes,
                    "symbol": symbol,
                    "color": colors,
                    "opacity": 0.92,
                    "line": {
                        "width": 1.2,
                        "color": "rgba(45, 50, 60, 0.8)",
                    },
                },
                name=name,
            )
        )

    background = st.session_state.background_color
    foreground = contrast_text_color(background)

    figure = go.Figure(data=traces)
    figure.update_layout(
        showlegend=True,
        hovermode="closest",
        dragmode="pan",
        margin={"l": 2, "r": 2, "t": 4, "b": 2},
        paper_bgcolor=background,
        plot_bgcolor=background,
        font={"color": foreground},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
            "font": {"color": foreground},
        },
        xaxis={
            "visible": False,
            "autorange": True,
        },
        yaxis={
            "visible": False,
            "autorange": True,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        height=420 if st.session_state.get("fit_dashboard", True) else 515,
        uirevision=f"fit-{st.session_state.graph_fit_nonce}",
    )
    return figure


def selected_from_plotly_event(event) -> str | None:
    """Extract a node ID from Streamlit's Plotly selection event."""
    try:
        points = event.selection.points
    except AttributeError:
        try:
            points = event["selection"]["points"]
        except (KeyError, TypeError):
            return None

    if not points:
        return None

    customdata = points[0].get("customdata")
    if not customdata:
        return None

    node_id = customdata[0]
    if isinstance(node_id, str):
        return node_id
    return None


def render_search(graph, paragraphs, concepts) -> None:
    st.sidebar.subheader("Search")

    query = st.sidebar.text_input(
        "Concept or paragraph",
        placeholder="Perception, §35 or 35",
        key="search_query",
    )

    if not query.strip():
        st.session_state.search_result = None
        return

    results = search_nodes(query, paragraphs, concepts)

    if not results:
        st.session_state.search_result = None
        st.sidebar.warning("No matching concept or paragraph.")
        return

    labels = {
        node_id: f"{graph.nodes[node_id]['label']} · {node_id}"
        for node_id in results
    }

    selected_result = st.sidebar.selectbox(
        "Result",
        options=results,
        format_func=lambda node_id: labels[node_id],
        key="search_result_selector",
    )
    st.session_state.search_result = selected_result

    if st.sidebar.button("Reveal result", use_container_width=True):
        select_and_reveal(graph, selected_result)
        st.rerun()


def render_node_details(graph: nx.Graph, node_id: str | None) -> None:
    st.subheader("Reading & relationships")

    if node_id is None:
        st.info(
            "Select a node in the graph, search for a concept or paragraph, "
            "or choose a discovered node from the sidebar."
        )
        return

    attributes = graph.nodes[node_id]

    if attributes["node_type"] == NODE_TYPE_PARAGRAPH:
        number = attributes["number"]
        st.markdown(f"### §{number}")
        paragraph_text = attributes["text"]
        if st.session_state.get("fit_dashboard", True):
            st.markdown(
                f"""
                <div class="paragraph-reader">
                    {paragraph_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.write(paragraph_text)

        previous_id = adjacent_paragraph_id(number, direction=-1)
        next_id = adjacent_paragraph_id(number, direction=1)

        previous_col, next_col = st.columns(2)

        if previous_id is not None:
            if previous_col.button(
                f"← §{number - 1}",
                use_container_width=True,
            ):
                select_and_reveal(graph, previous_id)
                st.rerun()

        if next_id is not None:
            if next_col.button(
                f"§{number + 1} →",
                use_container_width=True,
            ):
                select_and_reveal(graph, next_id)
                st.rerun()
    else:
        st.markdown(f"### {attributes['name']}")
        st.caption("Curated philosophical concept")

    if st.button(
        "Reveal connected nodes",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.visible_nodes = expand_one_hop(
            graph,
            st.session_state.visible_nodes,
            node_id,
        )
        st.rerun()

    relationships = connected_relationships(graph, node_id)

    st.markdown("#### Direct relationships")

    rows = "".join(
        "<tr>"
        f"<td>{escape(label)}</td>"
        f"<td>{escape(relationship)}</td>"
        "</tr>"
        for _, label, relationship in relationships
    )

    st.markdown(
        f"""
        <table class="relationship-table">
            <thead>
                <tr>
                    <th>Node</th>
                    <th>Relationship</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_full_graph_review(
    graph,
    positions,
    paragraphs,
    concepts,
    edges,
    theme_colors,
):
    st.caption(
        "Full-graph inspection mode for reviewing the complete curated network."
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Paragraphs", len(paragraphs))
    metric_cols[1].metric("Concepts", len(concepts))
    metric_cols[2].metric("Relationships", len(edges))
    metric_cols[3].metric(
        "Components",
        nx.number_connected_components(graph),
    )

    st.plotly_chart(
        graph_figure(
            graph,
            set(graph.nodes),
            positions,
            st.session_state.selected_node,
            show_all=True,
            theme_colors=theme_colors,
        ),
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True},
    )


def render_discovery_metrics(graph: nx.Graph) -> None:
    paragraph_count, concept_count = discovery_counts(
        graph,
        st.session_state.visible_nodes,
    )

    st.sidebar.subheader("Discovery")
    st.sidebar.metric(
        "Nodes",
        f"{len(st.session_state.visible_nodes)} / {graph.number_of_nodes()}",
    )

    col1, col2 = st.sidebar.columns(2)
    col1.metric("Paragraphs", f"{paragraph_count} / 90")
    col2.metric("Concepts", f"{concept_count} / 64")


def main() -> None:
    st.set_page_config(
        page_title="Monadology Explorer",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.05rem;
            padding-bottom: 0.5rem;
            max-width: 1600px;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.25rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(127, 127, 127, 0.06);
            border-radius: 0.6rem;
            padding: 0.55rem 0.7rem;
        }

        div[data-testid="stDataFrame"] {
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Monadology Explorer")
    st.caption(
        "A graph-based reading experience for Leibniz's Monadology. "
        "Start from a concept, reveal one-hop connections and move between "
        "semantic exploration and the canonical text."
    )

    try:
        paragraphs, concepts, edges, themes = load_data()
        graph = make_graph(paragraphs, concepts, edges)
        initialize_appearance(themes)
        apply_dashboard_background()
    except (DataLoadError, DatasetValidationError) as exc:
        LOGGER.exception("Failed to load Monadology dataset.")
        st.error(f"Unable to load the curated dataset: {exc}")
        st.stop()

    positions = make_layout(
        tuple(sorted(graph.nodes)),
        tuple(sorted(tuple(sorted(edge)) for edge in graph.edges)),
    )

    theme_by_name = {theme.name: theme for theme in themes}
    theme_name = st.sidebar.selectbox(
        "Theme",
        options=list(theme_by_name),
    )
    theme = theme_by_name[theme_name]

    initialize_session(
        theme.id,
        initial_visible_nodes(theme),
    )
    switch_theme(
        theme.id,
        initial_visible_nodes(theme),
    )

    st.sidebar.caption(
        f"Editorial navigation: §{theme.paragraph_start}–§{theme.paragraph_end}"
    )

    if st.sidebar.button("Reset exploration", use_container_width=True):
        reset_exploration(initial_visible_nodes(theme))
        st.rerun()

    render_search(graph, paragraphs, concepts)
    theme_colors = render_appearance_controls(themes)

    view = st.sidebar.radio(
        "View",
        ("Progressive reader", "Full graph"),
    )

    if view == "Full graph":
        render_full_graph_review(
            graph,
            positions,
            paragraphs,
            concepts,
            edges,
            theme_colors,
        )
        return

    render_discovery_metrics(graph)

    st.sidebar.subheader("Visible nodes")
    visible_options = sorted(
        st.session_state.visible_nodes,
        key=lambda node_id: graph.nodes[node_id]["label"].casefold(),
    )
    fallback_selection = st.sidebar.selectbox(
        "Jump to a discovered node",
        options=[""] + visible_options,
        format_func=lambda node_id: (
            "Choose a discovered node"
            if not node_id
            else graph.nodes[node_id]["label"]
        ),
        index=0,
        label_visibility="collapsed",
    )
    if (
        fallback_selection
        and fallback_selection != st.session_state.selected_node
    ):
        select_and_reveal(graph, fallback_selection)
        st.rerun()

    graph_col, detail_col = st.columns([1.8, 1], gap="large")

    with graph_col:
        st.subheader(theme.name)
        st.caption(
            "Start with a curated concept, select a node to inspect it, then "
            "expand exactly one hop. Layout: ForceAtlas2-style force-directed "
            "network with stable coordinates."
        )

        event = st.plotly_chart(
            graph_figure(
                graph,
                st.session_state.visible_nodes,
                positions,
                st.session_state.selected_node,
                show_all=False,
                theme_colors=theme_colors,
            ),
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": True},
            on_select="rerun",
            selection_mode="points",
            key="progressive_graph",
        )

        clicked_node = selected_from_plotly_event(event)
        if (
            clicked_node is not None
            and clicked_node in st.session_state.visible_nodes
            and clicked_node != st.session_state.selected_node
        ):
            st.session_state.selected_node = clicked_node
            st.rerun()

    with detail_col:
        render_node_details(
            graph,
            st.session_state.selected_node,
        )


if __name__ == "__main__":
    main()
