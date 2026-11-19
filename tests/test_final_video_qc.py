import json
import subprocess

import pytest

from finance_campus import final_video_qc


def _probe_json():
    return {
        "streams": [
            {
                "codec_type": "video", "codec_name": "h264", "width": 1080,
                "height": 1920, "pix_fmt": "yuv420p", "avg_frame_rate": "30/1",
                "nb_frames": "4500",
            },
            {
                "codec_type": "audio", "codec_name": "aac", "sample_rate": "24000",
                "channels": 1,
            },
        ],
        "format": {"duration": "150.000", "size": "250000"},
    }


def test_final_video_qc_passes_all_technical_checks(monkeypatch, tmp_path):
    video = tmp_path / "final.mp4"
    video.write_bytes(b"x" * 20_000)
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, json.dumps(_probe_json()), "")
        if "-af" in command:
            return subprocess.CompletedProcess(
                command, 0, "", "mean_volume: -19.0 dB\nmax_volume: -1.0 dB\n",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(final_video_qc.shutil, "which", lambda name: name)
    monkeypatch.setattr(final_video_qc.subprocess, "run", fake_run)
    report = final_video_qc.validate_final_video(video, video_format="short")
    assert report["passed"] is True
    assert report["fps"] == 30
    assert report["audio_peak_volume_db"] == -1.0
    assert len(calls) == 3


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("codec_name", "mpeg4", "H.264"),
        ("pix_fmt", "yuv444p", "yuv420p"),
        ("avg_frame_rate", "24/1", "frame rate"),
    ],
)
def test_final_video_qc_rejects_invalid_video_stream(monkeypatch, tmp_path, field, value, message):
    video = tmp_path / "final.mp4"
    video.write_bytes(b"x" * 20_000)
    data = _probe_json()
    data["streams"][0][field] = value

    def fake_run(command, **kwargs):
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, json.dumps(data), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(final_video_qc.shutil, "which", lambda name: name)
    monkeypatch.setattr(final_video_qc.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=message):
        final_video_qc.validate_final_video(video, video_format="short")


def test_final_video_qc_rejects_clipped_audio(monkeypatch, tmp_path):
    video = tmp_path / "final.mp4"
    video.write_bytes(b"x" * 20_000)

    def fake_run(command, **kwargs):
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, json.dumps(_probe_json()), "")
        if "-af" in command:
            return subprocess.CompletedProcess(
                command, 0, "", "mean_volume: -18.0 dB\nmax_volume: 0.0 dB\n",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(final_video_qc.shutil, "which", lambda name: name)
    monkeypatch.setattr(final_video_qc.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="clipping"):
        final_video_qc.validate_final_video(video, video_format="short")


def test_final_video_qc_rejects_videos_below_150_seconds(monkeypatch, tmp_path):
    video = tmp_path / "too-short.mp4"
    video.write_bytes(b"x" * 20_000)
    data = _probe_json()
    data["streams"][0]["nb_frames"] = "4499"
    data["format"]["duration"] = "149.967"

    def fake_run(command, **kwargs):
        if command[0] == "ffprobe":
            return subprocess.CompletedProcess(command, 0, json.dumps(data), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(final_video_qc.shutil, "which", lambda name: name)
    monkeypatch.setattr(final_video_qc.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="minimum is 150"):
        final_video_qc.validate_final_video(video, video_format="short")
