"""Real model comparison: scenario differences, not synthetic upside multipliers."""
import copy
import json
from pathlib import Path

import pytest
from farm_strategy.option_tradeoffs import compare_operating_options

ROOT = Path(__file__).resolve().parents[1]


def cases():
    p = ROOT / "data/templates/multiyear_scenarios_SYNTHETIC.json"
    return json.loads(p.read_text(encoding="utf-8"))["cases"]


def test_compare_own_vs_lease_from_same_crop_costs_not_fake_extra_yield():
    new, leased = cases()
    x = compare_operating_options(new, leased)
    assert x["status"] == "SIMULATED_PAIRED_OPTION_DELTAS_NOT_VERIFIED_ADVANTAGE"
    d = x["deltas_alternative_minus_baseline_krw"]
    assert d["net_expected_settlement"] == 0  # no invented greenhouse yield premium
    assert d["capital_expenditure"] == -20_000_000
    assert d["operating_cash_cost"] == 3*(1_500_000-240_000)
    assert d["operating_contribution_before_owner_labor_tax_depreciation"] == -d["operating_cash_cost"]
    assert d["project_npv_if_rate_supplied"] is not None
    assert x["deltas_alternative_minus_baseline_hours"]["owner"] == 0
    assert x["deltas_alternative_minus_baseline_hours"]["peak_owner_hours_above_capacity"] is None
    assert x["source_claim_counts"]["baseline"]["A"] > 0
    assert x["source_claim_counts"]["alternative"]["A"] > 0


def test_no_npv_without_explicit_input_and_owner_value():
    a,b = cases()
    a["annual_real_discount_rate"]=None
    b["annual_real_discount_rate"]=None
    x=compare_operating_options(a,b)
    d=x["deltas_alternative_minus_baseline_krw"]
    assert d["project_npv_if_rate_supplied"] is None
    assert d["economic_npv_if_rate_and_owner_value_supplied"] is None


def test_known_peak_labor_overflow_compared_without_implicit_hiring():
    a,b=cases()
    for c in (a,b):
        c["owner_available_hours_by_month"]=[0]*36
    b["operations"][0]["owner_hours_per_10a"]+=3
    x=compare_operating_options(a,b)
    assert x["deltas_alternative_minus_baseline_hours"]["owner"] == 3
    assert x["deltas_alternative_minus_baseline_hours"]["peak_owner_hours_above_capacity"] == 3


@pytest.mark.parametrize("key,value", [
    ("crop","OTHER CROP"), ("region","OTHER REGION"), ("area_m2",1100),
    ("start_year",2028), ("horizon_years",4),
    ("annual_real_discount_rate",.12), ("owner_hour_value_krw",10000),
    ("owner_available_hours_by_month",[12]*36),
])
def test_refuses_unlike_farm_systems(key,value):
    a,b=cases()
    b[key]=value
    with pytest.raises(ValueError,match="same assumptions"):
        compare_operating_options(a,b)


def test_refuses_same_identity():
    a,b=cases()
    b["id"]=a["id"]
    with pytest.raises(ValueError,match="distinct IDs"):
        compare_operating_options(a,b)
