"""Cash-versus-liability and annual funding guardrails."""
import math
import random
from pathlib import Path

from farm_strategy.model import one_path, read_config, read_weather, simulate
from farm_strategy.cashflow import nominal_to_real

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_config(ROOT / "configs/base.json")
WEATHER = read_weather(ROOT / "data/processed/annual_weather.csv")


def test_outstanding_principal_is_not_fictitious_2036_cash_outflow():
    path = one_path("new_cucumber_house", "base", WEATHER, CONFIG, random.Random(8))
    terminal = path["years"][-1]
    assert terminal["debt_end"] == 2400
    assert math.isclose(
        terminal["equity_cash"],
        terminal["project_cash"] + terminal["loan_draw"] - terminal["loan_payment"],
    )
    assert path["equity_terminal_liability_adjusted_npv"] < path["equity_npv"]
    terminal_real = nominal_to_real(terminal["debt_end"], 2036, CONFIG["finance"])
    pv = terminal_real / (1 + CONFIG["finance"]["real_discount_rate"]) ** 9
    assert math.isclose(
        path["equity_npv"] - path["equity_terminal_liability_adjusted_npv"], pv
    )


def test_annual_starting_cash_requirement_is_nonnegative_and_reproducible():
    path = one_path("new_cucumber_house", "base", WEATHER, CONFIG, random.Random(12))
    totals = []
    balance = 0.0
    for year in path["years"]:
        balance += year["equity_cash"]
        totals.append(balance)
    assert math.isclose(
        path["annual_liquidity_buffer_required"],
        max(0, -min(totals)),
    )
    result = simulate("new_cucumber_house", "base", WEATHER, CONFIG, paths=8, seed=8)
    assert "annual_liquidity_buffer_required" in result["metrics"]
    assert "equity_terminal_liability_adjusted_npv" in result["metrics"]
    assert "monthly" in result["data_quality"]["liquidity"]
