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
    signature = hashlib.sha256(f"{title}|{section}|{text}".encode()).hexdigest()
    variation = int(signature[:8], 16)
    shift_x = ((variation % 7) - 3) * width * .012
    shift_y = (((variation >> 4) % 5) - 2) * height * .009
    accent = ("navy", "green", "gold")[variation % 3]
    person = _element("person", width * .08 + shift_x, height * .19 + shift_y, width * .30, height * .43, accent, .15)
    character_direction = {
        "relatable_financial_problem": ("worried", "worried"),
        "escalating_real_world_stakes": ("overwhelmed", "overwhelmed"),
        "clear_explanation_of_why_it_matters": ("thinking", "calm"),
        "hopeful_and_realistic_possibility": ("reaching", "calm"),
        "practical_action_viewers_can_take": ("determined", "determined"),
        "empowering_close": ("celebrating", "calm"),
    }
    person["pose"], person["expression"] = character_direction.get(
        section, ("neutral", "calm"),
    )
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
        wallet["open_animation"] = {
            "start_seconds": 2.0,
            "end_seconds": 3.0,
            "easing": "ease_out",
        }
        cash = _element("money_note", width * .64, height * .445, width * .16, height * .09, "green", 2.55)
        cash["motion"] = {
            "from_x": round(width * .64), "from_y": round(height * .445),
            "to_x": round(width * .68), "to_y": round(height * .34),
            "start_seconds": 2.55, "end_seconds": 3.45,
            "easing": "ease_out",
        }
        elements.append(cash)
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

    # Add a topic-specific visual metaphor so different lessons do not reuse
    # the same wallet/coin composition.
    topic = text.casefold()
    motif = None
    if any(term in topic for term in ("scam", "fraud", "phishing", "fake investment")):
        motif = "phone"
    elif any(term in topic for term in ("insurance", "insured", "coverage", "premium", "claim")):
        motif = "shield"
    elif any(term in topic for term in ("inflation", "prices rise", "price increases", "purchasing power")):
        motif = "basket"
    elif any(term in topic for term in ("debt", "loan", "repayment", "borrow", "credit")):
        motif = "calendar"
    elif any(term in topic for term in ("invest", "stocks", "bonds", "etf", "portfolio", "compound")):
        motif = "chart"
    if motif:
        elements.append(_element(
            motif, width * .66, height * .075, width * .25, height * .16,
            "gold" if motif in {"phone", "basket"} else "green", 1.05,
        ))

    # Establish a readable physical setting instead of floating symbols.
    # The shared floor/table geometry anchors props and gives the character a
    # believable place to interact with the financial objects.
    environment = [
        {"type": "line", "x1": round(width*.045), "y1": round(height*.735),
         "x2": round(width*.955), "y2": round(height*.735), "color": "navy",
         "start_seconds": .05, "draw_seconds": .55},
        {"type": "line", "x1": round(width*.42), "y1": round(height*.69),
         "x2": round(width*.91), "y2": round(height*.69), "color": "navy",
         "start_seconds": .12, "draw_seconds": .35},
        {"type": "line", "x1": round(width*.46), "y1": round(height*.69),
         "x2": round(width*.46), "y2": round(height*.735), "color": "navy",
         "start_seconds": .42, "draw_seconds": .25},
        {"type": "line", "x1": round(width*.87), "y1": round(height*.69),
         "x2": round(width*.87), "y2": round(height*.735), "color": "navy",
         "start_seconds": .52, "draw_seconds": .25},
    ]
    if section == "escalating_real_world_stakes":
        # A household bill is shown as a document with a due marker, not
        # another unexplained floating rectangle.
        environment.extend([
            {"type": "rect", "x": round(width*.66), "y": round(height*.40),
             "width": round(width*.12), "height": round(height*.12), "color": "gold",
             "start_seconds": 1.35, "draw_seconds": .4},
            {"type": "line", "x1": round(width*.68), "y1": round(height*.445),
             "x2": round(width*.755), "y2": round(height*.445), "color": "navy",
             "start_seconds": 1.8, "draw_seconds": .2},
            {"type": "line", "x1": round(width*.68), "y1": round(height*.475),
             "x2": round(width*.735), "y2": round(height*.475), "color": "navy",
             "start_seconds": 2.0, "draw_seconds": .2},
        ])
    elif section in {"hopeful_and_realistic_possibility", "practical_action_viewers_can_take", "empowering_close"}:
        # A small, grounded savings station makes the goal feel tangible.
        environment.extend([
            {"type": "line", "x1": round(width*.58), "y1": round(height*.72),
             "x2": round(width*.84), "y2": round(height*.72), "color": "green",
             "start_seconds": 1.0, "draw_seconds": .3},
            {"type": "circle", "cx": round(width*.90), "cy": round(height*.66),
             "r": round(width*.025), "color": "gold",
             "start_seconds": 1.25, "draw_seconds": .35},
        ])
    elements.extend(environment)

    # Give the protagonist a specific physical relationship with the key prop.
    # Targets are expressed in storyboard canvas coordinates and are consumed by
    # the renderer when drawing the character's arm and hand.
    interaction_targets = {
        "relatable_financial_problem": ("receives_paycheck", width * .63, height * .285),
        "escalating_real_world_stakes": ("reaches_for_bill", width * .705, height * .605),
        "clear_explanation_of_why_it_matters": ("moves_money_to_savings", width * .825, height * .57),
        "hopeful_and_realistic_possibility": ("reaches_savings_jar", width * .725, height * .39),
        "practical_action_viewers_can_take": ("deposits_money", width * .815, height * .64),
        "empowering_close": ("protects_savings", width * .73, height * .48),
    }
    interaction, target_x, target_y = interaction_targets.get(
        section, ("neutral", width * .5, height * .5),
    )
    person["interaction"] = interaction
    person["interaction_target"] = {
        "x": round(target_x + shift_x),
        "y": round(target_y + shift_y),
    }
    person["interaction_animation"] = {
        "from_x": round(person["x"] + person["width"]),
        "from_y": round(person["y"] + person["height"] * .32),
        "start_seconds": 1.8,
        "end_seconds": 3.2,
        "easing": "ease_out",
    }
    if section in {"hopeful_and_realistic_possibility", "practical_action_viewers_can_take"}:
        walk_from_x = round(person["x"])
        person["motion"] = {
            "from_x": walk_from_x,
            "from_y": round(person["y"]),
            "to_x": round(walk_from_x + width * .075),
            "to_y": round(person["y"]),
            "start_seconds": .8,
            "end_seconds": 2.4,
            "easing": "ease_in_out",
        }
        person["walk_cycle"] = {
            "start_seconds": .8,
            "end_seconds": 2.4,
            "cycle_seconds": .52,
            "stride": .075,
        }

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
            "visual_signature": hashlib.sha256(f"{script['title']}|{section}|{narration}".encode()).hexdigest()[:16],
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
