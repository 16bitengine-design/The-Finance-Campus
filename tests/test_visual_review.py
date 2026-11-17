import subprocess

import pytest
from PIL import Image

from finance_campus import visual_review


def test_visual_review_sheet_extracts_frames_and_creates_contact_sheet(monkeypatch, tmp_path):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"video")

    def fake_which(name):
        return name

    def fake_run(command, **kwargs):
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, "12.0", "")
        if "-frames:v" in command:
            output = command[-1]
            Image.new("RGB", (108, 192), "white").save(output)
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(command)

    monkeypatch.setattr(visual_review.shutil, "which", fake_which)
    monkeypatch.setattr(visual_review.subprocess, "run", fake_run)
    report = visual_review.create_visual_review_sheet(video, tmp_path / "review.jpg")
    assert report["human_review_required"] is True
    assert report["sample_count"] == 8
    assert (tmp_path / "review.jpg").is_file()


def test_visual_review_requires_enough_samples(tmp_path):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="at least four"):
        visual_review.create_visual_review_sheet(video, tmp_path / "review.jpg", sample_count=3)
