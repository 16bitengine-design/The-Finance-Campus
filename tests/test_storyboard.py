import pytest

from finance_campus.storyboard import render_scene_svg, validate_storyboard


def sample_storyboard():
    return {
        "scenes": [{
            "id": "debt-growth",
            "narration": "Interest makes the amount you owe grow over time.",
            "duration_seconds": 8,
            "elements": [
                {"type": "rect", "x": 120, "y": 160, "width": 240, "height": 150, "color": "navy"},
                {"type": "arrow", "x1": 390, "y1": 240, "x2": 560, "y2": 240, "color": "gold"},
                {"type": "text", "x": 140, "y": 350, "text": "Amount owed", "color": "green"},
            ],
        }]
    }


def test_storyboard_requires_narration_and_actual_illustration():
    assert validate_storyboard(sample_storyboard()) == []


def test_text_only_scene_is_rejected():
    data = sample_storyboard()
    data["scenes"][0]["elements"] = [{"type": "text", "x": 10, "y": 20, "text": "Debt"}]
    assert any("text-only" in error for error in validate_storyboard(data))


def test_missing_narration_is_rejected():
    data = sample_storyboard()
    data["scenes"][0]["narration"] = ""
    assert any("narration" in error for error in validate_storyboard(data))


def test_unknown_palette_color_is_rejected():
    data = sample_storyboard()
    data["scenes"][0]["elements"][0]["color"] = "#ff00ff"
    assert any("palette" in error for error in validate_storyboard(data))


def test_renderer_produces_svg_with_draw_effect_and_escaped_text():
    data = sample_storyboard()["scenes"][0]
    data["elements"][2]["text"] = "Interest & fees"
    svg = render_scene_svg(data)
    assert "<svg" in svg
    assert "animation:draw" in svg
    assert "Interest &amp; fees" in svg
    assert "marker-end" in svg


def test_invalid_scene_cannot_be_rendered():
    scene = sample_storyboard()["scenes"][0]
    scene["elements"] = [{"type": "text", "x": 1, "y": 2, "text": "Only text"}]
    with pytest.raises(ValueError, match="text-only"):
        render_scene_svg(scene)


def test_character_interaction_animation_metadata_is_validated():
    data = sample_storyboard()
    data["scenes"][0]["elements"][0].update({
        "interaction_target": {"x": 700, "y": 300},
        "interaction_animation": {
            "from_x": 250, "from_y": 220,
            "start_seconds": 1, "end_seconds": 3,
            "easing": "ease_out",
        },
    })
    assert validate_storyboard(data) == []
    data["scenes"][0]["elements"][0]["interaction_animation"]["end_seconds"] = 0
    assert any(
        "interaction_animation timing" in error
        for error in validate_storyboard(data)
    )


def test_character_interaction_animation_requires_a_target():
    data = sample_storyboard()
    data["scenes"][0]["elements"][0]["interaction_animation"] = {
        "from_x": 250, "from_y": 220,
        "start_seconds": 1, "end_seconds": 3,
    }
    assert any(
        "requires interaction_target" in error
        for error in validate_storyboard(data)
    )


def test_walking_cycle_rejects_invalid_timing():
    data = sample_storyboard()
    data["scenes"][0]["elements"][0]["walk_cycle"] = {
        "start_seconds": 2, "end_seconds": 1, "cycle_seconds": 0,
    }
    errors = validate_storyboard(data)
    assert any("walk_cycle timing" in error for error in errors)
