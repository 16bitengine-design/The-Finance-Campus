"""Kokoro TTS narration synthesis and scene-aligned audio assembly."""
from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from finance_campus.storyboard import validate_storyboard

SAMPLE_RATE = 24_000
SUPPORTED_VOICES = {
    "af_heart": "female",
    "am_michael": "male",
    "bf_emma": "female",
    "bm_george": "male",
}


def _sentence_groups(text: str, *, min_words: int = 12, max_words: int = 24) -> list[str]:
    """Group complete sentences into natural chunks and split unusually long sentences."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    if not sentences:
        raise ValueError("Scene narration is empty")
    groups: list[str] = []
    pending: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal pending, count
        if pending:
            groups.append(" ".join(pending))
            pending, count = [], 0

    for sentence in sentences:
        words = sentence.split()
        if len(words) > max_words:
            flush()
            for offset in range(0, len(words), max_words):
                groups.append(" ".join(words[offset:offset + max_words]))
            continue
        if pending and count + len(words) > max_words:
            flush()
        pending.append(sentence)
        count += len(words)
        if count >= min_words and count >= max_words * 0.65:
            flush()

    if pending:
        if groups and count < min_words and len(groups[-1].split()) + count <= max_words:
            groups[-1] += " " + " ".join(pending)
        else:
            flush()
    return groups


def _audio_array(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    audio = np.asarray(value, dtype=np.float32).reshape(-1)
    if audio.size == 0 or not np.isfinite(audio).all():
        raise ValueError("Kokoro returned empty or non-finite audio")
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))
    if peak < 1e-5 or rms < 1e-6:
        raise ValueError("Kokoro returned silent narration")
    gain = min(0.1 / rms, 0.89 / peak)
    audio = audio * gain
    return audio


def _synthesize_chunk(pipeline: Any, text: str, voice: str, speed: float) -> np.ndarray:
    pieces: list[np.ndarray] = []
    try:
        generated = pipeline(text, voice=voice, speed=speed)
        for item in generated:
            if not isinstance(item, (tuple, list)) or len(item) < 3:
                raise RuntimeError("Unexpected Kokoro output; expected (graphemes, phonemes, audio)")
            pieces.append(_audio_array(item[2]))
    except Exception as exc:
        raise RuntimeError(f"Kokoro synthesis failed for narration chunk: {exc}") from exc
    if not pieces:
        raise RuntimeError("Kokoro produced no audio chunks")
    return np.concatenate(pieces)


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"


def _caption_lines(text: str, width: int = 48) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def synthesize_storyboard(
    storyboard: dict[str, Any],
    output_dir: str | Path,
    *,
    voice: str = "af_heart",
    speed: float = 1.0,
    device: str = "auto",
    transition_seconds: float = 0.25,
    scene_tail_seconds: float = 0.35,
    draw_fps: int = 24,
    pipeline_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Synthesize every scene, update its true duration, and write aligned WAV/SRT."""
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Invalid storyboard: " + "; ".join(errors))
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"Unsupported Kokoro voice {voice!r}; choose one of {', '.join(SUPPORTED_VOICES)}")
    if not math.isfinite(speed) or not 0.7 <= speed <= 1.3:
        raise ValueError("speed must be between 0.7 and 1.3")
    if not math.isfinite(transition_seconds) or transition_seconds < 0:
        raise ValueError("transition_seconds must be finite and non-negative")
    if not math.isfinite(scene_tail_seconds) or scene_tail_seconds < 0:
        raise ValueError("scene_tail_seconds must be finite and non-negative")
    if draw_fps < 1:
        raise ValueError("draw_fps must be positive")

    if pipeline_factory is None:
        try:
            from kokoro import KPipeline
        except ImportError as exc:
            raise RuntimeError(
                "Kokoro is not installed. Install the optional TTS dependencies with "
                "python -m pip install -e '.[tts]' and install espeak-ng."
            ) from exc
        kwargs: dict[str, Any] = {"lang_code": voice[0]}
        if device != "auto":
            kwargs["device"] = device
        pipeline = KPipeline(**kwargs)
    else:
        pipeline = pipeline_factory(lang_code=voice[0], device=None if device == "auto" else device)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    updated = {**storyboard, "scenes": []}
    audio_parts: list[np.ndarray] = []
    captions: list[str] = []
    timeline = 0.0
    cue_number = 1
    transition_gap = round(transition_seconds * draw_fps) / draw_fps
    tail_gap = round(scene_tail_seconds * draw_fps) / draw_fps

    for scene_index, scene in enumerate(storyboard["scenes"]):
        scene_copy = dict(scene)
        groups = _sentence_groups(str(scene["narration"]))
        scene_parts: list[np.ndarray] = []
        scene_offset = 0.0
        for group in groups:
            audio = _synthesize_chunk(pipeline, group, voice, speed)
            duration = len(audio) / SAMPLE_RATE
            scene_parts.append(audio)
            captions.append(
                f"{cue_number}\n{_timestamp(timeline + scene_offset)} --> "
                f"{_timestamp(timeline + scene_offset + duration)}\n"
                f"{_caption_lines(group)}\n"
            )
            cue_number += 1
            scene_offset += duration
        speech = np.concatenate(scene_parts)
        speech_duration = len(speech) / SAMPLE_RATE
        minimum_duration = float(scene.get("minimum_duration_seconds", 0.0))
        if not math.isfinite(minimum_duration) or minimum_duration < 0:
            raise ValueError(f"Scene {scene['id']} has invalid minimum_duration_seconds")
        visual_duration = math.ceil(max(speech_duration + tail_gap, minimum_duration) * draw_fps) / draw_fps
        actual_tail = max(0.0, visual_duration - speech_duration)
        audio_parts.append(speech)
        if actual_tail:
            audio_parts.append(np.zeros(round(actual_tail * SAMPLE_RATE), dtype=np.float32))
        scene_copy["duration_seconds"] = visual_duration
        scene_copy["narration_audio_seconds"] = round(speech_duration, 3)
        updated["scenes"].append(scene_copy)
        timeline += visual_duration
        if scene_index < len(storyboard["scenes"]) - 1 and transition_gap:
            audio_parts.append(np.zeros(round(transition_gap * SAMPLE_RATE), dtype=np.float32))
            timeline += transition_gap

    final_audio = np.concatenate(audio_parts)
    peak = float(np.max(np.abs(final_audio)))
    rms = float(np.sqrt(np.mean(np.square(final_audio))))
    if not np.isfinite(final_audio).all() or peak > 1.0 or rms < 1e-6:
        raise RuntimeError("Narration audio failed finite-value, peak, or silence validation")

    try:
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError("soundfile is missing; install the TTS extra with pip install -e '.[tts]'") from exc

    audio_path = destination / "narration.wav"
    captions_path = destination / "captions.srt"
    storyboard_path = destination / "storyboard_with_audio_timing.json"
    sf.write(str(audio_path), final_audio, SAMPLE_RATE, subtype="PCM_16")
    captions_path.write_text("\n".join(captions), encoding="utf-8")
    storyboard_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    info = sf.info(str(audio_path))
    if info.samplerate != SAMPLE_RATE or info.channels != 1 or info.frames == 0:
        raise RuntimeError("Written narration WAV failed sample-rate/channel/integrity validation")
    return {
        "audio_path": str(audio_path),
        "captions_path": str(captions_path),
        "storyboard_path": str(storyboard_path),
        "voice": voice,
        "voice_gender": SUPPORTED_VOICES[voice],
        "sample_rate": SAMPLE_RATE,
        "duration_seconds": round(info.duration, 3),
        "peak": round(peak, 5),
        "rms": round(rms, 5),
        "scene_count": len(updated["scenes"]),
    }
