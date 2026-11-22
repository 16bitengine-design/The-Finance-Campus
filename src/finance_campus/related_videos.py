"""Match scripts to previously verified public lessons for cross-video learning."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


GENERIC_CONCEPTS = {
    "financial", "finance", "money", "investing", "investment", "risk",
    "decisions", "goals", "performance", "education", "basics",
}


def _tokens(values: list[str]) -> set[str]:
    tokens = set()
    for value in values:
        if not isinstance(value, str):
            continue
        for token in re.findall(r"[a-z0-9]+", value.casefold()):
            if len(token) > 2:
                normalized = token[:-1] if token.endswith("s") and len(token) > 4 else token
                if normalized not in GENERIC_CONCEPTS:
                    tokens.add(normalized)
    return tokens


def _is_youtube_watch_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").casefold()
    return (
        parsed.scheme == "https"
        and (host == "youtube.com" or host == "www.youtube.com" or host == "youtu.be")
        and (parsed.path.startswith("/watch") or host == "youtu.be")
    )


def load_published_video_library(path: str | Path) -> list[dict[str, Any]]:
    """Load only records explicitly marked as publicly accessible and verified."""
    source = Path(path)
    if not source.exists():
        return []
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Published-video library must be a JSON array")
    accepted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        video_id = item.get("video_id")
        title = item.get("title")
        concepts = item.get("concepts")
        url = item.get("url")
        if (
            item.get("status") != "publicly_accessible_verified"
            or not isinstance(video_id, str) or not video_id.strip()
            or video_id in seen
            or not isinstance(title, str) or not title.strip()
            or not isinstance(concepts, list) or not concepts
            or not all(isinstance(tag, str) and tag.strip() for tag in concepts)
            or not _is_youtube_watch_url(url)
        ):
            continue
        seen.add(video_id)
        accepted.append(item)
    return accepted


def find_related_video(
    script: dict[str, Any],
    library_path: str | Path = "production/published-video-library.json",
) -> dict[str, Any] | None:
    """Find a previously published lesson using explicit concept tags, not loose guesses."""
    concepts = script.get("related_concepts", [])
    if not isinstance(concepts, list) or not concepts:
        return None
    wanted = _tokens(concepts)
    if not wanted:
        return None
    candidates = []
    for item in load_published_video_library(library_path):
        overlap = wanted & _tokens(item["concepts"])
        if overlap:
            candidates.append((len(overlap), item["title"].casefold(), item, sorted(overlap)))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], row[1]))
    _, _, item, matched = candidates[0]
    return {
        "video_id": item["video_id"],
        "title": item["title"],
        "url": item["url"],
        "matched_concepts": matched,
        "status": "publicly_accessible_verified",
        "spoken_cta": (
            f"Want to understand {item['title'].casefold()} better? "
            f"Watch our dedicated lesson, {item['title']}. "
            "You'll find the link in the description."
        ),
    }


def attach_related_video(
    script: dict[str, Any],
    library_path: str | Path = "production/published-video-library.json",
) -> dict[str, Any] | None:
    """Attach one verified related lesson and add its natural spoken CTA once."""
    related = find_related_video(script, library_path)
    if related is None:
        script.pop("related_video", None)
        return None
    script["related_video"] = related
    sections = script.get("sections")
    if isinstance(sections, dict):
        close = sections.get("empowering_close")
        if isinstance(close, str) and related["spoken_cta"] not in close:
            sections["empowering_close"] = f"{close} {related['spoken_cta']}"
    return related
