from finance_campus.branding import tokens_from_config, validate_asset_metadata
from finance_campus.config import load_yaml
from finance_campus.disclaimers import append_description_disclaimer, disclaimer_texts


def test_brand_tokens_are_centralized():
    tokens = tokens_from_config(load_yaml("config/branding.yaml"))
    assert tokens.name == "The Finance Campus"
    assert tokens.navy == "#102B55"


def test_graduation_visuals_are_rejected():
    errors = validate_asset_metadata(
        asset_type="banner",
        visual_description="Whiteboard illustration with a graduation cap and coins",
        brand_name="The Finance Campus",
    )
    assert any("Prohibited graduation imagery" in error for error in errors)


def test_wrong_brand_is_rejected():
    errors = validate_asset_metadata(
        asset_type="thumbnail",
        visual_description="Whiteboard illustration of a savings jar",
        brand_name="Another Brand",
    )
    assert "Asset brand name does not match the official brand" in errors


def test_description_disclaimer_is_added_once():
    config = load_yaml("config/disclaimer.yaml")
    texts = disclaimer_texts(config)
    result = append_description_disclaimer("A lesson about saving.", config)
    assert result.endswith(texts["description"])
    assert append_description_disclaimer(result, config) == result
