import shutil
import subprocess
from collections import Counter

import pytest
from PIL import Image, ImageChops, ImageDraw

from finance_campus.storyboard import render_scene_svg, validate_storyboard
from finance_campus.video_renderer import _draw_progressive_strokes, _point, render_video


def _storyboard():
    return {"scenes": [{
        "id": "money-flow",
        "narration": "A person receives income and divides it between needs and savings.",
        "duration_seconds": 2,
        "elements": [
            {"type": "circle", "cx": 180, "cy": 150, "r": 35, "color": "navy"},
            {"type": "line", "x1": 180, "y1": 185, "x2": 180, "y2": 290, "color": "navy"},
            {"type": "rect", "x": 360, "y": 150, "width": 170, "height": 100, "color": "green"},
            {"type": "arrow", "x1": 220, "y1": 220, "x2": 350, "y2": 200, "color": "gold"},
            {"type": "text", "x": 370, "y": 300, "text": "Savings", "color": "green"},
        ],
    }]}

@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_creates_playable_mp4(tmp_path):
    output = render_video(_storyboard(), tmp_path / "sample.mp4", fps=12, draw_fps=6, keep_frames=True)
    assert output.is_file()
    assert output.stat().st_size > 1024
    result = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True, check=False)
    assert "Video:" in result.stderr
    final_frame = Image.open(tmp_path / ".sample_frames" / "frame_000011.png").convert("RGB")
    white = Image.new("RGB", final_frame.size, (255, 255, 255))
    assert ImageChops.difference(final_frame, white).getbbox() is not None

def test_video_renderer_rejects_text_only_storyboard(tmp_path):
    storyboard = _storyboard()
    storyboard["scenes"][0]["elements"] = [{"type": "text", "x": 20, "y": 30, "text": "Only words"}]
    with pytest.raises(ValueError, match="text-only"):
        render_video(storyboard, tmp_path / "bad.mp4")



def test_financial_illustration_types_are_valid_and_render_to_svg():
    scene = {
        "id": "saving-for-the-future",
        "narration": "A worker puts money into a savings jar.",
        "duration_seconds": 3,
        "elements": [
            {"type": "person", "x": 100, "y": 100, "width": 160, "height": 300},
            {"type": "savings_jar", "x": 400, "y": 180, "width": 180, "height": 220, "color": "green"},
            {"type": "coin", "x": 650, "y": 120, "width": 90, "height": 90, "color": "gold"},
            {"type": "text", "x": 350, "y": 470, "text": "Save consistently"},
        ],
    }
    assert validate_storyboard({"scenes": [scene]}) == []
    svg = render_scene_svg(scene, {"width": 1000, "height": 1778})
    assert 'width="1080" height="1920"' in svg
    assert "<circle" in svg
    assert "Save consistently" in svg


def test_semantic_illustration_requires_positive_dimensions():
    scene = {
        "id": "invalid-wallet",
        "narration": "A wallet stores money.",
        "duration_seconds": 2,
        "elements": [{"type": "wallet", "x": 10, "y": 10, "width": 0, "height": 80}],
    }
    assert any("width and height must be positive" in error for error in validate_storyboard({"scenes": [scene]}))



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_muxes_narration_and_burns_captions(tmp_path):
    audio = tmp_path / "narration.mp3"
    generated = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-q:a", "8", "-acodec", "libmp3lame", str(audio),
        ],
        capture_output=True, text=True, check=False,
    )
    assert generated.returncode == 0
    captions = tmp_path / "captions.srt"
    captions.write_text(
        chr(10).join([
            "1",
            "00:00:00,000 --> 00:00:01,800",
            "A practical money lesson",
            "",
        ]),
        encoding="utf-8",
    )
    output = render_video(
        _storyboard(), tmp_path / "with-audio.mp4", fps=12, draw_fps=6,
        audio_path=audio, captions_path=captions,
    )
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    assert "Video:" in probe.stderr
    assert "Audio:" in probe.stderr



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_render_video_supports_landscape_long_form(tmp_path):
    output = render_video(
        _storyboard(), tmp_path / "long-form.mp4",
        video_format="long", fps=12, draw_fps=6,
    )
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(output), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    assert "1920x1080" in probe.stderr


def test_video_renderer_rejects_negative_transition_duration(tmp_path):
    with pytest.raises(ValueError, match="transition_seconds"):
        render_video(_storyboard(), tmp_path / "bad-transition.mp4", transition_seconds=-0.1)



def test_coordinate_mapping_uses_distinct_x_and_y_values():
    assert _point(120, 1450, 1.08, 1.08) == (130, 1566)



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_portrait_render_places_illustration_at_lower_canvas_coordinates(tmp_path):
    storyboard = {
        "canvas": {"width": 1000, "height": 1778},
        "scenes": [{
            "id": "lower-canvas-coin",
            "narration": "A coin appears near the bottom of the portrait canvas.",
            "duration_seconds": 1,
            "elements": [
                {"type": "coin", "x": 430, "y": 1450, "width": 120, "height": 120, "color": "gold"},
            ],
        }],
    }
    render_video(
        storyboard, tmp_path / "portrait-position.mp4",
        fps=12, draw_fps=6, keep_frames=True,
    )
    frame = Image.open(tmp_path / ".portrait-position_frames" / "frame_000005.png").convert("RGB")
    lower_region = frame.crop((0, 1400, 1080, 1920))
    white = Image.new("RGB", lower_region.size, (255, 255, 255))
    assert ImageChops.difference(lower_region, white).getbbox() is not None


def test_storyboard_accepts_narration_synchronized_illustration_cues():
    scene = {
        "id": "timed-money-flow",
        "narration": "Income arrives, then moves into savings.",
        "duration_seconds": 4,
        "elements": [
            {"type": "money_note", "x": 100, "y": 100, "width": 180, "height": 100,
             "start_seconds": 0.4, "draw_seconds": 0.8},
            {"type": "savings_jar", "x": 500, "y": 100, "width": 180, "height": 220,
             "start_seconds": 2.0, "draw_seconds": 1.0},
        ],
    }
    assert validate_storyboard({"scenes": [scene]}) == []


def test_storyboard_rejects_invalid_illustration_timing():
    scene = {
        "id": "bad-timing",
        "narration": "Money moves.",
        "duration_seconds": 2,
        "elements": [
            {"type": "coin", "x": 100, "y": 100, "width": 80, "height": 80,
             "start_seconds": -0.2, "draw_seconds": 0},
        ],
    }
    errors = validate_storyboard({"scenes": [scene]})
    assert any("start_seconds" in error for error in errors)
    assert any("draw_seconds" in error for error in errors)



def test_progressive_strokes_reveal_pen_path_in_order():
    image = Image.new("RGB", (120, 30), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    _draw_progressive_strokes(
        draw,
        [[(10, 15), (50, 15)], [(70, 15), (110, 15)]],
        0.5,
        (16, 43, 85),
        3,
    )
    # At 50% the first stroke is complete and the second has not started.
    assert image.getpixel((45, 15)) != (255, 255, 255)
    assert image.getpixel((75, 15)) == (255, 255, 255)



@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg is not installed")
def test_scene_transition_inserts_smooth_crossfade_frames(tmp_path):
    storyboard = {
        "canvas": {"width": 1000, "height": 562},
        "scenes": [
            {
                "id": "outgoing",
                "narration": "The first illustration.",
                "duration_seconds": 1,
                "elements": [
                    {"type": "circle", "cx": 500, "cy": 281, "r": 90, "color": "navy",
                     "start_seconds": 0, "draw_seconds": 0.1},
                ],
            },
            {
                "id": "incoming",
                "narration": "The next illustration.",
                "duration_seconds": 1,
                "elements": [
                    {"type": "circle", "cx": 500, "cy": 281, "r": 90, "color": "gold",
                     "start_seconds": 0, "draw_seconds": 0.1},
                ],
            },
        ],
    }
    render_video(
        storyboard, tmp_path / "crossfade.mp4",
        fps=4, draw_fps=4, transition_seconds=0.5, keep_frames=True,
    )
    frames = sorted((tmp_path / ".crossfade_frames").glob("frame_*.png"))
    # Four frames per scene plus two cross-dissolve frames.
    assert len(frames) == 10
    from PIL import ImageChops

    outgoing = Image.open(frames[3]).convert("RGB")
    halfway = Image.open(frames[5]).convert("RGB")
    incoming = Image.open(frames[7]).convert("RGB")
    # The selected centre pixel can be black in both scenes; compare whole
    # frames so the assertion measures the dissolve rather than one coordinate.
    assert ImageChops.difference(outgoing, incoming).getbbox() is not None
    assert ImageChops.difference(halfway, outgoing).getbbox() is not None
    assert ImageChops.difference(halfway, incoming).getbbox() is not None
    assert all(red == green == blue for red, green, blue in halfway.getdata())



def test_illustration_motion_interpolates_between_start_and_destination():
    from finance_campus.video_renderer import _motion_position

    element = {
        "type": "coin", "x": 10, "y": 20, "width": 40, "height": 40,
        "motion": {
            "from_x": 100, "from_y": 200, "to_x": 300, "to_y": 600,
            "start_seconds": 2, "end_seconds": 6,
        },
    }
    assert (_motion_position(element, 2)["x"], _motion_position(element, 2)["y"]) == (100, 200)
    halfway = _motion_position(element, 4)
    assert (halfway["x"], halfway["y"]) == (200, 400)
    finish = _motion_position(element, 8)
    assert (finish["x"], finish["y"]) == (300, 600)



def test_pen_hand_is_drawn_at_the_active_stroke_tip():
    from finance_campus.video_renderer import _draw_active_hand

    image = Image.new("RGB", (240, 160), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    strokes = [[(30, 30), (180, 30)]]
    _draw_active_hand(draw, strokes, 0.5, (22, 140, 67), 1.0)
    # The moving hand/marker is visible around the halfway drawing position.
    region = image.crop((90, 25, 190, 140))
    white = Image.new("RGB", region.size, (255, 255, 255))
    assert ImageChops.difference(region, white).getbbox() is not None


def test_character_poses_render_different_body_language():
    from finance_campus.video_renderer import _draw_element

    worried = Image.new("RGB", (300, 420), (255, 255, 255))
    determined = Image.new("RGB", (300, 420), (255, 255, 255))
    base = {
        "type": "person", "x": 60, "y": 35, "width": 180, "height": 340,
        "color": "navy",
    }
    _draw_element(
        ImageDraw.Draw(worried),
        {**base, "pose": "worried", "expression": "worried"},
        1.0, worried.size,
    )
    _draw_element(
        ImageDraw.Draw(determined),
        {**base, "pose": "determined", "expression": "determined"},
        1.0, determined.size,
    )
    assert ImageChops.difference(worried, determined).getbbox() is not None


def test_character_interaction_target_changes_reaching_arm_geometry():
    from finance_campus.video_renderer import _draw_element

    base = {
        "type": "person", "x": 40, "y": 30, "width": 180, "height": 340,
        "color": "navy", "pose": "reaching", "expression": "calm",
    }
    first = Image.new("RGB", (300, 420), (255, 255, 255))
    second = Image.new("RGB", (300, 420), (255, 255, 255))
    _draw_element(
        ImageDraw.Draw(first),
        {**base, "interaction_target": {"x": 500, "y": 250}},
        1.0, first.size,
    )
    _draw_element(
        ImageDraw.Draw(second),
        {**base, "interaction_target": {"x": 850, "y": 650}},
        1.0, second.size,
    )
    assert ImageChops.difference(first, second).getbbox() is not None


def test_character_reach_interpolates_over_time_without_object_motion():
    from finance_campus.video_renderer import _motion_position

    character = {
        "type": "person",
        "interaction_target": {"x": 700, "y": 500},
        "interaction_animation": {
            "from_x": 300, "from_y": 250,
            "start_seconds": 1, "end_seconds": 3,
            "easing": "ease_out",
        },
    }
    before = _motion_position(character, 0)["interaction_target"]
    halfway = _motion_position(character, 2)["interaction_target"]
    after = _motion_position(character, 3)["interaction_target"]
    assert before == {"x": 300, "y": 250}
    assert halfway["x"] > 500 and halfway["x"] < 700
    assert halfway["y"] > 250 and halfway["y"] < 500
    assert after == {"x": 700, "y": 500}


def test_walking_cycle_produces_distinct_gait_phases_and_body_bob():
    from finance_campus.video_renderer import _motion_position

    character = {
        "type": "person",
        "walk_cycle": {
            "start_seconds": 1, "end_seconds": 3,
            "cycle_seconds": .5,
        },
    }
    first = _motion_position(character, 1.125)
    second = _motion_position(character, 1.375)
    assert first["walk_phase"] != second["walk_phase"]
    assert first["body_bob"] != second["body_bob"]


def test_wallet_opening_animation_progresses_over_time():
    from finance_campus.video_renderer import _motion_position

    wallet = {
        "type": "wallet",
        "open_animation": {
            "start_seconds": 2, "end_seconds": 4, "easing": "ease_out",
        },
    }
    before = _motion_position(wallet, 1)
    halfway = _motion_position(wallet, 3)
    after = _motion_position(wallet, 4)
    assert before["open_progress"] == 0
    assert 0 < halfway["open_progress"] < 1
    assert after["open_progress"] == 1


def test_open_wallet_render_differs_from_closed_wallet():
    from finance_campus.video_renderer import _draw_element

    wallet = {
        "type": "wallet", "x": 40, "y": 40, "width": 220, "height": 140,
        "color": "navy",
    }
    closed = Image.new("RGB", (320, 240), (255, 255, 255))
    opened = Image.new("RGB", (320, 240), (255, 255, 255))
    _draw_element(ImageDraw.Draw(closed), {**wallet, "open_progress": 0}, 1, closed.size)
    _draw_element(ImageDraw.Draw(opened), {**wallet, "open_progress": 1}, 1, opened.size)
    assert ImageChops.difference(closed, opened).getbbox() is not None


def test_character_render_includes_clothing_and_body_detail():
    from finance_campus.video_renderer import _draw_element

    image = Image.new("RGB", (500, 500), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    _draw_element(
        draw,
        {
            "type": "person", "x": 120, "y": 35,
            "width": 240, "height": 410,
            "pose": "determined", "expression": "determined",
        },
        1.0, image.size,
    )
    non_white = sum(1 for pixel in image.getdata() if pixel != (255, 255, 255))
    assert non_white > 1800



def test_topic_specific_illustrations_render_in_raster_and_svg():
    from finance_campus.video_renderer import _draw_element

    kinds = ("phone", "shield", "calendar", "chart", "basket")
    for kind in kinds:
        element = {
            "type": kind, "x": 50, "y": 40, "width": 180, "height": 220,
            "color": "green",
        }
        image = Image.new("RGB", (300, 320), (255, 255, 255))
        _draw_element(ImageDraw.Draw(image), element, 1.0, image.size)
        white = Image.new("RGB", image.size, (255, 255, 255))
        assert ImageChops.difference(image, white).getbbox() is not None
        scene = {
            "id": f"topic-{kind}",
            "narration": f"A financial lesson illustrated with a {kind}.",
            "duration_seconds": 2,
            "elements": [element],
        }
        assert validate_storyboard({"scenes": [scene]}) == []
        svg = render_scene_svg(scene)
        assert "<svg" in svg and "<path" in svg or "<svg" in svg and "<rect" in svg

def test_active_marker_hand_stays_compact_at_full_hd_scale():
    from finance_campus.video_renderer import _draw_pen_hand

    image = Image.new("RGB", (320, 220), (255, 255, 255))
    _draw_pen_hand(ImageDraw.Draw(image), (150, 60), (22, 140, 67), 1.08)
    difference = ImageChops.difference(
        image, Image.new("RGB", image.size, (255, 255, 255)),
    )
    bounds = difference.getbbox()
    assert bounds is not None
    left, top, right, bottom = bounds
    assert right - left <= 70
    assert bottom - top <= 70


def test_character_render_uses_substantial_filled_illustration_not_only_wireframe():
    from finance_campus.video_renderer import _draw_element

    image = Image.new("RGB", (360, 520), (255, 255, 255))
    character = {
        "type": "person", "x": 75, "y": 35, "width": 210, "height": 440,
        "color": "navy", "pose": "worried", "expression": "worried",
    }
    _draw_element(ImageDraw.Draw(image), character, 1.0, image.size)
    counts = Counter(image.getdata())
    # Monochrome character art uses black ink, white paper and substantial
    # filled silhouettes rather than coloured skin/clothing fills.
    assert counts[(0, 0, 0)] > 12000
    assert set(counts) <= {(0, 0, 0), (255, 255, 255)}
    non_white = counts[(0, 0, 0)]
    assert non_white > 12000


def test_filled_rect_reveals_a_soft_tinted_surface_before_its_outline_finishes():
    from finance_campus.video_renderer import _draw_element

    image = Image.new("RGB", (200, 120), (255, 255, 255))
    _draw_element(
        ImageDraw.Draw(image),
        {"type": "rect", "x": 20, "y": 20, "width": 150, "height": 70,
         "color": "navy", "fill": True},
        0.5, image.size, image.size,
    )
    # Filled surfaces remain white paper; black cross-hatching provides
    # monochrome depth without introducing tinted colour fills.
    assert set(image.getdata()) <= {(0, 0, 0), (255, 255, 255)}
    assert image.getpixel((80, 55)) in {(0, 0, 0), (255, 255, 255)}
    assert sum(1 for pixel in image.getdata() if pixel == (0, 0, 0)) > 100


def test_svg_preserves_filled_room_surfaces_and_full_portrait_canvas():
    scene = {
        "id": "room",
        "narration": "A household reviews its budget at a table.",
        "duration_seconds": 3,
        "elements": [
            {"type": "rect", "x": 20, "y": 30, "width": 900, "height": 1500,
             "color": "navy", "fill": True},
        ],
    }
    svg = render_scene_svg(scene, {"width": 1000, "height": 1778})
    assert 'width="1080" height="1920"' in svg
    assert 'height="1778" fill="#FFFFFF"' in svg
    assert 'fill="#DEE7F2"' in svg
