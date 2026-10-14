"""Smoke and accounting invariants. Not empirical model calibration."""
from pathlib import Path
import math
from farm_strategy.model import (
    PLANS, read_config, read_weather, loan_cash,
    month_labor, simulate, one_path, weather_loss,
)
import random

ROOT = Path(__file__).resolve().parents[1]
CFG = read_config(ROOT / "configs/base.json")
WX = read_weather(ROOT / "data/processed/annual_weather.csv")

def test_observed_year_coverage():
    assert [int(x["year"]) for x in WX] == list(range(2006, 2026))

def test_loan_grace_and_outstanding():
    l = CFG["loan"]
    assert loan_cash(2027, l) == (0, 0, 0)
    assert loan_cash(2028, l) == (3000, 45, 3000)
    draw, pay, debt = loan_cash(2033, l)
    assert draw == 0 and pay == 195 and debt == 2850
    assert loan_cash(2036, l)[2] == 2400

def test_greenhouse_labor_is_not_in_2027():
    trial = one_path("new_cucumber_house", "base", WX, CFG, random.Random(1))
    first = trial["years"][0]
    assert first["loan_draw"] == 0
    assert first["loan_payment"] == 0
    assert first["hired_hours"] == month_labor(CFG["finance"], False)[1]
    assert trial["years"][1]["capex"] > 5000

def test_owner_labor_is_not_cash_expense():
    trial = one_path("field_trial", "base", WX, CFG, random.Random(2))
    y = trial["years"][2]
    assert y["owner_hours"] > 0
    assert math.isclose(y["project_cash"], y["revenue"] - y["cash_cost"] - y["capex"])
    assert trial["economic_npv"] < trial["project_npv"]

def test_lease_deposit_returned_at_end():
    case = one_path("leased_cucumber_house", "base", WX, CFG, random.Random(3))
    assert case["years"][1]["capex"] == CFG["finance"]["rent_deposit"] + CFG["finance"]["rent_fitout"]
    assert case["years"][-1]["debt_end"] == 0

def test_paused_after_2027_no_repeated_field_hours():
    case = one_path("pause_after_trial", "base", WX, CFG, random.Random(3))
    assert all(y["owner_hours"] == 0 and y["hired_hours"] == 0
               for y in case["years"][1:])

def test_same_seed_reproducible():
    a = simulate("new_cucumber_house", "base", WX, CFG, seed=47, paths=80)
    b = simulate("new_cucumber_house", "base", WX, CFG, seed=47, paths=80)
    assert a == b

def test_severe_weather_not_more_profitable_in_same_seed():
    a = simulate("new_cucumber_house", "weak_damage", WX, CFG, seed=5, paths=100)
    b = simulate("new_cucumber_house", "severe_damage", WX, CFG, seed=5, paths=100)
    assert a["metrics"]["project_npv"]["median"] >= b["metrics"]["project_npv"]["median"]

def test_cashflow_and_project_npv_financing_separate():
    case = one_path("new_cucumber_house", "base", WX, CFG, random.Random(4))
    y = case["years"][1]
    assert math.isclose(y["equity_cash"],
                        y["project_cash"] + y["loan_draw"] - y["loan_payment"])
    assert case["debt_end"] == 2400
    assert case["project_npv"] != case["equity_npv"]

def test_model_does_not_claim_measured_pest_or_prices():
    result = simulate("field_trial", "base", WX, CFG, paths=4)
    assert "UNVALIDATED" in result["data_quality"]["pest"]
    assert "KAMIS excluded" in result["data_quality"]["price"]
    assert CFG["tax_and_insurance"]["status"].startswith("UNKNOWN")

def test_weather_loss_bounded():
    for w in WX:
        assert all(0 <= x <= .6 for x in weather_loss(w, 2.0))
