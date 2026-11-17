"""Command-line checks and rendering tools for The Finance Campus."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finance_campus.config import load_yaml, validate_branding, validate_disclaimer
from finance_campus.script_pipeline import prepare_script
from finance_campus.script_quality import validate_script
from finance_campus.storyboard import render_storyboard, validate_storyboard
from finance_campus.video_renderer import render_video
from finance_campus.narration import synthesize_storyboard


def _read_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument("command", choices=("validate-config", "validate-script", "prepare-script", "validate-storyboard", "render-storyboard", "render-video", "synthesize-narration"))
    parser.add_argument("script_path", nargs="?", help="Input JSON script or storyboard")
    parser.add_argument("output_path", nargs="?", help="Output path for approved data, SVGs, or MP4")
    parser.add_argument("--format", choices=("short", "long"), default="short", dest="video_format")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--draw-fps", type=int, default=24)
    parser.add_argument("--audio", help="Optional narration audio file to mux into the MP4")
    parser.add_argument("--captions", help="Optional SRT captions file to burn into the video")
    parser.add_argument("--transition-seconds", type=float, default=0.25)
    parser.add_argument("--voice", choices=("af_heart", "am_michael", "bf_emma", "bm_george"), default="af_heart")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--scene-tail-seconds", type=float, default=0.35)
    args = parser.parse_args()
    if args.command == "validate-config":
        checks = {"branding": validate_branding(load_yaml("config/branding.yaml")), "disclaimer": validate_disclaimer(load_yaml("config/disclaimer.yaml"))}
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
            if args.command == "synthesize-narration":\n                result = synthesize_storyboard(\n                    storyboard, args.output_path, voice=args.voice, speed=args.speed,\n                    device=args.device, transition_seconds=args.transition_seconds,\n                    scene_tail_seconds=args.scene_tail_seconds, draw_fps=args.draw_fps,\n                )\n                print(json.dumps(result, indent=2))\n                return 0\n            if args.command == "render-storyboard":
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
