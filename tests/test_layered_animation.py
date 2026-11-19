from pathlib import Path

import pytest
from PIL import Image

from finance_campus.layered_animation import (
    LayeredSceneError,
    iter_layered_frames,
    render_layered_frame,
    validate_layered_scene,
)


def make_scene():
    return {
        "canvas": {"width": 120, "height": 80},
        "duration_seconds": 2,
        "layers": [
            {
                "id": "envelope",
                "asset": "envelope.png",
                "z": 1,
                "reveal": "left_to_right",
                "keyframes": [
                    {"at": 0, "x": 10, "y": 20, "reveal_progress": 0},
                    {"at": 1, "x": 30, "y": 20, "reveal_progress": 1, "easing": "ease_out"},
                    {"at": 2, "x": 40, "y": 20, "rotation": -8},
                ],
            }
        ],
    }


def test_layered_scene_contract_rejects_unordered_keyframes():
    scene = make_scene()
    scene["layers"][0]["keyframes"].reverse()
    assert any("must be ordered" in error for error in validate_layered_scene(scene))


def test_layered_frame_reveals_and_moves_authored_artwork(tmp_path: Path):
    artwork = Image.new("RGBA", (30, 20), (0, 140, 70, 255))
    artwork.save(tmp_path / "envelope.png")
    scene = make_scene()

    early = render_layered_frame(scene, 0, tmp_path)
    middle = render_layered_frame(scene, 1, tmp_path)
    assert early.getpixel((15, 25)) == (255, 255, 255, 255)
    assert middle.getpixel((35, 25))[3] == 255
    assert middle.getpixel((15, 25))[3] == 0


def test_layers_are_composited_in_z_order(tmp_path: Path):
    Image.new("RGBA", (20, 20), (0, 0, 255, 255)).save(tmp_path / "back.png")
    Image.new("RGBA", (20, 20), (255, 0, 0, 255)).save(tmp_path / "front.png")
    scene = {
        "canvas": {"width": 30, "height": 30},
        "duration_seconds": 1,
        "layers": [
            {"id": "front", "asset": "front.png", "z": 5, "keyframes": [{"at": 0, "x": 2, "y": 2}]},
            {"id": "back", "asset": "back.png", "z": 0, "keyframes": [{"at": 0, "x": 2, "y": 2}]},
        ],
    }
    assert render_layered_frame(scene, 0, tmp_path).getpixel((5, 5)) == (255, 0, 0, 255)


def test_asset_paths_cannot_escape_asset_root(tmp_path: Path):
    outside = tmp_path.parent / "outside.png"
    Image.new("RGBA", (2, 2), (1, 1, 1, 255)).save(outside)
    scene = make_scene()
    scene["layers"][0]["asset"] = "../outside.png"
    with pytest.raises(LayeredSceneError, match="escapes asset_root"):
        render_layered_frame(scene, 0, tmp_path)


def test_frame_iterator_uses_requested_frame_rate(tmp_path: Path):
    Image.new("RGBA", (4, 4), (20, 20, 20, 255)).save(tmp_path / "envelope.png")
    frames = list(iter_layered_frames(make_scene(), tmp_path, fps=2))
    assert len(frames) == 4
    assert all(frame.size == (120, 80) for frame in frames)


def test_missing_artwork_fails_instead_of_using_generic_fallback(tmp_path: Path):
    with pytest.raises(LayeredSceneError, match="missing illustration asset"):
        render_layered_frame(make_scene(), 0.5, tmp_path)
