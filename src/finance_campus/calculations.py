"""Transparent calculators for illustrative personal-finance education.

All rates are entered as decimals (for example, 0.12 for 12%). Loan APR is
treated as a nominal annual rate divided into monthly periods. Savings deposits
are assumed to occur at the end of each month.
"""
from __future__ import annotations

import math


def _non_negative(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be a finite, non-negative number")
    return number


def compound_growth(principal: float, annual_rate: float, years: float,
                    compounds_per_year: int = 12) -> dict[str, float]:
    """Calculate compound growth with periodic compounding."""
    principal = _non_negative("principal", principal)
    annual_rate = _non_negative("annual_rate", annual_rate)
    years = _non_negative("years", years)
    if not isinstance(compounds_per_year, int) or compounds_per_year < 1:
        raise ValueError("compounds_per_year must be a positive integer")
    periods = compounds_per_year * years
    final_value = principal * (1 + annual_rate / compounds_per_year) ** periods
    return {
        "principal": principal,
        "interest_earned": final_value - principal,
        "final_value": final_value,
    }


def monthly_loan_payment(principal: float, annual_rate: float,
                         months: int) -> dict[str, float]:
    """Calculate fixed monthly payment and total interest for a fully amortizing loan."""
    principal = _non_negative("principal", principal)
    annual_rate = _non_negative("annual_rate", annual_rate)
    if not isinstance(months, int) or months < 1:
        raise ValueError("months must be a positive integer")
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        payment = principal / months
    else:
        factor = (1 + monthly_rate) ** months
        payment = principal * monthly_rate * factor / (factor - 1)
    total_paid = payment * months
    return {
        "monthly_payment": payment,
        "total_paid": total_paid,
        "total_interest": total_paid - principal,
    }


def inflation_adjusted_value(amount: float, annual_inflation: float,
                             years: float) -> dict[str, float]:
    """Estimate the future purchasing power of today's amount under steady inflation."""
    amount = _non_negative("amount", amount)
    annual_inflation = _non_negative("annual_inflation", annual_inflation)
    years = _non_negative("years", years)
    real_value = amount / ((1 + annual_inflation) ** years)
    return {
        "today_amount": amount,
        "future_purchasing_power": real_value,
        "purchasing_power_lost": amount - real_value,
    }


def monthly_savings_plan(target: float, annual_rate: float,
                         months: int) -> dict[str, float]:
    """Calculate equal end-of-month deposits needed to reach a target.

    The rate is an illustrative effective annual return converted to an
    equivalent monthly rate. Returns are not guaranteed.
    """
    target = _non_negative("target", target)
    annual_rate = _non_negative("annual_rate", annual_rate)
    if not isinstance(months, int) or months < 1:
        raise ValueError("months must be a positive integer")
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
    if monthly_rate == 0:
        deposit = target / months
    else:
        deposit = target * monthly_rate / ((1 + monthly_rate) ** months - 1)
    return {
        "monthly_deposit": deposit,
        "total_deposits": deposit * months,
        "illustrative_growth": target - deposit * months,
    }
