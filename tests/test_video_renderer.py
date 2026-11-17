import shutil
import subprocess

import pytest

from finance_campus.storyboard import render_scene_svg, validate_storyboard
from finance_campus.video_renderer import render_video


def _storyboard():
    return {"scenes": [{
        "id": "money-flow",
        "narration": "A person receives income and divides it between needs and savings.",
        "duration_seconds": 2,
        "elements": [
            {"type": "circle", "cx": 180, "cy": 150, "r": 35, "color": "navy"},
            {"type": "line", "x1": 180, "y1": 185, "x2": 180, "y2": 290, "color": "navy"},
            {"type": "rect", "x": 360, "y": 150, "width": 170, "height": 100, "color": "green"},
            {"type": "arrow", "x1": 220, "y1": 220, "x2": 350, "y2": 200, "color": "gold"},
            {"type": "text", "x": 370, "y": 300, "text": "Savings", "color": "green"},
        ],
    }]}

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_creates_playable_mp4(tmp_path):
    output = render_video(_storyboard(), tmp_path / "sample.mp4", fps=12, draw_fps=6)
    assert output.is_file()
    assert output.stat().st_size > 1024
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True, check=False)
    assert "Video:" in result.stderr

def test_video_renderer_rejects_text_only_storyboard(tmp_path):
    storyboard = _storyboard()
    storyboard["scenes"][0]["elements"] = [{"type": "text", "x": 20, "y": 30, "text": "Only words"}]
    with pytest.raises(ValueError, match="text-only"):
        render_video(storyboard, tmp_path / "bad.mp4")



def test_financial_illustration_types_are_valid_and_render_to_svg():
    scene = {
        "id": "saving-for-the-future",
        "narration": "A worker puts money into a savings jar.",
        "duration_seconds": 3,
        "elements": [
            {"type": "person", "x": 100, "y": 100, "width": 160, "height": 300},
            {"type": "savings_jar", "x": 400, "y": 180, "width": 180, "height": 220, "color": "green"},
            {"type": "coin", "x": 650, "y": 120, "width": 90, "height": 90, "color": "gold"},
            {"type": "text", "x": 350, "y": 470, "text": "Save consistently"},
        ],
    }
    assert validate_storyboard({"scenes": [scene]}) == []
    svg = render_scene_svg(scene)
    assert "<circle" in svg
    assert "Save consistently" in svg


def test_semantic_illustration_requires_positive_dimensions():
    scene = {
        "id": "invalid-wallet",
        "narration": "A wallet stores money.",
        "duration_seconds": 2,
        "elements": [{"type": "wallet", "x": 10, "y": 10, "width": 0, "height": 80}],
    }
    assert any("width and height must be positive" in error for error in validate_storyboard({"scenes": [scene]}))
