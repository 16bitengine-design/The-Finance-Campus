from pathlib import Path

import numpy as np

import pytest
import soundfile as sf

from finance_campus.narration import SUPPORTED_VOICES, _sentence_groups, synthesize_storyboard


class FakeKokoroPipeline:
    def __call__(self, text, *, voice, speed):
        assert voice in SUPPORTED_VOICES
        assert 0.7 <= speed <= 1.3
        samples = np.sin(np.linspace(0, 2 * np.pi * 220 * 0.25, 6000, endpoint=False))
        yield text, "fake phonemes", samples.astype(np.float32) * 0.15


def fake_pipeline_factory(**kwargs):
    assert kwargs["lang_code"] in {"a", "b"}
    return FakeKokoroPipeline()


def _storyboard():
    return {
        "canvas": {"width": 1000, "height": 562},
        "scenes": [
            {
                "id": "income",
                "narration": (
                    "Money arrives in your account. Give every shilling a purpose "
                    "before spending begins."
                ),
                "duration_seconds": 2,
                "elements": [
                    {"type": "money_note", "x": 100, "y": 100, "width": 180, "height": 100}
                ],
            },
            {
                "id": "saving",
                "narration": (
                    "Move a manageable amount into savings. Repeat the habit "
                    "and your emergency buffer can grow."
                ),
                "duration_seconds": 2,
                "elements": [
                    {"type": "savings_jar", "x": 400, "y": 100, "width": 180, "height": 220}
                ],
            },
        ],
    }


def test_sentence_groups_keep_complete_sentences_and_avoid_tiny_chunks():
    groups = _sentence_groups(
        "Start with a plan. Track every expense. Then build your savings one step at a time."
    )
    assert groups
    assert "Start with a plan." in groups[0]
    assert groups[-1].endswith("time.")


def test_kokoro_synthesis_writes_valid_audio_captions_and_timed_storyboard(tmp_path):
    result = synthesize_storyboard(
        _storyboard(),
        tmp_path,
        voice="af_heart",
        transition_seconds=0.25,
        scene_tail_seconds=0.35,
        draw_fps=24,
        pipeline_factory=fake_pipeline_factory,
    )
    audio = sf.info(result["audio_path"])
    assert audio.samplerate == 24000
    assert audio.channels == 1
    assert audio.duration == pytest.approx(result["duration_seconds"], abs=0.001)
    assert result["voice_gender"] == "female"
    assert result["scene_count"] == 2

    import json

    updated = json.loads(Path(result["storyboard_path"]).read_text(encoding="utf-8"))
    assert all(scene["duration_seconds"] > 0.5 for scene in updated["scenes"])
    assert all(scene["narration_audio_seconds"] == 0.25 for scene in updated["scenes"])
    captions = Path(result["captions_path"]).read_text(encoding="utf-8")
    assert "00:00:00,000" in captions
    assert "Money arrives" in captions
    assert "Move a manageable amount" in captions
    assert "\\n" not in captions


def test_kokoro_synthesis_rejects_unknown_voice(tmp_path):
    with pytest.raises(ValueError, match="Unsupported Kokoro voice"):
        synthesize_storyboard(
            _storyboard(),
            tmp_path,
            voice="unknown_voice",
            pipeline_factory=fake_pipeline_factory,
        )


def test_kokoro_synthesis_rejects_invalid_speed(tmp_path):
    with pytest.raises(ValueError, match="speed"):
        synthesize_storyboard(
            _storyboard(),
            tmp_path,
            speed=2.0,
            pipeline_factory=fake_pipeline_factory,
        )


def test_sentence_groups_split_very_long_sentences_without_losing_words():
    sentence = " ".join(f"word{index}" for index in range(61))
    groups = _sentence_groups(sentence)
    assert all(len(group.split()) <= 24 for group in groups)
    assert [word for group in groups for word in group.split()] == sentence.split()
