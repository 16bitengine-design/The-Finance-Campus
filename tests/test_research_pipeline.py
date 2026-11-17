from datetime import UTC, datetime

from finance_campus.research_pipeline import refresh_topics


def fake_fetch(url):
    return {"status": 200, "title": "Official financial education guide", "text": "emergency savings cash income bills debt loan interest credit digital financial safety investing risk retirement old age budget spending goals account financial products services"}


def test_refresh_adds_unique_researched_topics(tmp_path):
    path = tmp_path / "topics.json"
    result = refresh_topics(
        path, target=5, fetcher=fake_fetch,
        now=datetime(2026, 11, 17, tzinfo=UTC),
    )
    assert result["added_count"] == 5
    assert result["target_met"] is True
    assert len(result["added"]) == 5
    assert all(item["research_status"] == "source_checked_needs_claim_review" for item in result["added"])


def test_refresh_skips_unreachable_sources_and_does_not_claim_target(tmp_path):
    def failed(_url):
        raise OSError("offline")
    result = refresh_topics(tmp_path / "topics.json", target=3, fetcher=failed)
    assert result["added_count"] == 0
    assert result["target_met"] is False
    assert result["rejected"]


def test_refresh_is_idempotent(tmp_path):
    path = tmp_path / "topics.json"
    first = refresh_topics(path, target=20, fetcher=fake_fetch)
    second = refresh_topics(path, target=20, fetcher=fake_fetch)
    assert first["added_count"] == 20
    assert second["added_count"] == 0



def test_refresh_persists_discovered_feed_topics_before_curated_fallback(tmp_path, monkeypatch):
    discovered_topic = {
        "id": "TFC-FEED000001",
        "title": "How consumer investment fraud works",
        "category": "Financial Scams and Fraud Prevention",
        "target_audience": ["global adults"],
        "geographic_relevance": ["global"],
        "research_sources": [{"url": "https://www.sec.gov/example", "publisher": "SEC"}],
        "sources": ["https://www.sec.gov/example"],
        "research_status": "discovered_needs_claim_review",
        "production_status": "not_started",
        "publication_status": "not_published",
        "editorial_brief": {
            "problem": "A financial issue needs explanation.",
            "stakes": "Only evidence-backed risks should be described.",
            "explanation": "Explain the issue in plain language.",
            "action": "Check official sources.",
        },
        "discovery_metadata": {"method": "official_rss_atom"},
    }

    def fake_discover(**kwargs):
        assert kwargs["target"] == 1
        return [discovered_topic], [], {"SEC investor alerts": 1}

    monkeypatch.setattr(
        "finance_campus.research_pipeline.discover_from_official_feeds",
        fake_discover,
    )
    path = tmp_path / "topics.json"
    result = refresh_topics(path, target=1)
    assert result["added_count"] == 1
    assert result["discovered_topic_count"] == 1
    assert result["curated_fallback_topic_count"] == 0
    assert result["added"][0]["research_status"] == "discovered_needs_claim_review"
