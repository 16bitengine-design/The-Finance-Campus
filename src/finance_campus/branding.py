"""Brand tokens and metadata checks shared by all visual generators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BrandTokens:
    name: str
    tagline: str
    slogan: str
    navy: str
    green: str
    gold: str
    white: str


def tokens_from_config(config: dict[str, Any]) -> BrandTokens:
    brand = config["brand"]
    palette = brand["palette"]
    return BrandTokens(
        name=brand["name"],
        tagline=brand["tagline"],
        slogan=brand["slogan"],
        navy=palette["navy"],
        green=palette["green"],
        gold=palette["gold"],
        white=palette["white"],
    )


def validate_asset_metadata(
    *,
    asset_type: str,
    visual_description: str,
    brand_name: str,
    required_brand_name: str = "The Finance Campus",
) -> list[str]:
    """Check declared visual metadata for prohibited themes and brand identity.

    This is a deterministic first-pass gate, not computer vision. Rendered-image
    inspection will be added as a separate production stage.
    """
    errors: list[str] = []
    if brand_name.strip().casefold() != required_brand_name.casefold():
        errors.append("Asset brand name does not match the official brand")
    description = visual_description.casefold()
    prohibited_terms = (
        "graduation cap", "graduation gown", "diploma", "graduation ceremony",
        "graduation certificate", "mortarboard",
    )
    found = [term for term in prohibited_terms if term in description]
    if found:
        errors.append("Prohibited graduation imagery referenced: " + ", ".join(found))
    if not asset_type.strip():
        errors.append("Asset type is required")
    if not visual_description.strip():
        errors.append("Visual description is required")
    return errors
