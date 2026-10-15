"""Paired five-plan screening: deterministic shocks and model-only risk."""
import csv
import random
from pathlib import Path

import pytest

from farm_strategy.comparison import compare_plans, save_comparison_csv
from farm_strategy.model import PLANS, SCENARIOS, one_path, read_config, read_weather

ROOT = Path(__file__).resolve().parents[1]
CFG = read_config(ROOT / "configs/base.json")
WX = read_weather(ROOT / "data/processed/annual_weather.csv")
POOL = [row for row in WX if row["year"] >= 2016]


def test_weather_draws_stay_paired_across_plans_and_scenarios():
    sampled = []
    for plan, scenario in (("field_trial", "base"),
                           ("pause_after_trial", "severe_damage"),
                           ("new_cucumber_house", "base"),
                           ("leased_cucumber_house", "price_down_15"),
                           ("new_cucumber_premium", "wage_up_30")):
        result = one_path(plan, scenario, POOL, CFG, random.Random(808))
        sampled.append([row["sampled_weather_year"] for row in result["years"]])
    assert all(sequence == sampled[0] for sequence in sampled)


def test_all_plans_share_identical_first_year_field_draws():
    values = [
        one_path(plan, "base", POOL, CFG, random.Random(31))["years"][0]
        for plan in PLANS
    ]
    for row in values[1:]:
        assert row["revenue"] == values[0]["revenue"]
        assert row["cash_cost"] == values[0]["cash_cost"]
        assert row["project_cash"] == values[0]["project_cash"]


def test_compare_is_reproducible_and_paired_vs_field_baseline():
    a = compare_plans(WX, CFG, seed=8, paths=8)
    b = compare_plans(WX, CFG, seed=8, paths=8)
    assert a == b
    assert a["comparison_method"] == "PAIRED_COMMON_RANDOM_NUMBERS"
    assert [x["plan"] for x in a["runs"]] == list(PLANS)
    assert len(a["scenarios"]) == 1
    base = a["scenarios"][0]
    assert len(base["paired_deltas_vs_field_trial"]) == len(PLANS) - 1
    assert sorted(base["illustrative_order_by_economic_npv_median"]) == sorted(PLANS)
    assert a["evidence_status"]["transaction_T"].startswith("NONE")

    rng = random.Random(8)
    trial_seeds = [rng.getrandbits(64) for _ in range(8)]
    manual = [
        one_path("leased_cucumber_house", "base", POOL, CFG,
                 random.Random(s))["economic_npv"]
        - one_path("field_trial", "base", POOL, CFG,
                   random.Random(s))["economic_npv"]
        for s in trial_seeds
    ]
    manual.sort()
    expected = round((manual[3] + manual[4]) / 2, 2)
    paired = next(x for x in base["paired_deltas_vs_field_trial"]
                  if x["plan"] == "leased_cucumber_house")
    assert paired["paired_delta"]["economic_npv"]["median"] == expected


def test_stress_matrix_is_complete_and_price_down_has_no_upside_for_same_shocks():
    r = compare_plans(WX, CFG, seed=45, paths=5, stress_matrix=True)
    assert len(r["scenarios"]) == len(SCENARIOS)
    cases = {x["scenario"]: x for x in r["scenarios"]}
    assert sorted(cases) == sorted(SCENARIOS)
    for plan in PLANS:
        ordinary = next(x for x in cases["base"]["runs"] if x["plan"] == plan)
        down = next(x for x in cases["price_down_15"]["runs"]
                    if x["plan"] == plan)
        assert down["metrics"]["project_npv"]["median"] <= (
            ordinary["metrics"]["project_npv"]["median"])


def test_model_only_downside_and_cash_buffers_reported_for_every_strategy():
    result = compare_plans(WX, CFG, seed=29, paths=5)
    for row in result["runs"]:
        metrics = row["metrics"]
        assert metrics["monthly_liquidity_buffer_required"]["p90"] >= (
            metrics["annual_liquidity_buffer_required"]["p90"])
        assert metrics["monthly_liquidity_buffer_required"]["p10"] >= 0
        for key in ("project_npv", "economic_npv",
                    "equity_terminal_liability_adjusted_npv",
                    "cash_2030_after_debt"):
            share = metrics[key]["negative_fraction_model_only"]
            assert 0 <= share <= 1


def test_flat_csv_exports_exact_one_row_per_scenario_and_plan(tmp_path):
    result = compare_plans(WX, CFG, seed=2, paths=3, stress_matrix=True)
    dest = tmp_path / "comparison" / "screening.csv"
    save_comparison_csv(result, dest)
    with dest.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(SCENARIOS) * len(PLANS)
    assert {row["scenario"] for row in rows} == set(SCENARIOS)
    assert {row["plan"] for row in rows} == set(PLANS)
    assert all(row["monthly_liquidity_buffer_required_p90"] for row in rows)
    assert all(row["economic_npv_negative_fraction_model_only"] for row in rows)


@pytest.mark.parametrize("paths", [0, -1, 1.5, True, 100001])
def test_invalid_path_counts_rejected(paths):
    with pytest.raises(ValueError, match="paths"):
        compare_plans(WX, CFG, paths=paths)


def test_unknown_scenario_and_window_rejected():
    with pytest.raises(ValueError, match="Unknown scenario"):
        compare_plans(WX, CFG, scenario="not-a-scenario")
    with pytest.raises(ValueError, match="window"):
        compare_plans(WX, CFG, window="not-a-window")
