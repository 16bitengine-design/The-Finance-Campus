"""Frame-based whiteboard video renderer using Pillow and FFmpeg.

This renderer draws storyboard geometry progressively into real raster frames,
then encodes a playable MP4. Narration generation is upstream; supplied audio and SRT captions can be muxed and burned in during rendering.
"""
from __future__ import annotations

import itertools
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


def _motion_position(element: dict[str, Any], elapsed: float) -> dict[str, Any]:
    """Return an element positioned along its optional, time-based motion path."""
    animated = dict(element)
    motion = element.get("motion")
    if isinstance(motion, dict):
        start, end = float(motion["start_seconds"]), float(motion["end_seconds"])
        progress = min(1.0, max(0.0, (elapsed - start) / (end - start)))
        if motion.get("easing") == "ease_in_out":
            progress = progress * progress * (3 - 2 * progress)
        animated["x"] = round(float(motion["from_x"]) + (float(motion["to_x"]) - float(motion["from_x"])) * progress)
        animated["y"] = round(float(motion["from_y"]) + (float(motion["to_y"]) - float(motion["from_y"])) * progress)
    walk = element.get("walk_cycle")
    if isinstance(walk, dict):
        walk_start, walk_end = float(walk["start_seconds"]), float(walk["end_seconds"])
        if walk_start <= elapsed <= walk_end:
            cycle = max(.1, float(walk.get("cycle_seconds", .52)))
            walk_progress = (elapsed - walk_start) / cycle
            animated["walk_phase"] = walk_progress % 1.0
            animated["body_bob"] = round(math.sin(walk_progress * 2 * math.pi) * 3)
        else:
            animated["walk_phase"] = 0.0
            animated["body_bob"] = 0
    opening = element.get("open_animation")
    if isinstance(opening, dict):
        open_start, open_end = float(opening["start_seconds"]), float(opening["end_seconds"])
        open_progress = min(1.0, max(0.0, (elapsed - open_start) / (open_end - open_start)))
        if opening.get("easing") == "ease_out":
            open_progress = 1 - (1 - open_progress) ** 3
        animated["open_progress"] = open_progress
    interaction = element.get("interaction_animation")
    target = element.get("interaction_target")
    if isinstance(interaction, dict) and isinstance(target, dict):
        action_start = float(interaction["start_seconds"])
        action_end = float(interaction["end_seconds"])
        action_progress = min(1.0, max(0.0, (elapsed - action_start) / (action_end - action_start)))
        if interaction.get("easing") == "ease_out":
            action_progress = 1 - (1 - action_progress) ** 3
        animated["interaction_target"] = {
            "x": round(float(interaction["from_x"]) + (float(target["x"]) - float(interaction["from_x"])) * action_progress),
            "y": round(float(interaction["from_y"]) + (float(target["y"]) - float(interaction["from_y"])) * action_progress),
        }
    return animated


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


def _ellipse_path(box: tuple[int, int, int, int], steps: int = 48) -> list[tuple[int, int]]:
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    rx, ry = (right - left) / 2, (bottom - top) / 2
    return [
        (round(cx + rx * math.cos(2 * math.pi * index / steps)),
         round(cy + ry * math.sin(2 * math.pi * index / steps)))
        for index in range(steps + 1)
    ]


def _progress_endpoint(
    strokes: list[list[tuple[int, int]]], progress: float,
) -> tuple[int, int] | None:
    """Find the current tip position along the ordered drawing path."""
    if not strokes or progress <= 0:
        return None
    lengths = [sum(math.dist(a, b) for a, b in itertools.pairwise(path)) for path in strokes]
    total = sum(lengths)
    if total <= 0:
        return None
    remaining = min(1.0, progress) * total
    endpoint = strokes[0][0]
    for path, length in zip(strokes, lengths):
        if not path or length <= 0:
            continue
        endpoint = path[0]
        if remaining >= length:
            remaining -= length
            endpoint = path[-1]
            continue
        for first, second in itertools.pairwise(path):
            segment = math.dist(first, second)
            if segment <= 0:
                continue
            if remaining <= segment:
                fraction = remaining / segment
                return (
                    round(first[0] + (second[0] - first[0]) * fraction),
                    round(first[1] + (second[1] - first[1]) * fraction),
                )
            remaining -= segment
            endpoint = second
        return endpoint
    return endpoint


def _draw_pen_hand(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    color: tuple[int, int, int],
    scale: float,
) -> None:
    """Draw a small hand gripping a colored marker at the active stroke tip."""
    x, y = tip
    # Keep the drawing hand subordinate to the artwork. The previous palm
    # was almost 100 px wide at 1080p and read as a floating brown circle.
    unit = max(2, round(6 * scale))
    skin = (224, 176, 137)
    skin_shadow = (168, 119, 91)
    dark = (70, 76, 84)
    # Slim marker barrel, nib, cap and a compact gripping hand.
    draw.line((x - unit * 3, y + unit * 3, x + unit, y - unit),
              fill=dark, width=max(2, unit // 2))
    draw.line((x - unit * 3, y + unit * 3, x - unit * 5, y + unit * 5),
              fill=color, width=max(3, unit // 2))
    draw.line((x + unit, y - unit, x + unit * 2, y - unit * 2),
              fill=dark, width=max(2, unit // 3))
    palm = (x - unit * 4, y + unit * 2, x + unit, y + unit * 7)
    draw.ellipse(palm, fill=skin, outline=skin_shadow, width=max(1, unit // 4))
    # Short finger arcs visibly wrap around the marker instead of forming a blob.
    for offset in (0, 1):
        px = x - unit * (2 + offset)
        py = y + unit * (3 + offset)
        draw.arc((px - unit, py, px + unit * 2, py + unit * 3),
                 start=185, end=330, fill=skin_shadow, width=max(1, unit // 3))


def _draw_progressive_strokes(
    draw: ImageDraw.ImageDraw,
    strokes: list[list[tuple[int, int]]],
    progress: float,
    color: tuple[int, int, int],
    width: int,
) -> None:
    """Reveal ordered pen strokes by travelled path length, not by wiping an image."""
    if not strokes or progress <= 0:
        return
    remaining = min(1.0, progress) * sum(
        sum(math.dist(a, b) for a, b in itertools.pairwise(path)) for path in strokes
    )
    for path in strokes:
        length = sum(math.dist(a, b) for a, b in itertools.pairwise(path))
        if remaining <= 0:
            break
        if length <= 0:
            continue
        if remaining >= length:
            draw.line(path, fill=color, width=width, joint="curve")
            remaining -= length
            continue
        travelled = 0.0
        partial = [path[0]]
        for first, second in itertools.pairwise(path):
            segment = math.dist(first, second)
            if travelled + segment <= remaining:
                partial.append(second)
                travelled += segment
                continue
            fraction = (remaining - travelled) / segment if segment else 0
            partial.append((
                round(first[0] + (second[0] - first[0]) * fraction),
                round(first[1] + (second[1] - first[1]) * fraction),
            ))
            break
        if len(partial) > 1:
            draw.line(partial, fill=color, width=width, joint="curve")
        break


def _draw_active_hand(
    draw: ImageDraw.ImageDraw,
    strokes: list[list[tuple[int, int]]],
    progress: float,
    color: tuple[int, int, int],
    scale: float,
) -> None:
    if 0 < progress < 1:
        tip = _progress_endpoint(strokes, progress)
        if tip is not None:
            _draw_pen_hand(draw, tip, color, scale)


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

    if progress <= 0:
        return
    if kind == "text":
        if progress >= 1:
            x, y = _point(element["x"], element["y"], sx, sy)
            draw.text((x, y), element["text"], fill=color, font=_font(max(16, round(25 * sy))))
        return

    if kind == "circle":
        cx, cy = _point(element["cx"], element["cy"], sx, sy)
        radius = max(1, round(element["r"] * min(sx, sy)))
        path = _ellipse_path((cx-radius, cy-radius, cx+radius, cy+radius))
        _draw_progressive_strokes(draw, [path], progress, color, width)
        _draw_active_hand(draw, [path], progress, color, min(sx, sy))
        return

    if kind in ILLUSTRATION_TYPES:
        y_position = float(element["y"]) + float(element.get("body_bob", 0))
        x, y = _point(element["x"], y_position, sx, sy)
        w, h = round(element["width"] * sx), round(element["height"] * sy)
        if w <= 0 or h <= 0:
            return
        right, bottom = x + w, y + h
        cx, cy = x + w // 2, y + h // 2
        strokes: list[list[tuple[int, int]]] = []

        def path(*points: tuple[int, int]) -> None:
            strokes.append(list(points))

        def ellipse(box: tuple[int, int, int, int]) -> None:
            strokes.append(_ellipse_path(box))

        def rect(left: int, top: int, r: int, b: int) -> None:
            path((left, top), (r, top), (r, b), (left, b), (left, top))

        if kind == "person":
            head = max(7, w // 5)
            ellipse((cx-head, y, cx+head, y+2*head))
            # Facial details are deliberately separate pen strokes.
            eye_y, eye_r = y + head, max(2, width)
            path((cx-head//3-eye_r, eye_y), (cx-head//3+eye_r, eye_y))
            path((cx+head//3-eye_r, eye_y), (cx+head//3+eye_r, eye_y))
            pose = element.get("pose", "neutral")
            expression = element.get("expression", "calm")
            mouth_y = y + int(head*1.65)
            if expression in {"worried", "overwhelmed"}:
                path((cx-head//3, mouth_y+head//12), (cx, mouth_y-head//10), (cx+head//3, mouth_y+head//12))
                path((cx-head//2, y+head//2), (cx-head//5, y+head//3))
                path((cx+head//5, y+head//3), (cx+head//2, y+head//2))
            elif expression == "determined":
                path((cx-head//3, mouth_y), (cx+head//3, mouth_y))
                path((cx-head//2, y+head//3), (cx-head//5, y+head//3))
                path((cx+head//5, y+head//3), (cx+head//2, y+head//3))
            else:
                path((cx-head//3, mouth_y), (cx, mouth_y+head//8), (cx+head//3, mouth_y))
            neck_y = y + 2*head
            shoulder = neck_y + max(8, h//24)
            waist = y + int(h*.66)
            path((cx, neck_y), (cx, shoulder))
            torso = [
                (cx-w//3, shoulder), (cx+w//3, shoulder),
                (cx+w//4, waist), (cx-w//4, waist),
            ]
            # A faint shirt fill gives the character visual weight while the
            # navy outline is still revealed progressively like marker ink.
            if progress >= .62:
                draw.polygon(torso, fill=(246, 249, 252))
            path(*torso, torso[0])
            path((cx-w//12, shoulder+width), (cx, shoulder+width*4), (cx+w//12, shoulder+width))
            path((cx, shoulder+width*4), (cx, waist-h//14))
            rect(cx+w//12, shoulder+h//12, cx+w//4, shoulder+h//5)
            # Clothing and facial details turn the protagonist into a character,
            # rather than a generic stick figure. Each detail remains an ordered
            # pen stroke so it participates in the whiteboard reveal.
            path((cx-head//2, y+head//2), (cx-head//4, y+head*2//3),
                 (cx, y+head), (cx+head//4, y+head*2//3),
                 (cx+head//2, y+head//2))
            path((cx, y+head), (cx, shoulder+h//5))
            path((cx-w//4, shoulder+h//12), (cx-w//3, shoulder+h//5),
                 (cx-w//5, shoulder+h//3))
            path((cx+w//4, shoulder+h//12), (cx+w//3, shoulder+h//5),
                 (cx+w//5, shoulder+h//3))
            path((cx+w//4, waist-h//10), (cx+w//7, waist-h//10),
                 (cx+w//7, waist-h//3), (cx+w//4, waist-h//3))
            path((cx-w//6, waist), (cx+w//6, waist))
            # Clear trouser legs and broad shoes replace the old thin,
            # disconnected stick-like feet.
            path((cx-w//7, waist), (cx-w//5, bottom-h//8),
                 (cx-w//4, bottom-h//18))
            path((cx+w//7, waist), (cx+w//5, bottom-h//8),
                 (cx+w//4, bottom-h//18))
            path((cx-w//4, bottom-h//18), (cx-w//3, bottom),
                 (cx-w//10, bottom))
            path((cx+w//4, bottom-h//18), (cx+w//3, bottom),
                 (cx+w//10, bottom))
            path((cx-w//3, bottom), (cx-w//10, bottom))
            path((cx+w//10, bottom), (cx+w//3, bottom))
            # Brows and hairline make expressions easier to read at phone size.
            path((cx-head//2, y+head//3), (cx-head//5, y+head//4))
            path((cx+head//5, y+head//4), (cx+head//2, y+head//3))
            path((cx-head, y+head//3), (cx-head//2, y-width),
                 (cx, y+head//8), (cx+head//2, y-width),
                 (cx+head, y+head//3))
            path((cx-head//2, y+head//2), (cx-head//3, y+head//3))
            ellipse((cx-head-width, y+head//2, cx-head+width, y+head))
            ellipse((cx+head-width, y+head//2, cx+head+width, y+head))
            elbow_y = y + int(h*.43)
            left_shoulder = (cx-w//4, shoulder+width)
            right_shoulder = (cx+w//4, shoulder+width)
            left_hand = (x+w//10, y+int(h*.56))
            right_hand = (right-w//10, y+int(h*.56))
            if pose in {"worried", "overwhelmed"}:
                left_hand = (cx-w//2, y+int(h*.22))
                right_hand = (cx+w//2, y+int(h*.22))
                path(left_shoulder, (x+w//12, y+int(h*.40)), left_hand)
                path(right_shoulder, (right-w//12, y+int(h*.40)), right_hand)
            elif pose == "thinking":
                left_hand = (x+w//10, y+int(h*.56))
                right_hand = (cx+w//2, y+int(h*.25))
                path(left_shoulder, (x+w//5, elbow_y), left_hand)
                path(right_shoulder, (right-w//8, y+int(h*.36)), right_hand)
            elif pose == "reaching":
                left_hand = (x+w//10, y+int(h*.56))
                right_hand = (right, y+int(h*.32))
                path(left_shoulder, (x+w//5, elbow_y), left_hand)
                path(right_shoulder, (right-w//8, y+int(h*.42)), right_hand)
            elif pose == "determined":
                left_hand = (x+w//10, y+int(h*.56))
                right_hand = (right-w//5, y+int(h*.12))
                path(left_shoulder, (x+w//5, elbow_y), left_hand)
                path(right_shoulder, (right-w//8, y+int(h*.32)), right_hand)
            elif pose == "celebrating":
                left_hand = (x+w//8, y+int(h*.12))
                right_hand = (right-w//8, y+int(h*.12))
                path(left_shoulder, (x+w//10, y+int(h*.32)), left_hand)
                path(right_shoulder, (right-w//10, y+int(h*.32)), right_hand)
            else:
                path(left_shoulder, (x+w//5, elbow_y), left_hand)
                path(right_shoulder, (right-w//5, elbow_y), right_hand)

            # When a scene specifies an interaction, the protagonist's hand
            # reaches the actual prop instead of stopping at a generic pose.
            target = element.get("interaction_target")
            if isinstance(target, dict) and pose != "celebrating":
                target_x = round(float(target["x"]) * sx)
                target_y = round(float(target["y"]) * sy)
                elbow = (
                    round((right_shoulder[0] + target_x) * .52),
                    round((right_shoulder[1] + target_y) * .48),
                )
                right_hand = (target_x, target_y)
                path(right_shoulder, elbow, right_hand)
            for hx, hy in (left_hand, right_hand):
                ellipse((hx-width*2, hy-width*2, hx+width*2, hy+width*2))
            walk_phase = float(element.get("walk_phase", 0.0))
            stride = round(math.sin(walk_phase * 2 * math.pi) * w * .075)
            path((cx-w//7, waist), (x+w//4-stride, bottom-h//12), (x+w//8-stride, bottom-h//20))
            path((cx+w//7, waist), (right-w//4+stride, bottom-h//12), (right-w//8+stride, bottom-h//20))
        elif kind == "bank":
            roof_y = y + h//4
            path((x, roof_y), (cx, y), (right, roof_y), (x, roof_y))
            path((x, roof_y), (right, roof_y))
            for col in range(4):
                px = round(x + w*(col+0.5)/4)
                path((px, roof_y+width), (px, bottom-h//6))
            path((x, bottom-h//6), (right, bottom-h//6))
            path((x-w//20, bottom), (right+w//20, bottom))
            rect(cx-w//5, roof_y+h//14, cx+w//5, roof_y+h//5)
            rect(cx-w//10, bottom-h//3, cx+w//10, bottom-h//6)
            if progress >= 1:
                draw.text((cx-w//10, roof_y+h//13), "BANK", fill=color, font=_font(max(10,w//15)))
        elif kind == "wallet":
            # Rounded wallet is represented by a hand-drawn multi-segment outline.
            path((x+w//10, y+h//4), (right-w//10, y+h//4), (right, y+h//3),
                 (right, bottom-h//10), (right-w//10, bottom), (x+w//10, bottom),
                 (x, bottom-h//10), (x, y+h//3), (x+w//10, y+h//4))
            open_progress = float(element.get("open_progress", 0.0))
            flap_lift = round(h * .30 * open_progress)
            if open_progress > 0.0:
                path((cx, y+h//2), (cx+w//10, y+h//2-flap_lift),
                     (right+w//12, y+h//2-flap_lift), (right+w//12, y+h//2))
            else:
                path((cx, y+h//2), (right+w//12, y+h//2), (right+w//12, y+h*3//4),
                     (cx, y+h*3//4), (cx, y+h//2))
            ellipse((right-w//5, y+h*5//8, right-w//7, y+h*5//8+w//12))
            path((x+w//8, y+h//3), (cx-w//12, y+h//3))
            path((x+w//8, y+h//2), (cx-w//12, y+h//2))
            path((x+w//3, y+h//5), (x+w//2, y+h//12), (x+w*2//3, y+h//5))
        elif kind == "house":
            roof_y = y+h//3
            path((x, roof_y), (cx, y), (right, roof_y))
            rect(x+w//8, roof_y, right-w//8, bottom)
            rect(cx-w//10, bottom-h//3, cx+w//10, bottom)
        elif kind == "phone":
            rect(x+w//5, y, right-w//5, bottom)
            path((x+w//4, y+h//7), (right-w//4, y+h//7))
            path((x+w//4, bottom-h//5), (right-w//4, bottom-h//5))
            ellipse((cx-width, bottom-h//10, cx+width, bottom-h//10+width*2))
        elif kind == "shield":
            path((cx, y), (right, y+h//5), (right-w//10, y+h*3//5),
                 (cx, bottom), (x+w//10, y+h*3//5), (x, y+h//5), (cx, y))
            path((x+w//4, y+h//2), (cx-width, y+h*2//3), (right-w//4, y+h//3))
        elif kind == "calendar":
            rect(x, y+h//8, right, bottom)
            path((x, y+h//3), (right, y+h//3))
            path((x+w//4, y), (x+w//4, y+h//4))
            path((right-w//4, y), (right-w//4, y+h//4))
            for row in (0.52, 0.72):
                path((x+w//5, y+int(h*row)), (right-w//5, y+int(h*row)))
        elif kind == "chart":
            path((x+w//8, y+h//10), (x+w//8, bottom), (right, bottom))
            path((x+w//5, y+h*4//5), (x+w*2//5, y+h*3//5),
                 (x+w*3//5, y+h*2//3), (right-w//8, y+h//5))
        elif kind == "basket":
            path((x+w//10, y+h//3), (right-w//10, y+h//3),
                 (right-w//5, bottom), (x+w//5, bottom), (x+w//10, y+h//3))
            path((x+w//4, y+h//3), (cx, y), (right-w//4, y+h//3))
            path((x+w//3, y+h//2), (x+w*2//5, bottom-h//10))
            path((cx, y+h//2), (cx, bottom-h//10))
            path((right-w//3, y+h//2), (right-w*2//5, bottom-h//10))
        elif kind == "coin":
            ellipse((x, y, right, bottom))
            ellipse((x+w//5, y+h//5, right-w//5, bottom-h//5))
            if progress >= 1:
                draw.text((cx-w//8, cy-h//4), "¤", fill=color, font=_font(max(12,w//2)))
        elif kind == "money_note":
            rect(x, y+h//6, right, bottom-h//6)
            ellipse((cx-w//9, cy-h//8, cx+w//9, cy+h//8))
            path((x+w//8, y+h//3), (x+w//4, y+h//3))
            path((right-w//4, bottom-h//3), (right-w//8, bottom-h//3))
            path((cx-w//12, y+h//4), (cx+w//12, y+h//4))
            path((cx-w//12, bottom-h//4), (cx+w//12, bottom-h//4))
        elif kind == "savings_jar":
            path((x+w//4, y+h//5), (right-w//4, y+h//5))
            path((x+w//5, y+h//4), (x+w//5, bottom-h//10),
                 (x+w//4, bottom), (right-w//4, bottom),
                 (right-w//5, bottom-h//10), (right-w//5, y+h//4),
                 (x+w//5, y+h//4))
            path((cx-w//8, y+h//5), (cx+w//8, y+h//5))
            ellipse((cx-w//7, cy-h//8, cx+w//7, cy+h//8))
            coin_y = bottom-h//5
            for offset in (-w//12, 0, w//12):
                ellipse((cx+offset-w//12, coin_y-h//12, cx+offset+w//12, coin_y+h//12))
            path((cx-w//5, y+h//3), (cx+w//5, y+h//3))

        _draw_progressive_strokes(draw, strokes, progress, color, width)
        _draw_active_hand(draw, strokes, progress, color, min(sx, sy))
        return

    if kind == "rect":
        x, y = _point(element["x"], element["y"], sx, sy)
        w = round(element["width"] * sx)
        h = round(element["height"] * sy)
        if w > 0 and h > 0:
            points = [(x,y), (x+w,y), (x+w,y+h), (x,y+h), (x,y)]
            _draw_progressive_strokes(draw, [points], progress, color, width)
            _draw_active_hand(draw, [points], progress, color, min(sx, sy))
        return

    x1, y1 = _point(element["x1"], element["y1"], sx, sy)
    x2, y2 = _point(element["x2"], element["y2"], sx, sy)
    end = (round(x1 + (x2 - x1) * progress), round(y1 + (y2 - y1) * progress))
    draw.line((x1, y1, end[0], end[1]), fill=color, width=width)
    if 0 < progress < 1:
        _draw_pen_hand(draw, end, color, min(sx, sy))
    if kind == "arrow" and progress >= 1:
        _draw_arrow(draw, (x1, y1, end[0], end[1]), color, width)


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
    transition_frames = round(transition_seconds * draw_fps)
    scene_frame_paths: list[list[Path]] = []
    try:
        # Render each scene independently first. This gives the transition compositor
        # clean incoming/outgoing frames without changing the drawing animation.
        for scene_index, scene in enumerate(storyboard["scenes"]):
            duration = float(scene["duration_seconds"])
            total_frames = max(1, math.ceil(duration * draw_fps))
            elements = scene["elements"]
            scene_paths: list[Path] = []
            for frame_index in range(total_frames):
                drawing = Image.new("RGB", (draw_width, draw_height), PALETTE["white"])
                draw = ImageDraw.Draw(drawing)
                elapsed = frame_index / draw_fps
                for element_index, element in enumerate(elements):
                    # Timed storyboard cues let each illustration react to the matching
                    # narration phrase. Untimed elements retain sequential fallback timing.
                    fallback_window = max(0.15, duration * 0.65 / max(1, len(elements)))
                    start = float(element.get("start_seconds", element_index * fallback_window))
                    reveal_window = float(element.get("draw_seconds", fallback_window))
                    progress = min(1.0, max(0.0, (elapsed - start) / reveal_window))
                    if progress > 0:
                        animated = _motion_position(element, elapsed)
                        _draw_element(draw, animated, progress, (draw_width, draw_height), coordinate_size)
                image = Image.new("RGB", (width, height), PALETTE["white"])
                image.paste(drawing, ((width - draw_width) // 2, (height - draw_height) // 2))
                scene_path = frame_dir / f"scene_{scene_index:03d}_frame_{frame_index:06d}.png"
                image.save(scene_path, optimize=True)
                scene_paths.append(scene_path)
            scene_frame_paths.append(scene_paths)

        # Insert true frame-by-frame cross dissolves between scenes. Original scene
        # frames remain intact, so the transition is a short bridge, not a wipe.
        for scene_index, paths in enumerate(scene_frame_paths):
            for source_path in paths:
                frame = Image.open(source_path).convert("RGB")
                frame.save(frame_dir / f"frame_{frame_number:06d}.png", optimize=True)
                frame_number += 1
            if transition_frames and scene_index < len(scene_frame_paths) - 1:
                outgoing = Image.open(paths[-1]).convert("RGB")
                incoming = Image.open(scene_frame_paths[scene_index + 1][0]).convert("RGB")
                for step in range(1, transition_frames + 1):
                    alpha = step / (transition_frames + 1)
                    blended = Image.blend(outgoing, incoming, alpha)
                    blended.save(frame_dir / f"frame_{frame_number:06d}.png", optimize=True)
                    frame_number += 1

        if frame_number == 0:
            raise RuntimeError("Renderer produced no frames")
        filter_chain = f"fps={fps},format=yuv420p"
        if captions is not None:
            caption_name = str(captions).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")
            style = "FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,BackColour=&HCC102B55,BorderStyle=3,Outline=0,Shadow=0,Alignment=2,MarginV=105,MarginL=90,MarginR=90"
            filter_chain += f",subtitles='{caption_name}':force_style='{style}'"
        command = [
            executable, "-hide_banner", "-loglevel", "error", "-y",
            "-framerate", str(draw_fps), "-i", str(frame_dir / "frame_%06d.png"),
        ]
        if audio is not None:
            command.extend(["-i", str(audio)])
        command.extend(["-vf", filter_chain, "-map", "0:v:0"])
        if audio is not None:
            total_duration = sum(float(scene["duration_seconds"]) for scene in storyboard["scenes"]) + transition_frames * max(0, len(scene_frame_paths) - 1) / draw_fps
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
