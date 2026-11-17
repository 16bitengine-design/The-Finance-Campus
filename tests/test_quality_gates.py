from finance_campus.quality_gates import validate_video_package


def test_missing_disclaimer_blocks_video():
    report = validate_video_package(
        sources=["https://example.org/source"],
        spoken_disclaimer_present=True,
        on_screen_disclaimer_present=False,
        description_disclaimer_present=True,
        brand_validation_passed=True,
        script_validation_passed=True,
        audio_validation_passed=True,
        video_validation_passed=True,
    )
    assert report.passed is False
    assert "On-screen disclaimer is missing" in report.errors


def test_complete_package_passes():
    report = validate_video_package(
        sources=["https://example.org/source"],
        spoken_disclaimer_present=True,
        on_screen_disclaimer_present=True,
        description_disclaimer_present=True,
        brand_validation_passed=True,
        script_validation_passed=True,
        audio_validation_passed=True,
        video_validation_passed=True,
    )
    assert report.passed is True
    assert report.errors == []


def test_script_editorial_failure_blocks_video():
    report = validate_video_package(
        sources=["https://example.org/source"],
        spoken_disclaimer_present=True,
        on_screen_disclaimer_present=True,
        description_disclaimer_present=True,
        brand_validation_passed=True,
        script_validation_passed=False,
        audio_validation_passed=True,
        video_validation_passed=True,
    )
    assert report.passed is False
    assert "Script editorial validation failed" in report.errors
