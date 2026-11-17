import pytest

from finance_campus.script_generator import generate_script


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
    assert script["script_generation"]["approved_for_production"] is False


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
    with pytest.raises(ValueError, match="editorial_brief"):
        generate_script(item)
