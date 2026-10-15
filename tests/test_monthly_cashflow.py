"""Monthly liquidity, cash reconciliation, and nominal/real financing regressions."""
from copy import deepcopy
import math
import random
from pathlib import Path

import pytest

from farm_strategy.cashflow import nominal_to_real, validate_cashflow_config
from farm_strategy.model import PLANS, one_path, read_config, read_weather, simulate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_config(ROOT / "configs/base.json")
WEATHER = read_weather(ROOT / "data/processed/annual_weather.csv")
CASH_KEYS = ("revenue", "cash_cost", "capex", "project_cash",
             "loan_draw", "loan_payment", "equity_cash")


@pytest.mark.parametrize("plan", PLANS)
def test_120_monthly_cash_entries_reconcile_all_annual_totals(plan):
    path = one_path(plan, "base", WEATHER, CONFIG, random.Random(21),
                    include_months=True)
    months = path["months"]
    assert len(months) == 120
    assert [(m["year"], m["month"]) for m in months] == [
        (y, month) for y in range(2027, 2037) for month in range(1, 13)
    ]
    for year in path["years"]:
        matching = [m for m in months if m["year"] == year["year"]]
        for key in CASH_KEYS:
            assert math.isclose(sum(m[key] for m in matching), year[key],
                                rel_tol=1e-10, abs_tol=1e-7), (plan, year["year"], key)
    annual_end_balances = [m["cumulative_equity_cash"] for m in months
                           if m["month"] == 12]
    all_month_end_balances = [m["cumulative_equity_cash"] for m in months]
    assert math.isclose(path["annual_liquidity_buffer_required"],
                        max(0, -min(annual_end_balances)), abs_tol=1e-7)
    assert math.isclose(path["monthly_liquidity_buffer_required"],
                        max(0, -min(all_month_end_balances)), abs_tol=1e-7)
    assert path["monthly_liquidity_buffer_required"] + 1e-7 >= (
        path["annual_liquidity_buffer_required"])


def test_greenhouse_monthly_capex_and_nominal_vs_real_draw():
    path = one_path("new_cucumber_house", "base", WEATHER, CONFIG, random.Random(4),
                    include_months=True)
    fy = CONFIG["finance"]
    y2028 = next(y for y in path["years"] if y["year"] == 2028)
    march = next(m for m in path["months"] if (m["year"], m["month"]) == (2028, 3))
    december = next(m for m in path["months"] if (m["year"], m["month"]) == (2028, 12))
    assert march["capex"] == fy["new_house_capex"]
    assert y2028["loan_draw_nominal"] == CONFIG["loan"]["principal"] == 3000
    assert math.isclose(march["loan_draw"],
                        nominal_to_real(3000, 2028, fy), abs_tol=1e-9)
    assert math.isclose(december["loan_payment"],
                        nominal_to_real(45, 2028, fy), abs_tol=1e-9)
    assert all(m["loan_payment"] == 0 for m in path["months"]
               if m["year"] == 2028 and m["month"] != 12)
    assert math.isclose(y2028["equity_cash"],
                        y2028["project_cash"] + y2028["loan_draw"]
                        - y2028["loan_payment"], abs_tol=1e-7)
    terminal = path["years"][-1]
    assert terminal["debt_end"] == 2400  # nominal liability
    assert math.isclose(terminal["debt_end_2026_real"],
                        nominal_to_real(2400, 2036, fy), abs_tol=1e-9)


def test_zero_inflation_matches_nominal_debt_cash_and_discounted_liability():
    cfg = deepcopy(CONFIG)
    cfg["finance"]["assumed_annual_inflation_rate"] = 0
    path = one_path("new_cucumber_house", "base", WEATHER, cfg, random.Random(11))
    y2028 = path["years"][1]
    assert y2028["loan_draw"] == y2028["loan_draw_nominal"] == 3000
    assert y2028["loan_payment"] == y2028["loan_payment_nominal"] == 45
    assert math.isclose(
        path["equity_npv"] - path["equity_terminal_liability_adjusted_npv"],
        2400 / 1.05 ** 9, abs_tol=1e-7)


def test_monthly_details_opt_in_and_seed_reproducible():
    result = simulate("leased_cucumber_house", "base", WEATHER, CONFIG,
                      seed=42, paths=8, include_monthly_details=True)
    assert "monthly_liquidity_buffer_required" in result["metrics"]
    example = result["illustrative_monthly_path"]
    assert len(example["months"]) == 120
    assert "NOT the Monte Carlo median" in example["warning"]
    assert result == simulate("leased_cucumber_house", "base", WEATHER, CONFIG,
                              seed=42, paths=8, include_monthly_details=True)
    without = simulate("leased_cucumber_house", "base", WEATHER, CONFIG,
                       seed=42, paths=8)
    assert "illustrative_monthly_path" not in without
    assert result["metrics"] == without["metrics"]


def test_monthly_timing_and_inflation_config_reject_invalid_values():
    cfg = deepcopy(CONFIG)
    cfg["monthly_cashflow"]["potato_sales"][5] = 2
    with pytest.raises(ValueError, match="monthly allocation weights"):
        validate_cashflow_config(cfg["finance"], cfg["monthly_cashflow"])
    cfg = deepcopy(CONFIG)
    cfg["monthly_cashflow"]["loan_draw_month"] = 13
    with pytest.raises(ValueError, match="Invalid month"):
        validate_cashflow_config(cfg["finance"], cfg["monthly_cashflow"])
    cfg = deepcopy(CONFIG)
    cfg["finance"]["assumed_annual_inflation_rate"] = -1
    with pytest.raises(ValueError, match="inflation"):
        validate_cashflow_config(cfg["finance"], cfg["monthly_cashflow"])
