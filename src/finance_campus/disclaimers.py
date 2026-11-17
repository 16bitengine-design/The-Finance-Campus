"""Canonical disclaimer text and video-description injection helpers."""
from __future__ import annotations

from typing import Any


def disclaimer_texts(config: dict[str, Any]) -> dict[str, str]:
    """Return the canonical spoken, on-screen, and description disclaimers."""
    data = config["disclaimer"]
    return {
        "spoken": str(data["spoken"]).strip(),
        "on_screen": str(data["on_screen"]).strip(),
        "description": str(data["description"]).strip(),
    }


def append_description_disclaimer(description: str, config: dict[str, Any]) -> str:
    """Append the canonical description disclaimer exactly once."""
    disclaimer = disclaimer_texts(config)["description"]
    if disclaimer.casefold() in description.casefold():
        return description
    base = description.rstrip()
    return f"{base}\n\n{disclaimer}" if base else disclaimer
