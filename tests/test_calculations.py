import pytest

from finance_campus.calculations import (
    compound_growth,
    inflation_adjusted_value,
    monthly_loan_payment,
    monthly_savings_plan,
)


def test_compound_growth_zero_rate_and_positive_rate():
    assert compound_growth(1000, 0, 2)["final_value"] == 1000
    result = compound_growth(1000, 0.12, 1, 12)
    assert result["final_value"] == pytest.approx(1126.825)
    assert result["interest_earned"] == pytest.approx(126.825, abs=0.01)


def test_zero_interest_loan_payment():
    result = monthly_loan_payment(1200, 0, 12)
    assert result["monthly_payment"] == 100
    assert result["total_interest"] == 0


def test_interest_bearing_loan_has_consistent_totals():
    result = monthly_loan_payment(1_000_000, 0.12, 12)
    assert result["monthly_payment"] > 88_333
    assert result["total_paid"] == pytest.approx(
        result["monthly_payment"] * 12
    )
    assert result["total_interest"] > 0


def test_inflation_reduces_purchasing_power():
    result = inflation_adjusted_value(1000, 0.10, 2)
    assert result["future_purchasing_power"] == pytest.approx(826.44628)
    assert result["purchasing_power_lost"] > 0


def test_savings_plan_zero_rate():
    result = monthly_savings_plan(1200, 0, 12)
    assert result["monthly_deposit"] == 100
    assert result["illustrative_growth"] == 0


def test_savings_plan_reaches_target_mathematically():
    result = monthly_savings_plan(10_000, 0.06, 12)
    assert result["monthly_deposit"] * 12 + result["illustrative_growth"] == pytest.approx(10_000)


@pytest.mark.parametrize(
    "call",
    [
        lambda: compound_growth(-1, 0.1, 2),
        lambda: compound_growth(100, float("nan"), 2),
        lambda: monthly_loan_payment(100, -0.1, 12),
        lambda: monthly_loan_payment(100, 0.1, 0),
        lambda: inflation_adjusted_value(100, 0.1, -2),
        lambda: monthly_savings_plan(100, 0.1, 0),
    ],
)
def test_invalid_inputs_are_rejected(call):
    with pytest.raises(ValueError):
        call()
