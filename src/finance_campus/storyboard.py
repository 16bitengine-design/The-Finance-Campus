"""Structured whiteboard storyboards and a dependency-free SVG renderer.

Coordinates use a 1000 x 562 viewBox. Each scene must contain at least one
non-text illustration so a storyboard cannot pass by animating captions alone.
"""
from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Any

WIDTH = 1000
HEIGHT = 562
ALLOWED_TYPES = {"circle", "rect", "line", "arrow", "text", "person", "bank", "wallet", "house", "coin", "money_note", "savings_jar"}
ILLUSTRATION_TYPES = {"person", "bank", "wallet", "house", "coin", "money_note", "savings_jar"}
ALLOWED_COLORS = {"navy": "#102B55", "green": "#168C43", "gold": "#F5B817", "white": "#FFFFFF", "black": "#17202A"}


def validate_storyboard(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["storyboard must be a JSON object"]
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["storyboard must contain a non-empty scenes list"]
    seen: set[str] = set()
    for index, scene in enumerate(scenes):
        prefix = f"scenes[{index}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix} must be an object")
            continue
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not scene_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif scene_id in seen:
            errors.append(f"duplicate scene id: {scene_id}")
        else:
            seen.add(scene_id)
        if not isinstance(scene.get("narration"), str) or not scene["narration"].strip():
            errors.append(f"{prefix}.narration must contain the spoken explanation")
        duration = scene.get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            errors.append(f"{prefix}.duration_seconds must be a positive finite number")
        elements = scene.get("elements")
        if not isinstance(elements, list) or not elements:
            errors.append(f"{prefix}.elements must be a non-empty list")
            continue
        illustrated = False
        for element_index, element in enumerate(elements):
            item_prefix = f"{prefix}.elements[{element_index}]"
            if not isinstance(element, dict):
                errors.append(f"{item_prefix} must be an object")
                continue
            kind = element.get("type")
            if kind not in ALLOWED_TYPES:
                errors.append(f"{item_prefix}.type must be one of {sorted(ALLOWED_TYPES)}")
                continue
            if kind != "text":
                illustrated = True
            color = element.get("color", "navy")
            if color not in ALLOWED_COLORS:
                errors.append(f"{item_prefix}.color must be a Finance Campus palette name")
            required = (
                ("x", "y", "width", "height") if kind in ILLUSTRATION_TYPES else {
                    "circle": ("cx", "cy", "r"),
                    "rect": ("x", "y", "width", "height"),
                    "line": ("x1", "y1", "x2", "y2"),
                    "arrow": ("x1", "y1", "x2", "y2"),
                    "text": ("x", "y", "text"),
                }[kind]
            )
            for field in required:
                if field not in element:
                    errors.append(f"{item_prefix}.{field} is required")
                elif field == "text":
                    if not isinstance(element[field], str) or not element[field].strip():
                        errors.append(f"{item_prefix}.text must be a non-empty string")
                elif isinstance(element[field], bool) or not isinstance(element[field], (int, float)) or not math.isfinite(element[field]):
                    errors.append(f"{item_prefix}.{field} must be a finite number")
            if kind in ILLUSTRATION_TYPES and any(
                isinstance(element.get(k), (int, float)) and element[k] <= 0
                for k in ("width", "height")
            ):
                errors.append(f"{item_prefix} illustration width and height must be positive")
            if kind == "circle" and isinstance(element.get("r"), (int, float)) and element["r"] <= 0:
                errors.append(f"{item_prefix}.r must be positive")
            if kind == "rect" and any(isinstance(element.get(k), (int, float)) and element[k] <= 0 for k in ("width", "height")):
                errors.append(f"{item_prefix} rectangle width and height must be positive")
        if not illustrated:
            errors.append(f"{prefix} needs at least one non-text illustration; text-only scenes are rejected")
    return errors


def _number(value: float) -> str:
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def _color(element: dict[str, Any]) -> str:
    return ALLOWED_COLORS.get(element.get("color", "navy"), ALLOWED_COLORS["navy"])


def _render_element(element: dict[str, Any], index: int) -> str:
    kind = element["type"]
    color = _color(element)
    common = f'stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    delay = index * 0.35
    animation = f'style="stroke-dasharray:1200;stroke-dashoffset:1200;animation:draw 1.1s ease-out {delay:.2f}s forwards"'
    if kind == "circle":
        return f'<circle cx="{_number(element["cx"])}" cy="{_number(element["cy"])}" r="{_number(element["r"])}" {common} {animation}/>'
    if kind == "rect":
        return f'<rect x="{_number(element["x"])}" y="{_number(element["y"])}" width="{_number(element["width"])}" height="{_number(element["height"])}" rx="8" {common} {animation}/>'
    if kind in {"line", "arrow"}:
        marker = ' marker-end="url(#arrowhead)"' if kind == "arrow" else ""
        return f'<line x1="{_number(element["x1"])}" y1="{_number(element["y1"])}" x2="{_number(element["x2"])}" y2="{_number(element["y2"])}" {common}{marker} {animation}/>'
    x, y = _number(element["x"]), _number(element["y"])
    label = html.escape(element["text"])
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="25" font-weight="600" opacity="0" style="animation:appear .35s ease-out {delay:.2f}s forwards">{label}</text>'


def render_scene_svg(scene: dict[str, Any]) -> str:
    """Render one already-validated scene as a 16:9 SVG whiteboard frame."""
    errors = validate_storyboard({"scenes": [scene]})
    if errors:
        raise ValueError("Invalid storyboard scene: " + "; ".join(errors))
    elements = "\n".join(_render_element(item, index) for index, item in enumerate(scene["elements"]))
    title = html.escape(scene["id"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 {WIDTH} {HEIGHT}">
<title>{title}</title>
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8" fill="#102B55"/></marker>
  <style>@keyframes draw {{ to {{ stroke-dashoffset: 0; }} }} @keyframes appear {{ to {{ opacity: 1; }} }}</style>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>
{elements}
</svg>
"""


def render_storyboard(data: dict[str, Any], output_dir: str | Path) -> list[Path]:
    """Validate and render all scenes to separate SVG files."""
    errors = validate_storyboard(data)
    if errors:
        raise ValueError("Invalid storyboard: " + "; ".join(errors))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for scene in data["scenes"]:
        path = destination / f'{scene["id"]}.svg'
        path.write_text(render_scene_svg(scene), encoding="utf-8")
        outputs.append(path)
    return outputs
