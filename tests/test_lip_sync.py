import math
import wave

import pytest

from finance_campus.lip_sync import LipSyncError, audio_energy_mouth_track


def write_test_wav(path):
    sample_rate = 24000
    samples = []
    for index in range(sample_rate * 2):
        if index < sample_rate:
            samples.append(0)
        else:
            value = int(12000 * math.sin(2 * math.pi * 220 * index / sample_rate))
            samples.append(value)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(value.to_bytes(2, "little", signed=True) for value in samples))


def test_audio_energy_track_follows_real_wav_amplitude(tmp_path):
    audio = tmp_path / "narration.wav"
    write_test_wav(audio)
    track = audio_energy_mouth_track(audio, fps=10)
    assert len(track) == 20
    assert max(track[:8]) == 0
    assert max(track[12:]) > 0.8


def test_audio_energy_track_rejects_invalid_fps(tmp_path):
    audio = tmp_path / "narration.wav"
    write_test_wav(audio)
    with pytest.raises(LipSyncError, match="fps must be a positive integer"):
        audio_energy_mouth_track(audio, fps=0)


def test_audio_energy_track_rejects_missing_audio(tmp_path):
    with pytest.raises(LipSyncError, match="cannot read narration WAV"):
        audio_energy_mouth_track(tmp_path / "missing.wav", fps=30)
