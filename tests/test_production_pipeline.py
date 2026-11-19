import json
from pathlib import Path

import pytest

from finance_campus import production_pipeline


def _script():
    path = Path(__file__).parents[1] / "examples" / "script-package.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_production_pipeline_runs_all_stages_and_fails_closed(monkeypatch, tmp_path):
    def fake_synthesis(storyboard, output_dir, **kwargs):
        root = Path(output_dir)
        audio = root / "narration.wav"
        captions = root / "captions.srt"
        timed = root / "storyboard_with_audio_timing.json"
        audio.write_bytes(b"fake audio")
        captions.write_text("1\n00:00:00,000 --> 00:00:03,500\nExample captions\n", encoding="utf-8")
        updated = {**storyboard, "scenes": []}
        for scene in storyboard["scenes"]:
            item = dict(scene)
            item["duration_seconds"] = 6 if item["id"] == "financial-education-disclaimer" else 1
            item["narration_audio_seconds"] = 0.5
            updated["scenes"].append(item)
        timed.write_text(json.dumps(updated), encoding="utf-8")
        return {
            "audio_path": str(audio),
            "captions_path": str(captions),
            "storyboard_path": str(timed),
            "voice": "af_heart",
            "duration_seconds": 150.0,
            "scene_count": 7,
        }

    def fake_render(storyboard, output_path, **kwargs):
        path = Path(output_path)
        path.write_bytes(b"fake mp4")
        assert kwargs["audio_path"].endswith("narration.wav")
        assert kwargs["captions_path"].endswith("captions.srt")
        return path

    monkeypatch.setattr(production_pipeline, "synthesize_storyboard", fake_synthesis)
    monkeypatch.setattr(production_pipeline, "render_video", fake_render)
    monkeypatch.setattr(
        production_pipeline, "validate_final_video",
        lambda *args, **kwargs: {"passed": True, "video_codec": "h264"},
    )
    monkeypatch.setattr(
        production_pipeline, "create_visual_review_sheet",
        lambda video, output: {
            "path": str(output), "sample_count": 8,
            "human_review_required": True,
        },
    )
    monkeypatch.setattr(
        production_pipeline,
        "_probe_video",
        lambda path, video_format: {
            "width": 1080, "height": 1920, "audio_sample_rate": 24000,
            "audio_channels": 1, "duration_seconds": 150.0,
        },
    )

    manifest = production_pipeline.produce_video_from_script(
        _script(), tmp_path, pipeline_factory=object(),
    )
    assert manifest["status"] == "awaiting_visual_review"
    assert manifest["technical_quality_approved"] is True
    assert manifest["human_visual_review_required"] is True
    assert manifest["stages"]["script_approved"]
    assert manifest["stages"]["storyboard_generated"]
    assert manifest["stages"]["kokoro_narration_generated"]
    assert manifest["stages"]["video_rendered"]
    assert manifest["stages"]["final_video_qc_passed"]
    assert manifest["stages"]["visual_review_sheet_generated"]
    assert manifest["stages"]["human_visual_review_passed"] is False
    assert manifest["stages"]["quality_gate_passed"]
    assert manifest["stages"]["audio_video_duration_aligned"]
    assert manifest["stages"]["uploaded"] is False
    assert Path(manifest["artifacts"]["description"]).is_file()
    assert Path(manifest["artifacts"]["video"]).is_file()
    saved = json.loads((tmp_path / "production-manifest.json").read_text(encoding="utf-8"))
    assert saved["status"] == "awaiting_visual_review"


def test_production_pipeline_rejects_scripts_without_research_sources(tmp_path):
    script = _script()
    script["sources"] = []
    with pytest.raises(ValueError, match="research source"):
        production_pipeline.produce_video_from_script(script, tmp_path)
    assert not (tmp_path / "finance-campus-video.mp4").exists()



def test_production_rejects_unapproved_or_insecure_research_sources(tmp_path):
    script = _script()
    script["sources"] = ["https://consumerfinance.gov.attacker.example/fake"]
    with pytest.raises(ValueError, match="unapproved research source"):
        production_pipeline.produce_video_from_script(script, tmp_path)
    assert not (tmp_path / "finance-campus-video.mp4").exists()


def test_production_rejects_plain_http_sources(tmp_path):
    script = _script()
    script["sources"] = ["http://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/"]
    with pytest.raises(ValueError, match="unapproved research source"):
        production_pipeline.produce_video_from_script(script, tmp_path)
