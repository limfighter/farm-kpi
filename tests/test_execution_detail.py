"""Weekly labor bottleneck and grade-specific cash timing regression."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import pytest

from farm_strategy.execution_detail import assess_weekly_labor, assess_grades, assess_execution

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"data/templates/execution_detail_SYNTHETIC.json"


def example():
    d=json.loads(FILE.read_text(encoding="utf-8"))
    return d["case"],d["detail"]


def test_weekly_reconciles_monthly_labor_but_detects_peak_shortage():
    c,d=example()
    r=assess_weekly_labor(c,d["weekly_allocations"],d["weekly_capacity"])
    assert r["weeks_exceeding_owner_capacity"]
    assert r["peak_owner_week_hours"]>0
    assert r["weeks_with_unknown_hired_capacity"]>=1
    assert r["status"]=="LABOR_TIMING_ASSUMPTIONS_NOT_VERIFIED_STAFFING"


def test_week_starts_monday_and_month_crosses_week_boundary():
    c,d=example()
    a=d["weekly_allocations"]
    for x in a:
        assert date.fromisoformat(x["work_date"]).year == c["start_year"] + c["operations"][x["operation_index"]]["year"]-1
    r=assess_weekly_labor(c,a,d["weekly_capacity"])
    assert all(date.fromisoformat(v["week_start"]).weekday()==0 for v in r["weeks"])


@pytest.mark.parametrize("mutate,reason",[
    (lambda d:d["weekly_allocations"][0].update(owner_hours=999),"reconcile"),
    (lambda d:d["weekly_allocations"][0].update(work_date="2039-09-09"),"declared month/year"),
    (lambda d:d["weekly_allocations"][0].update(operation_index=90),"operation_index"),
    (lambda d:d["weekly_allocations"][0].update(new_field=True),"unexpected fields"),
    (lambda d:d["weekly_allocations"][0].update(owner_hours=-1),"nonnegative"),
    (lambda d:d["weekly_capacity"][0].update(week_start="2027-03-30"),"Monday"),
    (lambda d:d["weekly_capacity"][0].update(owner_available_hours=-1),"nonnegative"),
    (lambda d:d.update(weekly_allocations=[]),"complete weekly"),
])
def test_bad_weekly_details_rejected(mutate,reason):
    c,d=example()
    mutate(d)
    with pytest.raises(ValueError,match=reason):
        assess_weekly_labor(c,d["weekly_allocations"],d["weekly_capacity"])


def test_grades_replace_base_sales_and_pay_packing_at_dispatch():
    c,d=example()
    r=assess_grades(c,d["grade_lots"])
    assert r["replaced_sale_count"] == len(c["sales"]) == 1
    assert r["grade_lot_count"] == 2
    diff=r["cash_deltas_alternative_minus_baseline_krw"]
    assert diff["net_expected_settlement_krw"] == pytest.approx(-110400)
    assert diff["operating_cash_cost_krw"] == pytest.approx(40000)
    assert diff["operating_contribution_before_owner_labor_tax_depreciation_krw"] == pytest.approx(-150400)
    assert sum(v["delta_krw"] for v in r["monthly_net_cash_deltas_krw"]) == pytest.approx(
        diff["cash_after_last_settlement_krw"])
    months={(v["year"],v["month"]):v["delta_krw"] for v in r["monthly_net_cash_deltas_krw"]}
    assert months[(2029,11)] == pytest.approx(-40000)
    assert months[(2030,1)] == pytest.approx(-110400)
    assert c["sales"][0]["name"] == "future test harvest"  # no mutation


@pytest.mark.parametrize("mutate,reason",[
    (lambda d:d["grade_lots"][0].update(sold_quantity_per_10a=200),"reconcile"),
    (lambda d:d["grade_lots"][0].update(quantity_unit="kg"),"quantity units"),
    (lambda d:d["grade_lots"][0].update(packing_krw_per_unit=-1),"nonnegative"),
    (lambda d:d["grade_lots"][0].update(sale_index=3),"sale_index"),
    (lambda d:d["grade_lots"][0].update(buyer_fake_discount=1),"unexpected fields"),
    (lambda d:d["grade_lots"][0].update(commission_fraction=1.5),"exceeds"),
    (lambda d:d["grade_lots"][0].update(source_kind="VERIFIED"),"source"),
    (lambda d:d["grade_lots"][0].update(grade="B"),"Duplicate"),
])
def test_bad_grade_detail_rejected(mutate,reason):
    c,d=example()
    mutate(d)
    with pytest.raises(ValueError,match=reason):
        assess_grades(c,d["grade_lots"])


def test_combined_output_and_unknown_capacity():
    c,d=example()
    r=assess_execution(c,d)
    assert r["status"] == "EXPLICIT_OPERATIONAL_DETAIL_NOT_SITE_VERIFIED"
    assert r["weekly"]["weeks_with_unknown_hired_capacity"] > 0
    assert r["grading"]["packing_is_expense_at_dispatch"] is True
