from __future__ import annotations

from finance_campus.narration import _retime_scene_animation
from finance_campus.config import load_yaml
from finance_campus.storyboard_builder import build_storyboard


def test_scene_actions_are_spread_over_real_kokoro_scene_duration():
    scene = {
        "elements": [
            {"type": "person", "start_seconds": 0.15, "draw_seconds": 0.85,
             "interaction_animation": {"start_seconds": 1.8, "end_seconds": 3.2}},
            {"type": "coin", "start_seconds": 1.15, "draw_seconds": 0.85,
             "motion": {"start_seconds": 2.0, "end_seconds": 4.2}},
            {"type": "text", "start_seconds": 4.45, "draw_seconds": 0.2},
        ]
    }
    _retime_scene_animation(scene, 18.0)
    starts = [item["start_seconds"] for item in scene["elements"]]
    assert starts == sorted(starts)
    assert starts[-1] > 14.0
    person = scene["elements"][0]
    assert person["interaction_animation"]["end_seconds"] > 10.0
    assert scene["elements"][1]["motion"]["end_seconds"] > 14.0


def test_story_dependent_cast_adds_a_second_character_when_relationship_is_narrated():
    script = {
        "title": "A Family Budget",
        "sections": {
            "relatable_financial_problem": "A parent and child discuss the household budget.",
            "escalating_real_world_stakes": "The family faces rising food costs.",
            "clear_explanation_of_why_it_matters": "A spending plan helps the household.",
            "hopeful_and_realistic_possibility": "The parent and child agree to save.",
            "practical_action_viewers_can_take": "The family records every expense.",
            "empowering_close": "Small family choices build resilience.",
        },
    }
    storyboard = build_storyboard(
        script, video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scene = storyboard["scenes"][0]
    people = [item for item in scene["elements"] if item["type"] == "person"]
    assert len(people) == 2
    assert people[1]["character_role"] == "family-member"
    assert people[1]["motion"]["end_seconds"] > people[1]["motion"]["start_seconds"]


def test_single_character_stories_do_not_receive_an_unnecessary_supporting_cast():
    script = {
        "title": "Personal Savings",
        "sections": {
            "relatable_financial_problem": "A worker struggles to save money.",
            "escalating_real_world_stakes": "Unexpected expenses reduce the balance.",
            "clear_explanation_of_why_it_matters": "A reserve can help manage risk.",
            "hopeful_and_realistic_possibility": "A small regular deposit can help.",
            "practical_action_viewers_can_take": "Set aside a manageable amount.",
            "empowering_close": "Consistency builds a buffer.",
        },
    }
    storyboard = build_storyboard(
        script, video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    people = [item for item in storyboard["scenes"][0]["elements"] if item["type"] == "person"]
    assert len(people) == 1
