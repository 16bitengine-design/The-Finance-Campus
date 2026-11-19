"""Validation for illustration-first, directed financial story scenes.

This contract deliberately separates art direction from low-level drawing primitives.
It is the input boundary for the layered illustration and motion-graphics renderer.
"""
from __future__ import annotations

from typing import Any

SHOT_SIZES = {"extreme_wide", "wide", "medium", "close_up", "detail"}
EXPRESSIONS = {
    "neutral", "worried", "anxious", "relieved", "curious", "focused",
    "determined", "hopeful", "joyful", "frustrated", "surprised",
}
ACTIONS = {
    "draw_reveal", "enter", "exit", "gesture", "look_at", "reach",
    "pick_up", "put_down", "hand_over", "receive", "open", "close",
    "move", "transform", "accumulate", "decrease", "appear", "disappear",
    "chart_grow", "bill_arrive", "decision",
}


def validate_visual_direction(scene: Any) -> list[str]:
    """Return actionable errors for a scene's authored visual direction."""
    if not isinstance(scene, dict):
        return ["scene must be an object"]
    direction = scene.get("visual_direction")
    if not isinstance(direction, dict):
        return ["visual_direction is required for illustration-first scenes"]

    errors: list[str] = []
    for field in ("setting", "takeaway", "visual_rationale"):
        if not isinstance(direction.get(field), str) or not direction[field].strip():
            errors.append(f"visual_direction.{field} must be a non-empty string")

    shot = direction.get("shot")
    if not isinstance(shot, dict):
        errors.append("visual_direction.shot must be an object")
    else:
        if shot.get("size") not in SHOT_SIZES:
            errors.append(f"visual_direction.shot.size must be one of {sorted(SHOT_SIZES)}")
        if not isinstance(shot.get("composition"), str) or not shot["composition"].strip():
            errors.append("visual_direction.shot.composition must be a non-empty string")

    layers = direction.get("layers")
    if not isinstance(layers, list) or len(layers) < 2:
        errors.append("visual_direction.layers must define at least two depth layers")
    else:
        layer_names = [layer.get("name") for layer in layers if isinstance(layer, dict)]
        if len(layer_names) != len(layers) or any(not isinstance(name, str) or not name.strip() for name in layer_names):
            errors.append("every visual layer must have a non-empty name")
        if len(set(layer_names)) != len(layer_names):
            errors.append("visual layer names must be unique")

    characters = direction.get("characters")
    if not isinstance(characters, list):
        errors.append("visual_direction.characters must be a list")
    else:
        for index, character in enumerate(characters):
            prefix = f"visual_direction.characters[{index}]"
            if not isinstance(character, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("id", "identity", "clothing", "gesture", "gaze"):
                if not isinstance(character.get(field), str) or not character[field].strip():
                    errors.append(f"{prefix}.{field} must be a non-empty string")
            if character.get("expression") not in EXPRESSIONS:
                errors.append(f"{prefix}.expression must be a recognised expression")
            if not isinstance(character.get("interactions"), list) or not character["interactions"]:
                errors.append(f"{prefix}.interactions must describe at least one prop or environmental interaction")

    beats = direction.get("action_beats")
    if not isinstance(beats, list) or not beats:
        errors.append("visual_direction.action_beats must be a non-empty ordered list")
    else:
        previous_time = -1.0
        for index, beat in enumerate(beats):
            prefix = f"visual_direction.action_beats[{index}]"
            if not isinstance(beat, dict):
                errors.append(f"{prefix} must be an object")
                continue
            action = beat.get("action")
            if action not in ACTIONS:
                errors.append(f"{prefix}.action must be one of {sorted(ACTIONS)}")
            time = beat.get("at_seconds")
            if isinstance(time, bool) or not isinstance(time, (int, float)) or time < 0:
                errors.append(f"{prefix}.at_seconds must be a non-negative number")
            elif time < previous_time:
                errors.append("action_beats must be ordered by at_seconds")
            else:
                previous_time = float(time)
            if not isinstance(beat.get("target"), str) or not beat["target"].strip():
                errors.append(f"{prefix}.target must identify the character, prop, or graphic")
            if not isinstance(beat.get("result"), str) or not beat["result"].strip():
                errors.append(f"{prefix}.result must describe the visible consequence")

    transition = direction.get("transition")
    if not isinstance(transition, dict):
        errors.append("visual_direction.transition must describe continuity into the next scene")
    else:
        if transition.get("type") not in {"match_cut", "camera_move", "object_carry", "draw_on", "morph", "wipe"}:
            errors.append("visual_direction.transition.type is not supported")
        if not isinstance(transition.get("continuity_anchor"), str) or not transition["continuity_anchor"].strip():
            errors.append("visual_direction.transition.continuity_anchor must identify what carries forward")

    safe_area = direction.get("caption_safe_area")
    if not isinstance(safe_area, dict) or not all(
        isinstance(safe_area.get(key), (int, float)) and not isinstance(safe_area.get(key), bool)
        for key in ("top", "bottom")
    ):
        errors.append("visual_direction.caption_safe_area must define numeric top and bottom boundaries")
    elif not 0 <= safe_area["top"] < safe_area["bottom"] <= 1:
        errors.append("caption_safe_area boundaries must be ordered normalized values from 0 to 1")

    return errors
