"""End-to-end production from an approved script to a narrated illustrated MP4."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from finance_campus.caption_qc import validate_srt
from finance_campus.config import load_yaml, validate_branding, validate_disclaimer
from finance_campus.disclaimers import append_description_disclaimer, disclaimer_texts
from finance_campus.final_video_qc import validate_final_video
from finance_campus.narration import synthesize_storyboard
from finance_campus.quality_gates import validate_video_package
from finance_campus.script_pipeline import prepare_script
from finance_campus.script_quality import validate_script
from finance_campus.storyboard import validate_storyboard
from finance_campus.storyboard_builder import build_storyboard
from finance_campus.video_renderer import render_video
from finance_campus.visual_review import create_visual_review_sheet


def _source_urls(script: dict[str, Any]) -> list[str]:
    values = list(script.get("sources", [])) if isinstance(script.get("sources", []), list) else []
    for claim in script.get("claims", []):
        if isinstance(claim, dict) and isinstance(claim.get("sources"), list):
            values.extend(claim["sources"])
    unique: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        parsed = urlparse(value.strip())
        if parsed.scheme in {"http", "https"} and parsed.netloc and value not in unique:
            unique.append(value)
    return unique


def _probe_video(path: Path, *, video_format: str) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required for production media validation")
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-show_entries",
            "stream=codec_type,width,height,sample_rate,channels:format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe rejected the rendered video: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    expected = (1080, 1920) if video_format == "short" else (1920, 1080)
    if not video or (video.get("width"), video.get("height")) != expected:
        raise RuntimeError(f"Rendered video dimensions are not {expected[0]}x{expected[1]}")
    if not audio or int(audio.get("sample_rate", 0)) <= 0 or int(audio.get("channels", 0)) < 1:
        raise RuntimeError("Rendered video is missing a valid narration audio stream")
    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError("Rendered video has no valid duration")
    return {
        "width": video["width"],
        "height": video["height"],
        "audio_sample_rate": int(audio["sample_rate"]),
        "audio_channels": int(audio["channels"]),
        "duration_seconds": round(duration, 3),
    }


def produce_video_from_script(
    script: dict[str, Any],
    output_dir: str | Path,
    *,
    video_format: str = "short",
    voice: str = "af_heart",
    speed: float = 1.0,
    device: str = "auto",
    fps: int = 30,
    draw_fps: int = 24,
    transition_seconds: float = 0.25,
    scene_tail_seconds: float = 0.35,
    pipeline_factory: Any = None,
) -> dict[str, Any]:
    """Validate, storyboard, narrate, render and quality-gate one approved script.

    Publishing is intentionally outside this function and remains disabled until
    separate platform authorization and end-to-end publication checks are approved.
    """
    report = validate_script(script)
    if not report.passed:
        raise ValueError("Script rejected: " + "; ".join(report.errors))
    sources = _source_urls(script)
    if not sources:
        raise ValueError("Production rejected: at least one reputable research source URL is required")

    branding_config = load_yaml("config/branding.yaml")
    disclaimer_config = load_yaml("config/disclaimer.yaml")
    brand_errors = validate_branding(branding_config)
    disclaimer_errors = validate_disclaimer(disclaimer_config)
    if brand_errors or disclaimer_errors:
        raise ValueError("Project configuration rejected: " + "; ".join(brand_errors + disclaimer_errors))

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    approved_script_path = destination / "approved_script.json"
    preparation = prepare_script(script, approved_script_path)
    if not preparation.approved:
        raise ValueError("Script approval failed: " + "; ".join(preparation.errors))

    storyboard = build_storyboard(
        script, video_format=video_format, disclaimer_config=disclaimer_config,
    )
    storyboard_errors = validate_storyboard(storyboard)
    if storyboard_errors:
        raise ValueError("Generated storyboard rejected: " + "; ".join(storyboard_errors))
    storyboard_path = destination / "storyboard.json"
    storyboard_path.write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    narration = synthesize_storyboard(
        storyboard,
        destination,
        voice=voice,
        speed=speed,
        device=device,
        transition_seconds=transition_seconds,
        scene_tail_seconds=scene_tail_seconds,
        draw_fps=draw_fps,
        pipeline_factory=pipeline_factory,
    )
    timed_storyboard = json.loads(Path(narration["storyboard_path"]).read_text(encoding="utf-8"))
    video_path = render_video(
        timed_storyboard,
        destination / "finance-campus-video.mp4",
        video_format=video_format,
        fps=fps,
        draw_fps=draw_fps,
        audio_path=narration["audio_path"],
        captions_path=narration["captions_path"],
        transition_seconds=transition_seconds,
    )
    media = _probe_video(video_path, video_format=video_format)
    final_video_report = validate_final_video(
        video_path, video_format=video_format, expected_fps=fps,
    )
    visual_review_report = create_visual_review_sheet(
        video_path, destination / "visual-review-contact-sheet.jpg",
    )
    narration_duration = float(narration["duration_seconds"])
    timed_scenes = timed_storyboard["scenes"]
    expected_speech_seconds = sum(
        float(scene["narration_audio_seconds"]) for scene in timed_scenes
    )
    caption_report = validate_srt(
        narration["captions_path"],
        audio_duration_seconds=narration_duration,
        expected_speech_seconds=expected_speech_seconds,
    )
    duration_tolerance = max(0.15, 2 / fps)
    duration_alignment_passed = abs(media["duration_seconds"] - narration_duration) <= duration_tolerance
    if not duration_alignment_passed:
        raise RuntimeError(
            "Rendered video duration does not align with Kokoro narration: "
            f"video={media['duration_seconds']}s, audio={narration_duration}s"
        )

    disclaimer = disclaimer_texts(disclaimer_config)
    all_spoken = " ".join(scene["narration"] for scene in storyboard["scenes"]).casefold()
    spoken_ok = disclaimer["spoken"].casefold() in all_spoken
    visible_lines = " ".join(
        str(element.get("text", ""))
        for scene in storyboard["scenes"]
        for element in scene["elements"]
        if element.get("type") == "text"
    ).casefold()
    visible_ok = all(
        phrase.casefold() in visible_lines
        for phrase in (
            "Educational content only",
            "not personalized financial, investment",
            "tax or legal advice",
            "Consult a qualified professional",
        )
    )
    description = append_description_disclaimer(
        str(script.get("description", "")).strip(), disclaimer_config,
    )
    description_path = destination / "description.txt"
    description_path.write_text(description + "\n", encoding="utf-8")
    description_ok = disclaimer["description"].casefold() in description.casefold()

    quality = validate_video_package(
        sources=sources,
        spoken_disclaimer_present=spoken_ok,
        on_screen_disclaimer_present=visible_ok,
        description_disclaimer_present=description_ok,
        brand_validation_passed=not brand_errors,
        script_validation_passed=report.passed,
        audio_validation_passed=Path(narration["audio_path"]).is_file() and narration["duration_seconds"] > 0,
        video_validation_passed=(
            video_path.is_file() and media["duration_seconds"] > 0
            and final_video_report["passed"]
        ),
    )
    manifest = {
        "title": script["title"],
        "status": "awaiting_visual_review" if quality.passed else "rejected",
        "technical_quality_approved": quality.passed,
        "human_visual_review_required": True,
        "stages": {
            "script_validated": True,
            "script_approved": True,
            "storyboard_generated": True,
            "kokoro_narration_generated": True,
            "captions_generated": True,
            "captions_validated": caption_report["passed"],
            "caption_cue_count": caption_report["cue_count"],
            "caption_speech_coverage_ratio": caption_report["speech_coverage_ratio"],
            "video_rendered": True,
            "media_streams_verified": True,
            "final_video_qc_passed": final_video_report["passed"],
            "visual_review_sheet_generated": True,
            "human_visual_review_required": True,
            "human_visual_review_passed": False,
            "audio_video_duration_aligned": duration_alignment_passed,
            "quality_gate_passed": quality.passed,
            "uploaded": False,
            "publicly_accessible": False,
        },
        "voice": voice,
        "video_format": video_format,
        "sources": sources,
        "narration": narration,
        "captions": caption_report,
        "media": media,
        "final_video_qc": final_video_report,
        "visual_review": visual_review_report,
        "quality_errors": quality.errors,
        "artifacts": {
            "approved_script": str(approved_script_path),
            "storyboard": str(storyboard_path),
            "timed_storyboard": narration["storyboard_path"],
            "audio": narration["audio_path"],
            "captions": narration["captions_path"],
            "video": str(video_path),
            "description": str(description_path),
            "visual_review_contact_sheet": visual_review_report["path"],
        },
    }
    manifest_path = destination / "production-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not quality.passed:
        raise RuntimeError("Rendered video rejected by quality gates: " + "; ".join(quality.errors))
    return manifest
