"""Command-line checks and rendering tools for The Finance Campus."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finance_campus.blender_backend import render_blender_project
from finance_campus.timeline_renderer import render_2d_timeline
from finance_campus.config import (
    load_yaml,
    validate_branding,
    validate_disclaimer,
    validate_settings,
)
from finance_campus.layered_animation import iter_layered_frames, validate_layered_scene
from finance_campus.narration import synthesize_storyboard
from finance_campus.production_pipeline import produce_video_from_script
from finance_campus.research_pipeline import refresh_topics
from finance_campus.script_generator import generate_from_library, generate_pending_scripts
from finance_campus.script_pipeline import prepare_script
from finance_campus.script_quality import validate_script
from finance_campus.storyboard import render_storyboard, validate_storyboard
from finance_campus.video_renderer import render_video


def _read_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument("command", choices=("validate-config", "validate-script", "prepare-script", "refresh-topics", "generate-script", "generate-pending-scripts", "validate-storyboard", "render-storyboard", "render-video", "synthesize-narration", "produce-video", "validate-layered-scene", "render-layered-scene", "render-2d-timeline", "render-3d-project"))
    parser.add_argument("script_path", nargs="?", help="Input JSON script or storyboard")
    parser.add_argument("output_path", nargs="?", help="Output path for approved data, SVGs, or MP4")
    parser.add_argument("--format", choices=("short", "long"), default="short", dest="video_format")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--target", type=int, default=20, help="Number of new topics to attempt")
    parser.add_argument("--topic-id", help="Topic ID to use for generate-script")
    parser.add_argument("--duration", choices=("short", "long"), default="short")
    parser.add_argument("--draw-fps", type=int, default=24)
    parser.add_argument("--audio", help="Optional narration audio file to mux into the MP4")
    parser.add_argument("--captions", help="Optional SRT captions file to burn into the video")
    parser.add_argument("--transition-seconds", type=float, default=0.25)
    parser.add_argument("--voice", choices=("af_heart", "am_michael", "bf_emma", "bm_george"), default="af_heart")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--scene-tail-seconds", type=float, default=0.35)
    parser.add_argument("--asset-root", help="Root directory containing transparent PNG scene layers")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--blender", default="blender", help="Blender executable path")
    args = parser.parse_args()
    if args.command in {"validate-layered-scene", "render-layered-scene"}:
        if not args.script_path:
            parser.error(f"{args.command} requires a layered scene JSON")
        try:
            scene = _read_json(args.script_path)
            errors = validate_layered_scene(scene)
            if errors:
                for error in errors:
                    print(f"FAIL layered scene: {error}")
                return 1
            if args.command == "validate-layered-scene":
                print("PASS layered scene: layers, keyframes and reveal directions are valid")
                return 0
            if not args.output_path or not args.asset_root:
                parser.error("render-layered-scene requires output path and --asset-root")
            output = Path(args.output_path)
            output.mkdir(parents=True, exist_ok=True)
            count = 0
            for count, frame in enumerate(iter_layered_frames(scene, args.asset_root, fps=args.fps), start=1):
                frame.save(output / f"frame_{count - 1:06d}.png")
            print(f"RENDERED {count} layered animation frames to {output}")
            return 0
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL layered scene rendering: {exc}")
            return 1
    if args.command in {"render-2d-timeline", "render-3d-project"}:
        if not args.script_path or not args.output_path:
            parser.error(f"{args.command} requires an input manifest/project and output MP4")
        try:
            if args.command == "render-2d-timeline":
                result = render_2d_timeline(args.script_path, args.output_path)
            else:
                result = render_blender_project(
                    args.script_path, args.output_path, width=args.width,
                    height=args.height, fps=args.fps, blender=args.blender,
                )
            print(json.dumps(result, indent=2))
            return 0
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL animation rendering: {exc}")
            return 1
    if args.command == "refresh-topics":
        if not args.script_path:
            parser.error("refresh-topics requires a topic-library JSON path")
        try:
            report = refresh_topics(args.script_path, target=args.target)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["target_met"] else 2
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"FAIL topic research: {exc}")
            return 1
    if args.command == "generate-script":
        if not args.script_path or not args.output_path or not args.topic_id:
            parser.error("generate-script requires topic-library path, output path, and --topic-id")
        try:
            report = generate_from_library(args.script_path, args.topic_id, args.output_path, duration=args.duration)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"FAIL script generation: {exc}")
            return 1
    if args.command == "generate-pending-scripts":
        if not args.script_path or not args.output_path:
            parser.error("generate-pending-scripts requires topic-library path and output directory")
        try:
            report = generate_pending_scripts(args.script_path, args.output_path, duration=args.duration)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"FAIL batch script generation: {exc}")
            return 1
    if args.command == "produce-video":
        if not args.script_path or not args.output_path:
            parser.error("produce-video requires an approved script JSON and an output directory")
        try:
            script = _read_json(args.script_path)
            result = produce_video_from_script(
                script, args.output_path, video_format=args.video_format,
                voice=args.voice, speed=args.speed, device=args.device,
                fps=args.fps, draw_fps=args.draw_fps,
                transition_seconds=args.transition_seconds,
                scene_tail_seconds=args.scene_tail_seconds,
            )
            print(json.dumps(result, indent=2))
            return 0
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL production: {exc}")
            return 1
    if args.command == "validate-config":
        checks = {"branding": validate_branding(load_yaml("config/branding.yaml")), "disclaimer": validate_disclaimer(load_yaml("config/disclaimer.yaml")), "settings": validate_settings(load_yaml("config/settings.yaml"))}
        failed = False
        for name, errors in checks.items():
            if errors:
                failed = True
                for error in errors:
                    print(f"FAIL {name}: {error}")
            else:
                print(f"PASS {name}")
        return 1 if failed else 0
    if args.command in {"validate-script", "prepare-script"}:
        if not args.script_path:
            parser.error(f"{args.command} requires an input JSON script package")
        if args.command == "prepare-script" and not args.output_path:
            parser.error("prepare-script requires an approved output path")
        try:
            script = _read_json(args.script_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL script: unable to read valid JSON ({exc})")
            return 1
        if args.command == "validate-script":
            report = validate_script(script)
            if report.passed:
                print("PASS script: editorial quality requirements met")
                return 0
            for error in report.errors:
                print(f"FAIL script: {error}")
            return 1
        result = prepare_script(script, args.output_path)
        if result.approved:
            print(f"PASS script: approved package written to {result.output_path}")
            return 0
        for error in result.errors:
            print(f"FAIL script: {error}")
        print("REJECTED: no approved package was written")
        return 1
    if args.command in {"validate-storyboard", "render-storyboard", "render-video", "synthesize-narration"}:
        if not args.script_path:
            parser.error(f"{args.command} requires an input storyboard JSON")
        if args.command != "validate-storyboard" and not args.output_path:
            parser.error(f"{args.command} requires an output path")
        try:
            storyboard = _read_json(args.script_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL storyboard: unable to read valid JSON ({exc})")
            return 1
        errors = validate_storyboard(storyboard)
        if errors:
            for error in errors:
                print(f"FAIL storyboard: {error}")
            return 1
        if args.command == "validate-storyboard":
            print("PASS storyboard: narration and actual illustrations found in every scene")
            return 0
        try:
            if args.command == "synthesize-narration":
                result = synthesize_storyboard(
                    storyboard, args.output_path, voice=args.voice, speed=args.speed,
                    device=args.device, transition_seconds=args.transition_seconds,
                    scene_tail_seconds=args.scene_tail_seconds, draw_fps=args.draw_fps,
                )
                print(json.dumps(result, indent=2))
                return 0
            if args.command == "render-storyboard":
                for output in render_storyboard(storyboard, args.output_path):
                    print(f"RENDERED SVG: {output}")
            else:
                output = render_video(storyboard, args.output_path, video_format=args.video_format, fps=args.fps, draw_fps=args.draw_fps, audio_path=args.audio, captions_path=args.captions, transition_seconds=args.transition_seconds)
                print(f"RENDERED MP4: {output} ({args.video_format}, {args.fps} fps)")
            return 0
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"FAIL rendering: {exc}")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
