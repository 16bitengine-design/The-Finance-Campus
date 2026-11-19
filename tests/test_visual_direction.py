from finance_campus.visual_direction import validate_visual_direction


def directed_scene():
    return {
        "visual_direction": {
            "setting": "A modest family kitchen at the end of payday.",
            "takeaway": "A bill competes with the family's savings goal.",
            "visual_rationale": "The viewer sees the choice happen at the kitchen table.",
            "shot": {"size": "medium", "composition": "Family left, bill foreground, savings envelope right."},
            "layers": [
                {"name": "background", "asset": "kitchen_background"},
                {"name": "characters", "asset": "family_characters"},
                {"name": "props", "asset": "bill_and_envelope"},
            ],
            "characters": [{
                "id": "parent_a",
                "identity": "Same recurring parent character, warm brown skin and short natural hair.",
                "clothing": "Mustard cardigan and dark trousers, consistent with character bible.",
                "expression": "worried",
                "gesture": "One hand holds the bill while the other pauses above the savings envelope.",
                "gaze": "Looks from the bill toward the envelope.",
                "interactions": ["holds overdue electricity bill", "reaches toward labelled savings envelope"],
            }],
            "action_beats": [
                {"at_seconds": 0.2, "action": "draw_reveal", "target": "kitchen table and bill", "result": "The setting and unexpected bill become visible."},
                {"at_seconds": 1.4, "action": "bill_arrive", "target": "electricity bill", "result": "The bill slides onto the table and draws the parent's attention."},
                {"at_seconds": 2.8, "action": "decision", "target": "parent_a", "result": "The parent hesitates before choosing which envelope to open."},
            ],
            "transition": {"type": "object_carry", "continuity_anchor": "The bill remains in the parent's hand as the camera moves closer."},
            "caption_safe_area": {"top": 0.06, "bottom": 0.82},
        }
    }


def test_complete_illustration_first_direction_passes():
    assert validate_visual_direction(directed_scene()) == []


def test_direction_requires_real_character_performance_and_interaction():
    scene = directed_scene()
    scene["visual_direction"]["characters"][0]["expression"] = "blank"
    scene["visual_direction"]["characters"][0]["interactions"] = []
    errors = validate_visual_direction(scene)
    assert any("expression" in error for error in errors)
    assert any("interactions" in error for error in errors)


def test_action_beats_must_show_ordered_visible_consequences():
    scene = directed_scene()
    scene["visual_direction"]["action_beats"][1]["at_seconds"] = 0.1
    assert any("ordered by at_seconds" in error for error in validate_visual_direction(scene))
    scene["visual_direction"]["action_beats"][2]["result"] = ""
    assert any("result" in error for error in validate_visual_direction(scene))


def test_direction_requires_depth_and_scene_continuity():
    scene = directed_scene()
    scene["visual_direction"]["layers"] = [{"name": "background", "asset": "room"}]
    scene["visual_direction"]["transition"]["continuity_anchor"] = ""
    errors = validate_visual_direction(scene)
    assert any("at least two depth layers" in error for error in errors)
    assert any("continuity_anchor" in error for error in errors)


def test_caption_safe_area_must_be_valid_normalized_range():
    scene = directed_scene()
    scene["visual_direction"]["caption_safe_area"] = {"top": 0.8, "bottom": 0.2}
    assert any("boundaries must be ordered" in error for error in validate_visual_direction(scene))
