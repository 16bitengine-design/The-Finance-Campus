"""Load and validate central project configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from a project-relative or absolute path."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    with candidate.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected a YAML mapping in {candidate}")
    return data


def validate_branding(config: dict[str, Any]) -> list[str]:
    """Return configuration errors; an empty list means the brand config is valid."""
    errors: list[str] = []
    brand = config.get("brand")
    if not isinstance(brand, dict):
        return ["Missing 'brand' mapping"]
    for key in ("name", "tagline", "slogan"):
        if not str(brand.get(key, "")).strip():
            errors.append(f"Missing brand.{key}")
    palette = brand.get("palette", {})
    for colour in ("navy", "green", "gold", "white"):
        value = str(palette.get(colour, ""))
        if len(value) != 7 or not value.startswith("#"):
            errors.append(f"Invalid or missing brand.palette.{colour}")
    identity = brand.get("visual_identity", {})
    if "whiteboard" not in str(identity.get("primary_style", "")).lower():
        errors.append("Primary visual style must include whiteboard illustration")
    prohibited = {str(x).lower() for x in brand.get("prohibited_visuals", [])}
    if "graduation caps" not in prohibited:
        errors.append("Graduation caps must remain explicitly prohibited")
    if brand.get("enforcement", {}).get("reject_on_failure") is not True:
        errors.append("Brand enforcement must reject failures")
    return errors


def validate_disclaimer(config: dict[str, Any]) -> list[str]:
    """Ensure all three mandatory disclaimer variants are configured."""
    disclaimer = config.get("disclaimer", {})
    errors = []
    for key in ("spoken", "on_screen", "description"):
        if not str(disclaimer.get(key, "")).strip():
            errors.append(f"Missing disclaimer.{key}")
    if disclaimer.get("required_in_every_video") is not True:
        errors.append("Disclaimers must be required in every video")
    if int(disclaimer.get("minimum_on_screen_seconds", 0)) < 6:
        errors.append("On-screen disclaimer duration must be at least 6 seconds")
    return errors


def validate_settings(config: dict[str, Any]) -> list[str]:
    """Reject unsafe or misleading operating settings until integrations are validated."""
    errors: list[str] = []
    project = config.get("project", {})
    if project.get("timezone") != "Africa/Kampala":
        errors.append("Project timezone must remain Africa/Kampala")
    audio = config.get("audio", {})
    if audio.get("provider") != "kokoro" or audio.get("allow_provider_replacement") is not False:
        errors.append("Kokoro must remain the only approved narration provider")
    cost = config.get("cost_policy", {})
    for key in ("allow_paid_services", "allow_paid_api_keys", "allow_paid_assets",
                "allow_paid_hosting", "allow_paid_compute"):
        if cost.get(key) is not False:
            errors.append(f"Zero-cost policy requires cost_policy.{key} to be false")
    production = config.get("production", {})
    platforms = config.get("platforms", {})
    if production.get("publishing_enabled") is not False:
        errors.append("Publishing must remain disabled until platform adapters and release tests pass")
    for platform in ("youtube", "tiktok"):
        if platforms.get(platform, {}).get("enabled") is not False:
            errors.append(f"{platform} publishing must remain disabled until its adapter is validated")
    automation = config.get("automation", {})
    if automation.get("auto_publish_after_all_gates_pass") is not False:
        errors.append("Automatic publishing cannot be enabled before platform release validation")
    if automation.get("auto_publication_verification") is not False:
        errors.append("Automatic publication verification is not implemented yet")
    if automation.get("require_routine_human_approval") is not True:
        errors.append("Human visual review must remain required until semantic visual QC is validated")
    return errors
