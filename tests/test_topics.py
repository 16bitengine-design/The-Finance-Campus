import pytest

from finance_campus.topics import add_topic, normalize_title


def sample_topic(topic_id="TFC-0001", title="Emergency funds: getting started"):
    return {
        "id": topic_id,
        "title": title,
        "category": "saving",
        "geographic_relevance": ["global", "Uganda", "East Africa"],
        "sources": ["https://www.consumerfinance.gov/"],
        "research_status": "needs_review",
        "production_status": "not_started",
        "publication_status": "not_published",
    }


def test_normalize_title():
    assert normalize_title("Compound-Interest 101!") == "compound interest 101"


def test_add_topic_and_reject_duplicate_title():
    topics = []
    assert add_topic(topics, sample_topic()) is True
    assert add_topic(topics, sample_topic("TFC-0002", "EMERGENCY FUNDS getting started")) is False
    assert len(topics) == 1


def test_topic_requires_source():
    topic = sample_topic()
    topic["sources"] = []
    with pytest.raises(ValueError):
        add_topic([], topic)
