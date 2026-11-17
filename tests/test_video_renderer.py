import shutil
import subprocess

import pytest
from PIL import Image

from finance_campus.video_renderer import render_video
from test_storyboard import sample_storyboard


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_creates_playable_mp4(tmp_path):
    output = render_video(sample_storyboard(), tmp_path / "sample.mp4", fps=12, draw_fps=6)
    assert output.is_file()
    assert output.stat().st_size > 1024
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    assert "Video:" in result.stderr


def test_video_renderer_rejects_text_only_storyboard(tmp_path):
    storyboard = sample_storyboard()
    storyboard["scenes"][0]["elements"] = [
        {"type": "text", "x": 20, "y": 30, "text": "Only words"}
    ]
    with pytest.raises(ValueError, match="text-only"):
        render_video(storyboard, tmp_path / "bad.mp4")
