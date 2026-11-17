"""Frame-based whiteboard video renderer using Pillow and FFmpeg.

This renderer draws storyboard geometry progressively into real raster frames,
then encodes a playable MP4. Audio narration is intentionally a separate stage.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from finance_campus.storyboard import ILLUSTRATION_TYPES, validate_storyboard

PALETTE = {
    "navy": (16, 43, 85),
    "green": (22, 140, 67),
    "gold": (245, 184, 23),
    "white": (255, 255, 255),
    "black": (23, 32, 42),
}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _point(value: float, scale_x: float, scale_y: float) -> tuple[int, int]:
    return round(value * scale_x), round(value * scale_y)


def _draw_arrow(draw: ImageDraw.ImageDraw, coords: tuple[int, int, int, int], fill: tuple[int, int, int], width: int) -> None:
    x1, y1, x2, y2 = coords
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = max(12, width * 4)
    left = (round(x2 - length * math.cos(angle - 0.55)), round(y2 - length * math.sin(angle - 0.55)))
    right = (round(x2 - length * math.cos(angle + 0.55)), round(y2 - length * math.sin(angle + 0.55)))
    draw.polygon(((x2, y2), left, right), fill=fill)


def _draw_element(
    draw: ImageDraw.ImageDraw,
    element: dict[str, Any],
    progress: float,
    size: tuple[int, int],
) -> None:
    sx, sy = size[0] / 1000, size[1] / 562
    color = PALETTE[element.get("color", "navy")]
    width = max(2, round(4 * min(sx, sy)))
    kind = element["type"]

    if kind == "text":
        if progress < 1:
            return
        x, y = _point(element["x"], sx, sy)
        draw.text((x, y), element["text"], fill=color, font=_font(max(16, round(25 * sy))))
        return

    if kind == "circle":
        cx, cy = _point(element["cx"], sx, sy)
        radius = max(1, round(element["r"] * min(sx, sy) * progress))
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color, width=width)
        return

    if kind in ILLUSTRATION_TYPES:
        x, y = _point(element["x"], sx, sy)
        w, h = _point(element["width"], sx, sy)
        if w <= 0 or h <= 0 or progress <= 0:
            return
        right, bottom = x + w, y + h
        layer = Image.new("RGB", draw._image.size, PALETTE["white"])
        art = ImageDraw.Draw(layer)
        cx, cy = x + w // 2, y + h // 2
        if kind == "person":
            head = max(5, w // 7)
            art.ellipse((cx-head, y, cx+head, y+2*head), outline=color, width=width)
            shoulder = y + 2*head + 5
            waist = y + int(h*.66)
            art.line((cx, shoulder, cx, waist), fill=color, width=width)
            art.line((cx, shoulder+8, x+w//8, y+int(h*.55)), fill=color, width=width)
            art.line((cx, shoulder+8, right-w//8, y+int(h*.55)), fill=color, width=width)
            art.line((cx, waist, x+w//4, bottom), fill=color, width=width)
            art.line((cx, waist, right-w//4, bottom), fill=color, width=width)
        elif kind == "bank":
            roof_y = y + h//4
            art.polygon(((x, roof_y), (cx, y), (right, roof_y)), outline=color)
            art.line((x, roof_y, right, roof_y), fill=color, width=width)
            for col in range(4):
                px = x + w*(col+0.5)/4
                art.line((round(px), roof_y+width, round(px), bottom-h//6), fill=color, width=width)
            art.line((x, bottom-h//6, right, bottom-h//6), fill=color, width=width)
            art.line((x-w//20, bottom, right+w//20, bottom), fill=color, width=width)
        elif kind == "wallet":
            art.rounded_rectangle((x, y+h//4, right, bottom), radius=max(4,h//10), outline=color, width=width)
            art.rounded_rectangle((cx, y+h//2, right+w//12, y+h*3//4), radius=max(3,h//16), outline=color, width=width)
            art.ellipse((right-w//5, y+h*5//8, right-w//7, y+h*5//8+w//12), outline=color, width=width)
        elif kind == "house":
            roof_y = y+h//3
            art.line((x, roof_y, cx, y), fill=color, width=width)
            art.line((cx, y, right, roof_y), fill=color, width=width)
            art.rectangle((x+w//8, roof_y, right-w//8, bottom), outline=color, width=width)
            art.rectangle((cx-w//10, bottom-h//3, cx+w//10, bottom), outline=color, width=width)
        elif kind == "coin":
            art.ellipse((x, y, right, bottom), outline=color, width=width)
            art.ellipse((x+w//5, y+h//5, right-w//5, bottom-h//5), outline=color, width=width)
            art.text((cx-w//8, cy-h//4), "$", fill=color, font=_font(max(12,w//2)))
        elif kind == "money_note":
            art.rounded_rectangle((x, y+h//6, right, bottom-h//6), radius=max(3,h//12), outline=color, width=width)
            art.ellipse((cx-w//9, cy-h//8, cx+w//9, cy+h//8), outline=color, width=width)
            art.line((x+w//8, y+h//3, x+w//4, y+h//3), fill=color, width=width)
            art.line((right-w//4, bottom-h//3, right-w//8, bottom-h//3), fill=color, width=width)
        elif kind == "savings_jar":
            art.line((x+w//4, y+h//5, right-w//4, y+h//5), fill=color, width=width)
            art.rounded_rectangle((x+w//5, y+h//4, right-w//5, bottom), radius=max(4,w//8), outline=color, width=width)
            art.line((cx-w//8, y+h//5, cx+w//8, y+h//5), fill=color, width=width)
            art.ellipse((cx-w//7, cy-h//8, cx+w//7, cy+h//8), outline=color, width=width)
        visible_right = x + max(1, round(w * progress))
        crop = layer.crop((x, y, min(right, visible_right), bottom))
        draw._image.paste(crop, (x, y))
        return

    if kind == "rect":
        x, y = _point(element["x"], sx, sy)
        w, h = _point(element["width"] * progress, sx, sy)
        if w > 0 and h > 0:
            draw.rounded_rectangle((x, y, x + w, y + h), radius=max(2, width * 2), outline=color, width=width)
        return

    x1, y1 = _point(element["x1"], sx, sy)
    x2, y2 = _point(element["x2"], sx, sy)
    end = (round(x1 + (x2 - x1) * progress), round(y1 + (y2 - y1) * progress))
    if kind == "arrow" and progress >= 1:
        _draw_arrow(draw, (x1, y1, end[0], end[1]), color, width)
    else:
        draw.line((x1, y1, end[0], end[1]), fill=color, width=width)


def render_video(
    storyboard: dict[str, Any],
    output_path: str | Path,
    *,
    video_format: str = "short",
    fps: int = 30,
    draw_fps: int = 12,
    ffmpeg: str = "ffmpeg",
    keep_frames: bool = False,
) -> Path:
    """Render a storyboard into an MP4 using progressive drawing frames."""
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Invalid storyboard: " + "; ".join(errors))
    if video_format not in {"short", "long"}:
        raise ValueError("video_format must be 'short' or 'long'")
    if fps < 1 or draw_fps < 1 or draw_fps > fps:
        raise ValueError("fps and draw_fps must be positive and draw_fps cannot exceed fps")
    executable = shutil.which(ffmpeg)
    if not executable:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and ensure it is on PATH.")

    width, height = (1080, 1920) if video_format == "short" else (1920, 1080)
    draw_width, draw_height = (1080, 607) if video_format == "short" else (1920, 1080)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame_dir = target.parent / f".{target.stem}_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_number = 0
    try:
        for scene in storyboard["scenes"]:
            duration = float(scene["duration_seconds"])
            total_frames = max(1, math.ceil(duration * draw_fps))
            elements = scene["elements"]
            for frame_index in range(total_frames):
                drawing = Image.new("RGB", (draw_width, draw_height), PALETTE["white"])
                draw = ImageDraw.Draw(drawing)
                elapsed = frame_index / draw_fps
                for element_index, element in enumerate(elements):
                    # Reveal each drawing in sequence during the first 65% of its scene.
                    reveal_window = max(0.15, duration * 0.65 / max(1, len(elements)))
                    start = element_index * reveal_window
                    progress = min(1.0, max(0.0, (elapsed - start) / reveal_window))
                    if progress > 0:
                        _draw_element(draw, element, progress, (draw_width, draw_height))
                if video_format == "short":
                    image = Image.new("RGB", (width, height), PALETTE["white"])
                    image.paste(drawing, (0, (height - draw_height) // 2))
                else:
                    image = drawing
                image.save(frame_dir / f"frame_{frame_number:06d}.png", optimize=True)
                frame_number += 1

        if frame_number == 0:
            raise RuntimeError("Renderer produced no frames")
        command = [
            executable, "-hide_banner", "-loglevel", "error", "-y",
            "-framerate", str(draw_fps), "-i", str(frame_dir / "frame_%06d.png"),
            "-vf", f"fps={fps},format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-movflags", "+faststart", str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"FFmpeg encoding failed: {completed.stderr.strip()}")
        if not target.is_file() or target.stat().st_size < 1024:
            raise RuntimeError("FFmpeg did not produce a valid non-empty MP4")
        probe = subprocess.run(
            [executable, "-hide_banner", "-i", str(target), "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        )
        if "Video:" not in (probe.stderr + probe.stdout):
            raise RuntimeError("Rendered MP4 failed FFmpeg playback/stream validation")
        return target
    finally:
        if not keep_frames:
            shutil.rmtree(frame_dir, ignore_errors=True)


def render_video_from_file(
    storyboard_path: str | Path,
    output_path: str | Path,
    *,
    video_format: str = "short",
    fps: int = 30,
) -> Path:
    with Path(storyboard_path).open("r", encoding="utf-8") as handle:
        storyboard = json.load(handle)
    return render_video(storyboard, output_path, video_format=video_format, fps=fps)
