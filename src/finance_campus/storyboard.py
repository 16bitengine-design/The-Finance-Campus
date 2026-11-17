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
    canvas = data.get("canvas", {"width": WIDTH, "height": HEIGHT})
    if not isinstance(canvas, dict):
        return ["canvas must be an object with positive width and height"]
    for dimension in ("width", "height"):
        value = canvas.get(dimension, WIDTH if dimension == "width" else HEIGHT)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            return [f"canvas.{dimension} must be a positive finite number"]
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
            motion = element.get("motion")
            if motion is not None:
                motion_fields = ("from_x", "from_y", "to_x", "to_y", "start_seconds", "end_seconds")
                if not isinstance(motion, dict):
                    errors.append(f"{item_prefix}.motion must be an object")
                else:
                    for motion_field in motion_fields:
                        motion_value = motion.get(motion_field)
                        if isinstance(motion_value, bool) or not isinstance(motion_value, (int, float)) or not math.isfinite(motion_value):
                            errors.append(f"{item_prefix}.motion.{motion_field} must be a finite number")
                    if (
                        all(
                            isinstance(motion.get(field), (int, float))
                            and not isinstance(motion.get(field), bool)
                            and math.isfinite(motion[field])
                            for field in motion_fields
                        )
                        and (motion["start_seconds"] < 0 or motion["end_seconds"] <= motion["start_seconds"])
                    ):
                        errors.append(f"{item_prefix}.motion timing must be non-negative and end after start")
            walk_cycle = element.get("walk_cycle")
            if walk_cycle is not None:
                if not isinstance(walk_cycle, dict):
                    errors.append(f"{item_prefix}.walk_cycle must be an object")
                else:
                    for field in ("start_seconds", "end_seconds", "cycle_seconds"):
                        value = walk_cycle.get(field)
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                            errors.append(f"{item_prefix}.walk_cycle.{field} must be a finite number")
                    if (
                        all(
                            isinstance(walk_cycle.get(field), (int, float))
                            and not isinstance(walk_cycle.get(field), bool)
                            and math.isfinite(walk_cycle[field])
                            for field in ("start_seconds", "end_seconds", "cycle_seconds")
                        )
                        and (
                            walk_cycle["start_seconds"] < 0
                            or walk_cycle["end_seconds"] <= walk_cycle["start_seconds"]
                            or walk_cycle["cycle_seconds"] <= 0
                        )
                    ):
                        errors.append(f"{item_prefix}.walk_cycle timing and cycle must be positive and ordered")
            interaction_target = element.get("interaction_target")
            if interaction_target is not None:
                if not isinstance(interaction_target, dict):
                    errors.append(f"{item_prefix}.interaction_target must be an object")
                else:
                    for coordinate in ("x", "y"):
                        value = interaction_target.get(coordinate)
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                            errors.append(f"{item_prefix}.interaction_target.{coordinate} must be a finite number")
            interaction_animation = element.get("interaction_animation")
            if interaction_animation is not None:
                if not isinstance(interaction_animation, dict):
                    errors.append(f"{item_prefix}.interaction_animation must be an object")
                else:
                    for field in ("from_x", "from_y", "start_seconds", "end_seconds"):
                        value = interaction_animation.get(field)
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                            errors.append(f"{item_prefix}.interaction_animation.{field} must be a finite number")
                    if (
                        all(
                            isinstance(interaction_animation.get(field), (int, float))
                            and not isinstance(interaction_animation.get(field), bool)
                            and math.isfinite(interaction_animation[field])
                            for field in ("start_seconds", "end_seconds")
                        )
                        and (
                            interaction_animation["start_seconds"] < 0
                            or interaction_animation["end_seconds"] <= interaction_animation["start_seconds"]
                        )
                    ):
                        errors.append(f"{item_prefix}.interaction_animation timing must be non-negative and end after start")
                    if interaction_animation.get("easing", "linear") not in {"linear", "ease_out"}:
                        errors.append(f"{item_prefix}.interaction_animation.easing must be linear or ease_out")
                    if interaction_target is None:
                        errors.append(f"{item_prefix}.interaction_animation requires interaction_target")
            for timing_field in ("start_seconds", "draw_seconds"):
                if timing_field in element:
                    timing_value = element[timing_field]
                    if isinstance(timing_value, bool) or not isinstance(timing_value, (int, float)) or not math.isfinite(timing_value):
                        errors.append(f"{item_prefix}.{timing_field} must be a finite number")
                    elif timing_value < 0 or (timing_field == "draw_seconds" and timing_value == 0):
                        errors.append(f"{item_prefix}.{timing_field} is outside its valid range")
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
    if kind in ILLUSTRATION_TYPES:
        x, y = element["x"], element["y"]
        w, h = element["width"], element["height"]
        right, bottom = x + w, y + h
        cx, cy = x + w / 2, y + h / 2
        if kind == "person":
            head = min(w, h) / 7
            eye_y = y + head
            eye_r = head / 12
            shoulder = y + 2 * head + h / 24
            waist = y + h * .66
            art = (
                f'<circle cx="{_number(cx)}" cy="{_number(y+head)}" r="{_number(head)}" {common}/>'
                f'<circle cx="{_number(cx-head/3)}" cy="{_number(eye_y)}" r="{_number(eye_r)}" fill="{color}"/>'
                f'<circle cx="{_number(cx+head/3)}" cy="{_number(eye_y)}" r="{_number(eye_r)}" fill="{color}"/>'
                f'<path d="M {_number(cx-head/3)} {_number(y+head*1.35)} Q {_number(cx)} {_number(y+head*1.75)} {_number(cx+head/3)} {_number(y+head*1.35)}" {common}/>'
                f'<path d="M {_number(cx)} {_number(y+2*head)} V {_number(shoulder)} M {_number(cx-w*.25)} {_number(shoulder)} L {_number(cx+w*.25)} {_number(shoulder)} L {_number(cx+w*.16)} {_number(waist)} L {_number(cx-w*.16)} {_number(waist)} Z" {common}/>'
                f'<path d="M {_number(cx-w*.25)} {_number(shoulder)} L {_number(x+w*.2)} {_number(y+h*.43)} L {_number(x+w*.1)} {_number(y+h*.56)} M {_number(cx+w*.25)} {_number(shoulder)} L {_number(right-w*.2)} {_number(y+h*.43)} L {_number(right-w*.1)} {_number(y+h*.56)}" {common}/>'
                f'<circle cx="{_number(x+w*.1)}" cy="{_number(y+h*.56)}" r="{_number(head/5)}" {common}/>'
                f'<circle cx="{_number(right-w*.1)}" cy="{_number(y+h*.56)}" r="{_number(head/5)}" {common}/>'
                f'<path d="M {_number(cx-w*.16)} {_number(waist)} L {_number(x+w*.25)} {_number(bottom-h*.08)} L {_number(x+w*.12)} {_number(bottom-h*.03)} M {_number(cx+w*.16)} {_number(waist)} L {_number(right-w*.25)} {_number(bottom-h*.08)} L {_number(right-w*.12)} {_number(bottom-h*.03)}" {common}/>'
            )
        elif kind == "bank":
            roof = y + h / 4
            art = f'<path d="M {_number(x)} {_number(roof)} L {_number(cx)} {_number(y)} L {_number(right)} {_number(roof)} M {_number(x)} {_number(roof)} H {_number(right)} M {_number(x)} {_number(bottom-h/6)} H {_number(right)} M {_number(x-w*.05)} {_number(bottom)} H {_number(right+w*.05)}" {common}/>' + "".join(f'<path d="M {_number(x+w*(i+.5)/4)} {_number(roof)} V {_number(bottom-h/6)}" {common}/>' for i in range(4))
        elif kind == "wallet":
            art = f'<rect x="{_number(x)}" y="{_number(y+h/4)}" width="{_number(w)}" height="{_number(h*3/4)}" rx="10" {common}/><rect x="{_number(cx)}" y="{_number(y+h/2)}" width="{_number(w/2)}" height="{_number(h/4)}" rx="6" {common}/><circle cx="{_number(right-w/8)}" cy="{_number(y+h*5/8)}" r="{_number(w/25)}" {common}/>'
        elif kind == "house":
            roof = y + h/3
            art = f'<path d="M {_number(x)} {_number(roof)} L {_number(cx)} {_number(y)} L {_number(right)} {_number(roof)} M {_number(x+w/8)} {_number(roof)} V {_number(bottom)} H {_number(right-w/8)} V {_number(roof)} M {_number(cx-w/10)} {_number(bottom)} V {_number(bottom-h/3)} H {_number(cx+w/10)} V {_number(bottom)}" {common}/>'
        elif kind == "coin":
            art = f'<circle cx="{_number(cx)}" cy="{_number(cy)}" r="{_number(min(w,h)/2)}" {common}/><circle cx="{_number(cx)}" cy="{_number(cy)}" r="{_number(min(w,h)/3)}" {common}/><text x="{_number(cx)}" y="{_number(cy+h*.16)}" text-anchor="middle" fill="{color}" font-size="{_number(h*.45)}">$</text>'
        elif kind == "money_note":
            art = f'<rect x="{_number(x)}" y="{_number(y+h/6)}" width="{_number(w)}" height="{_number(h*2/3)}" rx="8" {common}/><circle cx="{_number(cx)}" cy="{_number(cy)}" r="{_number(h/8)}" {common}/><path d="M {_number(x+w/8)} {_number(y+h/3)} h {_number(w/8)} M {_number(right-w/4)} {_number(bottom-h/3)} h {_number(w/8)}" {common}/>'
        else:
            art = f'<path d="M {_number(x+w/4)} {_number(y+h/5)} H {_number(right-w/4)} M {_number(x+w/5)} {_number(y+h/4)} Q {_number(x)} {_number(y+h/4)} {_number(x+w/5)} {_number(bottom)} H {_number(right-w/5)} Q {_number(right)} {_number(y+h/4)} {_number(right-w/5)} {_number(y+h/4)}" {common}/><path d="M {_number(cx-w/8)} {_number(y+h/5)} H {_number(cx+w/8)}" {common}/><circle cx="{_number(cx)}" cy="{_number(cy)}" r="{_number(w/8)}" {common}/>'
        return f'<g {animation}>{art}</g>'
    x, y = _number(element["x"]), _number(element["y"])
    label = html.escape(element["text"])
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="25" font-weight="600" opacity="0" style="animation:appear .35s ease-out {delay:.2f}s forwards">{label}</text>'


def render_scene_svg(scene: dict[str, Any], canvas: dict[str, Any] | None = None) -> str:
    """Render one validated scene as an SVG matching its storyboard canvas."""
    errors = validate_storyboard({"canvas": canvas or {"width": WIDTH, "height": HEIGHT}, "scenes": [scene]})
    if errors:
        raise ValueError("Invalid storyboard scene: " + "; ".join(errors))
    elements = "\n".join(_render_element(item, index) for index, item in enumerate(scene["elements"]))
    title = html.escape(scene["id"])
    canvas_width = float((canvas or {}).get("width", WIDTH))
    canvas_height = float((canvas or {}).get("height", HEIGHT))
    output_width, output_height = (1920, 1080) if canvas_width >= canvas_height else (1080, 1920)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{output_width}" height="{output_height}" viewBox="0 0 {_number(canvas_width)} {_number(canvas_height)}">
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
        path.write_text(render_scene_svg(scene, data.get("canvas")), encoding="utf-8")
        outputs.append(path)
    return outputs
