"""Frame-based whiteboard video renderer using Pillow and FFmpeg.

This renderer draws storyboard geometry progressively into real raster frames,
then encodes a playable MP4. Narration generation is upstream; supplied audio and SRT captions can be muxed and burned in during rendering.
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


def _point(x: float, y: float, scale_x: float, scale_y: float) -> tuple[int, int]:
    return round(x * scale_x), round(y * scale_y)


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
    coordinate_size: tuple[float, float] = (1000, 562),
) -> None:
    sx, sy = size[0] / coordinate_size[0], size[1] / coordinate_size[1]
    color = PALETTE[element.get("color", "navy")]
    width = max(2, round(4 * min(sx, sy)))
    kind = element["type"]

    if kind == "text":
        if progress < 1:
            return
        x, y = _point(element["x"], element["y"], sx, sy)
        draw.text((x, y), element["text"], fill=color, font=_font(max(16, round(25 * sy))))
        return

    if kind == "circle":
        cx, cy = _point(element["cx"], element["cy"], sx, sy)
        radius = max(1, round(element["r"] * min(sx, sy) * progress))
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color, width=width)
        return

    if kind in ILLUSTRATION_TYPES:
        x, y = _point(element["x"], element["y"], sx, sy)
        w, h = round(element["width"] * sx), round(element["height"] * sy)
        if w <= 0 or h <= 0 or progress <= 0:
            return
        right, bottom = x + w, y + h
        layer = Image.new("RGB", draw._image.size, PALETTE["white"])
        art = ImageDraw.Draw(layer)
        cx, cy = x + w // 2, y + h // 2
        if kind == "person":
            head = max(5, w // 7)
            art.ellipse((cx-head, y, cx+head, y+2*head), outline=color, width=width)
            eye_y = y + head
            eye_r = max(2, width)
            art.ellipse((cx-head//3-eye_r, eye_y-eye_r, cx-head//3+eye_r, eye_y+eye_r), fill=color)
            art.ellipse((cx+head//3-eye_r, eye_y-eye_r, cx+head//3+eye_r, eye_y+eye_r), fill=color)
            art.arc((cx-head//3, y+head, cx+head//3, y+int(head*1.65)), 10, 170, fill=color, width=width)
            neck_y = y + 2*head
            shoulder = neck_y + max(8, h//24)
            waist = y + int(h*.66)
            art.line((cx, neck_y, cx, shoulder), fill=color, width=width)
            art.polygon(((cx-w//4, shoulder), (cx+w//4, shoulder), (cx+w//6, waist), (cx-w//6, waist)), outline=color)
            elbow_y = y + int(h*.43)
            hand_r = max(4, width*2)
            left_hand = (x+w//10, y+int(h*.56))
            right_hand = (right-w//10, y+int(h*.56))
            art.line((cx-w//4, shoulder+width, x+w//5, elbow_y, left_hand[0], left_hand[1]), fill=color, width=width)
            art.line((cx+w//4, shoulder+width, right-w//5, elbow_y, right_hand[0], right_hand[1]), fill=color, width=width)
            for hx, hy in (left_hand, right_hand):
                art.ellipse((hx-hand_r, hy-hand_r, hx+hand_r, hy+hand_r), outline=color, width=width)
            art.line((cx-w//7, waist, x+w//4, bottom-h//12), fill=color, width=width)
            art.line((cx+w//7, waist, right-w//4, bottom-h//12), fill=color, width=width)
            art.line((x+w//4, bottom-h//12, x+w//8, bottom-h//20), fill=color, width=width)
            art.line((right-w//4, bottom-h//12, right-w//8, bottom-h//20), fill=color, width=width)
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
        x, y = _point(element["x"], element["y"], sx, sy)
        w = round(element["width"] * progress * sx)
        h = round(element["height"] * progress * sy)
        if w > 0 and h > 0:
            draw.rounded_rectangle((x, y, x + w, y + h), radius=max(2, width * 2), outline=color, width=width)
        return

    x1, y1 = _point(element["x1"], element["y1"], sx, sy)
    x2, y2 = _point(element["x2"], element["y2"], sx, sy)
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
    draw_fps: int = 24,
    ffmpeg: str = "ffmpeg",
    keep_frames: bool = False,
    audio_path: str | Path | None = None,
    captions_path: str | Path | None = None,
    transition_seconds: float = 0.25,
) -> Path:
    """Render a storyboard into an MP4 using progressive drawing frames."""
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Invalid storyboard: " + "; ".join(errors))
    if video_format not in {"short", "long"}:
        raise ValueError("video_format must be 'short' or 'long'")
    if fps < 1 or draw_fps < 1 or draw_fps > fps:
        raise ValueError("fps and draw_fps must be positive and draw_fps cannot exceed fps")
    if not math.isfinite(transition_seconds) or transition_seconds < 0:
        raise ValueError("transition_seconds must be a finite non-negative number")
    executable = shutil.which(ffmpeg)
    if not executable:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and ensure it is on PATH.")
    audio = Path(audio_path).resolve() if audio_path is not None else None
    captions = Path(captions_path).resolve() if captions_path is not None else None
    for label, media_path in (("audio", audio), ("captions", captions)):
        if media_path is not None and (not media_path.is_file() or media_path.stat().st_size == 0):
            raise ValueError(f"{label} file does not exist or is empty: {media_path}")

    width, height = (1080, 1920) if video_format == "short" else (1920, 1080)
    canvas = storyboard.get("canvas", {"width": 1000, "height": 562})
    coordinate_size = (float(canvas.get("width", 1000)), float(canvas.get("height", 562)))
    scale = min(width / coordinate_size[0], height / coordinate_size[1])
    draw_width = max(1, round(coordinate_size[0] * scale))
    draw_height = max(1, round(coordinate_size[1] * scale))
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
                        _draw_element(draw, element, progress, (draw_width, draw_height), coordinate_size)
                image = Image.new("RGB", (width, height), PALETTE["white"])
                image.paste(drawing, ((width - draw_width) // 2, (height - draw_height) // 2))
                image.save(frame_dir / f"frame_{frame_number:06d}.png", optimize=True)
                frame_number += 1

        if frame_number == 0:
            raise RuntimeError("Renderer produced no frames")
        filter_chain = f"fps={fps},format=yuv420p"
        if captions is not None:
            caption_name = str(captions).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")
            style = "FontName=DejaVu Sans,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00102B55,BorderStyle=1,Outline=2,Alignment=2,MarginV=90"
            filter_chain += f",subtitles='{caption_name}':force_style='{style}'"
        command = [
            executable, "-hide_banner", "-loglevel", "error", "-y",
            "-framerate", str(draw_fps), "-i", str(frame_dir / "frame_%06d.png"),
        ]
        if audio is not None:
            command.extend(["-i", str(audio)])
        command.extend(["-vf", filter_chain, "-map", "0:v:0"])
        if audio is not None:
            total_duration = sum(float(scene["duration_seconds"]) for scene in storyboard["scenes"])
            command.extend(["-map", "1:a:0", "-af", "apad", "-t", f"{total_duration:.3f}", "-c:a", "aac", "-b:a", "192k"])
        else:
            command.append("-an")
        command.extend([
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-movflags", "+faststart", str(target),
        ])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"FFmpeg encoding failed: {completed.stderr.strip()}")
        if not target.is_file() or target.stat().st_size < 1024:
            raise RuntimeError("FFmpeg did not produce a valid non-empty MP4")
        probe = subprocess.run(
            [executable, "-hide_banner", "-i", str(target), "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        )
        probe_output = probe.stderr + probe.stdout
        if "Video:" not in probe_output:
            raise RuntimeError("Rendered MP4 failed FFmpeg playback/stream validation")
        if audio is not None and "Audio:" not in probe_output:
            raise RuntimeError("Rendered MP4 is missing its requested narration audio stream")
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
    audio_path: str | Path | None = None,
    captions_path: str | Path | None = None,
    transition_seconds: float = 0.25,
) -> Path:
    with Path(storyboard_path).open("r", encoding="utf-8") as handle:
        storyboard = json.load(handle)
    return render_video(
        storyboard, output_path, video_format=video_format, fps=fps,
        audio_path=audio_path, captions_path=captions_path,
        transition_seconds=transition_seconds,
    )
