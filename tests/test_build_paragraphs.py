from scripts.build_paragraphs import extract_numbered_paragraphs


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