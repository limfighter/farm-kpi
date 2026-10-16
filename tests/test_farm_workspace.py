"""One canonical farm scenario, optional screens, honest cash reconciliation."""
from copy import deepcopy
import json
from pathlib import Path
import pytest

from farm_strategy.farm_workspace import run_farm_workspace
from farm_strategy.portfolio import simulate_portfolio
from farm_strategy.execution_detail import assess_grades

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/"data/templates/farm_workspace_SYNTHETIC.json"
LOG=ROOT/"data/templates/field_log_SYNTHETIC.csv"


def sample():
    return json.loads(WORK.read_text(encoding="utf-8"))


def graded():
    x=sample()
    p=x["portfolio"]["plantings"][0]["case"]
    sold=p["sales"][0]["quantity_per_10a"]*p["sales"][0]["marketable_fraction"]
    unit=p["sales"][0]["quantity_unit"]
    x["grade_lots_by_case"]={p["id"]:[
        {"sale_index":0,"grade":"A","sold_quantity_per_10a":sold*.7,
         "quantity_unit":unit,"price_krw_per_unit":1600,
         "commission_fraction":.05,"buyer_deduction_krw_per_unit":20,
         "packing_krw_per_unit":75,"source_kind":"A","source_ref":"SYNTHETIC_LOT_A"},
        {"sale_index":0,"grade":"B","sold_quantity_per_10a":sold*.3,
         "quantity_unit":unit,"price_krw_per_unit":1100,
         "commission_fraction":.05,"buyer_deduction_krw_per_unit":20,
         "packing_krw_per_unit":75,"source_kind":"A","source_ref":"SYNTHETIC_LOT_B"},
    ]}
    return x


def test_workspace_has_one_financial_ledger_and_all_optional_screens():
    result=run_farm_workspace(sample(),field_log=LOG)
    assert result["status"]=="UNIFIED_ASSUMPTION_WORKSPACE_NOT_FARM_APPROVAL"
    assert result["enabled_sections"]=={"grades":False,"physical":True,"stress":True,"field_log":True}
    ledger=result["authoritative_portfolio"]
    phys=result["physical_operations"]
    assert len(ledger["per_crop"])==2
    assert len(ledger["monthly"])>=24
    assert ledger["ending_cash_krw"]==pytest.approx(phys["financed_ending_cash_krw"])
    assert result["stress"]["baseline_ending_cash_krw"]==pytest.approx(ledger["ending_cash_krw"])
    assert ledger["financing"]["drawn_krw"]==1000000
    assert len(phys["loan_schedule"]["events"])==27
    assert result["field_log"]["rows"]==9
    assert result["field_log"]["cases"][0]["recorded_rows"]>0


def test_optional_sections_are_unknown_not_auto_zero():
    x=sample()
    x.update(physical_detail=None,grade_lots_by_case={},stress=None)
    result=run_farm_workspace(x)
    direct=simulate_portfolio(x["portfolio"])
    assert result["authoritative_portfolio"]["ending_cash_krw"]==direct["ending_cash_krw"]
    assert result["physical_operations"] is None
    assert result["stress"] is None
    assert result["field_log"] is None
    assert result["grade_adjustments"]=={}
    assert result["enabled_sections"]=={"grades":False,"physical":False,"stress":False,"field_log":False}


def test_grade_sales_replace_original_and_pack_cost_once():
    x=graded()
    x["stress"]=None
    result=run_farm_workspace(x)
    case=x["portfolio"]["plantings"][0]["case"]
    independent=assess_grades(case,x["grade_lots_by_case"][case["id"]])
    assert result["grade_adjustments"][case["id"]]["grade_lot_count"]==2
    expected=(result["ungraded_baseline_ending_cash_krw"]
              +independent["cash_deltas_alternative_minus_baseline_krw"]["cash_after_last_settlement_krw"])
    assert result["authoritative_portfolio"]["ending_cash_krw"]==pytest.approx(expected)
    assert result["physical_operations"]["financed_ending_cash_krw"]==pytest.approx(expected)
    assert x["portfolio"]["plantings"][0]["case"]["sales"]==case["sales"]


def test_packing_cost_and_yield_stress_cannot_be_silently_decoupled():
    with pytest.raises(ValueError,match="Grade packing expense changes"):
        run_farm_workspace(graded())


def test_grade_with_price_only_stress_remains_one_cash_ledger():
    x=graded()
    for s in x["stress"]["scenarios"]:
        for f in s["case_factors"].values():
            f["yield_factor"]=1
    r=run_farm_workspace(x)
    assert len(r["stress"]["scenarios"])==3
    assert r["stress"]["baseline_ending_cash_krw"]==pytest.approx(
        r["authoritative_portfolio"]["ending_cash_krw"])


def test_invalid_grade_unit_is_rejected_not_guessed():
    x=graded()
    x["grade_lots_by_case"]["SYNTHETIC SPRING CROP"][0]["quantity_unit"]="boxes"
    with pytest.raises(ValueError,match="quantity units"):
        run_farm_workspace(x)


def test_no_double_book_manual_and_generated_loan():
    x=sample()
    original=deepcopy(x["portfolio"])
    x["portfolio"]["financing_events"]=[{
        "name":"duplicated loan", "year":1,"month":2,"kind":"DRAW",
        "amount_krw":500,"source_kind":"A","source_ref":"TEST_DUPLICATE",
    }]
    with pytest.raises(ValueError):
        run_farm_workspace(x)
    assert original["financing_events"]==[]


def test_strict_workspace_schema_no_fallbacks():
    for change in (
        lambda x:x.update(random_unverified_profit=1),
        lambda x:x.update(schema_version=2),
        lambda x:x.update(grade_lots_by_case={"unknown-case":[]}),
    ):
        x=sample()
        change(x)
        with pytest.raises(ValueError):
            run_farm_workspace(x)


def test_workspace_does_not_mutate_canonical_input():
    x=graded()
    x["stress"]=None
    old=deepcopy(x)
    run_farm_workspace(x)
    assert x==old
