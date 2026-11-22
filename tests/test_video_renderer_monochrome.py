from PIL import Image, ImageDraw

from finance_campus.video_renderer import PALETTE, _draw_element


def test_production_palette_is_strictly_monochrome():
    assert set(PALETTE.values()) == {(0, 0, 0), (255, 255, 255)}


def test_person_illustration_uses_only_black_and_white_pixels():
    image = Image.new("RGB", (400, 225), PALETTE["white"])
    draw = ImageDraw.Draw(image)
    _draw_element(
        draw,
        {
            "type": "person",
            "x": 250,
            "y": 60,
            "width": 220,
            "height": 390,
            "color": "green",
            "pose": "worried",
            "expression": "worried",
        },
        1.0,
        image.size,
        coordinate_size=(1000, 562),
    )
    colours = set(image.getdata())
    assert colours <= {(0, 0, 0), (255, 255, 255)}
