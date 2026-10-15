"""Regression guards for multi-year crop & facility timing and economics."""
import copy
import math
import pytest
from farm_strategy.lifecycle import simulate_multiyear, compare_multiyear


def scenario():
    return {
        "id": "synthetic", "crop": "TEST CROP", "system": "TEST GREENHOUSE",
        "region": "FAKE TEST REGION", "area_m2": 1000,
        "start_year": 2027, "horizon_years": 3,
        "annual_real_discount_rate": None,
        "owner_hour_value_krw": None,
        "owner_available_hours_by_month": None,
        "no_sales_reason": None,
        "operations": [{
            "name": "plant test", "year": 1, "month": 4,
            "owner_hours_per_10a": 6, "hired_hours_per_10a": 2,
            "hired_hour_wage_krw": 10000,
            "materials_krw_per_10a": 10000, "contractor_krw_per_10a": 5000,
            "source_kind": "A", "source_ref": "synthetic test only",
        }],
        "sales": [{
            "name": "harvest after immature years", "year": 3, "month": 12,
            "quantity_per_10a": 100, "quantity_unit": "본",
            "marketable_fraction": 1, "price_krw_per_unit": 1000,
            "commission_fraction": .1, "deduction_krw_per_unit": 100,
            "transport_krw_per_10a": 3000, "settlement_lag_months": 2,
            "source_kind": "A", "source_ref": "synthetic test only",
        }],
        "facility_events": [
            {"name": "construct", "year": 1, "month": 1, "kind": "CAPEX",
             "amount_krw": 200000, "source_kind": "A", "source_ref": "test"},
            {"name": "deposit", "year": 1, "month": 1, "kind": "DEPOSIT_PAID",
             "amount_krw": 50000, "source_kind": "A", "source_ref": "test"},
            {"name": "return", "year": 3, "month": 12, "kind": "DEPOSIT_RETURN",
             "amount_krw": 50000, "source_kind": "A", "source_ref": "test"},
            {"name": "salvage", "year": 3, "month": 12, "kind": "SALVAGE_RECEIPT",
             "amount_krw": 20000, "source_kind": "A", "source_ref": "test"},
        ],
    }


def test_cash_labor_settlement_lag_and_no_double_capex():
    r = simulate_multiyear(scenario())
    assert r["gross_expected_revenue_krw"] == 100000
    assert r["net_expected_settlement_krw"] == 80000
    assert r["operating_cash_cost_krw"] == 38000
    assert r["operating_contribution_before_owner_labor_tax_depreciation_krw"] == 42000
    assert r["capital_expenditure_krw"] == 200000
    assert r["salvage_received_krw"] == 20000
    assert r["deposit_outstanding_krw"] == 0
    assert r["unsettled_settlement_after_horizon_krw"] == 80000
    assert r["cash_end_of_horizon_krw"] == -218000
    assert r["cash_after_last_settlement_krw"] == -138000
    assert r["peak_month_end_funding_gap_krw"] == 288000
    assert r["owner_hours"] == 6
    assert r["hired_hours"] == 2
    assert len(r["months"]) == 38
    assert r["months"][-1]["year"] == 2030
    assert r["months"][-1]["month"] == 2
    assert r["project_npv_krw_if_rate_supplied"] is None
    assert r["economic_npv_krw_if_owner_value_and_rate_supplied"] is None
    assert r["source_event_counts"]["A"] == 6
    assert r["years"][0]["capex_krw"] == 200000
    assert r["years"][1]["received_krw"] == 0


def test_preproductive_orchard_zero_sales_must_be_explicit():
    s = scenario()
    s["horizon_years"] = 2
    s["sales"] = []
    s["no_sales_reason"] = "PRE_PRODUCTIVE_WINDOW"
    s["facility_events"] = []
    r = simulate_multiyear(s)
    assert r["no_sales_reason"] == "PRE_PRODUCTIVE_WINDOW"
    assert r["net_expected_settlement_krw"] == 0
    assert r["years"][1]["received_krw"] == 0
    s["no_sales_reason"] = None
    with pytest.raises(ValueError, match="Empty sales require"):
        simulate_multiyear(s)


def test_four_year_harvest_occurs_only_at_explicit_year():
    s = scenario()
    s["horizon_years"] = 4
    s["sales"][0].update(year=4, month=9, settlement_lag_months=1)
    r = simulate_multiyear(s)
    assert len(r["years"]) == 4
    assert r["years"][0]["received_krw"] == 0
    assert r["years"][1]["received_krw"] == 0
    assert r["years"][2]["received_krw"] == 0
    assert r["years"][3]["received_krw"] == 80000


def test_owner_shortage_is_flagged_not_silently_paid():
    s = scenario()
    s["owner_available_hours_by_month"] = [0.0] * 36
    r = simulate_multiyear(s)
    assert r["owner_hours_over_capacity_by_month"][3] == 6
    assert r["operating_cash_cost_krw"] == 38000


def test_discount_assumptions_are_explicit_and_optional():
    s = scenario()
    s["annual_real_discount_rate"] = .05
    s["owner_hour_value_krw"] = 15000
    r = simulate_multiyear(s)
    assert math.isfinite(r["project_npv_krw_if_rate_supplied"])
    assert (r["economic_npv_krw_if_owner_value_and_rate_supplied"]
            < r["project_npv_krw_if_rate_supplied"])
    s["annual_real_discount_rate"] = None
    assert simulate_multiyear(s)["project_npv_krw_if_rate_supplied"] is None


@pytest.mark.parametrize("change,needle", [
    (lambda c: c.update(area_m2=None), "nonnegative"),
    (lambda c: c.update(area_m2=0), "positive"),
    (lambda c: c.update(horizon_years=11), "horizon"),
    (lambda c: c["sales"][0].update(year=4), "year"),
    (lambda c: c["sales"][0].update(settlement_lag_months=7), "lag"),
    (lambda c: c["sales"][0].update(marketable_fraction=1.2), "exceeds"),
    (lambda c: c["sales"][0].update(quantity_unit=""), "nonempty"),
    (lambda c: c["sales"][0].update(source_kind="VERIFIED"), "R/O/T/Q/A"),
    (lambda c: c["sales"][0].update(yield_source="R"), "required fields"),
    (lambda c: c["facility_events"][-2].update(amount_krw=50001), "prior deposits"),
    (lambda c: c.update(owner_available_hours_by_month=[10]*12), "every modeled month"),
])
def test_invalid_case_rejected(change, needle):
    s = scenario()
    change(s)
    with pytest.raises(ValueError, match=needle):
        simulate_multiyear(s)


def test_cross_case_horizon_and_discount_rate_consistency():
    a, b = scenario(), copy.deepcopy(scenario())
    b["id"] = "different"
    b["system"] = "LEASE"
    assert len(compare_multiyear([a,b])["cases"]) == 2
    b["annual_real_discount_rate"] = .03
    with pytest.raises(ValueError, match="mismatched time windows"):
        compare_multiyear([a,b])
