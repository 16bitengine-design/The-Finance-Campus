"""Command-line checks for project configuration and editorial quality."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finance_campus.config import load_yaml, validate_branding, validate_disclaimer
from finance_campus.script_pipeline import prepare_script
from finance_campus.script_quality import validate_script


def _read_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument(
        "command",
        choices=("validate-config", "validate-script", "prepare-script"),
        help="The validation or preparation task to run",
    )
    parser.add_argument("script_path", nargs="?", help="Input JSON script package")
    parser.add_argument("output_path", nargs="?", help="Approved output path for prepare-script")
    args = parser.parse_args()

    if args.command == "validate-config":
        checks = {
            "branding": validate_branding(load_yaml("config/branding.yaml")),
            "disclaimer": validate_disclaimer(load_yaml("config/disclaimer.yaml")),
        }
        failures = False
        for name, errors in checks.items():
            if errors:
                failures = True
                for error in errors:
                    print(f"FAIL {name}: {error}")
            else:
                print(f"PASS {name}")
        return 1 if failures else 0

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
