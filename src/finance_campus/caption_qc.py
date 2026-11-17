"""Strict validation for SRT captions against synthesized narration timing."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_TIMESTAMP = re.compile(r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3})$")


def _seconds(value: str) -> float:
    match = _TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"Out-of-range SRT timestamp: {value!r}")
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def validate_srt(
    captions_path: str | Path,
    *,
    audio_duration_seconds: float,
    expected_speech_seconds: float | None = None,
    tolerance_seconds: float = 0.08,
) -> dict[str, Any]:
    """Reject malformed, overlapping, empty, out-of-range or incomplete captions."""
    path = Path(captions_path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Caption file is missing or empty")
    if audio_duration_seconds <= 0 or tolerance_seconds < 0:
        raise ValueError("Audio duration must be positive and tolerance non-negative")
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        raise ValueError("Caption file contains no cues")

    blocks = re.split(r"\r?\n\s*\r?\n", content)
    previous_end = 0.0
    covered_seconds = 0.0
    first_start: float | None = None
    last_end = 0.0
    for expected_index, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            raise ValueError(f"Caption cue {expected_index} is incomplete")
        if not lines[0].isdigit() or int(lines[0]) != expected_index:
            raise ValueError(f"Caption cue numbering is not sequential at cue {expected_index}")
        timing = lines[1].split("-->")
        if len(timing) != 2:
            raise ValueError(f"Caption cue {expected_index} has invalid timing syntax")
        start, end = _seconds(timing[0]), _seconds(timing[1])
        if end <= start:
            raise ValueError(f"Caption cue {expected_index} has zero or negative duration")
        if start + tolerance_seconds < previous_end:
            raise ValueError(f"Caption cue {expected_index} overlaps the previous cue")
        if end > audio_duration_seconds + tolerance_seconds:
            raise ValueError(f"Caption cue {expected_index} extends beyond the audio")
        if not any(line.strip() for line in lines[2:]):
            raise ValueError(f"Caption cue {expected_index} has no caption text")
        if first_start is None:
            first_start = start
        previous_end = end
        last_end = end
        covered_seconds += end - start

    coverage = None
    if expected_speech_seconds is not None:
        if expected_speech_seconds <= 0:
            raise ValueError("Expected speech duration must be positive")
        # Genuine word-level timestamps leave natural pauses between caption
        # phrases. Allow a bounded 8% timing gap while still rejecting materially
        # incomplete caption tracks; never stretch cues to cover silent audio.
        coverage = covered_seconds / expected_speech_seconds
        minimum_coverage = 0.92
        if coverage < minimum_coverage:
            raise ValueError(
                "Caption coverage is incomplete for synthesized speech: "
                f"captions={covered_seconds:.3f}s, speech={expected_speech_seconds:.3f}s, "
                f"coverage={coverage:.1%}, required={minimum_coverage:.0%}"
            )

    return {
        "passed": True,
        "cue_count": len(blocks),
        "first_caption_seconds": round(first_start or 0.0, 3),
        "last_caption_seconds": round(last_end, 3),
        "caption_covered_seconds": round(covered_seconds, 3),
        "speech_coverage_ratio": round(coverage, 4) if coverage is not None else None,
        "audio_duration_seconds": round(audio_duration_seconds, 3),
    }
