import pytest
from pathlib import Path

from PIL import Image

from finance_campus.character_rig import (
    CharacterRigError,
    render_character_frame,
    render_character_sequence,
    validate_character_rig,
)


def rig():
    return {
        "id": "parent_01", "name": "Amina",
        "canvas": {"width": 300, "height": 400},
        "skin": "#8A5238", "hair": "#211A18",
        "clothing": {"top": "#2F6F9F", "trousers": "#26364A"},
        "duration_seconds": 1,
        "poses": [
            {"at": 0, "expression": "worried", "joints": {
                "head": [150, 70], "neck": [150, 115], "shoulders": [150, 145],
                "elbows": [110, 190], "hands": [95, 230], "hips": [150, 230],
                "knees": [140, 300], "feet": [135, 370]}},
            {"at": 1, "expression": "hopeful", "joints": {
                "head": [155, 65], "neck": [155, 110], "shoulders": [155, 140],
                "elbows": [200, 180], "hands": [230, 140], "hips": [155, 225],
                "knees": [145, 295], "feet": [140, 365]}}
        ],
    }


def test_rig_validates_and_renders_transparent_character():
    spec = rig()
    assert validate_character_rig(spec) == []
    frame = render_character_frame(spec, 0.5)
    assert frame.mode == "RGBA"
    assert frame.size == (300, 400)
    assert frame.getchannel("A").getbbox() is not None


def test_rig_rejects_missing_joints():
    spec = rig()
    spec["poses"][0]["joints"].pop("hands")
    assert any("must define" in error for error in validate_character_rig(spec))


def test_rig_exports_consistent_frame_sequence(tmp_path: Path):
    count = render_character_sequence(rig(), tmp_path, fps=2)
    assert count == 2
    assert len(list(tmp_path.glob("character_*.png"))) == 2
    assert Image.open(tmp_path / "character_000000.png").size == (300, 400)


def test_invalid_expression_is_rejected():
    spec = rig()
    spec["poses"][0]["expression"] = "sleepwalking"
    with pytest.raises(CharacterRigError):
        render_character_frame(spec, 0)
