"""Audio-envelope-driven mouth animation for character sequences.

This provides real audio synchronization at frame rate. It is not phoneme or
viseme recognition: mouth aperture follows the measured narration energy.
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


class LipSyncError(ValueError):
    """Raised when narration audio cannot drive a mouth animation track."""


def audio_energy_mouth_track(
    audio_path: str | Path, *, fps: int = 30
) -> list[float]:
    """Return one normalized mouth-aperture value per video frame."""
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise LipSyncError("fps must be a positive integer")
    path = Path(audio_path)
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frame_count = wav.getnframes()
            if wav.getcomptype() != "NONE":
                raise LipSyncError("audio must be uncompressed PCM WAV")
            if channels < 1 or sample_rate < 1 or frame_count < 1:
                raise LipSyncError("audio WAV has invalid channel, rate or frame count")
            if sample_width not in {1, 2, 4}:
                raise LipSyncError("audio WAV must use 8-bit, 16-bit or 32-bit PCM")
            raw = wav.readframes(frame_count)
    except (OSError, wave.Error) as exc:
        raise LipSyncError(f"cannot read narration WAV: {exc}") from exc

    if not raw:
        raise LipSyncError("audio WAV contains no samples")
    if sample_width == 1:
        samples = [((value - 128) / 128.0) for value in raw]
    elif sample_width == 2:
        samples = [value[0] / 32768.0 for value in struct.iter_unpack("<h", raw)]
    else:
        samples = [value[0] / 2147483648.0 for value in struct.iter_unpack("<i", raw)]

    samples_per_frame = max(1, round(sample_rate * channels / fps))
    energies: list[float] = []
    for start in range(0, len(samples), samples_per_frame):
        chunk = samples[start:start + samples_per_frame]
        rms = math.sqrt(sum(value * value for value in chunk) / len(chunk))
        energies.append(rms)

    ordered = sorted(energies)
    floor = ordered[min(len(ordered)-1, int((len(ordered)-1) * 0.2))]
    ceiling = ordered[min(len(ordered)-1, int((len(ordered)-1) * 0.9))]
    if ceiling <= floor + 1e-8:
        return [0.0] * len(energies)

    track: list[float] = []
    previous = 0.0
    for energy in energies:
        raw_open = min(1.0, max(0.0, (energy-floor) / (ceiling-floor)))
        # Smooth small frame-to-frame energy changes while retaining attacks.
        value = 0.65 * raw_open + 0.35 * previous
        track.append(round(value, 4))
        previous = value
    return track
