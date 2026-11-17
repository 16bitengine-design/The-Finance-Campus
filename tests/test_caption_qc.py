from pathlib import Path

import pytest

from finance_campus.caption_qc import validate_srt


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "captions.srt"
    path.write_text(body, encoding="utf-8")
    return path


def test_validate_srt_accepts_ordered_cues_matching_speech(tmp_path):
    path = _write(
        tmp_path,
        "1\n00:00:00,000 --> 00:00:01,200\nMoney arrives.\n\n"
        "2\n00:00:01,200 --> 00:00:02,500\nSave some regularly.\n",
    )
    report = validate_srt(
        path, audio_duration_seconds=3.0, expected_speech_seconds=2.5
    )
    assert report["passed"] is True
    assert report["cue_count"] == 2
    assert report["speech_coverage_ratio"] == 1.0


@pytest.mark.parametrize(
    "body, message",
    [
        ("", "empty"),
        ("1\n00:00:00,000 --> 00:00:00,000\nNo duration", "zero or negative"),
        (
            ("1\n00:00:00,000 --> 00:00:01,500\nFirst\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nSecond"),
            "overlaps",
        ),
        (
            "1\n00:00:00,000 --> 00:00:04,000\nToo long",
            "beyond the audio",
        ),
        (
            "1\n00:00:00,000 --> 00:00:01,000\nOnly half",
            "coverage does not match",
        ),
    ],
)
def test_validate_srt_rejects_bad_caption_timing(tmp_path, body, message):
    path = _write(tmp_path, body)
    with pytest.raises(ValueError, match=message):
        validate_srt(
            path,
            audio_duration_seconds=3.0,
            expected_speech_seconds=2.0 if "half" in body else None,
        )


def test_validate_srt_rejects_non_sequential_cue_numbers(tmp_path):
    path = _write(tmp_path, "2\n00:00:00,000 --> 00:00:01,000\nCaption")
    with pytest.raises(ValueError, match="numbering is not sequential"):
        validate_srt(path, audio_duration_seconds=2.0)


def test_validate_srt_rejects_malformed_timestamps(tmp_path):
    path = _write(tmp_path, "1\n00:00:xx,000 --> 00:00:01,000\nCaption")
    with pytest.raises(ValueError, match="Invalid SRT timestamp"):
        validate_srt(path, audio_duration_seconds=2.0)
