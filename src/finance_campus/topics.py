"""Persistent JSON topic-library utilities with duplicate protection."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def normalize_title(title: str) -> str:
    """Normalize a topic title for conservative duplicate detection."""
    return re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()


def load_topics(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError("Topic library must contain a JSON array")
    return data


def add_topic(topics: list[dict[str, Any]], topic: dict[str, Any]) -> bool:
    """Add a sourced topic if its ID and normalized title are both new."""
    required = ("id", "title", "category", "geographic_relevance", "sources")
    missing = [key for key in required if not topic.get(key)]
    if missing:
        raise ValueError(f"Topic is missing required fields: {', '.join(missing)}")
    if not isinstance(topic["sources"], list) or not topic["sources"]:
        raise ValueError("Every topic must include at least one source")
    new_title = normalize_title(str(topic["title"]))
    for existing in topics:
        if existing.get("id") == topic["id"]:
            return False
        if normalize_title(str(existing.get("title", ""))) == new_title:
            return False
    topics.append(topic)
    return True


def save_topics(path: str | Path, topics: list[dict[str, Any]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = file_path.with_suffix(file_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(topics, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(file_path)
