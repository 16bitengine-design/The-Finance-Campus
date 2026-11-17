import json
from pathlib import Path

from finance_campus.config import load_yaml
from finance_campus.storyboard import validate_storyboard
from finance_campus.storyboard_builder import build_storyboard


def _script():
    path = Path(__file__).parents[1] / "examples" / "script-package.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_approved_script_becomes_six_illustrated_scenes_and_disclaimer():
    storyboard = build_storyboard(
        _script(),
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    assert len(storyboard["scenes"]) == 7
    assert all(any(item["type"] != "text" for item in scene["elements"]) for scene in storyboard["scenes"])
    assert storyboard["scenes"][-1]["minimum_duration_seconds"] >= 6
    assert storyboard["spoken_disclaimer_text"] in storyboard["scenes"][-1]["narration"]
    assert validate_storyboard(storyboard) == []


def test_long_form_storyboard_uses_landscape_canvas():
    storyboard = build_storyboard(
        _script(),
        video_format="long",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    assert storyboard["canvas"] == {"width": 1778, "height": 1000}
    assert validate_storyboard(storyboard) == []


def test_storyboard_builder_rejects_unknown_format():
    try:
        build_storyboard(
            _script(),
            video_format="square",
            disclaimer_config=load_yaml("config/disclaimer.yaml"),
        )
    except ValueError as exc:
        assert "video_format" in str(exc)
    else:
        raise AssertionError("Unknown video format should be rejected")
