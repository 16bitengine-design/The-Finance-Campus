import math
import wave
from pathlib import Path

import pytest
from PIL import Image

from finance_campus.character_rig import (
    CharacterRigError,
    render_character_frame,
    render_character_sequence,
    validate_character_rig,
)


def rig():
    return {
        "id": "parent_01",
        "name": "Amina",
        "canvas": {"width": 400, "height": 500},
        "skin": "#8A5238",
        "hair": "#211A18",
        "clothing": {"top": "#2F6F9F", "trousers": "#26364A"},
        "duration_seconds": 1,
        "props": [{"type": "bill", "hand": "left", "from": 0, "to": 1}],
        "poses": [
            {
                "at": 0,
                "expression": "worried",
                "mouth_open": 0.1,
                "hands": {"left": "hold", "right": "open"},
                "joints": {
                    "head": [200, 90], "neck": [200, 150],
                    "shoulder_left": [165, 185], "shoulder_right": [235, 185],
                    "elbow_left": [120, 230], "elbow_right": [280, 230],
                    "hand_left": [100, 250], "hand_right": [300, 250],
                    "hip_left": [180, 315], "hip_right": [220, 315],
                    "knee_left": [170, 390], "knee_right": [230, 390],
                    "foot_left": [160, 470], "foot_right": [240, 470],
                },
            },
            {
                "at": 1,
                "expression": "hopeful",
                "mouth_open": 0.8,
                "hands": {"left": "closed", "right": "point"},
                "joints": {
                    "head": [205, 85], "neck": [205, 145],
                    "shoulder_left": [170, 180], "shoulder_right": [240, 180],
                    "elbow_left": [130, 230], "elbow_right": [290, 210],
                    "hand_left": [110, 260], "hand_right": [330, 170],
                    "hip_left": [185, 310], "hip_right": [225, 310],
                    "knee_left": [175, 385], "knee_right": [235, 385],
                    "foot_left": [165, 465], "foot_right": [245, 465],
                },
            },
        ],
    }


def test_rig_validates_and_renders_transparent_character():
    spec = rig()
    assert validate_character_rig(spec) == []
    frame = render_character_frame(spec, 0.5)
    assert frame.mode == "RGBA"
    assert frame.size == (400, 500)
    assert frame.getchannel("A").getbbox() is not None


def test_rig_rejects_missing_bilateral_joint():
    spec = rig()
    spec["poses"][0]["joints"].pop("hand_right")
    assert any("must define" in error for error in validate_character_rig(spec))


def test_rig_exports_consistent_frame_sequence(tmp_path: Path):
    count = render_character_sequence(rig(), tmp_path, fps=2)
    assert count == 2
    assert len(list(tmp_path.glob("character_*.png"))) == 2
    assert Image.open(tmp_path / "character_000000.png").size == (400, 500)


def test_invalid_expression_is_rejected():
    spec = rig()
    spec["poses"][0]["expression"] = "sleepwalking"
    with pytest.raises(CharacterRigError):
        render_character_frame(spec, 0)


def test_mouth_animation_is_validated():
    spec = rig()
    spec["poses"][0]["mouth_open"] = 1.5
    assert any("mouth_open" in error for error in validate_character_rig(spec))


def test_prop_attachment_is_validated():
    spec = rig()
    spec["props"][0]["hand"] = "middle"
    assert any("hand must be left or right" in error for error in validate_character_rig(spec))



def test_character_sequence_can_sync_mouth_to_audio(tmp_path: Path):
    audio = tmp_path / "speech.wav"
    sample_rate = 24000
    samples = []
    for index in range(sample_rate):
        value = 0 if index < sample_rate // 2 else int(
            12000 * math.sin(2 * math.pi * 220 * index / sample_rate)
        )
        samples.append(value)
    with wave.open(str(audio), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(
            b"".join(value.to_bytes(2, "little", signed=True) for value in samples)
        )
    spec = rig()
    output = tmp_path / "synced-frames"
    assert render_character_sequence(spec, output, fps=10, audio_path=audio) == 10
    assert len(list(output.glob("character_*.png"))) == 10
