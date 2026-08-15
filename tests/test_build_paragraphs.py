import pytest

from scripts.build_paragraphs import (
    build_records,
    extract_numbered_paragraphs,
)


def test_extraction_stops_before_wikisource_license_metadata():
    html = """
    <div id="mw-content-text">
      <div class="mw-parser-output">
        <p>89. Paragraph eighty-nine.</p>
        <p>90. Final canonical paragraph.</p>
        <p>Canonical continuation of paragraph ninety.</p>
        <p>
          This work is a translation and has a separate copyright status
          to the applicable copyright protections of the original content.
        </p>
        <p>Public domain metadata.</p>
      </div>
    </div>
    """

    paragraphs = extract_numbered_paragraphs(html)

    assert paragraphs[90] == (
        "Final canonical paragraph. "
        "Canonical continuation of paragraph ninety."
    )

    assert "copyright status" not in paragraphs[90]
    assert "Public domain" not in paragraphs[90]
    
def test_build_records_rejects_wikisource_metadata_contamination():
    paragraphs = {
        number: f"Canonical paragraph {number}."
        for number in range(1, 91)
    }
    paragraphs[90] += (
        " This work is a translation and has a separate copyright status."
    )

    themes = [
        {
            "id": "test_theme",
            "paragraph_start": 1,
            "paragraph_end": 90,
        }
    ]

    with pytest.raises(
        RuntimeError,
        match="contains Wikisource metadata",
    ):
        build_records(paragraphs, themes)