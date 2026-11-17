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


def test_refresh_uses_new_topics_without_repeating_previous_batch(tmp_path):
    path = tmp_path / "topics.json"
    first = refresh_topics(path, target=20, fetcher=fake_fetch)
    second = refresh_topics(path, target=20, fetcher=fake_fetch)
    third = refresh_topics(path, target=20, fetcher=fake_fetch)
    assert first["added_count"] == 20
    assert second["added_count"] == 20
    assert {item["id"] for item in first["added"]}.isdisjoint(
        {item["id"] for item in second["added"]}
    )
    assert third["added_count"] == 0




def test_refresh_adds_evergreen_mindset_topics_not_news_headlines(tmp_path):
    result = refresh_topics(tmp_path / "topics.json", target=20, fetcher=fake_fetch)
    assert result["added_count"] == 20
    assert result["discovery_method"] == "evergreen_money_mindset_blueprints"
    assert result["news_feed_topics_added"] == 0
    assert result["mindset_topics_added"] == 20
    assert all(item["content_focus"] == "money_mindset_and_behaviour" for item in result["added"])
    assert all(
        item["discovery_metadata"]["method"] == "evergreen_money_mindset_blueprint"
        for item in result["added"]
    )
    assert any("looking rich" in item["title"].casefold() for item in result["added"])
    assert any("comparison" in item["title"].casefold() for item in result["added"])
