"""Fail-closed handoff from script generation to downstream production."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finance_campus.script_quality import ScriptQualityReport, validate_script


@dataclass
class ScriptPreparationResult:
    """Outcome of validating and storing a production-ready script package."""

    approved: bool
    output_path: str | None
    errors: list[str]


def prepare_script(
    candidate: Any,
    output_path: str | Path,
) -> ScriptPreparationResult:
    """Validate a generated candidate and atomically save it only when it passes.

    The function deliberately does not generate text or call an AI provider.
    A future generator must supply a candidate package to this trusted handoff.
    Invalid candidates never create or overwrite an approved output file.
    """
    report: ScriptQualityReport = validate_script(candidate)
    if not report.passed:
        return ScriptPreparationResult(False, None, report.errors)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    except OSError:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise

    return ScriptPreparationResult(True, str(destination), [])
