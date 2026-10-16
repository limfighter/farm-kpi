"""Assumption shocks and confidential local farm logs never invent real returns."""
from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest
from farm_strategy.farm_records_stress import read_farm_log, stress_portfolio, analyze_farm

ROOT=Path(__file__).resolve().parents[1]
PORT=ROOT/"data/templates/portfolio_SYNTHETIC.json"
SCEN=ROOT/"data/templates/farm_stresses_SYNTHETIC.json"
LOG=ROOT/"data/templates/field_log_SYNTHETIC.csv"


def portfolio():
    return json.loads(PORT.read_text(encoding="utf-8"))


def cases():
    return json.loads(SCEN.read_text(encoding="utf-8"))


def test_control_does_not_move_any_cash_or_capacity():
    a=stress_portfolio(portfolio(),cases()["scenarios"])
    x=a["scenarios"][0]
    assert x["net_expected_settlement_delta_krw"]==0
    assert x["ending_cash_delta_krw"]==0
    assert x["unlevered_npv_delta_krw_if_rate_supplied"]==0
    assert x["peak_month_end_cash_shortfall_delta_krw"]==0
    assert x["scarcity"]["irrigation_m3"]["baseline"]==x["scarcity"]["irrigation_m3"]["stressed"]
    assert x["physical_supply_status"]=="NO_MODELED_MONTHLY_RESOURCE_DEFICIT"


def test_price_and_yield_are_joint_multiplied_with_same_commission_and_fixed_freight():
    s=cases()["scenarios"][0]
    s["case_factors"]={"SYNTHETIC SPRING CROP":{"yield_factor":.5,"price_factor":.8}}
    z=stress_portfolio(portfolio(),[s])["scenarios"][0]
    # gross (400 kg*0.9 marketable)*1500; new gross*0.5*0.8,
    # commission=5% of each gross; kg deduction 20 times new kg;
    # transport fixed 10000, independent of output.
    old=360*1500*(1-.05)-360*20-10000
    new=360*.5*1500*.8*(1-.05)-360*.5*20-10000
    assert z["net_expected_settlement_delta_krw"]==pytest.approx(new-old)
    assert z["ending_cash_delta_krw"]==pytest.approx(new-old)
    assert z["unlevered_npv_delta_krw_if_rate_supplied"]<0


def test_scarcity_alone_is_not_invented_weather_damage():
    z=stress_portfolio(portfolio(),cases()["scenarios"])["scenarios"][-1]
    assert z["net_expected_settlement_delta_krw"]==0
    assert z["ending_cash_delta_krw"]==0
    assert z["scarcity"]["irrigation_m3"]["stressed"]["months_short"]>0
    assert z["scarcity"]["electricity_kwh"]["stressed"]["months_short"]>0
    assert z["physical_supply_status"]=="RESOURCE_DEFICIT_UNPRICED_YIELD_RISK"
    assert z["financial_result_is_conditional_not_feasibility_approval"]


def test_unknown_supply_remains_unknown_even_after_shock():
    d=portfolio()
    d["site"]["water_supply_m3_by_month"]=None
    z=stress_portfolio(d,[cases()["scenarios"][2]])["scenarios"][0]
    assert z["scarcity"]["irrigation_m3"]["stressed"]["months_supply_unknown"]==24
    assert z["scarcity"]["irrigation_m3"]["stressed"]["maximum_shortage"] is None
    assert z["physical_supply_status"]=="SUPPLY_UNKNOWN_NOT_EVALUABLE"


def test_locally_redacted_records_are_separate_from_simulation():
    data=read_farm_log(LOG,portfolio())
    assert data["rows"]==9
    assert len(data["cases"])==2
    crop={x["case_id"]:x for x in data["cases"]}
    spring=crop["SYNTHETIC SPRING CROP"]
    assert spring["recorded_rows"]==6
    assert spring["provenance_claim_counts"]=={"A":6,"T":0,"O":0}
    assert spring["recorded"]["settled_cash_krw"]==490000
    assert spring["recorded"]["owner_hours_recorded"]==10
    assert spring["recorded"]["paid_expense_krw"]==25000
    assert spring["recorded"]["water_m3_recorded"]==10
    assert spring["coverage"]=="PARTIAL_UNVERIFIED"
    assert "DEMO_BANK_01" not in str(data)
    assert "unmodeled_logs_do_not_change_scenario_cash" in data
    together=analyze_farm(portfolio(),cases(),LOG)
    assert together["stress"]["baseline_ending_cash_krw"]==stress_portfolio(
        portfolio(), cases()["scenarios"])["baseline_ending_cash_krw"]


def mutate_csv(tmp_path,apply):
    with LOG.open(encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        cols=list(r.fieldnames)
        rows=list(r)
    apply(rows)
    path=tmp_path/"local.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.mark.parametrize("change,reason",[
 (lambda rows: rows[0].update(source_kind="T"),"provenance"),
 (lambda rows: rows[0].update(source_kind="O"),"Future-dated"),
 (lambda rows: rows[0].update(amount_krw="300"),"WORK requires"),
 (lambda rows: rows[1].update(unit="plants"),"quantity"),
 (lambda rows: rows[2].update(amount_krw=""),"SETTLEMENT must"),
 (lambda rows: rows[2].update(source_ref="Buyer Name PII"),"redacted"),
 (lambda rows: rows[5].update(category="CREDIT_CARD_111"),"EXPENSE requires"),
 (lambda rows: rows[3].update(quantity="-1"),"nonnegative"),
 (lambda rows: rows[4].update(unit="m3"),"correctly dimensioned"),
 (lambda rows: rows[3].update(case_id="fake-crop"),"not in selected"),
 (lambda rows: rows[1].update(date="2031-06-30"),"outside"),
])
def test_invalid_private_log_values_rejected(tmp_path,change,reason):
    p=mutate_csv(tmp_path,change)
    with pytest.raises(ValueError,match=reason):
        read_farm_log(p,portfolio())


def test_header_only_logs_show_unknown_not_zero_yield(tmp_path):
    p=tmp_path/"empty.csv"
    p.write_text(LOG.read_text(encoding="utf-8").splitlines()[0]+"\n",encoding="utf-8")
    r=read_farm_log(p,portfolio())
    assert r["rows"]==0
    assert all(x["coverage"]=="NO_RECORDS_UNKNOWN" for x in r["cases"])


@pytest.mark.parametrize("mutate,reason",[
 (lambda s:s[0].update(source_kind="T"),"always A"),
 (lambda s:s[0].update(water_supply_factor=-1),"nonnegative"),
 (lambda s:s[0].update(months_affected=[1,1]),"Duplicate"),
 (lambda s:s[0].update(months_affected=[25]),"month"),
 (lambda s:s[0].update(case_factors={"not-a-crop":{"yield_factor":.8,"price_factor":1}}),"Unknown stress crop"),
 (lambda s:s[0].update(case_factors={"SYNTHETIC SPRING CROP":{"yield_factor":.8}}),"requires"),
 (lambda s:s[0].update(source_ref="a private invoice number"),"redacted"),
 (lambda s:s[0].update(electricity_supply_factor=float("nan")),"finite"),
])
def test_inaccurate_stress_assumptions_rejected(mutate,reason):
    s=deepcopy(cases()["scenarios"])
    mutate(s)
    with pytest.raises(ValueError,match=reason):
        stress_portfolio(portfolio(),s)


def test_stress_does_not_mutate_orig_portfolio_or_template():
    p=portfolio()
    before=deepcopy(p)
    stress_portfolio(p,cases()["scenarios"])
    assert p==before


def test_duplicate_rows_cannot_double_book_farm_receipts(tmp_path):
    p=mutate_csv(tmp_path,lambda rows:rows.append(deepcopy(rows[2])))
    with pytest.raises(ValueError,match="Duplicate farm log row"):
        read_farm_log(p,portfolio())


def test_duplicate_settlement_booking_ref_with_changed_amount_is_rejected(tmp_path):
    def duplicate(rows):
        new=deepcopy(rows[2])
        new["amount_krw"]="550000"  # amounts differ but same receipt identity
        rows.append(new)
    p=mutate_csv(tmp_path,duplicate)
    with pytest.raises(ValueError,match="Duplicate settlement reference"):
        read_farm_log(p,portfolio())


def test_separate_settlement_receipts_may_share_buyer_but_not_booking_id(tmp_path):
    def extra(rows):
        new=deepcopy(rows[2])
        new["source_ref"]="DEMO_BANK_03"
        new["amount_krw"]="1000"
        new["quantity"]="1"
        rows.append(new)
    p=mutate_csv(tmp_path,extra)
    report=read_farm_log(p,portfolio())
    a=next(x for x in report["cases"] if x["case_id"]=="SYNTHETIC SPRING CROP")
    assert a["recorded"]["settled_cash_krw"]==491000
    assert a["record_kind_counts"]["SETTLEMENT"]==2


def test_missing_observations_export_null_not_pseudo_zero(tmp_path):
    p=tmp_path/"only_harvest.csv"
    with LOG.open(encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        cols=list(r.fieldnames)
        rows=[x for x in r if x["kind"]=="HARVEST" and x["case_id"]=="SYNTHETIC SPRING CROP"]
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    report=read_farm_log(p,portfolio())
    spring=next(x for x in report["cases"] if x["case_id"]=="SYNTHETIC SPRING CROP")
    recorded=spring["recorded"]
    assert recorded["harvest_quantity_by_unit"]=={"kg":400}
    assert recorded["settled_cash_krw"] is None
    assert recorded["settled_quantity_by_unit"] is None
    assert recorded["paid_expense_krw"] is None
    assert recorded["owner_hours_recorded"] is None
    assert recorded["hired_hours_recorded"] is None
    assert recorded["water_m3_recorded"] is None
    assert recorded["electricity_kwh_recorded"] is None
    assert spring["record_kind_counts"]["HARVEST"]==1
    assert spring["record_kind_counts"]["SETTLEMENT"]==0
    fall=next(x for x in report["cases"] if x["case_id"]=="SYNTHETIC AUTUMN CROP")
    assert fall["coverage"]=="NO_RECORDS_UNKNOWN"
    assert all(v is None for k,v in fall["recorded"].items() if k!="expense_by_category_krw")
    assert fall["recorded"]["expense_by_category_krw"] is None


def test_actual_recorded_zero_differs_from_unknown(tmp_path):
    def zero_owner(rows):
        rows[0]["owner_hours"]="0"
        rows[0]["hired_hours"]=""  # WORK: explicitly owner zero, hired never observed
        rows[3]["quantity"]="0"  # an explicit water-meter zero reading
    p=mutate_csv(tmp_path,zero_owner)
    output=read_farm_log(p,portfolio())
    crop=next(x for x in output["cases"] if x["case_id"]=="SYNTHETIC SPRING CROP")
    assert crop["recorded"]["owner_hours_recorded"]==0
    assert crop["recorded"]["hired_hours_recorded"] is None
    assert crop["recorded"]["water_m3_recorded"]==0
    assert crop["recorded"]["electricity_kwh_recorded"]==20


def test_export_contains_neither_exact_log_dates_nor_source_refs():
    output=read_farm_log(LOG,portfolio())
    encoded=json.dumps(output,ensure_ascii=False)
    assert "first_record_date" not in encoded
    assert "last_record_date" not in encoded
    assert "2027-04-12" not in encoded
    assert "2028-01-31" not in encoded
    assert "DEMO_BANK_01" not in encoded
    assert "DEMO_WORK_01" not in encoded
