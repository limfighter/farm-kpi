"""Exercise cash versus accrual, workflow labor, area, facility and source guards."""
import copy
import pytest
from farm_strategy.workflow import compare_workflows, simulate_workflow


def case():
    return {
        "id": "demo", "crop": "TEST ONLY", "facility": "test facility",
        "region": "TEST REGION", "basis_year": 2027, "area_m2": 1000,
        "owner_available_hours_by_month": None,
        "operations": [{
            "name": "plant", "month": 2, "owner_hours_per_10a": 10,
            "hired_hours_per_10a": 2, "hired_wage_krw_per_hour": 10000,
            "materials_krw_per_10a": 100000, "contractor_krw_per_10a": 30000,
            "source_kind": "A", "source_ref": "synthetic test"
        }],
        "harvests": [{
            "name": "harvest", "month": 11, "yield_kg_per_10a": 200,
            "marketable_fraction": 1, "price_krw_per_kg": 1000,
            "commission_fraction": .10, "buyer_deduction_krw_per_kg": 100,
            "transport_krw_per_10a": 10000, "settlement_lag_months": 2,
            "source_kind": "A", "source_ref": "synthetic test"
        }],
        "facility_events": [
            {"name": "build", "month": 1, "kind": "CAPEX", "amount_krw": 500000,
             "source_kind": "A", "source_ref": "synthetic test"},
            {"name": "lease deposit", "month": 1, "kind": "DEPOSIT_PAID",
             "amount_krw": 100000, "source_kind": "A", "source_ref": "synthetic test"},
            {"name": "deposit back", "month": 12, "kind": "DEPOSIT_RETURN",
             "amount_krw": 100000, "source_kind": "A", "source_ref": "synthetic test"},
        ],
    }


def test_workflow_cash_timing_and_no_deposit_or_capex_in_operating_margin():
    r = simulate_workflow(case())
    assert r["gross_receipts_krw"] == 200000
    assert r["net_receivables_krw"] == 160000
    assert r["operating_cash_cost_krw"] == 160000
    assert r["operating_contribution_before_owner_labor_tax_depreciation_krw"] == 0
    assert r["upfront_capex_krw"] == 500000
    assert r["december_cash_balance_krw"] == -660000
    assert r["unsettled_receivables_after_december_krw"] == 160000
    assert r["cash_after_last_settlement_krw"] == -500000
    assert r["peak_month_end_funding_gap_krw"] == 760000
    assert r["months"][12]["month"] == 1
    assert r["months"][12]["year"] == 2028
    assert r["source_event_counts"] == {"A": 5, "O": 0, "R": 0, "T": 0, "Q": 0}
    assert r["owner_hours_over_capacity_by_month"] is None


def test_area_scaling_and_monthly_labor_constraint():
    s = case()
    s["facility_events"] = []
    s["area_m2"] = 2000
    s["owner_available_hours_by_month"] = [5]*12
    r = simulate_workflow(s)
    assert r["owner_hours"] == 20
    assert r["hired_hours"] == 4
    assert r["owner_hours_over_capacity_by_month"][1] == 15
    assert r["gross_receipts_krw"] == 400000
    assert r["net_receivables_krw"] == 320000


def test_lease_operating_cash_counts_as_cost_not_capex():
    s = case()
    s["facility_events"] = [{
        "name": "rent", "month": 3, "kind": "OPERATING",
        "amount_krw": 90000, "source_kind": "Q", "source_ref": "synthetic quote ID",
    }]
    r = simulate_workflow(s)
    assert r["operating_cash_cost_krw"] == 250000
    assert r["upfront_capex_krw"] == 0
    assert r["source_event_counts"]["Q"] == 1


@pytest.mark.parametrize("alter, message", [
    (lambda c: c.update(area_m2=0), "positive"),
    (lambda c: c.update(area_m2=None), "number"),
    (lambda c: c["operations"][0].update(source_kind="VERIFIED"), "source kind"),
    (lambda c: c["operations"][0].update(inputs_krw_per_10a=500), "required fields"),
    (lambda c: c["harvests"][0].update(marketable_fraction=1.1), "exceeds"),
    (lambda c: c["harvests"][0].update(settlement_lag_months=-1), "lag"),
    (lambda c: c["harvests"][0].update(buyer_deduction_krw_per_kg=2000), "negative buyer"),
    (lambda c: c["facility_events"][0].update(kind="FREE_LOAN"), "unknown facility"),
    (lambda c: c.update(owner_available_hours_by_month=[0, 1]), "12 monthly"),
])
def test_input_guards(alter, message):
    s = case()
    alter(s)
    with pytest.raises(ValueError, match=message):
        simulate_workflow(s)


def test_deposit_refund_cannot_create_revenue():
    s = case()
    s["facility_events"] = [s["facility_events"][-1]]
    with pytest.raises(ValueError, match="Deposit refund"):
        simulate_workflow(s)


def test_different_basis_years_not_comparable():
    one, two = case(), copy.deepcopy(case())
    two["id"] = "other"
    two["basis_year"] = 2028
    with pytest.raises(ValueError, match="different nominal basis"):
        compare_workflows([one, two])


def test_compare_multiple_systems_without_auto_ranking():
    one, two = case(), copy.deepcopy(case())
    two["id"], two["facility"] = "lease", "leased"
    two["facility_events"] = []
    result = compare_workflows([one, two])
    assert len(result["cases"]) == 2
    assert "No automatic ranking" in result["comparison_rule"]
