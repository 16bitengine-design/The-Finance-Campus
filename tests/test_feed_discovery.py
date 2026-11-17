from finance_campus.feed_discovery import discover_from_official_feeds, parse_feed


RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
<title>Investor alert: recognize investment fraud warning signs</title>
<link>https://www.sec.gov/example/investor-fraud-alert</link>
<description>Learn to identify fraudulent investment offers and protect investors.</description>
<pubDate>Mon, 16 Nov 2026 10:00:00 GMT</pubDate>
</item></channel></rss>"""


def test_parse_rss_feed():
    entries = parse_feed(RSS)
    assert len(entries) == 1
    assert entries[0]["title"].startswith("Investor alert")
    assert entries[0]["url"] == "https://www.sec.gov/example/investor-fraud-alert"
    assert "fraudulent investment" in entries[0]["summary"]


def test_parse_atom_feed():
    atom = """<feed xmlns="http://www.w3.org/2005/Atom"><entry>
    <title>Consumer credit education update</title>
    <link href="https://example.gov/credit"/>
    <summary>Information about consumer credit.</summary>
    <updated>2026-11-16T10:00:00Z</updated>
    </entry></feed>"""
    entries = parse_feed(atom)
    assert entries[0]["url"] == "https://example.gov/credit"
    assert entries[0]["published"] == "2026-11-16T10:00:00Z"


def test_discovery_creates_unapproved_topic_from_official_article():
    article_text = ("Investment fraud can involve misleading claims and pressure. " * 12)
    topics, rejected, feed_counts = discover_from_official_feeds(
        existing_topics=[],
        target=1,
        timestamp="2026-11-17T00:00:00+00:00",
        feed_fetcher=lambda url: RSS if "sec.gov" in url else '<rss version="2.0"><channel /></rss>',
        article_fetcher=lambda url: {
            "status": 200,
            "url": url,
            "final_url": url,
            "text": article_text,
        },
    )
    assert len(topics) == 1
    assert topics[0]["research_status"] == "discovered_needs_claim_review"
    assert topics[0]["discovery_metadata"]["method"] == "official_rss_atom"
    assert topics[0]["production_status"] == "not_started"
    assert topics[0]["publication_status"] == "not_published"
    assert not rejected
    assert feed_counts["SEC investor alerts"] == 1


def test_discovery_rejects_off_domain_article_links():
    bad_feed = RSS.replace(
        "https://www.sec.gov/example/investor-fraud-alert",
        "https://example.com/fake-investment-alert",
    )
    topics, rejected, _ = discover_from_official_feeds(
        existing_topics=[],
        target=1,
        feed_fetcher=lambda _url: bad_feed,
        article_fetcher=lambda _url: {"status": 200, "text": "x" * 500},
    )
    assert topics == []
    assert any("outside the official publisher domain" in item["reason"] for item in rejected)
