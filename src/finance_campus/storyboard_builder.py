"""Turn an approved financial script into a visual whiteboard storyboard."""
from __future__ import annotations

import re
from typing import Any

from finance_campus.disclaimers import disclaimer_texts

SECTION_ORDER = (
    ("relatable_financial_problem", "The money problem"),
    ("escalating_real_world_stakes", "When the pressure grows"),
    ("clear_explanation_of_why_it_matters", "Understand what is happening"),
    ("hopeful_and_realistic_possibility", "A better way is possible"),
    ("practical_action_viewers_can_take", "Your next practical step"),
    ("empowering_close", "Small steps matter"),
)


def _visual_types(text: str, section: str) -> tuple[str, str, str]:
    words = set(re.findall(r"[a-z]+", text.casefold()))
    if words & {"debt", "borrow", "borrowing", "loan", "repayment", "credit"}:
        return "wallet", "money_note", "arrow"
    if words & {"save", "savings", "buffer", "emergency", "fund"}:
        return "person", "savings_jar", "coin"
    if words & {"inflation", "prices", "price", "cost", "costs", "expensive"}:
        return "money_note", "coin", "arrow"
    if words & {"income", "payday", "salary", "earn", "earning", "wages"}:
        return "person", "money_note", "wallet"
    if words & {"invest", "investment", "compound", "interest", "returns"}:
        return "coin", "bank", "arrow"
    if section == "relatable_financial_problem":
        return "person", "wallet", "coin"
    if section == "escalating_real_world_stakes":
        return "house", "money_note", "arrow"
    if section == "clear_explanation_of_why_it_matters":
        return "bank", "money_note", "arrow"
    if section == "hopeful_and_realistic_possibility":
        return "person", "savings_jar", "coin"
    if section == "practical_action_viewers_can_take":
        return "wallet", "savings_jar", "arrow"
    return "person", "savings_jar", "coin"


def _element(kind: str, x: float, y: float, width: float, height: float, color: str, start: float) -> dict[str, Any]:
    return {
        "type": kind,
        "x": round(x),
        "y": round(y),
        "width": round(width),
        "height": round(height),
        "color": color,
        "start_seconds": start,
        "draw_seconds": 0.85,
    }


def _scene_elements(text: str, section: str, title: str, width: int, height: int) -> list[dict[str, Any]]:
    first, second, third = _visual_types(text, section)
    # The connecting arrow is drawn explicitly between the two main objects.
    # Keep the lower supporting illustration a drawable object, not a second arrow.
    if third == "arrow":
        third = "coin"
    left_x, right_x = width * 0.08, width * 0.64
    top_y = height * 0.22
    obj_w, obj_h = width * 0.27, height * 0.35
    elements: list[dict[str, Any]] = [
        _element(first, left_x, top_y, obj_w, obj_h, "navy", 0.2),
        {
            "type": "arrow",
            "x1": round(width * 0.40),
            "y1": round(height * 0.43),
            "x2": round(width * 0.59),
            "y2": round(height * 0.43),
            "color": "gold",
            "start_seconds": 0.9,
            "draw_seconds": 0.55,
        },
        _element(second, right_x, top_y, obj_w, obj_h, "green", 1.5),
        _element(third, width * 0.37, height * 0.53, width * 0.22, height * 0.19, "gold", 2.4),
        {
            "type": "text",
            "x": round(width * 0.08),
            "y": round(height * 0.84),
            "text": title,
            "color": "navy",
            "start_seconds": 3.0,
            "draw_seconds": 0.2,
        },
    ]
    return elements


def build_storyboard(
    script: dict[str, Any],
    *,
    video_format: str = "short",
    disclaimer_config: dict[str, Any],
) -> dict[str, Any]:
    """Build six illustrated teaching scenes plus a spoken/visible disclaimer scene.

    This is a deterministic visual mapper, not a generative AI illustrator. It
    chooses appropriate hand-drawn financial objects from each approved section.
    """
    if video_format not in {"short", "long"}:
        raise ValueError("video_format must be 'short' or 'long'")
    width, height = (1000, 1778) if video_format == "short" else (1778, 1000)
    scenes: list[dict[str, Any]] = []

    for index, (section, title) in enumerate(SECTION_ORDER):
        narration = str(script["sections"][section]).strip()
        scenes.append({
            "id": section.replace("_", "-"),
            "narration": narration,
            "duration_seconds": 5.0,
            "elements": _scene_elements(narration, section, title, width, height),
        })

    disclaimer = disclaimer_texts(disclaimer_config)
    on_screen = disclaimer["on_screen"]
    # Break the canonical wording into readable, separately drawn lines.
    lines = [
        "Educational content only —",
        "not personalized financial, investment,",
        "tax or legal advice.",
        "Consult a qualified professional.",
    ]
    disclaimer_elements: list[dict[str, Any]] = [
        _element("bank", width * 0.37, height * 0.08, width * 0.26, height * 0.28, "navy", 0.2),
    ]
    for line_index, line in enumerate(lines):
        disclaimer_elements.append({
            "type": "text",
            "x": round(width * 0.08),
            "y": round(height * (0.55 + line_index * 0.075)),
            "text": line,
            "color": "navy",
            "start_seconds": 0.4 + line_index * 0.15,
            "draw_seconds": 0.2,
        })
    scenes.append({
        "id": "financial-education-disclaimer",
        "narration": disclaimer["spoken"],
        "duration_seconds": 6.0,
        "minimum_duration_seconds": max(6.0, float(disclaimer_config["disclaimer"].get("minimum_on_screen_seconds", 6))),
        "elements": disclaimer_elements,
    })
    return {
        "title": str(script["title"]).strip(),
        "canvas": {"width": width, "height": height},
        "scenes": scenes,
        "on_screen_disclaimer_text": on_screen,
        "spoken_disclaimer_text": disclaimer["spoken"],
    }
