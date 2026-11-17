from finance_campus.script_quality import validate_script


def valid_script():
    return {
        "title": "Why an emergency fund matters",
        "sections": {
            "relatable_financial_problem": "An unexpected repair can disrupt a tight household budget.",
            "escalating_real_world_stakes": (
                "Without savings, the household may borrow and face interest costs."
            ),
            "clear_explanation_of_why_it_matters": (
                "Debt repayments can reduce money available for essential expenses."
            ),
            "hopeful_and_realistic_possibility": (
                "A small, consistent savings habit can build a useful buffer over time."
            ),
            "practical_action_viewers_can_take": (
                "Review one expense and set aside an affordable amount this week."
            ),
            "empowering_close": (
                "Start where you are; a first step is still progress."
            ),
        },
        "claims": [
            {
                "text": "Borrowing can involve interest and fees.",
                "sources": ["https://www.consumerfinance.gov/"],
            }
        ],
        "hypothetical_examples": [
            {
                "label": "Hypothetical example",
                "text": "Imagine a household setting aside a small amount each week."
            }
        ],
    }


def test_complete_action_driven_script_passes():
    report = validate_script(valid_script())
    assert report.passed is True
    assert report.errors == []


def test_financial_hardship_and_urgency_are_allowed():
    script = valid_script()
    script["sections"]["relatable_financial_problem"] = (
        "Poverty, unstable income and financial insecurity can make emergencies harder."
    )
    script["sections"]["escalating_real_world_stakes"] = (
        "A missed payment may lead to fees and more pressure on an already tight budget."
    )
    report = validate_script(script)
    assert report.passed is True


def test_missing_hope_or_action_blocks_script():
    script = valid_script()
    script["sections"]["hopeful_and_realistic_possibility"] = ""
    report = validate_script(script)
    assert report.passed is False
    assert any("hopeful_and_realistic_possibility" in error for error in report.errors)


def test_guaranteed_wealth_claim_blocks_script():
    script = valid_script()
    script["sections"]["empowering_close"] = "This method guarantees wealth."
    report = validate_script(script)
    assert report.passed is False
    assert any("guaranteed-outcome" in error for error in report.errors)


def test_shaming_language_blocks_script():
    script = valid_script()
    script["sections"]["relatable_financial_problem"] = "Poverty is your fault."
    report = validate_script(script)
    assert report.passed is False
    assert any("Shaming language" in error for error in report.errors)


def test_unsourced_claim_blocks_script():
    script = valid_script()
    script["claims"][0]["sources"] = []
    report = validate_script(script)
    assert report.passed is False
    assert any("no supporting source" in error for error in report.errors)


def test_invalid_source_url_blocks_script():
    script = valid_script()
    script["claims"][0]["sources"] = ["not-a-url"]
    report = validate_script(script)
    assert report.passed is False
    assert any("invalid source URL" in error for error in report.errors)


def test_unlabelled_hypothetical_example_blocks_script():
    script = valid_script()
    script["hypothetical_examples"][0]["label"] = "Example"
    report = validate_script(script)
    assert report.passed is False
    assert any("labelled hypothetical" in error for error in report.errors)


def test_non_object_script_is_rejected():
    report = validate_script("not a script")
    assert report.passed is False
    assert "Script package must be a JSON object" in report.errors
