import pytest

from finance_campus.config import load_yaml
from finance_campus.post_metadata import generate_post_metadata


def sample_script():
    return {
        "title": "Why Your Money Needs a Plan",
        "category": "Budgeting",
        "description": "A simple money mindset lesson about making deliberate spending choices.",
    }


def test_metadata_generates_distinct_platform_copy_and_relevant_tags():
    config = load_yaml("config/disclaimer.yaml")
    result = generate_post_metadata(sample_script(), config)
    youtube = result["platforms"]["youtube"]
    tiktok = result["platforms"]["tiktok"]
    assert youtube["description"] != tiktok["caption"]
    assert "#Budgeting" in youtube["hashtags"]
    assert "#MoneyManagement" in tiktok["hashtags"]
    assert len(youtube["hashtags"]) <= 3
    assert len(tiktok["hashtags"]) <= 5
    assert "money" in youtube["search_tags"]
    assert result["validation"]["platform_copy_is_distinct"]


def test_both_platform_descriptions_include_required_disclaimer():
    config = load_yaml("config/disclaimer.yaml")
    result = generate_post_metadata(sample_script(), config)
    required = config["disclaimer"]["description"]
    assert required in result["platforms"]["youtube"]["description"]
    assert required in result["platforms"]["tiktok"]["caption"]
    assert result["validation"]["youtube_disclaimer_present"]
    assert result["validation"]["tiktok_disclaimer_present"] is True


def test_metadata_rejects_missing_title():
    with pytest.raises(ValueError, match="title"):
        generate_post_metadata({"category": "Saving"}, load_yaml("config/disclaimer.yaml"))


def test_long_form_metadata_targets_youtube_only():
    config = load_yaml("config/disclaimer.yaml")
    result = generate_post_metadata(sample_script(), config, video_format="long")
    assert set(result["platforms"]) == {"youtube"}
    assert result["validation"]["tiktok_disclaimer_present"] is None


def test_metadata_includes_verified_related_video_link_in_youtube_description():
    config = load_yaml("config/disclaimer.yaml")
    script = sample_script()
    script["related_video"] = {
        "title": "What Are Stocks and How Do They Work?",
        "url": "https://www.youtube.com/watch?v=abc123xyz89",
        "status": "publicly_accessible_verified",
    }
    result = generate_post_metadata(script, config)
    youtube = result["platforms"]["youtube"]["description"]
    tiktok = result["platforms"]["tiktok"]["caption"]
    assert "https://www.youtube.com/watch?v=abc123xyz89" in youtube
    assert "What Are Stocks and How Do They Work?" in tiktok
