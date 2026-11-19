"""Bilateral 2D character rig with hand poses, props and mouth animation.

This is a lightweight authored illustration rig, not a substitute for bespoke
character artwork or a full skeletal/IK animation package.
"""
from __future__ import annotations

import math
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

EXPRESSIONS = {
    "neutral", "worried", "anxious", "relieved", "curious", "focused",
    "determined", "hopeful", "joyful", "frustrated", "surprised",
}
HAND_POSES = {"open", "closed", "point", "hold"}
PROP_TYPES = {"phone", "bill", "envelope", "coin"}
JOINTS = {
    "head", "neck", "shoulder_left", "shoulder_right",
    "elbow_left", "elbow_right", "hand_left", "hand_right",
    "hip_left", "hip_right", "knee_left", "knee_right",
    "foot_left", "foot_right",
}


class CharacterRigError(ValueError):
    """Raised when a character identity or pose timeline is invalid."""


def _valid_point(point: Any) -> bool:
    return (
        isinstance(point, list)
        and len(point) == 2
        and all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            for value in point
        )
    )


def validate_character_rig(spec: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["character rig must be an object"]
    for field in ("id", "name", "skin", "hair", "clothing"):
        if not isinstance(spec.get(field), (str, dict)) or not spec[field]:
            errors.append(f"{field} must be supplied")
    canvas = spec.get("canvas", {})
    if not isinstance(canvas, dict) or any(
        isinstance(canvas.get(key), bool)
        or not isinstance(canvas.get(key), int)
        or canvas[key] <= 0
        for key in ("width", "height")
    ):
        errors.append("canvas must define positive integer width and height")
    poses = spec.get("poses")
    if not isinstance(poses, list) or not poses:
        errors.append("poses must be a non-empty list")
        return errors
    last = -1.0
    for index, pose in enumerate(poses):
        if (
            not isinstance(pose, dict)
            or isinstance(pose.get("at"), bool)
            or not isinstance(pose.get("at"), (int, float))
            or not math.isfinite(pose.get("at", -1))
            or pose.get("at", -1) < last
        ):
            errors.append(f"poses[{index}] must have an ordered non-negative time")
            continue
        last = float(pose["at"])
        if pose.get("expression", "neutral") not in EXPRESSIONS:
            errors.append(f"poses[{index}].expression is unsupported")
        joints = pose.get("joints")
        if not isinstance(joints, dict) or not JOINTS.issubset(joints):
            errors.append(f"poses[{index}].joints must define {sorted(JOINTS)}")
            continue
        for joint in JOINTS:
            if not _valid_point(joints[joint]):
                errors.append(f"poses[{index}].joints.{joint} must be a finite [x, y] pair")
        mouth_open = pose.get("mouth_open", 0)
        if (
            isinstance(mouth_open, bool)
            or not isinstance(mouth_open, (int, float))
            or not math.isfinite(mouth_open)
            or not 0 <= mouth_open <= 1
        ):
            errors.append(f"poses[{index}].mouth_open must be between 0 and 1")
        hands = pose.get("hands", {})
        if not isinstance(hands, dict) or any(
            hands.get(side, "open") not in HAND_POSES for side in ("left", "right")
        ):
            errors.append(f"poses[{index}].hands must use supported left/right hand poses")
    props = spec.get("props", [])
    if not isinstance(props, list):
        errors.append("props must be a list")
    else:
        for index, prop in enumerate(props):
            if not isinstance(prop, dict):
                errors.append(f"props[{index}] must be an object")
                continue
            if prop.get("type") not in PROP_TYPES:
                errors.append(f"props[{index}].type is unsupported")
            if prop.get("hand") not in {"left", "right"}:
                errors.append(f"props[{index}].hand must be left or right")
            if "from" in prop and (
                isinstance(prop["from"], bool)
                or not isinstance(prop["from"], (int, float))
                or prop["from"] < 0
            ):
                errors.append(f"props[{index}].from must be non-negative")
            if "to" in prop and (
                isinstance(prop["to"], bool)
                or not isinstance(prop["to"], (int, float))
                or prop["to"] < prop.get("from", 0)
            ):
                errors.append(f"props[{index}].to must be >= from")
    return errors


def _sample_pose(poses: list[dict[str, Any]], at: float) -> dict[str, Any]:
    if at <= poses[0]["at"]:
        return poses[0]
    if at >= poses[-1]["at"]:
        return poses[-1]
    for first, second in pairwise(poses):
        if first["at"] <= at <= second["at"]:
            span = second["at"] - first["at"]
            t = (at - first["at"]) / span if span else 1.0
            joints = {
                name: [
                    first["joints"][name][axis]
                    + (second["joints"][name][axis] - first["joints"][name][axis]) * t
                    for axis in (0, 1)
                ]
                for name in JOINTS
            }
            return {
                "joints": joints,
                "expression": second.get("expression", first.get("expression", "neutral")),
                "mouth_open": first.get("mouth_open", 0)
                + (second.get("mouth_open", 0) - first.get("mouth_open", 0)) * t,
                "hands": second.get("hands", first.get("hands", {})),
            }
    return poses[-1]


def _draw_limb(draw: ImageDraw.ImageDraw, start: tuple[int, int],
               end: tuple[int, int], color: str, outline: str, width: int) -> None:
    draw.line((start, end), fill=outline, width=width + 6)
    draw.line((start, end), fill=color, width=width)
    radius = width // 2
    for x, y in (start, end):
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color, outline=outline, width=2)


def _draw_hand(draw: ImageDraw.ImageDraw, point: tuple[int, int], skin: str,
               outline: str, hand_pose: str, scale: int = 1) -> None:
    x, y = point
    palm = 11 * scale
    draw.ellipse((x-palm, y-palm, x+palm, y+palm), fill=skin, outline=outline, width=2)
    if hand_pose == "closed":
        return
    if hand_pose == "point":
        draw.line((x+4*scale, y-3*scale, x+17*scale, y-14*scale), fill=outline, width=5*scale)
        draw.line((x+4*scale, y-3*scale, x+17*scale, y-14*scale), fill=skin, width=3*scale)
        return
    for offset in (-7, 0, 7):
        draw.line((x+offset*scale, y-5*scale, x+offset*scale, y-18*scale),
                  fill=outline, width=4*scale)
        draw.line((x+offset*scale, y-5*scale, x+offset*scale, y-18*scale),
                  fill=skin, width=2*scale)


def _draw_prop(draw: ImageDraw.ImageDraw, prop: dict[str, Any],
               hand: tuple[int, int], outline: str) -> None:
    offset = prop.get("offset", [12, 0])
    x, y = hand[0] + round(offset[0]), hand[1] + round(offset[1])
    kind = prop["type"]
    if kind == "phone":
        draw.rounded_rectangle((x-17, y-31, x+17, y+31), radius=5,
                               fill="#26364A", outline=outline, width=3)
        draw.rounded_rectangle((x-12, y-23, x+12, y+21), radius=2,
                               fill="#DCEAF4", outline="#102B55", width=1)
        draw.ellipse((x-2, y+24, x+2, y+28), fill="#F5B817")
    elif kind == "bill":
        draw.rectangle((x-25, y-16, x+25, y+16), fill="#FFFDF5",
                       outline="#168C43", width=3)
        draw.ellipse((x-7, y-7, x+7, y+7), outline="#168C43", width=2)
        draw.line((x-19, y-10, x-12, y-10), fill="#168C43", width=2)
        draw.line((x+12, y+10, x+19, y+10), fill="#168C43", width=2)
    elif kind == "envelope":
        draw.rectangle((x-24, y-16, x+24, y+16), fill="#FFFDF5",
                       outline="#C28A16", width=3)
        draw.line((x-23, y-14, x, y+4, x+23, y-14), fill="#C28A16", width=2)
    else:
        draw.ellipse((x-13, y-13, x+13, y+13), fill="#F5B817",
                     outline="#9B6A08", width=3)
        draw.ellipse((x-5, y-5, x+5, y+5), outline="#9B6A08", width=2)


def render_character_frame(
    spec: dict[str, Any],
    at_seconds: float,
    *,
    mouth_open_override: float | None = None,
) -> Image.Image:
    errors = validate_character_rig(spec)
    if errors:
        raise CharacterRigError("; ".join(errors))
    if not math.isfinite(at_seconds) or at_seconds < 0:
        raise CharacterRigError("at_seconds must be finite and non-negative")
    width, height = spec["canvas"]["width"], spec["canvas"]["height"]
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    pose = dict(_sample_pose(spec["poses"], at_seconds))
    if mouth_open_override is not None:
        if (
            isinstance(mouth_open_override, bool)
            or not isinstance(mouth_open_override, (int, float))
            or not math.isfinite(mouth_open_override)
            or not 0 <= mouth_open_override <= 1
        ):
            raise CharacterRigError("mouth_open_override must be between 0 and 1")
        pose["mouth_open"] = float(mouth_open_override)
    joints = {
        key: tuple(round(value) for value in point)
        for key, point in pose["joints"].items()
    }
    skin = spec["skin"]
    hair = spec["hair"]
    clothing = spec["clothing"]
    outline = spec.get("outline", "#26364A")
    trousers = clothing.get("trousers", "#26364A")
    shoes = clothing.get("shoes", "#202936")
    top = clothing.get("top", "#2F6F9F")

    # Rear limbs are drawn first to keep the torso and hands visually in front.
    for side in ("left", "right"):
        _draw_limb(draw, joints[f"hip_{side}"], joints[f"knee_{side}"],
                   trousers, outline, 28)
        _draw_limb(draw, joints[f"knee_{side}"], joints[f"foot_{side}"],
                   trousers, outline, 23)
        fx, fy = joints[f"foot_{side}"]
        draw.rounded_rectangle((fx-25, fy-10, fx+25, fy+12), radius=8,
                               fill=shoes, outline=outline, width=3)

    left_shoulder, right_shoulder = joints["shoulder_left"], joints["shoulder_right"]
    left_hip, right_hip = joints["hip_left"], joints["hip_right"]
    torso = [
        (left_shoulder[0]-17, left_shoulder[1]),
        (right_shoulder[0]+17, right_shoulder[1]),
        (right_hip[0]+20, right_hip[1]),
        (left_hip[0]-20, left_hip[1]),
    ]
    draw.polygon(torso, fill=top)
    draw.line(torso + [torso[0]], fill=outline, width=5)
    draw.line((left_shoulder[0]+8, left_shoulder[1]+20,
               (left_shoulder[0]+right_shoulder[0])//2,
               left_shoulder[1]+39,
               right_shoulder[0]-8, right_shoulder[1]+20),
              fill=clothing.get("trim", "#F5B817"), width=5)

    # Arms have independent elbow and wrist paths on both sides.
    active_props = [
        prop for prop in spec.get("props", [])
        if prop.get("from", 0) <= at_seconds <= prop.get("to", float("inf"))
    ]
    for side in ("left", "right"):
        shoulder = joints[f"shoulder_{side}"]
        elbow = joints[f"elbow_{side}"]
        hand = joints[f"hand_{side}"]
        _draw_limb(draw, shoulder, elbow, skin, outline, 22)
        _draw_limb(draw, elbow, hand, skin, outline, 18)
        held = next((prop for prop in active_props if prop["hand"] == side), None)
        if held:
            _draw_prop(draw, held, hand, outline)
        _draw_hand(draw, hand, skin, outline,
                   "hold" if held else pose.get("hands", {}).get(side, "open"))

    # Neck, head silhouette, hair, brows and expressive face.
    head_x, head_y = joints["head"]
    neck_x, neck_y = joints["neck"]
    draw.rounded_rectangle((neck_x-13, neck_y-4, neck_x+13, neck_y+35),
                           radius=9, fill=skin, outline=outline, width=3)
    draw.ellipse((head_x-48, head_y-58, head_x+48, head_y+58),
                 fill=skin, outline=outline, width=5)
    draw.pieslice((head_x-51, head_y-65, head_x+51, head_y+28),
                  180, 360, fill=hair, outline=outline, width=4)
    draw.ellipse((head_x-51, head_y-12, head_x-34, head_y+24),
                 fill=hair, outline=outline, width=2)
    draw.ellipse((head_x+34, head_y-12, head_x+51, head_y+24),
                 fill=hair, outline=outline, width=2)

    expression = pose.get("expression", "neutral")
    eye_y = head_y - 3
    eye_offset = 17
    brow_raise = -10 if expression in {"worried", "anxious", "surprised"} else -6
    for direction in (-1, 1):
        eye_x = head_x + direction * eye_offset
        draw.line((eye_x-8, eye_y+brow_raise, eye_x+8, eye_y+brow_raise+2),
                  fill=outline, width=3)
        draw.ellipse((eye_x-3, eye_y-1, eye_x+3, eye_y+7), fill=outline)
    mouth_open = float(pose.get("mouth_open", 0))
    mouth_top = head_y + 21
    if mouth_open > 0.08:
        mouth_height = 4 + round(15 * mouth_open)
        draw.ellipse((head_x-8, mouth_top, head_x+8, mouth_top+mouth_height),
                     fill="#5A2020", outline=outline, width=2)
        if mouth_open > 0.55:
            draw.line((head_x-5, mouth_top+4, head_x+5, mouth_top+4),
                      fill="#FFFFFF", width=2)
    elif expression in {"joyful", "hopeful", "relieved"}:
        draw.arc((head_x-14, head_y+17, head_x+14, head_y+40),
                 5, 175, fill=outline, width=4)
    elif expression in {"worried", "anxious", "frustrated"}:
        draw.arc((head_x-13, head_y+25, head_x+13, head_y+40),
                 185, 355, fill=outline, width=4)
    elif expression == "surprised":
        draw.ellipse((head_x-5, head_y+22, head_x+5, head_y+36),
                     outline=outline, width=3)
    else:
        draw.line((head_x-10, head_y+29, head_x+10, head_y+29),
                  fill=outline, width=3)

    if spec.get("accessory") == "glasses":
        for eye_x in (head_x-eye_offset, head_x+eye_offset):
            draw.ellipse((eye_x-12, eye_y-9, eye_x+12, eye_y+13),
                         outline=outline, width=3)
        draw.line((head_x-5, eye_y+1, head_x+5, eye_y+1),
                  fill=outline, width=3)
    return image


def render_character_sequence(
    spec: dict[str, Any],
    output_dir: str | Path,
    *,
    fps: int = 30,
    audio_path: str | Path | None = None,
) -> int:
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise CharacterRigError("fps must be a positive integer")
    errors = validate_character_rig(spec)
    if errors:
        raise CharacterRigError("; ".join(errors))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    duration = float(spec.get("duration_seconds", spec["poses"][-1]["at"]))
    if not math.isfinite(duration) or duration <= 0:
        raise CharacterRigError("duration_seconds must be positive and finite")
    frame_count = math.ceil(duration * fps)
    mouth_track = None
    if audio_path is not None:
        from finance_campus.lip_sync import audio_energy_mouth_track

        mouth_track = audio_energy_mouth_track(audio_path, fps=fps)
        if not mouth_track:
            raise CharacterRigError("audio produced an empty lip-sync track")
    for index in range(frame_count):
        mouth_open = mouth_track[min(index, len(mouth_track)-1)] if mouth_track else None
        render_character_frame(
            spec, index / fps, mouth_open_override=mouth_open
        ).save(destination / f"character_{index:06d}.png")
    return frame_count
