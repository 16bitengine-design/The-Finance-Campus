"""Turn an approved financial script into a visual whiteboard storyboard."""
from __future__ import annotations

import hashlib
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
    """Compose a distinct illustrated story beat for each part of the lesson."""
    _, _, _ = _visual_types(text, section)
    # A stable per-video signature varies composition and accent choices without
    # introducing randomness between retries of the same production.
    signature = hashlib.sha256(f"{title}|{section}|{text}".encode("utf-8")).hexdigest()
    variation = int(signature[:8], 16)
    shift_x = ((variation % 7) - 3) * width * .012
    shift_y = (((variation >> 4) % 5) - 2) * height * .009
    accent = ("navy", "green", "gold")[variation % 3]
    person = _element("person", width * .08 + shift_x, height * .19 + shift_y, width * .30, height * .43, accent, .15)
    paycheck = _element("money_note", width * .48, height * .20, width * .30, height * .17, "green", .75)
    wallet = _element("wallet", width * .58, height * .49, width * .29, height * .19, "navy", 1.55)
    jar = _element("savings_jar", width * .60, height * .38, width * .27, height * .31, "green", 1.75)
    coin = _element("coin", width * .43, height * .28, width * .09, height * .055, "gold", 1.15)
    house = _element("house", width * .58, height * .20, width * .31, height * .27, "navy", 1.1)
    expense = _element("money_note", width * .58, height * .54, width * .25, height * .13, "gold", 2.0)

    if section == "relatable_financial_problem":
        elements = [person, paycheck, {
            "type": "arrow", "x1": round(width*.39), "y1": round(height*.35),
            "x2": round(width*.53), "y2": round(height*.35), "color": "gold",
            "start_seconds": 1.0, "draw_seconds": .45,
        }, {
            "type": "arrow", "x1": round(width*.53), "y1": round(height*.48),
            "x2": round(width*.64), "y2": round(height*.55), "color": "green",
            "start_seconds": 1.3, "draw_seconds": .4,
        }, wallet, coin]
    elif section == "escalating_real_world_stakes":
        person["x"], person["y"] = round(width*.06), round(height*.27)
        person["width"], person["height"] = round(width*.24), round(height*.38)
        elements = [person, house, expense, {
            "type": "arrow", "x1": round(width*.70), "y1": round(height*.49),
            "x2": round(width*.48), "y2": round(height*.63), "color": "gold",
            "start_seconds": 2.4, "draw_seconds": .5,
        }, wallet]
    elif section == "clear_explanation_of_why_it_matters":
        person["x"], person["width"] = round(width*.05), round(width*.23)
        paycheck["x"], paycheck["y"] = round(width*.35), round(height*.22)
        jar["x"], jar["y"] = round(width*.67), round(height*.43)
        coin["x"], coin["y"] = round(width*.49), round(height*.30)
        coin["motion"] = {
            "from_x": round(width*.49), "from_y": round(height*.30),
            "to_x": round(width*.75), "to_y": round(height*.52),
            "start_seconds": 2.0, "end_seconds": 4.2,
        }
        elements = [person, paycheck, {
            "type": "arrow", "x1": round(width*.29), "y1": round(height*.39),
            "x2": round(width*.43), "y2": round(height*.39), "color": "green",
            "start_seconds": 1.35, "draw_seconds": .45,
        }, jar, coin]
    elif section == "hopeful_and_realistic_possibility":
        person["x"], person["y"] = round(width*.08), round(height*.24)
        person["width"], person["height"] = round(width*.25), round(height*.39)
        jar["x"], jar["y"] = round(width*.57), round(height*.38)
        jar["width"], jar["height"] = round(width*.31), round(height*.34)
        elements = [person, jar,
            _element("coin", width*.64, height*.29, width*.075, height*.045, "gold", 1.1),
            _element("coin", width*.75, height*.25, width*.075, height*.045, "gold", 1.8),
            {"type": "arrow", "x1": round(width*.38), "y1": round(height*.43),
             "x2": round(width*.56), "y2": round(height*.43), "color": "green",
             "start_seconds": 2.2, "draw_seconds": .5}]
    elif section == "practical_action_viewers_can_take":
        person["x"], person["y"] = round(width*.05), round(height*.25)
        person["width"], person["height"] = round(width*.24), round(height*.39)
        paycheck["x"], paycheck["y"] = round(width*.34), round(height*.18)
        jar["x"], jar["y"] = round(width*.66), round(height*.48)
        coin["x"], coin["y"] = round(width*.50), round(height*.34)
        coin["motion"] = {
            "from_x": round(width*.50), "from_y": round(height*.34),
            "to_x": round(width*.76), "to_y": round(height*.58),
            "start_seconds": 1.5, "end_seconds": 4.4,
        }
        elements = [person, paycheck, {
            "type": "arrow", "x1": round(width*.57), "y1": round(height*.39),
            "x2": round(width*.70), "y2": round(height*.48), "color": "gold",
            "start_seconds": 1.0, "draw_seconds": .5,
        }, jar, coin]
    else:
        person["x"], person["y"] = round(width*.12), round(height*.25)
        person["width"], person["height"] = round(width*.27), round(height*.42)
        jar["x"], jar["y"] = round(width*.58), round(height*.34)
        jar["width"], jar["height"] = round(width*.30), round(height*.37)
        elements = [person, jar,
            _element("coin", width*.65, height*.24, width*.08, height*.05, "gold", 1.0),
            _element("coin", width*.75, height*.21, width*.08, height*.05, "gold", 1.7),
            _element("coin", width*.70, height*.30, width*.08, height*.05, "gold", 2.35)]

    # The scene title is deliberately kept above the reserved caption area.
    elements.append({
        "type": "text", "x": round(width*.08), "y": round(height*.83),
        "text": title, "color": "navy", "start_seconds": 4.45, "draw_seconds": .2,
    })
    elements.sort(key=lambda item: float(item.get("start_seconds", 0)))
    # Apply the script-specific composition offset to the full illustration group.
    for item in elements:
        if "x" in item and item["type"] != "text":
            item["x"] = round(item["x"] + shift_x)
        if "y" in item and item["type"] != "text":
            item["y"] = round(item["y"] + shift_y)
        if isinstance(item.get("motion"), dict):
            for coordinate in ("from_x", "to_x"):
                item["motion"][coordinate] = round(item["motion"][coordinate] + shift_x)
            for coordinate in ("from_y", "to_y"):
                item["motion"][coordinate] = round(item["motion"][coordinate] + shift_y)
        if item["type"] in {"coin", "money_note", "savings_jar"}:
            item["color"] = accent
    elements.sort(key=lambda item: float(item.get("start_seconds", 0)))
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
            "visual_signature": hashlib.sha256(f"{script['title']}|{section}|{narration}".encode("utf-8")).hexdigest()[:16],
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
