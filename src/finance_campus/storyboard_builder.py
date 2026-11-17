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


VISUAL_PATTERNS = (
    (("compound", "compounding", "interest on interest"), ("coin", "bank", "savings_jar"), "Repeated growth can build on earlier growth"),
    (("inflation", "purchasing power", "prices rise", "price increases"), ("money_note", "coin", "wallet"), "Rising prices reduce what the same money can buy"),
    (("repayment", "debt", "borrow", "borrowing", "loan", "credit"), ("wallet", "money_note", "house"), "Borrowed money creates a repayment obligation"),
    (("emergency fund", "emergency savings", "unexpected bill", "unexpected expense", "rainy day"), ("house", "wallet", "savings_jar"), "A reserve can absorb an unexpected cost"),
    (("budget", "spending plan", "allocate", "expenses"), ("wallet", "money_note", "savings_jar"), "Income is divided between needs and goals"),
    (("income", "payday", "salary", "wages", "earnings"), ("person", "money_note", "wallet"), "Earnings flow into the household budget"),
    (("invest", "investment", "stocks", "bonds", "etf", "portfolio"), ("person", "bank", "coin"), "Investing puts money into assets that carry risk"),
    (("insurance", "cover", "premium", "claim", "risk"), ("house", "bank", "wallet"), "Protection helps manage specified financial risks"),
    (("scam", "fraud", "phishing", "fake investment"), ("person", "wallet", "bank"), "A deceptive request can put money at risk"),
    (("save", "savings", "buffer", "fund", "deposit"), ("person", "savings_jar", "coin"), "Regular deposits build a financial buffer"),
)


def _visual_types(text: str, section: str) -> tuple[tuple[str, str, str], str, list[str]]:
    normalized = re.sub(r"[^a-z0-9 ]+", " ", text.casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for phrases, objects, relationship in VISUAL_PATTERNS:
        matched = [phrase for phrase in phrases if phrase in normalized]
        if matched:
            return objects, relationship, matched
    defaults = {
        "relatable_financial_problem": (("person", "wallet", "coin"), "A household faces a money decision"),
        "escalating_real_world_stakes": (("house", "wallet", "money_note"), "Financial pressure affects everyday needs"),
        "clear_explanation_of_why_it_matters": (("bank", "money_note", "wallet"), "A financial mechanism links choices to outcomes"),
        "hopeful_and_realistic_possibility": (("person", "savings_jar", "coin"), "A manageable action can improve resilience"),
        "practical_action_viewers_can_take": (("wallet", "savings_jar", "coin"), "A practical step moves money toward a goal"),
        "empowering_close": (("person", "savings_jar", "coin"), "Consistent small actions can build progress"),
    }
    objects, relationship = defaults.get(section, (("person", "wallet", "coin"), "A financial choice has consequences"))
    return objects, relationship, []


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
    (first, second, third), _, _ = _visual_types(text, section)
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
        {
            "type": "arrow",
            "x1": round(width * 0.78),
            "y1": round(height * 0.59),
            "x2": round(width * 0.52),
            "y2": round(height * 0.66),
            "color": "green",
            "start_seconds": 2.35,
            "draw_seconds": 0.55,
        },
        _element(third, width * 0.37, height * 0.68, width * 0.22, height * 0.13, "gold", 2.95),
        {
            "type": "text",
            "x": round(width * 0.08),
            "y": round(height * 0.91),
            "text": title,
            "color": "navy",
            "start_seconds": 3.7,
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
        (visual_objects, visual_relationship, matched_terms) = _visual_types(narration, section)
        scenes.append({
            "id": section.replace("_", "-"),
            "narration": narration,
            "duration_seconds": 5.0,
            "visual_intent": visual_relationship,
            "visual_objects": list(visual_objects),
            "matched_visual_terms": matched_terms,
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
    normalized_lines = " ".join(lines).casefold()
    normalized_required = " ".join(on_screen.split()).casefold()
    if normalized_required not in normalized_lines:
        raise ValueError("On-screen disclaimer configuration does not match the visible disclaimer layout")
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
