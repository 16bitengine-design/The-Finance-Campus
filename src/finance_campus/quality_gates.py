"""Pre-publication checks. Publishing adapters must call these gates."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityReport:
    passed: bool
    errors: list[str] = field(default_factory=list)


def validate_video_package(
    *,
    sources: list[str],
    spoken_disclaimer_present: bool,
    on_screen_disclaimer_present: bool,
    description_disclaimer_present: bool,
    brand_validation_passed: bool,
    script_validation_passed: bool,
    audio_validation_passed: bool,
    video_validation_passed: bool,
) -> QualityReport:
    """Fail closed: any missing mandatory condition blocks publication."""
    errors: list[str] = []
    if not sources:
        errors.append("At least one research source is required")
    if not spoken_disclaimer_present:
        errors.append("Spoken disclaimer is missing")
    if not on_screen_disclaimer_present:
        errors.append("On-screen disclaimer is missing")
    if not description_disclaimer_present:
        errors.append("Description disclaimer is missing")
    if not brand_validation_passed:
        errors.append("Brand validation failed")
    if not script_validation_passed:
        errors.append("Script editorial validation failed")
    if not audio_validation_passed:
        errors.append("Audio validation failed")
    if not video_validation_passed:
        errors.append("Video validation failed")
    return QualityReport(passed=not errors, errors=errors)
