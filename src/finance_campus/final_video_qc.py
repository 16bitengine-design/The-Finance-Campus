"""Final technical quality checks on the encoded MP4, not just render success."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _rate(value: str) -> float:
    numerator, denominator = value.split("/", 1)
    divisor = float(denominator)
    if divisor == 0:
        raise ValueError("Invalid zero-denominator frame rate")
    return float(numerator) / divisor


def validate_final_video(
    video_path: str | Path,
    *,
    video_format: str,
    expected_fps: int = 30,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
) -> dict[str, Any]:
    """Verify codecs, dimensions, frame rate, audio levels and full-file decoding.

    This is an automated technical gate. It cannot judge whether illustrations
    are semantically appropriate or whether captions are visually attractive;
    those remain reviewable production artifacts.
    """
    path = Path(video_path)
    if not path.is_file() or path.stat().st_size < 10_000:
        raise RuntimeError("Final video is missing or implausibly small")
    ffmpeg_path, ffprobe_path = shutil.which(ffmpeg), shutil.which(ffprobe)
    if not ffmpeg_path or not ffprobe_path:
        raise RuntimeError("FFmpeg and ffprobe are required for final video QC")
    if video_format not in {"short", "long"} or expected_fps < 1:
        raise ValueError("Unsupported format or invalid expected frame rate")

    probe = subprocess.run(
        [
            ffprobe_path, "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,nb_frames,"
            "sample_rate,channels:format=duration,size",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    if probe.returncode:
        raise RuntimeError(f"ffprobe rejected final MP4: {probe.stderr.strip()}")
    try:
        data = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON for final MP4") from exc

    streams = data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise RuntimeError("Final MP4 must contain both video and narration audio streams")

    expected_size = (1080, 1920) if video_format == "short" else (1920, 1080)
    actual_size = (int(video.get("width", 0)), int(video.get("height", 0)))
    if actual_size != expected_size:
        raise RuntimeError(f"Final video dimensions {actual_size} do not match {expected_size}")
    if video.get("codec_name") != "h264":
        raise RuntimeError(f"Final video codec must be H.264, got {video.get('codec_name')!r}")
    if video.get("pix_fmt") != "yuv420p":
        raise RuntimeError(f"Final video pixel format must be yuv420p, got {video.get('pix_fmt')!r}")
    fps = _rate(str(video.get("avg_frame_rate", "0/0")))
    if abs(fps - expected_fps) > 0.05:
        raise RuntimeError(f"Final video frame rate {fps:.3f} does not match {expected_fps} fps")
    if audio.get("codec_name") != "aac":
        raise RuntimeError(f"Final narration codec must be AAC, got {audio.get('codec_name')!r}")
    sample_rate = int(audio.get("sample_rate", 0))
    channels = int(audio.get("channels", 0))
    if sample_rate != 24000 or channels != 1:
        raise RuntimeError(
            f"Final narration must be 24 kHz mono AAC; got {sample_rate} Hz, {channels} channel(s)"
        )

    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError("Final MP4 has no positive duration")
    frame_count_raw = video.get("nb_frames")
    frame_count = int(frame_count_raw) if frame_count_raw not in (None, "N/A") else None
    if frame_count is not None and abs(frame_count / fps - duration) > max(0.15, 2 / fps):
        raise RuntimeError("Encoded frame count and container duration are inconsistent")

    decode = subprocess.run(
        [ffmpeg_path, "-hide_banner", "-v", "error", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if decode.returncode or decode.stderr.strip():
        raise RuntimeError(f"Full-file decode check failed: {decode.stderr.strip()}")

    levels = subprocess.run(
        [
            ffmpeg_path, "-hide_banner", "-i", str(path),
            "-af", "volumedetect", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    level_text = levels.stderr + levels.stdout
    mean_match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", level_text)
    peak_match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", level_text)
    if levels.returncode or not mean_match or not peak_match:
        raise RuntimeError("Could not measure final narration loudness and peak level")
    mean_volume, peak_volume = float(mean_match.group(1)), float(peak_match.group(1))
    if mean_volume < -36:
        raise RuntimeError(f"Final narration is too quiet (mean {mean_volume:.1f} dB)")
    if peak_volume < -12:
        raise RuntimeError(f"Final narration peak is too quiet ({peak_volume:.1f} dB)")
    if peak_volume > -0.1:
        raise RuntimeError(f"Final narration risks clipping (peak {peak_volume:.1f} dB)")

    return {
        "passed": True,
        "video_codec": video["codec_name"],
        "pixel_format": video["pix_fmt"],
        "width": actual_size[0],
        "height": actual_size[1],
        "fps": round(fps, 3),
        "frame_count": frame_count,
        "audio_codec": audio["codec_name"],
        "audio_sample_rate": sample_rate,
        "audio_channels": channels,
        "audio_mean_volume_db": round(mean_volume, 2),
        "audio_peak_volume_db": round(peak_volume, 2),
        "duration_seconds": round(duration, 3),
        "file_size_bytes": path.stat().st_size,
        "full_file_decode_passed": True,
    }
