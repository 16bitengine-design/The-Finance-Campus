import shutil
import subprocess

import pytest
from PIL import Image, ImageChops

from finance_campus.storyboard import render_scene_svg, validate_storyboard
from finance_campus.video_renderer import _point, render_video


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
    output = render_video(_storyboard(), tmp_path / "sample.mp4", fps=12, draw_fps=6, keep_frames=True)
    assert output.is_file()
    assert output.stat().st_size > 1024
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True, check=False)
    assert "Video:" in result.stderr
    final_frame = Image.open(tmp_path / ".sample_frames" / "frame_000011.png").convert("RGB")
    white = Image.new("RGB", final_frame.size, (255, 255, 255))
    assert ImageChops.difference(final_frame, white).getbbox() is not None

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
    svg = render_scene_svg(scene, {"width": 1000, "height": 1778})
    assert 'width="1080" height="1920"' in svg
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



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_muxes_narration_and_burns_captions(tmp_path):
    audio = tmp_path / "narration.mp3"
    generated = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-q:a", "8", "-acodec", "libmp3lame", str(audio),
        ],
        capture_output=True, text=True, check=False,
    )
    assert generated.returncode == 0
    captions = tmp_path / "captions.srt"
    captions.write_text(
        chr(10).join([
            "1",
            "00:00:00,000 --> 00:00:01,800",
            "A practical money lesson",
            "",
        ]),
        encoding="utf-8",
    )
    output = render_video(
        _storyboard(), tmp_path / "with-audio.mp4", fps=12, draw_fps=6,
        audio_path=audio, captions_path=captions,
    )
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    assert "Video:" in probe.stderr
    assert "Audio:" in probe.stderr



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_supports_landscape_long_form(tmp_path):
    output = render_video(
        _storyboard(), tmp_path / "long-form.mp4",
        video_format="long", fps=12, draw_fps=6,
    )
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    assert "1920x1080" in probe.stderr


def test_video_renderer_rejects_negative_transition_duration(tmp_path):
    with pytest.raises(ValueError, match="transition_seconds"):
        render_video(_storyboard(), tmp_path / "bad-transition.mp4", transition_seconds=-0.1)



def test_coordinate_mapping_uses_distinct_x_and_y_values():
    assert _point(120, 1450, 1.08, 1.08) == (130, 1566)
