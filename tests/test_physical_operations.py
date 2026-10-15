"""Physical farm execution and amortization are independently auditable."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from farm_strategy.physical_operations import assess_daily_farm, amortization_events

SAMPLE=Path(__file__).resolve().parents[1]/"data/templates/physical_operations_SYNTHETIC.json"


def load():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_daily_stage_reconciles_monthly_resources_and_loan_repayment():
    d=load()
    x=assess_daily_farm(d["portfolio"],d["detail"])
    assert x["crop_count"]==2
    assert x["growth_stage_count"]==8
    assert x["date_turnarounds"][0]["free_days_between"]==31
    assert x["days_with_unknown_pump_capacity"]==0
    assert x["days_exceeding_pump_window"]==[]
    assert x["days_exceeding_peak_kw"]==[]
    assert x["loan_schedule"]["maturity_extends_beyond_horizon"] is False
    assert x["financing_summary"]["outstanding_principal_krw"]==pytest.approx(0,abs=1e-6)
    assert x["financing_summary"]["interest_paid_krw"]>0
    assert x["financed_ending_cash_krw"]!=x["base_ending_cash_krw"]


def test_loan_grace_and_real_interest_monthly_no_fictional_rate():
    d=load()
    t=d["detail"]["loan_terms"]
    x=amortization_events(d["portfolio"]["site"],t)
    events=x["events"]
    assert len([e for e in events if e["kind"]=="DRAW"])==1
    assert len([e for e in events if e["kind"]=="INTEREST"])==14
    assert len([e for e in events if e["kind"]=="PRINCIPAL"])==12
    assert events[0]["month"]==2
    assert events[1]["month"]==3
    assert events[1]["amount_krw"]==pytest.approx(1000000*.04/12)
    first_principal=next(e for e in events if e["kind"]=="PRINCIPAL")
    assert first_principal["month"]==5
    assert first_principal["amount_krw"]==pytest.approx(1000000/12)


def test_maturity_beyond_horizon_not_fictional_bullet_payoff():
    d=load()
    d["detail"]["loan_terms"]["equal_principal_repayment_months"]=120
    x=assess_daily_farm(d["portfolio"],d["detail"])
    assert x["loan_schedule"]["maturity_extends_beyond_horizon"]
    assert x["financing_summary"]["outstanding_principal_krw"]>0


def test_unmeasured_peak_capacities_stay_unknown():
    d=load()
    d["detail"]["site_peak_limits"].update(
        pump_capacity_m3_per_hour=None,
        pumping_hours_available_per_day=None,
        simultaneous_electric_capacity_kw=None)
    x=assess_daily_farm(d["portfolio"],d["detail"])
    assert x["days_with_unknown_pump_capacity"]==len(x["daily_capacity"])
    assert x["days_with_unknown_electric_peak_capacity"]==len(x["daily_capacity"])


def test_shortage_detected_even_with_monthly_water_energy_supply_sufficient():
    d=load()
    d["detail"]["site_peak_limits"].update(
        pump_capacity_m3_per_hour=.01,
        pumping_hours_available_per_day=1,
        simultaneous_electric_capacity_kw=.5)
    x=assess_daily_farm(d["portfolio"],d["detail"])
    assert x["days_exceeding_pump_window"]
    assert x["days_exceeding_peak_kw"]
    # Monthly m3/kWh remain the unchanged portfolio amounts.
    assert x["growth_stage_count"]==8


@pytest.mark.parametrize("change,reason",[
    (lambda d:d["detail"]["stage_demands"][0].update(water_m3_per_day=.1),"reconcile"),
    (lambda d:d["detail"]["stage_demands"][0].update(start_date="2027-02-28"),"outside actual planted"),
    (lambda d:d["detail"]["stage_demands"][0].update(concurrent_peak_kw=-1),"nonnegative"),
    (lambda d:d["detail"]["stage_demands"][0].update(source_kind="VERIFIED"),"source"),
    (lambda d:d["detail"]["stage_demands"].pop(),"Every planted day"),
    (lambda d:d["detail"]["site_peak_limits"].update(minimum_turnaround_days=35),"Insufficient days"),
    (lambda d:d["detail"]["site_peak_limits"].update(pumping_hours_available_per_day=30),"cannot exceed 24"),
    (lambda d:d["detail"]["site_peak_limits"].update(pump_capacity_m3_per_hour=0),"Pump capacity"),
    (lambda d:d["detail"]["loan_terms"].update(grace_months=-1),"grace_months"),
    (lambda d:d["detail"]["loan_terms"].update(principal_krw=-1),"nonnegative"),
    (lambda d:d["detail"]["loan_terms"].update(annual_real_interest_rate=2),"rate exceeds"),
    (lambda d:d["portfolio"]["financing_events"].append({
        "name":"duplicate financing","year":1,"month":2,"kind":"DRAW","amount_krw":1,
        "source_kind":"A","source_ref":"synthetic"
    }),"Cannot combine"),
])
def test_inconsistent_or_duplicate_claims_are_rejected(change,reason):
    d=load()
    change(d)
    with pytest.raises(ValueError,match=reason):
        assess_daily_farm(d["portfolio"],d["detail"])


def test_non_cropped_days_are_not_called_impossible():
    d=load()
    assert all(s["case_id"].startswith("SYNTHETIC ") for s in d["detail"]["stage_demands"])
    x=assess_daily_farm(d["portfolio"],d["detail"])
    assert x["status"]=="DAILY_ASSUMPTION_LEDGER_NOT_FIELD_OR_BANK_VALIDATION"
    assert "not bank-approved" in x["loan_schedule"]["assumption"].lower()
