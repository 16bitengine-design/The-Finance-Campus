from finance_campus.config import load_yaml, validate_branding, validate_disclaimer


def test_brand_configuration_passes():
    assert validate_branding(load_yaml("config/branding.yaml")) == []


def test_disclaimer_configuration_passes():
    assert validate_disclaimer(load_yaml("config/disclaimer.yaml")) == []


def test_publishing_starts_disabled():
    settings = load_yaml("config/settings.yaml")
    assert settings["production"]["publishing_enabled"] is False
    assert settings["platforms"]["youtube"]["enabled"] is False
    assert settings["platforms"]["tiktok"]["enabled"] is False
