"""Reusable articulated 2D character rig for illustrated finance storytelling.

The rig draws a consistent character identity from named body-part poses. It
supports time-sampled poses, expressive faces, clothing and transparent PNG
frames so each character can be composited independently over authored scenes.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

EXPRESSIONS = {"neutral", "worried", "anxious", "relieved", "curious", "focused", "determined", "hopeful", "joyful", "frustrated", "surprised"}
POSE_PARTS = {"head", "neck", "shoulders", "elbows", "hands", "hips", "knees", "feet"}


class CharacterRigError(ValueError):
    """Raised when a character identity or pose timeline is invalid."""


def validate_character_rig(spec: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["character rig must be an object"]
    for field in ("id", "name", "skin", "hair", "clothing"):
        if not isinstance(spec.get(field), (str, dict)) or not spec[field]:
            errors.append(f"{field} must be supplied")
    canvas = spec.get("canvas", {})
    if not isinstance(canvas, dict) or any(not isinstance(canvas.get(k), int) or canvas[k] <= 0 for k in ("width", "height")):
        errors.append("canvas must define positive integer width and height")
    poses = spec.get("poses")
    if not isinstance(poses, list) or not poses:
        errors.append("poses must be a non-empty list")
        return errors
    last = -1.0
    for i, pose in enumerate(poses):
        if not isinstance(pose, dict) or not isinstance(pose.get("at"), (int, float)) or pose.get("at", -1) < last:
            errors.append(f"poses[{i}] must have an ordered non-negative time")
            continue
        last = float(pose["at"])
        if pose.get("expression", "neutral") not in EXPRESSIONS:
            errors.append(f"poses[{i}].expression is unsupported")
        joints = pose.get("joints")
        if not isinstance(joints, dict) or not POSE_PARTS.issubset(joints):
            errors.append(f"poses[{i}].joints must define {sorted(POSE_PARTS)}")
            continue
        for part in POSE_PARTS:
            point = joints[part]
            if not isinstance(point, list) or len(point) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in point):
                errors.append(f"poses[{i}].joints.{part} must be a finite [x, y] pair")
    return errors


def _sample_pose(poses: list[dict[str, Any]], at: float) -> dict[str, Any]:
    if at <= poses[0]["at"]:
        return poses[0]
    if at >= poses[-1]["at"]:
        return poses[-1]
    for first, second in zip(poses, poses[1:]):
        if first["at"] <= at <= second["at"]:
            t = (at - first["at"]) / (second["at"] - first["at"])
            joints = {part: [first["joints"][part][axis] + (second["joints"][part][axis] - first["joints"][part][axis]) * t for axis in (0, 1)] for part in POSE_PARTS}
            return {"joints": joints, "expression": second.get("expression", first.get("expression", "neutral"))}
    return poses[-1]


def render_character_frame(spec: dict[str, Any], at_seconds: float) -> Image.Image:
    errors = validate_character_rig(spec)
    if errors:
        raise CharacterRigError("; ".join(errors))
    if not math.isfinite(at_seconds) or at_seconds < 0:
        raise CharacterRigError("at_seconds must be finite and non-negative")
    width, height = spec["canvas"]["width"], spec["canvas"]["height"]
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    pose = _sample_pose(spec["poses"], at_seconds)
    j = {key: tuple(round(v) for v in value) for key, value in pose["joints"].items()}
    skin = spec["skin"]
    hair = spec["hair"]
    clothes = spec["clothing"]
    outline = spec.get("outline", "#26364A")

    def limb(a: str, b: str, color: str, thickness: int):
        draw.line([j[a], j[b]], fill=outline, width=thickness + 5)
        draw.line([j[a], j[b]], fill=color, width=thickness)
        radius = thickness // 2
        for key in (a, b):
            x, y = j[key]
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color, outline=outline, width=3)

    # Rear limbs first, then torso, arms and hands.
    limb("hips", "knees", clothes.get("trousers", "#26364A"), 30)
    # Both legs share the knee/hip anchor but splay naturally at the feet.
    hip_x, hip_y = j["hips"]
    knee_x, knee_y = j["knees"]
    foot_x, foot_y = j["feet"]
    limb("knees", "feet", clothes.get("trousers", "#26364A"), 26)
    draw.ellipse((foot_x-28, foot_y-12, foot_x+30, foot_y+12), fill=clothes.get("shoes", "#202936"), outline=outline, width=3)
    shoulder_x, shoulder_y = j["shoulders"]
    hip_x, hip_y = j["hips"]
    torso_box = (min(shoulder_x, hip_x)-43, shoulder_y, max(shoulder_x, hip_x)+43, hip_y+12)
    draw.rounded_rectangle(torso_box, radius=32, fill=clothes.get("top", "#2F6F9F"), outline=outline, width=5)
    # Clothing seam and collar add readable garment construction.
    draw.line((shoulder_x-18, shoulder_y+20, shoulder_x, shoulder_y+38, shoulder_x+18, shoulder_y+20), fill=clothes.get("trim", "#F5B817"), width=5)
    limb("shoulders", "elbows", skin, 24)
    limb("elbows", "hands", skin, 20)
    for key in ("hands",):
        x, y = j[key]
        draw.ellipse((x-14, y-13, x+14, y+13), fill=skin, outline=outline, width=3)
    # Neck and head.
    neck_x, neck_y = j["neck"]
    draw.rounded_rectangle((neck_x-13, neck_y-4, neck_x+13, neck_y+34), radius=9, fill=skin, outline=outline, width=3)
    head_x, head_y = j["head"]
    draw.ellipse((head_x-48, head_y-58, head_x+48, head_y+58), fill=skin, outline=outline, width=5)
    # Hair cap and side locks create a stable silhouette.
    draw.pieslice((head_x-51, head_y-65, head_x+51, head_y+28), 180, 360, fill=hair, outline=outline, width=4)
    draw.ellipse((head_x-51, head_y-12, head_x-34, head_y+24), fill=hair, outline=outline, width=2)
    draw.ellipse((head_x+34, head_y-12, head_x+51, head_y+24), fill=hair, outline=outline, width=2)
    expression = pose.get("expression", "neutral")
    eye_y = head_y - 3
    eye_offset = 17
    if expression in {"worried", "anxious", "surprised"}:
        draw.arc((head_x-eye_offset-8, eye_y-12, head_x-eye_offset+8, eye_y+3), 190, 350, fill=outline, width=3)
        draw.arc((head_x+eye_offset-8, eye_y-12, head_x+eye_offset+8, eye_y+3), 190, 350, fill=outline, width=3)
    else:
        draw.line((head_x-eye_offset-7, eye_y-7, head_x-eye_offset+7, eye_y-7), fill=outline, width=3)
        draw.line((head_x+eye_offset-7, eye_y-7, head_x+eye_offset+7, eye_y-7), fill=outline, width=3)
    draw.ellipse((head_x-eye_offset-3, eye_y-1, head_x-eye_offset+3, eye_y+7), fill=outline)
    draw.ellipse((head_x+eye_offset-3, eye_y-1, head_x+eye_offset+3, eye_y+7), fill=outline)
    mouth_box = (head_x-13, head_y+19, head_x+13, head_y+35)
    if expression in {"joyful", "hopeful", "relieved"}:
        draw.arc(mouth_box, 5, 175, fill=outline, width=4)
    elif expression in {"worried", "anxious", "frustrated"}:
        draw.arc(mouth_box, 185, 355, fill=outline, width=4)
    elif expression == "surprised":
        draw.ellipse((head_x-5, head_y+20, head_x+5, head_y+34), outline=outline, width=3)
    else:
        draw.line((head_x-10, head_y+27, head_x+10, head_y+27), fill=outline, width=3)
    # Optional accessory identity marker (e.g. glasses) is consistent across scenes.
    if spec.get("accessory") == "glasses":
        for cx in (head_x-eye_offset, head_x+eye_offset):
            draw.ellipse((cx-12, eye_y-9, cx+12, eye_y+13), outline=outline, width=3)
        draw.line((head_x-5, eye_y+1, head_x+5, eye_y+1), fill=outline, width=3)
    return image


def render_character_sequence(spec: dict[str, Any], output_dir: str | Path, *, fps: int = 30) -> int:
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise CharacterRigError("fps must be a positive integer")
    errors = validate_character_rig(spec)
    if errors:
        raise CharacterRigError("; ".join(errors))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    duration = float(spec.get("duration_seconds", spec["poses"][-1]["at"]))
    if duration <= 0:
        raise CharacterRigError("duration_seconds must be positive")
    frames = math.ceil(duration * fps)
    for index in range(frames):
        render_character_frame(spec, index / fps).save(destination / f"character_{index:06d}.png")
    return frames
