"""Discover finance education topic candidates from official publisher RSS feeds.

Feed headlines are only discovery signals. Every candidate must link to a page on
an allow-listed publisher, the article must be readable, and the topic remains
unapproved until its factual claims are independently checked.
"""
from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html import unescape
from typing import Any
from urllib.parse import urlparse

from finance_campus.research_pipeline import USER_AGENT, fetch_source


OFFICIAL_FEEDS: tuple[dict[str, str], ...] = (
    {
        "name": "CFPB newsroom",
        "url": "https://www.consumerfinance.gov/about-us/newsroom/feed/",
        "domain": "consumerfinance.gov",
        "geography": "United States; global educational relevance only",
    },
    {
        "name": "FTC consumer protection",
        "url": "https://www.ftc.gov/feeds/press-release-consumer-protection.xml",
        "domain": "ftc.gov",
        "geography": "United States; global educational relevance only",
    },
    {
        "name": "SEC investor alerts",
        "url": "https://www.sec.gov/rss/investor/alertsandbulletins.xml",
        "domain": "sec.gov",
        "geography": "United States; global educational relevance only",
    },
)

CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "Financial Scams and Fraud Prevention": ("fraud", "scam", "phishing", "identity theft", "deceptive"),
    "Debt and Loans": ("loan", "debt", "credit", "lending", "mortgage", "borrow"),
    "Banking and Financial Services": ("bank", "account", "payment", "deposit", "financial service"),
    "Investing Fundamentals": ("invest", "investor", "securities", "stock", "bond", "fund"),
    "Insurance and Risk Management": ("insurance", "insurer", "policyholder"),
    "Inflation and Purchasing Power": ("inflation", "prices", "cost of living", "purchasing power"),
    "Saving and Emergency Funds": ("saving", "savings", "emergency fund"),
    "Entrepreneurship and Business Finance": ("small business", "business finance", "entrepreneur", "cash flow"),
    "Financial Literacy": ("financial education", "financial literacy", "consumer finance", "money management"),
}
FINANCE_TERMS = tuple(term for terms in CATEGORY_TERMS.values() for term in terms)


def _tag_text(element: ET.Element, names: set[str]) -> str:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1].casefold() in names and child.text:
            return unescape(child.text).strip()
    return ""


def parse_feed(xml_text: str, *, limit: int = 60) -> list[dict[str, str]]:
    """Parse RSS 2.0 or Atom entries without third-party dependencies."""
    root = ET.fromstring(xml_text)
    entries = [
        node for node in root.iter()
        if node.tag.rsplit("}", 1)[-1].casefold() in {"item", "entry"}
    ]
    parsed: list[dict[str, str]] = []
    for entry in entries[:limit]:
        title = _tag_text(entry, {"title"})
        link = ""
        for node in entry.iter():
            if node.tag.rsplit("}", 1)[-1].casefold() == "link":
                link = node.attrib.get("href", "") or (node.text or "").strip()
                if link:
                    break
        summary = _tag_text(entry, {"description", "summary", "content"})
        published = _tag_text(entry, {"pubdate", "published", "updated", "date"})
        if title and link:
            parsed.append({
                "title": re.sub(r"\\s+", " ", title),
                "url": link,
                "summary": re.sub(r"\\s+", " ", summary)[:2500],
                "published": published,
            })
    return parsed


def fetch_feed(url: str, timeout: int = 15) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"Feed returned HTTP {response.status}: {url}")
        return response.read(1_500_000).decode("utf-8", errors="replace")


def _trusted_link(url: str, domain: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    return parsed.scheme == "https" and (host == domain or host.endswith("." + domain))


def _category(text: str) -> str | None:
    folded = text.casefold()
    for category, terms in CATEGORY_TERMS.items():
        if any(term in folded for term in terms):
            return category
    return None


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:72]


def discover_from_official_feeds(
    *,
    existing_topics: list[dict[str, Any]],
    target: int,
    timestamp: str | None = None,
    feed_fetcher=fetch_feed,
    article_fetcher=fetch_source,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    """Discover original topic candidates from fresh official RSS/Atom articles."""
    checked_at = timestamp or datetime.now(UTC).isoformat()
    known_titles = {
        re.sub(r"[^a-z0-9]+", " ", str(item.get("title", "")).casefold()).strip()
        for item in existing_topics
    }
    known_ids = {str(item.get("id")) for item in existing_topics}
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    feed_counts: dict[str, int] = {}

    for feed in OFFICIAL_FEEDS:
        try:
            entries = parse_feed(feed_fetcher(feed["url"]))
            feed_counts[feed["name"]] = len(entries)
        except (OSError, ValueError, ET.ParseError, TimeoutError, urllib.error.URLError) as exc:
            rejected.append({"source": feed["name"], "reason": f"Feed unavailable or invalid: {exc}"})
            continue

        for entry in entries:
            if len(candidates) >= target:
                break
            title = entry["title"].strip()
            normalized = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
            if len(title) < 18 or normalized in known_titles:
                continue
            combined = f"{title} {entry['summary']}"
            category = _category(combined)
            if not category or not any(term in combined.casefold() for term in FINANCE_TERMS):
                continue
            if not _trusted_link(entry["url"], feed["domain"]):
                rejected.append({"title": title, "reason": "Article link is outside the official publisher domain"})
                continue
            try:
                article = article_fetcher(entry["url"])
                article_text = str(article.get("text", "")).strip()
                if article.get("status") != 200 or len(article_text) < 350:
                    raise ValueError("Official article did not provide enough readable text")
                article_url = str(article.get("url") or entry["url"])
                if not _trusted_link(article_url, feed["domain"]):
                    raise ValueError("Article redirected outside the trusted publisher domain")
            except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:
                rejected.append({"title": title, "reason": str(exc)})
                continue

            topic_id = "TFC-" + hashlib.sha256(entry["url"].encode()).hexdigest()[:10].upper()
            if topic_id in known_ids or normalized in known_titles:
                continue
            snippet = re.sub(r"\\s+", " ", entry["summary"]).strip()
            topic = {
                "id": topic_id,
                "title": title if title.endswith("?") else f"What {title[0].lower() + title[1:]} means for your money",
                "category": category,
                "target_audience": ["global adults", "young adults", "households", "entrepreneurs"],
                "geographic_relevance": [feed["geography"]],
                "research_sources": [{
                    "url": article_url,
                    "publisher": feed["name"],
                    "domain": feed["domain"],
                    "http_status": 200,
                    "checked_at": checked_at,
                    "page_title": entry["title"],
                    "published_at": entry["published"],
                    "feed_summary": snippet,
                    "verification": "official_article_reachable_and_text_extracted",
                    "evidence_note": "Discovered from an official publisher feed. The article is readable; individual script claims still require claim-level evidence review.",
                }],
                "sources": [article_url],
                "research_status": "discovered_needs_claim_review",
                "research_checked_at": checked_at,
                "production_status": "not_started",
                "publication_status": "not_published",
                "editorial_brief": {
                    "problem": f"Viewers may not understand the financial issue raised by this official publication: {entry['title']}.",
                    "stakes": "Explain only consequences explicitly supported by the article and additional authoritative evidence; do not infer or exaggerate outcomes.",
                    "explanation": "Translate the publication into plain-language financial education, distinguish general principles from country-specific rules, and explain relevant limitations.",
                    "action": "Give viewers a practical, non-personalized learning step based on verified information and direct them to the original official source.",
                },
                "discovery_metadata": {
                    "method": "official_rss_atom",
                    "feed_name": feed["name"],
                    "feed_url": feed["url"],
                    "source_headline": entry["title"],
                    "source_summary": snippet,
                    "article_text_characters": len(article_text),
                    "candidate_only": True,
                },
                "topic_slug": _slug(title),
            }
            candidates.append(topic)
            known_ids.add(topic_id)
            known_titles.add(normalized)
        if len(candidates) >= target:
            break

    return candidates, rejected, feed_counts
