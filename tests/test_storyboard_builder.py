import json
from pathlib import Path

from finance_campus.config import load_yaml
from finance_campus.storyboard import validate_storyboard
from finance_campus.storyboard_builder import build_storyboard


def _script():
    path = Path(__file__).parents[1] / "examples" / "script-package.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_approved_script_becomes_six_illustrated_scenes_and_disclaimer():
    storyboard = build_storyboard(
        _script(),
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    assert len(storyboard["scenes"]) == 7
    assert all(any(item["type"] != "text" for item in scene["elements"]) for scene in storyboard["scenes"])
    assert storyboard["scenes"][-1]["minimum_duration_seconds"] >= 6
    assert storyboard["spoken_disclaimer_text"] in storyboard["scenes"][-1]["narration"]
    assert validate_storyboard(storyboard) == []


def test_long_form_storyboard_uses_landscape_canvas():
    storyboard = build_storyboard(
        _script(),
        video_format="long",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    assert storyboard["canvas"] == {"width": 1778, "height": 1000}
    assert validate_storyboard(storyboard) == []


def test_storyboard_builder_rejects_unknown_format():
    try:
        build_storyboard(
            _script(),
            video_format="square",
            disclaimer_config=load_yaml("config/disclaimer.yaml"),
        )
    except ValueError as exc:
        assert "video_format" in str(exc)
    else:
        raise AssertionError("Unknown video format should be rejected")


def test_visual_mapping_records_concept_and_relationship_for_review():
    script = _script()
    script["sections"]["relatable_financial_problem"] = (
        "Prices rise and purchasing power falls: the same money buys less food."
    )
    storyboard = build_storyboard(
        script,
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scene = storyboard["scenes"][0]
    assert scene["visual_objects"] == ["money_note", "coin", "wallet"]
    assert "purchasing power" in scene["matched_visual_terms"]
    assert "same money" in scene["visual_intent"]


def test_debt_visual_mapping_shows_repayment_obligation():
    script = _script()
    script["sections"]["relatable_financial_problem"] = (
        "A household borrows money through a loan and must make repayments."
    )
    storyboard = build_storyboard(
        script,
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scene = storyboard["scenes"][0]
    assert scene["visual_objects"] == ["wallet", "money_note", "house"]
    assert "repayment" in scene["matched_visual_terms"]
    assert any(item["type"] == "arrow" for item in scene["elements"])


def test_storyboard_connects_cause_effect_and_outcome_with_ordered_draw_cues():
    storyboard = build_storyboard(
        _script(),
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scene = storyboard["scenes"][0]
    arrows = [item for item in scene["elements"] if item["type"] == "arrow"]
    assert len(arrows) == 2
    starts = [item["start_seconds"] for item in scene["elements"]]
    assert starts == sorted(starts)
    outcome = scene["elements"][-2]
    assert outcome["type"] in {"person", "bank", "wallet", "house", "coin", "money_note", "savings_jar"}
    assert outcome["start_seconds"] > arrows[-1]["start_seconds"]

def test_portrait_scene_titles_stay_above_the_caption_safe_zone():
    storyboard = build_storyboard(
        _script(),
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    height = storyboard["canvas"]["height"]
    for scene in storyboard["scenes"][:-1]:
        title = next(item for item in scene["elements"] if item["type"] == "text")
        assert title["y"] <= height * 0.85



def test_pay_yourself_first_storyboard_uses_distinct_story_scenes_and_moving_money():
    script = _script()
    script["title"] = "Why You Should Pay Yourself First"
    script["sections"] = {
        "relatable_financial_problem": "A worker receives a paycheck but the money disappears into daily spending.",
        "escalating_real_world_stakes": "Bills compete with household needs and leave little money at the end.",
        "clear_explanation_of_why_it_matters": "Paying yourself first moves money into savings before other spending.",
        "hopeful_and_realistic_possibility": "Small regular deposits can gradually build a useful savings buffer.",
        "practical_action_viewers_can_take": "Choose a realistic amount and move it into savings on payday.",
        "empowering_close": "A consistent habit helps you make progress toward your goals.",
    }
    storyboard = build_storyboard(
        script, video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scenes = storyboard["scenes"][:-1]
    assert all(any(item["type"] == "person" for item in scene["elements"]) for scene in scenes)
    layouts = [
        tuple((item["type"], item.get("x"), item.get("y")) for item in scene["elements"] if item["type"] != "text")
        for scene in scenes
    ]
    assert len(set(layouts)) == len(layouts)
    moving = [
        item for scene in scenes for item in scene["elements"]
        if item.get("motion")
    ]
    assert moving
    assert moving[0]["type"] == "money_note"
    wallet = next(item for item in scenes[0]["elements"] if item["type"] == "wallet")
    assert wallet["open_animation"]["start_seconds"] < wallet["open_animation"]["end_seconds"]
    assert validate_storyboard(storyboard) == []



def test_video_specific_visual_signature_changes_with_script_content():
    script = _script()
    first = build_storyboard(
        script, video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    changed = json.loads(json.dumps(script))
    changed["title"] = "A Different Money Lesson"
    second = build_storyboard(
        changed, video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    assert first["scenes"][0]["visual_signature"] != second["scenes"][0]["visual_signature"]


def test_character_performance_changes_with_the_emotional_story_arc():
    storyboard = build_storyboard(
        _script(),
        video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scenes = storyboard["scenes"][:-1]
    expected = [
        ("worried", "worried"),
        ("overwhelmed", "overwhelmed"),
        ("thinking", "calm"),
        ("reaching", "calm"),
        ("determined", "determined"),
        ("celebrating", "calm"),
    ]
    actual = []
    for scene in scenes:
        character = next(item for item in scene["elements"] if item["type"] == "person")
        actual.append((character["pose"], character["expression"]))
    assert actual == expected


def test_story_scenes_assign_protagonist_interactions_to_financial_props():
    storyboard = build_storyboard(
        _script(), video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    scenes = storyboard["scenes"][:-1]
    assert len(scenes) == 6
    assert all(
        isinstance(next(item for item in scene["elements"] if item["type"] == "person").get("interaction_target"), dict)
        for scene in scenes
    )
    interactions = [
        next(item for item in scene["elements"] if item["type"] == "person")["interaction"]
        for scene in scenes
    ]
    assert len(set(interactions)) == 6


def test_character_interactions_have_timed_eased_reach_choreography():
    storyboard = build_storyboard(
        _script(), video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    for scene in storyboard["scenes"][:-1]:
        character = next(item for item in scene["elements"] if item["type"] == "person")
        animation = character["interaction_animation"]
        target = character["interaction_target"]
        assert animation["start_seconds"] < animation["end_seconds"]
        assert animation["easing"] == "ease_out"
        assert (animation["from_x"], animation["from_y"]) != (target["x"], target["y"])


def test_hopeful_and_practical_scenes_include_walking_choreography():
    storyboard = build_storyboard(
        _script(), video_format="short",
        disclaimer_config=load_yaml("config/disclaimer.yaml"),
    )
    for scene in storyboard["scenes"][3:5]:
        character = next(item for item in scene["elements"] if item["type"] == "person")
        assert character["motion"]["to_x"] > character["motion"]["from_x"]
        assert character["walk_cycle"]["cycle_seconds"] > 0
