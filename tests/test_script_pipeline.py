import json

from finance_campus.script_pipeline import prepare_script
from finance_campus.script_quality import validate_script


def candidate():
    return {
        "title": "A practical first step toward an emergency fund",
        "sections": {
            "relatable_financial_problem": (
                "An unexpected expense can be frightening when money is already tight."
            ),
            "escalating_real_world_stakes": (
                "Without a buffer, a household may need expensive borrowing."
            ),
            "clear_explanation_of_why_it_matters": (
                "Interest and repayments can make future budgets harder to manage."
            ),
            "hopeful_and_realistic_possibility": (
                "A small amount saved regularly can begin building a financial cushion."
            ),
            "practical_action_viewers_can_take": (
                "Choose an affordable amount and set it aside this week."
            ),
            "empowering_close": (
                "You can start small and build the habit one step at a time."
            ),
        },
        "claims": [],
        "hypothetical_examples": [],
    }


def test_prepare_script_writes_valid_candidate(tmp_path):
    output = tmp_path / "approved" / "script.json"
    result = prepare_script(candidate(), output)
    assert result.approved is True
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == candidate()


def test_prepare_script_rejects_invalid_candidate_without_output(tmp_path):
    output = tmp_path / "approved.json"
    invalid = candidate()
    invalid["sections"]["practical_action_viewers_can_take"] = ""
    result = prepare_script(invalid, output)
    assert result.approved is False
    assert not output.exists()
    assert result.output_path is None


def test_prepare_script_does_not_overwrite_existing_approved_file(tmp_path):
    output = tmp_path / "approved.json"
    output.write_text('{"previous": "approved"}', encoding="utf-8")
    invalid = candidate()
    invalid["sections"]["empowering_close"] = "Get rich overnight."
    result = prepare_script(invalid, output)
    assert result.approved is False
    assert json.loads(output.read_text(encoding="utf-8")) == {"previous": "approved"}


def test_pipeline_validator_and_direct_validator_agree(tmp_path):
    script = candidate()
    direct = validate_script(script)
    result = prepare_script(script, tmp_path / "approved.json")
    assert result.approved is direct.passed
