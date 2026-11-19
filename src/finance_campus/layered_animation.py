"""Layered, keyframe-driven illustration compositor.

This is the migration renderer for authored transparent artwork. It does not
invent illustrations: artists/design tools supply scene-specific PNG layers,
and this module animates those layers with deterministic, testable timing.
"""
from __future__ import annotations

import itertools
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from PIL import Image

EASINGS = {"linear", "ease_in_out", "ease_out"}
REVEALS = {"none", "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"}


class LayeredSceneError(ValueError):
    """Raised when a directed layered scene is incomplete or unsafe."""


def validate_layered_scene(scene: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(scene, dict):
        return ["scene must be an object"]
    canvas = scene.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must define width and height")
    else:
        for key in ("width", "height"):
            value = canvas.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                errors.append(f"canvas.{key} must be a positive integer")
    duration = scene.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
        errors.append("duration_seconds must be positive")
    layers = scene.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + ["layers must be a non-empty list"]
    ids: set[str] = set()
    for index, layer in enumerate(layers):
        prefix = f"layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("id", "asset"):
            if not isinstance(layer.get(key), str) or not layer[key].strip():
                errors.append(f"{prefix}.{key} must be a non-empty string")
        layer_id = layer.get("id")
        if isinstance(layer_id, str):
            if layer_id in ids:
                errors.append(f"duplicate layer id: {layer_id}")
            ids.add(layer_id)
        if not isinstance(layer.get("z", 0), (int, float)):
            errors.append(f"{prefix}.z must be numeric")
        reveal = layer.get("reveal", "none")
        if reveal not in REVEALS:
            errors.append(f"{prefix}.reveal is unsupported")
        keyframes = layer.get("keyframes")
        if not isinstance(keyframes, list) or not keyframes:
            errors.append(f"{prefix}.keyframes must be a non-empty list")
            continue
        last_time = -1.0
        for frame_index, keyframe in enumerate(keyframes):
            kprefix = f"{prefix}.keyframes[{frame_index}]"
            if not isinstance(keyframe, dict):
                errors.append(f"{kprefix} must be an object")
                continue
            time = keyframe.get("at")
            if isinstance(time, bool) or not isinstance(time, (int, float)) or time < 0:
                errors.append(f"{kprefix}.at must be non-negative")
            elif time < last_time:
                errors.append(f"{prefix}.keyframes must be ordered by at")
            else:
                last_time = float(time)
            for field in ("x", "y", "scale", "rotation", "opacity", "reveal_progress"):
                if field in keyframe:
                    value = keyframe[field]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        errors.append(f"{kprefix}.{field} must be finite")
            if keyframe.get("scale", 1) <= 0:
                errors.append(f"{kprefix}.scale must be positive")
            if not 0 <= keyframe.get("opacity", 1) <= 1:
                errors.append(f"{kprefix}.opacity must be between 0 and 1")
            if not 0 <= keyframe.get("reveal_progress", 1) <= 1:
                errors.append(f"{kprefix}.reveal_progress must be between 0 and 1")
            if keyframe.get("easing", "linear") not in EASINGS:
                errors.append(f"{kprefix}.easing is unsupported")
    return errors


def _ease(value: float, name: str) -> float:
    value = min(1.0, max(0.0, value))
    if name == "ease_out":
        return 1 - (1 - value) ** 3
    if name == "ease_in_out":
        return value * value * (3 - 2 * value)
    return value


def _sample(keyframes: list[dict[str, Any]], at: float) -> dict[str, float]:
    fields = ("x", "y", "scale", "rotation", "opacity", "reveal_progress")
    if at <= keyframes[0]["at"]:
        return {field: float(keyframes[0].get(field, {"scale": 1, "opacity": 1, "reveal_progress": 1}.get(field, 0))) for field in fields}
    if at >= keyframes[-1]["at"]:
        return {field: float(keyframes[-1].get(field, {"scale": 1, "opacity": 1, "reveal_progress": 1}.get(field, 0))) for field in fields}
    for first, second in itertools.pairwise(keyframes):
        if first["at"] <= at <= second["at"]:
            span = second["at"] - first["at"]
            amount = (at - first["at"]) / span if span else 1
            amount = _ease(amount, second.get("easing", "linear"))
            result = {}
            for field in fields:
                default = {"scale": 1, "opacity": 1, "reveal_progress": 1}.get(field, 0)
                start = float(first.get(field, default))
                end = float(second.get(field, default))
                result[field] = start + (end - start) * amount
            return result
    raise LayeredSceneError("could not sample keyframes")


def _reveal(image: Image.Image, progress: float, direction: str) -> Image.Image:
    width, height = image.size
    if progress <= 0:
        hidden = image.copy()
        hidden.putalpha(0)
        return hidden
    if progress >= 1:
        return image
    mask = Image.new("L", (width, height), 0)
    draw_width = round(width * progress)
    draw_height = round(height * progress)
    if direction == "left_to_right":
        bounds = (0, 0, draw_width, height)
    elif direction == "right_to_left":
        bounds = (width - draw_width, 0, width, height)
    elif direction == "top_to_bottom":
        bounds = (0, 0, width, draw_height)
    elif direction == "bottom_to_top":
        bounds = (0, height - draw_height, width, height)
    else:
        return image
    from PIL import ImageDraw
    ImageDraw.Draw(mask).rectangle(bounds, fill=255)
    result = image.copy()
    result.putalpha(Image.composite(image.getchannel("A"), Image.new("L", image.size, 0), mask))
    return result


def render_layered_frame(
    scene: dict[str, Any],
    at_seconds: float,
    asset_root: str | Path,
) -> Image.Image:
    """Composite one animation frame from authored transparent PNG layers.

    Layer x/y values are the layer's top-left canvas position in pixels.
    Artwork assets are never modified on disk.
    """
    errors = validate_layered_scene(scene)
    if errors:
        raise LayeredSceneError("; ".join(errors))
    if not math.isfinite(at_seconds) or at_seconds < 0:
        raise LayeredSceneError("at_seconds must be a finite non-negative number")
    width, height = scene["canvas"]["width"], scene["canvas"]["height"]
    canvas = Image.new("RGBA", (width, height), tuple(scene.get("background_rgba", [255, 255, 255, 255])))
    root = Path(asset_root).resolve()
    for layer in sorted(scene["layers"], key=lambda item: item.get("z", 0)):
        asset = (root / layer["asset"]).resolve()
        if root not in asset.parents:
            raise LayeredSceneError(f"asset path escapes asset_root: {layer['asset']}")
        if not asset.is_file():
            raise LayeredSceneError(f"missing illustration asset: {layer['asset']}")
        state = _sample(layer["keyframes"], at_seconds)
        artwork = Image.open(asset).convert("RGBA")
        if state["scale"] != 1:
            size = (max(1, round(artwork.width * state["scale"])), max(1, round(artwork.height * state["scale"])))
            artwork = artwork.resize(size, Image.Resampling.LANCZOS)
        if state["rotation"]:
            artwork = artwork.rotate(state["rotation"], resample=Image.Resampling.BICUBIC, expand=True)
        if layer.get("reveal", "none") != "none":
            artwork = _reveal(artwork, state["reveal_progress"], layer["reveal"])
        if state["opacity"] < 1:
            alpha = artwork.getchannel("A").point(lambda value, opacity=state["opacity"]: round(value * opacity))
            artwork.putalpha(alpha)
        x, y = round(state["x"]), round(state["y"])
        canvas.alpha_composite(artwork, (x, y))
    return canvas


def iter_layered_frames(
    scene: dict[str, Any],
    asset_root: str | Path,
    fps: int = 30,
) -> Iterator[Image.Image]:
    """Yield deterministic RGBA frames from time zero through scene duration."""
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise LayeredSceneError("fps must be a positive integer")
    errors = validate_layered_scene(scene)
    if errors:
        raise LayeredSceneError("; ".join(errors))
    frame_count = math.ceil(scene["duration_seconds"] * fps)
    for frame_number in range(frame_count):
        yield render_layered_frame(scene, frame_number / fps, asset_root)
