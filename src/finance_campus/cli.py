"""Command-line checks for project configuration and editorial quality."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finance_campus.config import load_yaml, validate_branding, validate_disclaimer
from finance_campus.script_quality import validate_script


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument(
        "command",
        choices=("validate-config", "validate-script"),
        help="The validation task to run",
    )
    parser.add_argument(
        "script_path",
        nargs="?",
        help="JSON script package path (required for validate-script)",
    )
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

    if args.command == "validate-script":
        if not args.script_path:
            parser.error("validate-script requires a JSON script package path")
        try:
            with Path(args.script_path).open("r", encoding="utf-8") as handle:
                script = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL script: unable to read valid JSON ({exc})")
            return 1
        report = validate_script(script)
        if report.passed:
            print("PASS script: editorial quality requirements met")
            return 0
        for error in report.errors:
            print(f"FAIL script: {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
