"""Paired Monte Carlo screening of five existing hypothetical farm plans.

Plans and stress scenarios share path-specific weather/price/pest/repair streams.
Results describe ASSUMPTION-BASED sensitivity, never calibrated odds or a
recommendation to borrow, construct or plant.
"""
import csv
import math
import random
from pathlib import Path

from .cashflow import validate_cashflow_config
from .model import PLANS, SCENARIOS, one_path
from .sampling import choose_pool, quantile

BASELINE_PLAN = "field_trial"
KPI_KEYS = (
    "project_npv", "economic_npv", "equity_npv",
    "equity_terminal_liability_adjusted_npv",
    "monthly_liquidity_buffer_required",
    "annual_liquidity_buffer_required", "cash_2030_after_debt",
    "hired_hours_2030", "debt_end",
)
DELTA_KEYS = (
    "project_npv", "economic_npv",
    "equity_terminal_liability_adjusted_npv",
    "monthly_liquidity_buffer_required",
)
RISK_KEYS = ("project_npv", "economic_npv",
             "equity_terminal_liability_adjusted_npv",
             "cash_2030_after_debt")


def describe(values, negative_fraction=False, positive_fraction=False):
    if not values:
        raise ValueError("No observations available to summarize")
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("Nonfinite values cannot be used in comparison")
    item = {
        "p10": round(quantile(values, 0.10), 2),
        "median": round(quantile(values, 0.50), 2),
        "p90": round(quantile(values, 0.90), 2),
    }
    if negative_fraction:
        item["negative_fraction_model_only"] = round(
            sum(v < 0 for v in values) / len(values), 4)
    if positive_fraction:
        item["positive_fraction_model_only"] = round(
            sum(v > 0 for v in values) / len(values), 4)
    return item


def compare_plans(weather, config, *, seed=42, paths=1000, scenario="base",
                  window="recent10", stress_matrix=False):
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    if not isinstance(paths, int) or isinstance(paths, bool) or not 1 <= paths <= 100000:
        raise ValueError("paths must be 1–100,000")
    pool = choose_pool(weather, window)
    validate_cashflow_config(config["finance"], config["monthly_cashflow"])
    cases = SCENARIOS if stress_matrix else (scenario,)
    # Generate a fresh common seed per trial, reused by all plans/scenarios.
    # This also avoids RNG stream drift caused by any future variable numbers
    # of random draws in a different *trial*.
    generator = random.Random(seed)
    trial_seeds = [generator.getrandbits(64) for _ in range(paths)]

    cases_out = []
    for case in cases:
        vectors = {plan: {key: [] for key in KPI_KEYS} for plan in PLANS}
        delta_vectors = {
            plan: {key: [] for key in DELTA_KEYS}
            for plan in PLANS if plan != BASELINE_PLAN
        }

        for trial_seed in trial_seeds:
            trial = {
                plan: one_path(plan, case, pool, config, random.Random(trial_seed))
                for plan in PLANS
            }
            for plan in PLANS:
                for key in KPI_KEYS:
                    vectors[plan][key].append(trial[plan][key])
            baseline = trial[BASELINE_PLAN]
            for plan in delta_vectors:
                for key in DELTA_KEYS:
                    delta_vectors[plan][key].append(trial[plan][key] - baseline[key])

        runs = []
        for plan in PLANS:
            runs.append({
                "plan": plan, "scenario": case, "seed": seed, "paths": paths,
                "window": window,
                "metrics": {
                    key: describe(vectors[plan][key], negative_fraction=key in RISK_KEYS)
                    for key in KPI_KEYS
                },
            })

        paired = []
        for plan in delta_vectors:
            paired.append({
                "plan": plan, "baseline": BASELINE_PLAN,
                "paired_delta": {
                    key: describe(delta_vectors[plan][key],
                                  positive_fraction=(key != "monthly_liquidity_buffer_required"))
                    for key in DELTA_KEYS
                },
            })

        order = [
            row["plan"] for row in sorted(
                runs,
                key=lambda r: (-r["metrics"]["economic_npv"]["median"], r["plan"]))
        ]
        cases_out.append({
            "scenario": case,
            "runs": runs,
            "paired_deltas_vs_field_trial": paired,
            "illustrative_order_by_economic_npv_median": order,
        })

    return {
        "schema_version": 1,
        "comparison_method": "PAIRED_COMMON_RANDOM_NUMBERS",
        "alignment": ("Within each path, each plan and stress scenario samples "
                      "the same weather years, price and pest shocks, and "
                      "major-repair draw. Differences reflect plan assumptions."),
        "seed": seed, "paths": paths, "window": window,
        "units": "2026-constant KRW 10,000 except hours, fractions and nominal debt_end",
        "baseline_plan": BASELINE_PLAN,
        "runs": next(c["runs"] for c in cases_out if c["scenario"] == scenario),
        "scenarios": cases_out,
        "warning": ("MODEL-ONLY sensitivity analysis, NOT observed loss odds or an "
                    "investment ranking. Crop prices, production losses, build/lease "
                    "quotes, contract dates, loan eligibility and monthly settlement "
                    "timing are not validated. NPV measures are different constructs."),
        "evidence_status": {
            "observed_O": "KMA ASOS station 146 year-level 2006-2025 features (derived)",
            "reported_R": "NONE VERIFIED for farmgate crop sale prices or loss functions",
            "transaction_T": "NONE entered for actual farm receipts or vendor quotes",
            "assumption_A": ("All crop revenues, losses, wages, build/rent costs, "
                             "monthly schedules, pest rates and nominal financing"),
        },
    }


def save_comparison_csv(result, output):
    """One row per plan/scenario with separate downside and liquidity columns."""
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = ["scenario", "plan", "paths", "seed", "window",
               "project_npv_p10", "project_npv_median", "project_npv_p90",
               "project_npv_negative_fraction_model_only",
               "economic_npv_p10", "economic_npv_median", "economic_npv_p90",
               "economic_npv_negative_fraction_model_only",
               "equity_terminal_liability_adjusted_npv_p10",
               "equity_terminal_liability_adjusted_npv_median",
               "equity_terminal_liability_adjusted_npv_negative_fraction_model_only",
               "monthly_liquidity_buffer_required_median",
               "monthly_liquidity_buffer_required_p90",
               "annual_liquidity_buffer_required_p90",
               "cash_2030_after_debt_median",
               "hired_hours_2030_median",
               "debt_end_nominal_median"]
    with dest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for case in result["scenarios"]:
            for item in case["runs"]:
                m = item["metrics"]
                writer.writerow({
                    "scenario": case["scenario"], "plan": item["plan"],
                    "paths": item["paths"], "seed": item["seed"],
                    "window": item["window"],
                    "project_npv_p10": m["project_npv"]["p10"],
                    "project_npv_median": m["project_npv"]["median"],
                    "project_npv_p90": m["project_npv"]["p90"],
                    "project_npv_negative_fraction_model_only":
                        m["project_npv"]["negative_fraction_model_only"],
                    "economic_npv_p10": m["economic_npv"]["p10"],
                    "economic_npv_median": m["economic_npv"]["median"],
                    "economic_npv_p90": m["economic_npv"]["p90"],
                    "economic_npv_negative_fraction_model_only":
                        m["economic_npv"]["negative_fraction_model_only"],
                    "equity_terminal_liability_adjusted_npv_p10":
                        m["equity_terminal_liability_adjusted_npv"]["p10"],
                    "equity_terminal_liability_adjusted_npv_median":
                        m["equity_terminal_liability_adjusted_npv"]["median"],
                    "equity_terminal_liability_adjusted_npv_negative_fraction_model_only":
                        m["equity_terminal_liability_adjusted_npv"][
                            "negative_fraction_model_only"],
                    "monthly_liquidity_buffer_required_median":
                        m["monthly_liquidity_buffer_required"]["median"],
                    "monthly_liquidity_buffer_required_p90":
                        m["monthly_liquidity_buffer_required"]["p90"],
                    "annual_liquidity_buffer_required_p90":
                        m["annual_liquidity_buffer_required"]["p90"],
                    "cash_2030_after_debt_median":
                        m["cash_2030_after_debt"]["median"],
                    "hired_hours_2030_median": m["hired_hours_2030"]["median"],
                    "debt_end_nominal_median": m["debt_end"]["median"],
                })
    return dest
