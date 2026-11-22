from PIL import ImageChops

from finance_campus.multi_character_compositor import (
    render_multi_character_frame,
    validate_multi_character_scene,
)


def _rig(color="#2F6F9F"):
    joints = {
        "head": [50, 20], "neck": [50, 45],
        "shoulder_left": [30, 55], "shoulder_right": [70, 55],
        "elbow_left": [20, 80], "elbow_right": [80, 80],
        "hand_left": [15, 105], "hand_right": [85, 105],
        "hip_left": [40, 115], "hip_right": [60, 115],
        "knee_left": [35, 155], "knee_right": [65, 155],
        "foot_left": [30, 190], "foot_right": [70, 190],
    }
    return {
        "id": color, "name": "Test character", "skin": "#A86F4D",
        "hair": "#202020",
        "clothing": {"top": color, "trousers": "#26364A"},
        "canvas": {"width": 100, "height": 210},
        "poses": [{"at": 0, "joints": joints}],
    }


def test_multi_character_scene_validates_and_composites_in_z_order():
    specs = {"back": _rig("#168C43"), "front": _rig("#F5B817")}
    scene = {
        "canvas": {"width": 240, "height": 240}, "fps": 30,
        "duration_seconds": 1,
        "characters": [
            {"id": "front", "z": 2, "keyframes": [{"at": 0, "x": 70, "y": 10}]},
            {"id": "back", "z": 1, "keyframes": [{"at": 0, "x": 70, "y": 10}]},
        ],
    }
    assert validate_multi_character_scene(scene, specs) == []
    frame = render_multi_character_frame(scene, specs, 0)
    assert frame.mode == "RGBA"
    assert frame.size == (240, 240)
    # The combined frame must match a front-only render at overlapping pixels.
    front_only = {**scene, "characters": [scene["characters"][0]]}
    front_frame = render_multi_character_frame(front_only, specs, 0)
    difference = ImageChops.difference(frame, front_frame)
    assert difference.getbbox() is None


def test_character_tracks_interpolate_position_and_opacity():
    specs = {"person": _rig()}
    scene = {
        "canvas": {"width": 240, "height": 240}, "fps": 30,
        "duration_seconds": 2,
        "characters": [{
            "id": "person", "keyframes": [
                {"at": 0, "x": 0, "y": 0, "opacity": 0.5},
                {"at": 2, "x": 40, "y": 20, "opacity": 1},
            ],
        }],
    }
    assert validate_multi_character_scene(scene, specs) == []
    frame = render_multi_character_frame(scene, specs, 1)
    assert frame.size == (240, 240)
    assert frame.getchannel("A").getextrema()[1] == 255


def test_multi_character_scene_rejects_missing_spec_and_bad_scale():
    scene = {
        "canvas": {"width": 240, "height": 240}, "fps": 30,
        "duration_seconds": 1,
        "characters": [{"id": "missing", "keyframes": [{"at": 0, "scale": 0}]}],
    }
    errors = validate_multi_character_scene(scene, {})
    assert any("no character spec" in error for error in errors)
    assert any("scale must be positive" in error for error in errors)
