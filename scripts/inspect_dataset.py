"""Inspect the curated Monadology graph dataset."""

from collections import Counter
from pathlib import Path

from monadology_explorer.loader import (
    load_concepts,
    load_edges,
    load_paragraphs,
    load_themes,
)
from monadology_explorer.validation import validate_dataset

DATA_DIR = Path("data")


def main() -> None:
    paragraphs = load_paragraphs(DATA_DIR / "paragraphs.json")
    concepts = load_concepts(DATA_DIR / "concepts.json")
    edges = load_edges(DATA_DIR / "edges.json")
    themes = load_themes(DATA_DIR / "themes.json")

    validate_dataset(paragraphs, concepts, edges, themes)

    paragraph_ids = {paragraph.id for paragraph in paragraphs}
    concept_ids = {concept.id for concept in concepts}
    node_ids = paragraph_ids | concept_ids

    degrees = Counter()

    for edge in edges:
        degrees[edge.source] += 1
        degrees[edge.target] += 1

    isolated = sorted(node_ids - set(degrees))
    connected_paragraphs = paragraph_ids & set(degrees)
    connected_concepts = concept_ids & set(degrees)

    relationship_counts = Counter(
        edge.relationship for edge in edges
    )

    print("Monadology Explorer — Dataset Inspection")
    print("=" * 48)
    print(f"Paragraphs          : {len(paragraphs)}")
    print(f"Concepts            : {len(concepts)}")
    print(f"Edges               : {len(edges)}")
    print(f"Themes              : {len(themes)}")
    print(f"Connected paragraphs: {len(connected_paragraphs)}/90")
    print(
        f"Connected concepts  : "
        f"{len(connected_concepts)}/{len(concepts)}"
    )
    print(f"Isolated nodes      : {len(isolated)}")

    print("\nParagraph coverage by theme")
    print("-" * 48)

    for theme in themes:
        theme_paragraphs = {
            paragraph.id
            for paragraph in paragraphs
            if paragraph.theme == theme.id
        }
        connected = theme_paragraphs & connected_paragraphs
        print(
            f"{theme.name:<32} "
            f"{len(connected):>2}/{len(theme_paragraphs):<2}"
        )

    print("\nRelationships")
    print("-" * 48)

    for relationship, count in relationship_counts.most_common():
        print(f"{relationship:<18} {count:>4}")

    print("\nHighest-degree nodes")
    print("-" * 48)

    for node_id, degree in degrees.most_common(15):
        print(f"{node_id:<35} {degree:>4}")

    print("\nIsolated nodes")
    print("-" * 48)

    if isolated:
        for node_id in isolated:
            print(node_id)
    else:
        print("None")


if __name__ == "__main__":
    main()
