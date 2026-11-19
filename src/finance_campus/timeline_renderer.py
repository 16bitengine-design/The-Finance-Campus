"""Multi-scene 2D renderer built on the layered illustration compositor."""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from finance_campus.layered_animation import iter_layered_frames, validate_layered_scene


class TimelineRenderError(ValueError):
    """Raised when a timeline is invalid or cannot be rendered."""


def validate_timeline(timeline: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(timeline, dict):
        return ["timeline must be an object"]
    canvas = timeline.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must define width and height")
    else:
        for key in ("width", "height"):
            value = canvas.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                errors.append(f"canvas.{key} must be a positive integer")
    fps = timeline.get("fps", 30)
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        errors.append("fps must be a positive integer")
    scenes = timeline.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty ordered list")
    else:
        for index, item in enumerate(scenes):
            if not isinstance(item, dict):
                errors.append(f"scenes[{index}] must be an object")
                continue
            for field in ("scene", "asset_root"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"scenes[{index}].{field} must be a non-empty path")
    return errors


def _frames(timeline: dict[str, Any], manifest_dir: Path) -> Iterator[Any]:
    canvas = timeline["canvas"]
    for index, entry in enumerate(timeline["scenes"]):
        scene_path = (manifest_dir / entry["scene"]).resolve()
        asset_root = (manifest_dir / entry["asset_root"]).resolve()
        try:
            scene = json.loads(scene_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TimelineRenderError(f"scene {index} cannot be loaded: {scene_path}: {exc}") from exc
        errors = validate_layered_scene(scene)
        if errors:
            raise TimelineRenderError(f"scene {index} is invalid: {'; '.join(errors)}")
        if (scene["canvas"]["width"], scene["canvas"]["height"]) != (canvas["width"], canvas["height"]):
            raise TimelineRenderError(f"scene {index} canvas does not match timeline canvas")
        yield from iter_layered_frames(scene, asset_root, fps=timeline.get("fps", 30))


def render_2d_timeline(
    timeline_path: str | Path, output_path: str | Path, *, ffmpeg: str = "ffmpeg"
) -> dict[str, Any]:
    """Stream ordered layered scenes to an H.264 MP4 without buffering all frames."""
    manifest_path = Path(timeline_path).resolve()
    timeline = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_timeline(timeline)
    if errors:
        raise TimelineRenderError("; ".join(errors))
    ffmpeg_path = shutil.which(ffmpeg)
    if not ffmpeg_path:
        raise TimelineRenderError("FFmpeg executable was not found")
    width, height = timeline["canvas"]["width"], timeline["canvas"]["height"]
    fps = timeline.get("fps", 30)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pix_fmt", "rgba", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(destination),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_count = 0
    try:
        assert process.stdin is not None
        for frame in _frames(timeline, manifest_path.parent):
            process.stdin.write(frame.tobytes())
            frame_count += 1
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code != 0 or frame_count == 0 or not destination.is_file():
        raise TimelineRenderError(f"FFmpeg timeline render failed ({return_code}): {stderr}")
    return {
        "passed": True,
        "renderer": "2d_layered_timeline",
        "frames": frame_count,
        "fps": fps,
        "width": width,
        "height": height,
        "duration_seconds": round(frame_count / fps, 3),
        "output": str(destination),
    }
