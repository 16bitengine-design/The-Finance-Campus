import json

from finance_campus.related_videos import (
    attach_related_video,
    find_related_video,
    load_published_video_library,
)


def test_related_video_matches_explicit_concept_and_adds_spoken_cta(tmp_path):
    library = tmp_path / "published.json"
    library.write_text(json.dumps([{
        "video_id": "stocks-101",
        "title": "What Are Stocks and How Do They Work?",
        "url": "https://www.youtube.com/watch?v=abc123xyz89",
        "concepts": ["stocks", "shares", "ownership"],
        "status": "publicly_accessible_verified",
    }]), encoding="utf-8")
    script = {
        "related_concepts": ["investing", "stocks"],
        "sections": {"empowering_close": "Learn, apply, and grow."},
    }

    result = attach_related_video(script, library)

    assert result is not None
    assert result["video_id"] == "stocks-101"
    assert "watch our dedicated lesson" in result["spoken_cta"]
    assert result["spoken_cta"] in script["sections"]["empowering_close"]


def test_unverified_or_invalid_video_is_never_recommended(tmp_path):
    library = tmp_path / "published.json"
    library.write_text(json.dumps([
        {
            "video_id": "draft-1",
            "title": "What Are Stocks?",
            "url": "https://www.youtube.com/watch?v=abc123xyz89",
            "concepts": ["stocks"],
            "status": "uploaded",
        },
        {
            "video_id": "fake-2",
            "title": "Stock Basics",
            "url": "https://example.com/video",
            "concepts": ["stocks"],
            "status": "publicly_accessible_verified",
        },
    ]), encoding="utf-8")

    assert load_published_video_library(library) == []
    assert find_related_video({"related_concepts": ["stocks"]}, library) is None


def test_no_related_concept_match_does_not_add_irrelevant_cta(tmp_path):
    library = tmp_path / "published.json"
    library.write_text(json.dumps([{
        "video_id": "stocks-101",
        "title": "What Are Stocks?",
        "url": "https://www.youtube.com/watch?v=abc123xyz89",
        "concepts": ["stocks"],
        "status": "publicly_accessible_verified",
    }]), encoding="utf-8")
    script = {
        "related_concepts": ["emergency savings"],
        "sections": {"empowering_close": "Learn, apply, and grow."},
    }

    assert attach_related_video(script, library) is None
    assert "related_video" not in script
    assert script["sections"]["empowering_close"] == "Learn, apply, and grow."
