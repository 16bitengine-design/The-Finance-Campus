"""Deterministic multi-character scene compositor for transparent character rigs."""
from __future__ import annotations

import math
from itertools import pairwise
from collections.abc import Iterator
from typing import Any

from PIL import Image

from finance_campus.character_rig import render_character_frame, validate_character_rig


class MultiCharacterSceneError(ValueError):
    """Raised when a multi-character composition is invalid."""


def validate_multi_character_scene(scene: Any, character_specs: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(scene, dict):
        return ["scene must be an object"]
    canvas = scene.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must define width and height")
    else:
        for field in ("width", "height"):
            value = canvas.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                errors.append(f"canvas.{field} must be a positive integer")
    fps = scene.get("fps", 30)
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        errors.append("fps must be a positive integer")
    duration = scene.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        errors.append("duration_seconds must be positive and finite")
    entries = scene.get("characters")
    if not isinstance(entries, list) or not entries:
        return errors + ["characters must be a non-empty list"]
    ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"characters[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        identity = entry.get("id")
        if not isinstance(identity, str) or not identity.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
            continue
        if identity in ids:
            errors.append(f"duplicate character id: {identity}")
        ids.add(identity)
        if identity not in character_specs:
            errors.append(f"{prefix} has no character spec for {identity}")
        else:
            errors.extend(f"{prefix}.{message}" for message in validate_character_rig(character_specs[identity]))
        z = entry.get("z", 0)
        if isinstance(z, bool) or not isinstance(z, (int, float)) or not math.isfinite(z):
            errors.append(f"{prefix}.z must be finite and numeric")
        keyframes = entry.get("keyframes")
        if not isinstance(keyframes, list) or not keyframes:
            errors.append(f"{prefix}.keyframes must be a non-empty list")
            continue
        last_at = -1.0
        for frame_index, keyframe in enumerate(keyframes):
            kprefix = f"{prefix}.keyframes[{frame_index}]"
            if not isinstance(keyframe, dict):
                errors.append(f"{kprefix} must be an object")
                continue
            at = keyframe.get("at")
            if isinstance(at, bool) or not isinstance(at, (int, float)) or not math.isfinite(at) or at < 0 or at < last_at:
                errors.append(f"{kprefix}.at must be finite, non-negative and ordered")
            else:
                last_at = float(at)
            for field in ("x", "y", "scale", "opacity"):
                value = keyframe.get(field, {"scale": 1, "opacity": 1}.get(field, 0))
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    errors.append(f"{kprefix}.{field} must be finite and numeric")
            if keyframe.get("scale", 1) <= 0:
                errors.append(f"{kprefix}.scale must be positive")
            if not 0 <= keyframe.get("opacity", 1) <= 1:
                errors.append(f"{kprefix}.opacity must be between 0 and 1")
    return errors


def _sample_track(keyframes: list[dict[str, Any]], at: float) -> dict[str, float]:
    fields = ("x", "y", "scale", "opacity")
    if at <= keyframes[0]["at"]:
        frame = keyframes[0]
        return {field: float(frame.get(field, {"scale": 1, "opacity": 1}.get(field, 0))) for field in fields}
    if at >= keyframes[-1]["at"]:
        frame = keyframes[-1]
        return {field: float(frame.get(field, {"scale": 1, "opacity": 1}.get(field, 0))) for field in fields}
    for first, second in pairwise(keyframes):
        if first["at"] <= at <= second["at"]:
            amount = (at - first["at"]) / (second["at"] - first["at"])
            return {
                field: float(first.get(field, {"scale": 1, "opacity": 1}.get(field, 0)))
                + (float(second.get(field, {"scale": 1, "opacity": 1}.get(field, 0)))
                   - float(first.get(field, {"scale": 1, "opacity": 1}.get(field, 0)))) * amount
                for field in fields
            }
    raise MultiCharacterSceneError("could not sample character track")


def render_multi_character_frame(
    scene: dict[str, Any], character_specs: dict[str, Any], at_seconds: float
) -> Image.Image:
    """Render one RGBA frame; z-order is ascending and larger z values appear in front."""
    errors = validate_multi_character_scene(scene, character_specs)
    if errors:
        raise MultiCharacterSceneError("; ".join(errors))
    if isinstance(at_seconds, bool) or not isinstance(at_seconds, (int, float)) or not math.isfinite(at_seconds) or at_seconds < 0:
        raise MultiCharacterSceneError("at_seconds must be finite and non-negative")
    width, height = scene["canvas"]["width"], scene["canvas"]["height"]
    background = scene.get("background_rgba", [255, 255, 255, 255])
    if (not isinstance(background, list) or len(background) != 4
            or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for v in background)):
        raise MultiCharacterSceneError("background_rgba must contain four integers from 0 to 255")
    canvas = Image.new("RGBA", (width, height), tuple(background))
    for entry in sorted(scene["characters"], key=lambda item: item.get("z", 0)):
        state = _sample_track(entry["keyframes"], float(at_seconds))
        character = render_character_frame(character_specs[entry["id"]], float(at_seconds))
        if state["scale"] != 1:
            size = (max(1, round(character.width * state["scale"])),
                    max(1, round(character.height * state["scale"])))
            character = character.resize(size, Image.Resampling.LANCZOS)
        if state["opacity"] < 1:
            alpha = character.getchannel("A").point(lambda value, opacity=state["opacity"]: round(value * opacity))
            character.putalpha(alpha)
        canvas.alpha_composite(character, (round(state["x"]), round(state["y"])))
    return canvas


def iter_multi_character_frames(
    scene: dict[str, Any], character_specs: dict[str, Any]
) -> Iterator[Image.Image]:
    """Yield frame-indexed deterministic RGBA frames at the scene's declared FPS."""
    errors = validate_multi_character_scene(scene, character_specs)
    if errors:
        raise MultiCharacterSceneError("; ".join(errors))
    fps = scene.get("fps", 30)
    frame_count = math.ceil(scene["duration_seconds"] * fps)
    for frame in range(frame_count):
        yield render_multi_character_frame(scene, character_specs, frame / fps)
