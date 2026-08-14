from app import contrast_text_color


def test_contrast_text_color_uses_dark_text_on_light_background():
    assert contrast_text_color("#FFFFFF") == "#111111"


def test_contrast_text_color_uses_light_text_on_dark_background():
    assert contrast_text_color("#111111") == "#F7F7F7"
