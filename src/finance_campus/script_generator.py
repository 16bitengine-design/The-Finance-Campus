"""Deterministic script drafting from researched topic briefs.

No paid API or external model is called. Generated drafts are candidates only:
source support and editorial accuracy must pass validation before production.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from finance_campus.topics import load_topics


def _safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def generate_script(topic: dict[str, Any], *, duration: str = "short") -> dict[str, Any]:
    """Generate a complete structured draft from a researched topic's editorial brief."""
    if duration not in {"short", "long"}:
        raise ValueError("duration must be 'short' or 'long'")
    brief = topic.get("editorial_brief")
    if not isinstance(brief, dict):
        raise TypeError("Topic has no editorial_brief; research and approve its brief first")
    required = ("problem", "stakes", "explanation", "action")
    if any(not isinstance(brief.get(key), str) or not brief[key].strip() for key in required):
        raise ValueError("Topic editorial brief is incomplete")
    source_records = topic.get("research_sources", [])
    if not isinstance(source_records, list) or not source_records:
        raise ValueError("Topic has no checked research source record")
    if not all(item.get("verification") == "reachable_and_keyword_checked" for item in source_records):
        raise ValueError("Topic source has not passed the source reachability and relevance check")

    problem = brief["problem"]
    stakes = brief["stakes"]
    explanation = brief["explanation"]
    action = brief["action"]
    if duration == "short":
        sections = {
            "relatable_financial_problem": problem,
            "escalating_real_world_stakes": stakes,
            "clear_explanation_of_why_it_matters": explanation,
            "hopeful_and_realistic_possibility": "You do not need to solve the whole problem today. A clear first step, repeated consistently and adjusted to your circumstances, can improve the decisions available to you.",
            "practical_action_viewers_can_take": action,
            "empowering_close": "Your circumstances may be difficult, but understanding the next decision gives you a place to begin. Learn, apply, and grow.",
        }
        target_seconds = [45, 90]
    else:
        sections = {
            "relatable_financial_problem": problem + " Many people face this challenge while balancing essential costs, family responsibilities and uncertain income.",
            "escalating_real_world_stakes": stakes + " If the pattern continues, it can affect other goals and reduce the room available to handle the next setback.",
            "clear_explanation_of_why_it_matters": explanation + " The important distinction is between what is known, what depends on personal circumstances and what needs to be checked before acting.",
            "hopeful_and_realistic_possibility": "There may be practical ways to improve the situation gradually. Progress does not require a perfect income or a dramatic overnight change; it starts with an honest picture of the numbers and a manageable decision.",
            "practical_action_viewers_can_take": action + " Review the result, adjust it to your actual income and obligations, and seek qualified help where the decision is complex.",
            "empowering_close": "The goal is not to judge where you are today. It is to make the next money decision with better information and a realistic plan. Learn, apply, and grow.",
        }
        target_seconds = [300, 600]

    return {
        "id": f"{topic.get('id', 'TFC-UNASSIGNED')}-{duration.upper()}",
        "title": topic["title"],
        "category": topic["category"],
        "geographic_relevance": topic.get("geographic_relevance", ["global"]),
        "target_audience": topic.get("target_audience", []),
        "format": duration,
        "target_duration_seconds": target_seconds,
        "sections": sections,
        "sources": [item["url"] for item in source_records],
        "source_records": source_records,
        "claims": [
            {
                "text": explanation,
                "sources": [item["url"] for item in source_records],
                "verification_status": "source_linked_needs_claim_level_review",
            }
        ],
        "hypothetical_examples": [],
        "description": (
            f"Learn about {topic['title'].casefold()} with The Finance Campus. "
            "Educational content only; not personalized financial, investment, tax or legal advice. "
            "Consult a qualified professional about your circumstances."
        ),
        "script_generation": {
            "method": "deterministic_editorial_template",
            "human_or_claim_level_review_required": True,
            "approved_for_production": False,
        },
    }


def generate_from_library(
    library_path: str | Path,
    topic_id: str,
    output_path: str | Path,
    *,
    duration: str = "short",
) -> dict[str, Any]:
    topics = load_topics(library_path)
    topic = next((item for item in topics if item.get("id") == topic_id), None)
    if topic is None:
        raise ValueError(f"Topic ID not found in library: {topic_id}")
    script = generate_script(topic, duration=duration)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return {"script": script, "saved_to": str(destination), "status": "candidate_needs_review"}

def generate_pending_scripts(
    library_path: str | Path,
    output_dir: str | Path,
    *,
    duration: str = "short",
) -> dict[str, Any]:
    """Draft candidates for eligible topics, skipping existing files and unreviewed PDFs."""
    topics = load_topics(library_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    skipped: list[dict[str, str]] = []
    for topic in topics:
        topic_id = str(topic.get("id", ""))
        if not topic_id:
            skipped.append({"topic_id": "", "reason": "missing topic ID"})
            continue
        output = destination / f"{_safe_slug(topic_id)}-{duration}.json"
        if output.exists():
            continue
        try:
            generate_from_library(library_path, topic_id, output, duration=duration)
            generated.append(str(output))
        except ValueError as exc:
            skipped.append({"topic_id": topic_id, "reason": str(exc)})
    return {
        "generated_count": len(generated),
        "generated": generated,
        "skipped": skipped,
        "status": "candidate_only_no_production_or_publishing",
    }
