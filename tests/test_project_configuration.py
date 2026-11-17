from finance_campus.config import (
    load_yaml,
    validate_branding,
    validate_disclaimer,
    validate_settings,
)


def test_brand_configuration_passes():
    assert validate_branding(load_yaml("config/branding.yaml")) == []


def test_disclaimer_configuration_passes():
    assert validate_disclaimer(load_yaml("config/disclaimer.yaml")) == []


def test_publishing_starts_disabled():
    settings = load_yaml("config/settings.yaml")
    assert settings["production"]["publishing_enabled"] is False
    assert settings["platforms"]["youtube"]["enabled"] is False
    assert settings["platforms"]["tiktok"]["enabled"] is False



def test_operational_settings_pass_release_safety_validation():
    assert validate_settings(load_yaml("config/settings.yaml")) == []


def test_operational_settings_reject_early_publishing_activation():
    settings = load_yaml("config/settings.yaml")
    settings["production"]["publishing_enabled"] = True
    assert any("Publishing must remain disabled" in error for error in validate_settings(settings))


def test_operational_settings_reject_non_kokoro_narration():
    settings = load_yaml("config/settings.yaml")
    settings["audio"]["provider"] = "other"
    assert any("Kokoro" in error for error in validate_settings(settings))


def test_operational_settings_require_visual_review_until_semantic_qc_exists():
    settings = load_yaml("config/settings.yaml")
    settings["automation"]["require_routine_human_approval"] = False
    assert any("Human visual review" in error for error in validate_settings(settings))
