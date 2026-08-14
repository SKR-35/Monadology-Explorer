"""Build the canonical paragraph dataset from the Latta Wikisource edition.

This script is a development-time content acquisition utility.
The deployed application reads the generated static JSON file and does not
fetch canonical text at runtime.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

SOURCE_URL = (
    "https://en.wikisource.org/wiki/"
    "Monadology_(Leibniz,_tr._Latta)"
)

OUTPUT_PATH = Path("data/paragraphs.json")
THEMES_PATH = Path("data/themes.json")

PARAGRAPH_START = re.compile(r"^\s*(\d{1,2})\.\s*(.*)$", re.DOTALL)

WORK_END_MARKERS = (
    "This work is a translation and has a separate copyright status",
    "Original:",
    "Translation:",
)

def fetch_html() -> str:
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": (
                "monadology-explorer/0.1 "
                "(development dataset builder)"
            )
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def extract_numbered_paragraphs(html: str) -> dict[int, str]:
    soup = BeautifulSoup(html, "html.parser")

    content = soup.select_one("#mw-content-text .mw-parser-output")
    if content is None:
        raise RuntimeError("Could not locate Wikisource article content.")

    paragraphs: dict[int, list[str]] = {}
    current_number: int | None = None

    for element in content.find_all("p", recursive=True):
        text = normalize_text(element.get_text(" ", strip=True))

        if not text:
            continue

        # Wikisource appends licensing/public-domain metadata after the
        # canonical work. Stop before that content can be attached to §90.
        if current_number == 90 and any(
            text.startswith(marker) for marker in WORK_END_MARKERS
        ):
            break

        match = PARAGRAPH_START.match(text)

        if match:
            number = int(match.group(1))

            if not 1 <= number <= 90:
                continue

            current_number = number
            paragraphs.setdefault(number, [])

            remainder = normalize_text(match.group(2))
            if remainder:
                paragraphs[number].append(remainder)

            continue

        if current_number is not None:
            paragraphs[current_number].append(text)

    return {
        number: normalize_text(" ".join(parts))
        for number, parts in paragraphs.items()
    }


def load_theme_ranges() -> list[dict]:
    with THEMES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def theme_for_paragraph(number: int, themes: list[dict]) -> str:
    matches = [
        theme["id"]
        for theme in themes
        if theme["paragraph_start"] <= number <= theme["paragraph_end"]
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Paragraph {number} matched {len(matches)} themes; expected 1."
        )

    return matches[0]


def build_records(
    paragraphs: dict[int, str],
    themes: list[dict],
) -> list[dict]:
    expected = set(range(1, 91))
    actual = set(paragraphs)

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    if missing or unexpected:
        raise RuntimeError(
            "Canonical extraction failed. "
            f"Missing={missing}, unexpected={unexpected}"
        )

    return [
        {
            "id": f"p{number:03d}",
            "number": number,
            "text": paragraphs[number],
            "theme": theme_for_paragraph(number, themes),
        }
        for number in range(1, 91)
    ]
    
    forbidden_metadata_markers = (
        "This work is a translation",
        "public domain worldwide",
        "Retrieved from",
    )

    contaminated = [
        number
        for number, text in paragraphs.items()
        if any(marker in text for marker in forbidden_metadata_markers)
    ]

    if contaminated:
        raise RuntimeError(
            "Canonical extraction contains Wikisource metadata in "
            f"paragraphs: {contaminated}"
        )


def main() -> None:
    html = fetch_html()
    paragraphs = extract_numbered_paragraphs(html)
    themes = load_theme_ranges()
    records = build_records(paragraphs, themes)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Wrote {len(records)} canonical paragraphs to {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()