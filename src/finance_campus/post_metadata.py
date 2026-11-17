"""Platform-specific social metadata generation for every Finance Campus post.

Metadata is deterministic, original, and generated locally from the approved script.
It is a draft for review, not a claim about trending hashtags or guaranteed reach.
"""
from __future__ import annotations

import re

from finance_campus.disclaimers import append_description_disclaimer
from typing import Any


CATEGORY_TAGS = {
    "budgeting": ("#Budgeting", "#MoneyManagement", "#TheFinanceCampus"),
    "saving": ("#SavingMoney", "#EmergencyFund", "#TheFinanceCampus"),
    "debt": ("#DebtManagement", "#FinancialWellness", "#TheFinanceCampus"),
    "investing": ("#InvestingBasics", "#FinancialEducation", "#TheFinanceCampus"),
    "financial psychology": ("#MoneyMindset", "#FinancialHabits", "#TheFinanceCampus"),
    "money mindset": ("#MoneyMindset", "#SmartMoneyHabits", "#TheFinanceCampus"),
    "banking": ("#BankingBasics", "#MoneyEducation", "#TheFinanceCampus"),
    "wealth creation": ("#BuildingWealth", "#MoneyMindset", "#TheFinanceCampus"),
    "financial literacy": ("#FinancialLiteracy", "#MoneyLessons", "#TheFinanceCampus"),
}


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _slug_hashtag(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "#" + "".join(word[:1].upper() + word[1:] for word in words) if words else ""


def _keywords(title: str, category: str) -> list[str]:
    stop = {"about", "after", "before", "being", "every", "from", "have", "into",
            "that", "their", "there", "these", "this", "those", "what", "when",
            "where", "which", "while", "with", "your", "should", "could", "would"}
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", title.casefold())
    result: list[str] = []
    for token in [*tokens, category.casefold(), "money mindset", "financial education"]:
        cleaned = token.strip("'-")
        if cleaned and cleaned not in stop and cleaned not in result:
            result.append(cleaned)
    return result[:15]


def _topic_hashtags(title: str, category: str, limit: int) -> list[str]:
    mapped = CATEGORY_TAGS.get(category.casefold(), ())
    candidates = [*mapped, _slug_hashtag(title), "#MoneyMindset", "#FinancialEducation",
                  "#TheFinanceCampus"]
    result: list[str] = []
    for tag in candidates:
        if tag and tag.casefold() not in {item.casefold() for item in result}:
            result.append(tag)
        if len(result) == limit:
            break
    return result


def generate_post_metadata(
    script: dict[str, Any],
    disclaimer_config: dict[str, Any],
    *,
    video_format: str = "short",
) -> dict[str, Any]:
    """Create distinct platform copy, with the required disclaimer on each destination."""
    if video_format not in {"short", "long"}:
        raise ValueError("video_format must be short or long")
    title = _clean_text(script.get("title"))
    category = _clean_text(script.get("category")) or "Financial Literacy"
    if not title:
        raise ValueError("Post metadata requires a non-empty script title")

    base = _clean_text(script.get("description"))
    if not base:
        sections = script.get("sections", {})
        if isinstance(sections, dict):
            base = _clean_text(sections.get("clear_explanation_of_why_it_matters"))
    if not base:
        base = f"Explore the money lesson behind {title.casefold()}."

    keywords = _keywords(title, category)
    youtube_hashtags = _topic_hashtags(title, category, 3)
    tiktok_hashtags = _topic_hashtags(title, category, 5)
    youtube_body = (
        f"{base}\n\nIn this Finance Campus lesson, we explore {title.casefold()}, "
        "why it matters, and one practical step you can consider. "
        "Learn, apply, and grow.\n\n"
        "Subscribe to The Finance Campus for clear, practical money lessons.\n\n"
        + " ".join(youtube_hashtags)
    )
    tiktok_body = (
        f"{base}\n\nA money mindset lesson from The Finance Campus. "
        "Follow for practical ideas that help you think more clearly about money.\n\n"
        + " ".join(tiktok_hashtags)
    )
    youtube_description = append_description_disclaimer(youtube_body, disclaimer_config)
    tiktok_caption = append_description_disclaimer(tiktok_body, disclaimer_config)
    if len(youtube_description) > 5000:
        raise ValueError("Generated YouTube description exceeds the conservative 5,000-character limit")
    if video_format == "short" and len(tiktok_caption) > 2200:
        raise ValueError("Generated TikTok caption exceeds the conservative 2,200-character limit")

    platforms = {
        "youtube": {
            "description": youtube_description,
            "hashtags": youtube_hashtags,
            "search_tags": keywords,
            "character_count": len(youtube_description),
        }
    }
    if video_format == "short":
        platforms["tiktok"] = {
            "caption": tiktok_caption,
            "hashtags": tiktok_hashtags,
            "character_count": len(tiktok_caption),
        }
    return {
        "title": title,
        "category": category,
        "video_format": video_format,
        "platforms": platforms,
        "validation": {
            "platform_copy_is_distinct": video_format != "short" or youtube_description != tiktok_caption,
            "youtube_disclaimer_present": disclaimer_config["disclaimer"]["description"].casefold()
                in youtube_description.casefold(),
            "tiktok_disclaimer_present": (
                disclaimer_config["disclaimer"]["description"].casefold()
                in tiktok_caption.casefold()
                if video_format == "short"
                else None
            ),
            "hashtags_are_unique": (
                len({tag.casefold() for tag in youtube_hashtags}) == len(youtube_hashtags)
                and (
                    video_format != "short"
                    or len({tag.casefold() for tag in tiktok_hashtags}) == len(tiktok_hashtags)
                )
            ),
            "status": "generated_needs_editorial_review",
        },
    }
