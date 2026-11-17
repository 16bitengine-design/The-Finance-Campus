"""Command-line checks for project configuration."""
from __future__ import annotations

import argparse
import sys

from finance_campus.config import load_yaml, validate_branding, validate_disclaimer


def main() -> int:
    parser = argparse.ArgumentParser(description="The Finance Campus project tools")
    parser.add_argument("command", choices=("validate-config",))
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
