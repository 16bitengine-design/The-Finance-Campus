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
    inspiration = topic.get("inspiration")
    inspiration_line = ""
    if inspiration is not None:
        if not isinstance(inspiration, dict):
            raise ValueError("inspiration must be a structured, source-verified record")
        required_inspiration = ("kind", "author", "work", "source_url", "text")
        if any(not isinstance(inspiration.get(key), str) or not inspiration[key].strip() for key in required_inspiration):
            raise ValueError("inspiration requires kind, author, work, source_url and text")
        source_url = inspiration["source_url"].strip()
        if not source_url.startswith(("https://", "http://")):
            raise ValueError("inspiration source_url must be HTTP(S)")
        if inspiration.get("verification") != "author_and_original_work_verified":
            raise ValueError("inspiration author and original work must be verified")
        if inspiration["kind"] == "paraphrase":
            if inspiration.get("original_wording_reused") is True:
                raise ValueError("paraphrased inspiration must use independently written wording")
            inspiration_line = (
                f" A useful idea discussed by {inspiration['author']} in "
                f"{inspiration['work']} is this: {inspiration['text']}"
            )
        elif inspiration["kind"] == "direct_quote":
            if inspiration.get("rights_basis") not in {"public_domain", "permission_granted", "compatible_license"}:
                raise ValueError("direct quotation requires verified public-domain status, permission or a compatible licence")
            if inspiration.get("rights_verified") is not True:
                raise ValueError("direct quotation rights must be verified for the intended use and territory")
            if len(inspiration["text"].split()) > 15:
                raise ValueError("direct quotation exceeds the project's 15-word editorial limit")
            inspiration_line = (
                f" As {inspiration['author']} wrote in {inspiration['work']}: "
                f"“{inspiration['text']}”"
            )
        else:
            raise ValueError("inspiration kind must be paraphrase or direct_quote")
    if duration == "short":
        sections = {
            "relatable_financial_problem": f"Have you ever found yourself in this situation? {problem}",
            "escalating_real_world_stakes": f"Here is the part people often miss: {stakes}",
            "clear_explanation_of_why_it_matters": f"Here is the money lesson: {explanation}{inspiration_line}",
            "hopeful_and_realistic_possibility": "This pattern does not have to define your future. You may not control every circumstance, but you can learn to recognise the pattern and make a more deliberate next decision.",
            "practical_action_viewers_can_take": f"Try this: {action}",
            "empowering_close": "Do not measure your progress by appearances or someone else's timeline. Make the next decision with intention. Learn, apply, and grow.",
        }
        target_seconds = [45, 90]
    else:
        sections = {
            "relatable_financial_problem": f"Start with an honest question: have you ever recognised this pattern in your own life? {problem} This can happen to people with different incomes and responsibilities.",
            "escalating_real_world_stakes": f"The problem is not always obvious at first. {stakes} Over time, the pattern can influence confidence, choices and the options available when life changes.",
            "clear_explanation_of_why_it_matters": f"The key idea is simple: {explanation} The point is not to judge anyone. It is to understand the behaviour and see where a different choice may help.",
            "hopeful_and_realistic_possibility": "Change does not require a perfect income, perfect discipline or an overnight transformation. It can begin with noticing one trigger, setting one boundary or repeating one manageable habit. Progress should fit real circumstances.",
            "practical_action_viewers_can_take": f"Here is a practical place to begin: {action} Review what happens, adjust the approach to your circumstances and seek qualified help when a decision is complex.",
            "empowering_close": "Your current financial situation is not your identity. You can learn, question old habits and make the next decision more deliberately. Learn, apply, and grow.",
        }
        target_seconds = [300, 600]

    spoken_text = " ".join(sections.values())
    spoken_word_count = len(re.findall(r"\\b[\\w’'-]+\\b", spoken_text))
    estimated_duration_seconds = round(spoken_word_count / 145 * 60)
    duration_fit = (
        "under_target" if estimated_duration_seconds < target_seconds[0]
        else "over_target" if estimated_duration_seconds > target_seconds[1]
        else "within_target"
    )

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
        "inspiration": inspiration,
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
            "spoken_word_count": spoken_word_count,
            "estimated_duration_seconds": estimated_duration_seconds,
            "duration_fit": duration_fit,
            "words_per_minute_assumption": 145,
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
