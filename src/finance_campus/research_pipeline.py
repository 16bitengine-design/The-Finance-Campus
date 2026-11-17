"""Zero-cost, evergreen money-mindset topic discovery with authoritative source checks.

Topics are selected from human money behaviours and beliefs. Official educational
sources are checked for relevance; candidates remain unapproved pending claim review.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import urllib.error
import urllib.request

from finance_campus.mindset_topics import MINDSET_TOPIC_BLUEPRINTS
from finance_campus.topics import add_topic, load_topics, save_topics


USER_AGENT = "TheFinanceCampusResearchBot/1.0 (educational research; contact via GitHub repository)"
SOURCE_CATALOG: dict[str, dict[str, str]] = {
    "cfpb_emergency": {
        "url": "https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/",
        "publisher": "Consumer Financial Protection Bureau",
        "domain": "consumerfinance.gov",
    },
    "cfpb_toolkit": {
        "url": "https://www.consumerfinance.gov/consumer-tools/educator-tools/your-money-your-goals/toolkit/",
        "publisher": "Consumer Financial Protection Bureau",
        "domain": "consumerfinance.gov",
    },
    "bou_literacy": {
        "url": "https://bou.or.ug/financial_literacy",
        "publisher": "Bank of Uganda",
        "domain": "bou.or.ug",
    },
    "bou_strategy": {
        "url": "https://www.bou.or.ug/uploads/Strategy_for_Financial_in_Uganda_2026_2031_Detailed_Version_signed_Oct_2_2026_bffc2d40d2.pdf",
        "publisher": "Bank of Uganda",
        "domain": "bou.or.ug",
    },
    "sec_investor": {
        "url": "https://www.investor.gov/introduction-investing",
        "publisher": "U.S. Securities and Exchange Commission",
        "domain": "investor.gov",
    },
}

# Topic definitions are deliberately explicit: each one has a real learning outcome,
# a geographic label, a source, and the key phrases expected on that source page.
class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if not self.in_script and data.strip():
            self.parts.append(data.strip())


def fetch_source(url: str, timeout: int = 15) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(2_000_000)
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200:
            raise ValueError(f"Source returned HTTP {response.status}: {url}")
        if "pdf" in content_type.casefold() or url.casefold().endswith(".pdf"):
            # PDFs are accepted as reachable official sources, but text extraction is
            # deliberately not claimed here; PDF evidence needs a separate parser/review.
            return {"url": url, "final_url": response.geturl(), "status": response.status, "content_type": content_type, "text": ""}
        parser = _TextExtractor()
        parser.feed(body.decode("utf-8", errors="replace"))
        text = re.sub(r"\s+", " ", " ".join(parser.parts))
        if len(text) < 200:
            raise ValueError(f"Source page returned too little readable text: {url}")
        return {"url": url, "final_url": response.geturl(), "status": response.status, "content_type": content_type, "text": text[:50000]}


def _default_fetcher(url: str) -> dict[str, Any]:
    return fetch_source(url)


def refresh_topics(
    library_path: str | Path,
    *,
    target: int = 20,
    fetcher: Callable[[str], dict[str, Any]] = _default_fetcher,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Add up to target unused topics whose official source pages are reachable."""
    if target < 1:
        raise ValueError("target must be at least 1")
    topics = load_topics(library_path)
    known = {str(item.get("id")) for item in topics}
    timestamp = (now or datetime.now(UTC)).isoformat()
    cache: dict[str, dict[str, Any]] = {}
    added: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    # Topic discovery is deliberately evergreen and mindset-first. News feeds are
    # not used to set the editorial agenda; official sources only validate principles.
    for blueprint in MINDSET_TOPIC_BLUEPRINTS:
        if len(added) >= target:
            break
        topic_id = "TFC-" + hashlib.sha1(blueprint["slug"].encode()).hexdigest()[:10].upper()
        if topic_id in known:
            continue
        source_key = blueprint["source"]
        source_meta = SOURCE_CATALOG[source_key]
        try:
            if source_key not in cache:
                cache[source_key] = fetcher(source_meta["url"])
            source_result = cache[source_key]
            if source_result.get("status") != 200:
                raise ValueError("Source did not return HTTP 200")
            page_text = str(source_result.get("text", "")).casefold()
            if page_text:
                matched = [word for word in blueprint["keywords"] if word.casefold() in page_text]
                if len(matched) < min(1, len(blueprint["keywords"])):
                    raise ValueError("Source page did not contain the topic's expected evidence keywords")
            elif not source_meta["url"].endswith(".pdf"):
                raise ValueError("Source page has no extracted text for relevance checking")
            source_record = {
                "url": source_meta["url"],
                "publisher": source_meta["publisher"],
                "domain": source_meta["domain"],
                "http_status": 200,
                "checked_at": timestamp,
                "page_title": source_result.get("title", ""),
                "verification": ("reachable_pdf_needs_text_review" if not page_text and source_meta["url"].casefold().endswith(".pdf") else "reachable_and_keyword_checked"),
                "evidence_note": "Official source page was reachable and contained at least one mapped topic keyword; claim-level support still requires editorial review.",
            }
        except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:  # Fail closed.
            rejected.append({"title": blueprint["title"], "reason": str(exc)})
            continue

        topic = {
            "id": topic_id,
            "title": blueprint["title"],
            "category": blueprint["category"],
            "target_audience": ["global adults", "young adults", "households", "entrepreneurs"],
            "geographic_relevance": blueprint["geo"],
            "research_sources": [source_record],
            "sources": [source_meta["url"]],
            "research_status": ("source_reachable_needs_manual_review" if not page_text and source_meta["url"].casefold().endswith(".pdf") else "source_checked_needs_claim_review"),
            "research_checked_at": timestamp,
            "production_status": "not_started",
            "publication_status": "not_published",
            "editorial_brief": {
                "problem": blueprint["problem"],
                "stakes": blueprint["stakes"],
                "explanation": blueprint["explanation"],
                "action": blueprint["action"],
            },
            "topic_slug": blueprint["slug"],
            "discovery_metadata": {"method": "evergreen_money_mindset_blueprint", "candidate_only": True},
        }
        if add_topic(topics, topic):
            added.append(topic)
            known.add(topic_id)

    save_topics(library_path, topics)
    return {
        "target": target,
        "added_count": len(added),
        "library_count": len(topics),
        "added": added,
        "rejected": rejected,
        "discovery_method": "evergreen_money_mindset_blueprints",
        "news_feed_topics_added": 0,
        "mindset_topics_added": len(added),
        "target_met": len(added) >= target,
        "saved_to": str(library_path),
        "research_limitations": "Topics are selected from an evergreen money-mindset library. Official source pages are checked for reachability and mapped relevance keywords; this does not prove claim-level support. Every candidate requires editorial review.",
    }


def main_refresh(library_path: str, target: int = 20) -> int:
    report = refresh_topics(library_path, target=target)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["target_met"] else 2
