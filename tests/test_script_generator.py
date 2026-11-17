import pytest

from finance_campus.script_generator import generate_script
from finance_campus.script_quality import validate_script


def topic():
    return {
        "id": "TFC-TEST",
        "title": "How to start an emergency fund",
        "category": "Saving",
        "geographic_relevance": ["global", "Uganda"],
        "editorial_brief": {
            "problem": "An unexpected bill can disrupt a tight household budget.",
            "stakes": "Without a buffer, a household may need to borrow.",
            "explanation": "An emergency fund is money set aside for necessary unplanned costs.",
            "action": "Choose an affordable amount and set it aside regularly.",
        },
        "research_sources": [{
            "url": "https://www.consumerfinance.gov/example",
            "verification": "reachable_and_keyword_checked",
        }],
    }


def test_generate_short_script_contains_all_required_sections():
    script = generate_script(topic())
    assert set(script["sections"]) == {
        "relatable_financial_problem", "escalating_real_world_stakes",
        "clear_explanation_of_why_it_matters", "hopeful_and_realistic_possibility",
        "practical_action_viewers_can_take", "empowering_close",
    }
    assert script["format"] == "short"
    assert script["sections"]["relatable_financial_problem"].startswith("Have you ever")
    assert script["sections"]["practical_action_viewers_can_take"].startswith("Try this:")
    assert "someone else's timeline" in script["sections"]["empowering_close"]
    assert script["script_generation"]["approved_for_production"] is False
    report = validate_script(script)
    assert report.passed is False
    assert any("still a candidate" in error for error in report.errors)


def test_generate_long_script():
    assert generate_script(topic(), duration="long")["target_duration_seconds"] == [300, 600]


def test_generator_rejects_unchecked_source():
    item = topic()
    item["research_sources"][0]["verification"] = "unverified"
    with pytest.raises(ValueError, match="not passed"):
        generate_script(item)


def test_generator_rejects_missing_editorial_brief():
    item = topic()
    del item["editorial_brief"]
    with pytest.raises(TypeError, match="editorial_brief"):
        generate_script(item)

def test_verified_paraphrased_inspiration_is_attributed_without_quote_marks():
    item = topic()
    item["inspiration"] = {
        "kind": "paraphrase",
        "author": "Example Speaker",
        "work": "A verified book",
        "source_url": "https://example.org/original-work",
        "text": "clear goals can help people make more deliberate choices about money",
        "verification": "author_and_original_work_verified",
        "original_wording_reused": False,
    }
    script = generate_script(item)
    explanation = script["sections"]["clear_explanation_of_why_it_matters"]
    assert "Example Speaker" in explanation
    assert "A verified book" in explanation
    assert "clear goals can help" in explanation
    assert "“" not in explanation


def test_direct_quote_requires_documented_rights_review():
    item = topic()
    item["inspiration"] = {
        "kind": "direct_quote",
        "author": "Example Author",
        "work": "Example Work",
        "source_url": "https://example.org/work",
        "text": "A short verified line.",
        "verification": "author_and_original_work_verified",
    }
    with pytest.raises(ValueError, match="requires verified"):
        generate_script(item)


def test_direct_quote_rejects_more_than_fifteen_words():
    item = topic()
    item["inspiration"] = {
        "kind": "direct_quote",
        "author": "Example Author",
        "work": "Example Work",
        "source_url": "https://example.org/work",
        "text": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen",
        "verification": "author_and_original_work_verified",
        "rights_basis": "permission_granted",
        "rights_verified": True,
    }
    with pytest.raises(ValueError, match="15-word"):
        generate_script(item)
