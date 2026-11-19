from finance_campus.timeline_renderer import validate_timeline


def test_timeline_accepts_valid_manifest():
    assert validate_timeline({
        "canvas": {"width": 1080, "height": 1920},
        "fps": 30,
        "scenes": [{"scene": "scene.json", "asset_root": "assets"}],
    }) == []


def test_timeline_rejects_invalid_dimensions_rate_and_paths():
    errors = validate_timeline({
        "canvas": {"width": 0, "height": 1920},
        "fps": 0,
        "scenes": [{"scene": "", "asset_root": "assets"}],
    })
    assert any("canvas.width" in item for item in errors)
    assert any("fps" in item for item in errors)
    assert any("scenes[0].scene" in item for item in errors)
