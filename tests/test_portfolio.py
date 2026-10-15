"""Full farm example: area, overlap, common scarce inputs and debt cash."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from farm_strategy.portfolio import simulate_portfolio

EXAMPLE = Path(__file__).resolve().parents[1]/"data/templates/portfolio_SYNTHETIC.json"


def sample():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_sequential_crop_rotation_avoids_simultaneous_double_use():
    r = simulate_portfolio(sample())
    assert len(r["per_crop"]) == 2
    assert r["total_usable_area_m2"] == 1200
    assert r["unallocated_area_m2"] == 200
    plot = r["land_occupancy_m2_by_plot"]["PLOT-ONE"]
    assert plot[3] == 1000 and plot[7] == 1000 and plot[6] == 0
    assert r["shared_capex_krw"] == 2000000
    assert r["financing"]["outstanding_principal_krw"] == 750000
    assert r["financing"]["interest_paid_krw"] == 50000
    assert r["weekly_labor_status"] == "COMPLETE_FOR_ENTERED_CROPS"
    assert all(x["owner_shortage"] == 2 for x in r["weekly_labor"])
    assert r["unlevered_npv_if_rate_supplied_krw"] is not None


@pytest.mark.parametrize("mutate,reason", [
 (lambda d: d["plantings"][1]["occupancies"][0].update(start_month=6), "Overlapping crop land"),
 (lambda d: d["plantings"][1]["case"].update(area_m2=1300), "exceeds its plot"),
 (lambda d: d["site"].update(usable_area_m2=500), "exceeds usable"),
 (lambda d: d["plantings"][0]["occupancies"][0].update(end_month=5), "fit its plot"),
 (lambda d: d["plantings"][0]["resources"].pop(), "Every occupied crop month"),
 (lambda d: d["plantings"][0]["resources"][0].update(water_m3=-1), "nonnegative"),
 (lambda d: d["plantings"][0]["case"].update(region="REAL"), "share region"),
 (lambda d: d["plantings"][0]["case"].update(owner_available_hours_by_month=[10]*24), "Portfolio owns"),
 (lambda d: d["plantings"][0]["case"]["facility_events"].append({
   "name":"duplicate pump","year":1,"month":1,"kind":"CAPEX",
   "amount_krw":2000000,"source_kind":"A","source_ref":"A"}), "double counting"),
 (lambda d: d["financing_events"][2].update(amount_krw=1500000), "exceeds outstanding"),
 (lambda d: d["financing_events"].pop(1), "explicit interest"),
 (lambda d: d["weekly_capacity"].append(deepcopy(d["weekly_capacity"][0])), "unique Mondays"),
 (lambda d: d["plantings"][0].update(weekly_allocations=None), "partial crop work"),
])
def test_bad_explicit_portfolio_is_rejected(mutate, reason):
    d = sample()
    mutate(d)
    with pytest.raises(ValueError, match=reason):
        simulate_portfolio(d)


def test_unknown_capacity_does_not_become_zero():
    d=sample()
    d["site"]["water_supply_m3_by_month"]=None
    d["site"]["electricity_supply_kwh_by_month"]=None
    r=simulate_portfolio(d)
    w=r["resource_and_labor_limits"]["irrigation_m3"][2]
    assert w["required"] == 10 and w["shortage"] is None


def test_water_energy_shortfall_and_total_weekly_labor():
    d=sample()
    d["site"]["water_supply_m3_by_month"][3]=5
    d["site"]["electricity_supply_kwh_by_month"][3]=12
    r=simulate_portfolio(d)
    assert r["resource_and_labor_limits"]["irrigation_m3"][3]["shortage"] == 5
    assert r["resource_and_labor_limits"]["electricity_kwh"][3]["shortage"] == 8


def test_two_plots_simultaneous_crops_share_labor_and_water():
    d=sample()
    d["site"]["usable_area_m2"]=2000
    d["plots"].append({"id":"PLOT-TWO","area_m2":1000})
    p=d["plantings"][1]
    p["plot_id"]="PLOT-TWO"
    p["occupancies"][0].update(start_month=3,end_month=6)
    p["case"]["operations"][0]["month"]=4
    p["case"]["sales"][0]["month"]=6
    p["resources"]=deepcopy(d["plantings"][0]["resources"])
    p["weekly_allocations"][0]["work_date"]="2027-04-12"
    d["weekly_capacity"]=[d["weekly_capacity"][0]]
    r=simulate_portfolio(d)
    assert r["weekly_labor"][0]["owner_required_hours"] == 20
    assert r["weekly_labor"][0]["owner_shortage"] == 12
    assert r["resource_and_labor_limits"]["irrigation_m3"][3]["required"] == 20


def test_incomplete_weekly_record_never_approves_staffing():
    d=sample()
    d["plantings"][1]["weekly_allocations"]=None
    d["weekly_capacity"]=[]
    r=simulate_portfolio(d)
    assert r["weekly_labor"] is None
    assert r["weekly_labor_status"] == "UNKNOWN_PARTIAL_WORK_DATES"


def test_finance_changes_cash_but_not_unlevered_npv():
    d=sample()
    financed=simulate_portfolio(d)
    d["financing_events"]=[]
    none=simulate_portfolio(d)
    assert financed["unlevered_npv_if_rate_supplied_krw"] == none["unlevered_npv_if_rate_supplied_krw"]
    assert financed["ending_cash_krw"]-none["ending_cash_krw"] == 700000
    assert none["financing"]["status"] == "NOT_ENTERED_UNKNOWN"
