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
        # Word-level Kokoro timestamps intentionally leave small gaps between
        # spoken words and phrases. Summing cue lengths therefore understates
        # the duration of the speech timeline. Compare the first-to-last cue
        # span instead; still report the actual on-screen captioned seconds.
        timeline_span = max(0.0, last_end - (first_start or 0.0))
        coverage = timeline_span / expected_speech_seconds
        if abs(timeline_span - expected_speech_seconds) > max(
            tolerance_seconds * len(blocks), expected_speech_seconds * 0.02
        ):
            raise ValueError(
                "Caption timeline does not match synthesized speech duration: "
                f"timeline={timeline_span:.3f}s, speech={expected_speech_seconds:.3f}s"
            )

    return {
        "passed": True,
        "cue_count": len(blocks),
        "first_caption_seconds": round(first_start or 0.0, 3),
        "last_caption_seconds": round(last_end, 3),
        "caption_covered_seconds": round(covered_seconds, 3),
        "caption_timeline_span_seconds": (
            round(last_end - (first_start or 0.0), 3)
            if expected_speech_seconds is not None else None
        ),
        "speech_coverage_ratio": round(coverage, 4) if coverage is not None else None,
        "audio_duration_seconds": round(audio_duration_seconds, 3),
    }
