from datetime import UTC, datetime

from finance_campus.research_pipeline import refresh_topics


def fake_fetch(url):
    return {"status": 200, "final_url": url, "title": "Official financial education guide", "text": "emergency savings cash income bills debt loan interest credit digital financial safety investing risk retirement old age budget spending goals account financial products services control freedom security values habits planning decisions familiarity performance trading panic manias momentum diversification fees research information questions progress choices literacy wellbeing business education expenses"}


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
    assert all(
        len(item["research_sources"][0]["matched_keywords"])
        >= item["research_sources"][0]["keyword_match_threshold"]
        for item in result["added"]
    )


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
    fourth = refresh_topics(path, target=20, fetcher=fake_fetch)
    fifth = refresh_topics(path, target=20, fetcher=fake_fetch)
    assert first["added_count"] == 20
    assert second["added_count"] == 20
    assert {item["id"] for item in first["added"]}.isdisjoint(
        {item["id"] for item in second["added"]}
    )
    assert third["added_count"] == 20
    assert fourth["added_count"] == 6
    assert fifth["added_count"] == 0




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


def test_inspiration_blueprints_are_carried_into_topic_records(tmp_path):
    result = refresh_topics(tmp_path / "topics.json", target=66, fetcher=fake_fetch)
    inspired = {
        item["topic_slug"]: item["inspiration"]
        for item in result["added"]
        if item.get("inspiration")
    }
    assert "pay-yourself-first" in inspired
    assert inspired["pay-yourself-first"]["author"] == "George S. Clason"
    assert "every-purchase-costs-time" in inspired
    assert inspired["every-purchase-costs-time"]["author"] == "Vicki Robin and Joe Dominguez"
    assert "know-when-to-walk-away" in inspired
    assert "judge-the-decision-not-only-the-result" in inspired
    assert "luck-is-not-a-repeatable-money-plan" in inspired
    assert all(
        item["inspiration"]["kind"] == "paraphrase"
        and item["inspiration"]["source_url"].startswith("https://")
        and item["inspiration"]["verification"] == "author_and_original_work_verified"
        and item["inspiration"]["original_wording_reused"] is False
        for item in result["added"] if item.get("inspiration")
    )
    assert all(
        item["inspiration"]["use"] == "paraphrased_idea_no_direct_quote"
        for item in result["added"]
        if item.get("inspiration")
    )



def test_catalogue_has_enough_distinct_topics_for_three_full_weekly_batches():
    from finance_campus.mindset_topics import MINDSET_TOPIC_BLUEPRINTS

    slugs = [item["slug"] for item in MINDSET_TOPIC_BLUEPRINTS]
    titles = [item["title"].casefold() for item in MINDSET_TOPIC_BLUEPRINTS]
    assert len(slugs) == 66
    assert len(slugs) == len(set(slugs))
    assert len(titles) == len(set(titles))


def test_new_topic_sources_are_mapped_to_authoritative_educational_sources(tmp_path):
    result = refresh_topics(tmp_path / "topics.json", target=66, fetcher=fake_fetch)
    added = {item["topic_slug"]: item for item in result["added"]}
    expected_urls = {
        "money-needs-a-regular-check-in": "https://www.consumerfinance.gov/consumer-tools/financial-well-being/about/",
        "annual-expenses-are-not-surprises": "https://www.fdic.gov/consumer-resource-center/money-smart-adults",
        "familiar-investment-is-not-automatically-safe": "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-72",
        "routine-beats-waiting-for-motivation": "https://www.consumerfinance.gov/consumer-tools/educator-tools/youth-financial-education/learn/financial-habits-norms/",
    }
    for slug, expected_url in expected_urls.items():
        item = added[slug]
        assert item["research_sources"][0]["url"] == expected_url
        assert item["research_sources"][0]["publisher"] in {
            "Consumer Financial Protection Bureau",
            "Federal Deposit Insurance Corporation",
            "U.S. Securities and Exchange Commission",
        }
        assert item["research_status"] == "source_checked_needs_claim_review"



def test_refresh_rejects_redirects_outside_approved_publisher_domain(tmp_path):
    def redirected(url):
        return {
            "status": 200,
            "final_url": "https://investor.gov.example-attacker.test/fake",
            "title": "Copied financial education page",
            "text": "financial literacy emergency savings budget investing risk habits planning decisions",
        }

    result = refresh_topics(tmp_path / "topics.json", target=1, fetcher=redirected)
    assert result["added_count"] == 0
    assert result["target_met"] is False
    assert "redirected away" in result["rejected"][0]["reason"]


def test_research_source_record_preserves_verified_final_url(tmp_path):
    result = refresh_topics(tmp_path / "topics.json", target=1, fetcher=fake_fetch)
    source = result["added"][0]["research_sources"][0]
    assert source["final_url"] == source["url"]


def test_only_approved_https_publisher_domains_are_accepted():
    from finance_campus.research_pipeline import is_approved_research_url

    assert is_approved_research_url("https://www.consumerfinance.gov/guide")
    assert is_approved_research_url("https://www.bou.or.ug/financial_literacy")
    assert not is_approved_research_url("http://www.consumerfinance.gov/guide")
    assert not is_approved_research_url("https://consumerfinance.gov.attacker.example/guide")
    assert not is_approved_research_url("https://example.org/guide")
    assert not is_approved_research_url("https://user:pass@consumerfinance.gov/guide")
    assert not is_approved_research_url("https://consumerfinance.gov:8443/guide")



def test_refresh_report_tracks_remaining_catalogue_and_canonical_path(tmp_path):
    path = tmp_path / "production" / "topic-library.json"
    result = refresh_topics(path, target=5, fetcher=fake_fetch)
    assert result["library_path"] == str(path)
    assert result["blueprint_catalogue_count"] == 66
    assert result["unused_blueprints_remaining"] == 61
    assert result["estimated_weeks_of_catalogue_cover_at_21_per_week"] == 2.9
    assert result["catalogue_exhaustion_warning"] is None


def test_reachable_pdf_without_extractable_text_is_not_counted_as_researched(tmp_path):
    def pdf_without_text(url):
        return {
            "status": 200,
            "final_url": url,
            "title": "Official PDF",
            "text": "",
        }

    result = refresh_topics(tmp_path / "topics.json", target=1, fetcher=pdf_without_text)
    assert result["added_count"] == 0
    assert result["target_met"] is False
    assert "no extractable text" in result["rejected"][0]["reason"]
