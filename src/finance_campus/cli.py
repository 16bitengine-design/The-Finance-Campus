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


def _read_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument("command", choices=("validate-config", "validate-script", "prepare-script", "validate-storyboard", "render-storyboard", "render-video"))
    parser.add_argument("script_path", nargs="?", help="Input JSON script or storyboard")
    parser.add_argument("output_path", nargs="?", help="Output path for approved data, SVGs, or MP4")
    parser.add_argument("--format", choices=("short", "long"), default="short", dest="video_format")
    parser.add_argument("--fps", type=int, default=30)
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
    if args.command in {"validate-storyboard", "render-storyboard", "render-video"}:
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
            if args.command == "render-storyboard":
                for output in render_storyboard(storyboard, args.output_path):
                    print(f"RENDERED SVG: {output}")
            else:
                output = render_video(storyboard, args.output_path, video_format=args.video_format, fps=args.fps)
                print(f"RENDERED MP4: {output} ({args.video_format}, {args.fps} fps)")
            return 0
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"FAIL rendering: {exc}")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
