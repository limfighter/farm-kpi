"""Paired operating-option tradeoffs on explicit input cashflows.

This is not a crop selector. Require the SAME crop, actual area, time horizon,
region, discount rate, owner opportunity value and owner capacity before
computing differences. Simulated deltas are not verified improvement or ROI.
"""
from .lifecycle import simulate_multiyear


def compare_operating_options(baseline, alternative):
    b = simulate_multiyear(baseline)
    a = simulate_multiyear(alternative)
    equal = ("crop", "region", "area_m2", "start_year", "horizon_years",
             "annual_real_discount_rate", "owner_hour_value_krw",
             "owner_available_hours_by_month")
    changed = [name for name in equal if baseline[name] != alternative[name]]
    if changed:
        raise ValueError("Paired option comparison requires same assumptions: "
                         + ", ".join(changed))
    if baseline["id"] == alternative["id"]:
        raise ValueError("Operating alternatives must have distinct IDs")
    delta = lambda key: a[key] - b[key]
    npv = "project_npv_krw_if_rate_supplied"
    econ = "economic_npv_krw_if_owner_value_and_rate_supplied"
    def optional_delta(key):
        return None if a[key] is None or b[key] is None else delta(key)

    def peak_excess(row):
        vals = row["owner_hours_over_capacity_by_month"]
        return None if vals is None else max(vals, default=0.0)

    def beyond(row):
        return row["peak_month_end_funding_gap_krw"]
    return {
        "status": "SIMULATED_PAIRED_OPTION_DELTAS_NOT_VERIFIED_ADVANTAGE",
        "scope": "ONE crop/region/usable area over the same time and owner constraints",
        "baseline": {"id": b["id"], "system": b["system"]},
        "alternative": {"id": a["id"], "system": a["system"]},
        "input_basis": {"area_m2": a["area_m2"], "years": a["horizon_years"],
                        "start_year": a["start_year"],
                        "annual_real_discount_rate": a["annual_real_discount_rate_input"]},
        "deltas_alternative_minus_baseline_krw": {
            "net_expected_settlement": delta("net_expected_settlement_krw"),
            "operating_cash_cost": delta("operating_cash_cost_krw"),
            "operating_contribution_before_owner_labor_tax_depreciation":
                delta("operating_contribution_before_owner_labor_tax_depreciation_krw"),
            "capital_expenditure": delta("capital_expenditure_krw"),
            "end_of_horizon_cash_balance": delta("cash_end_of_horizon_krw"),
            "peak_month_end_funding_gap": beyond(a) - beyond(b),
            "project_npv_if_rate_supplied": optional_delta(npv),
            "economic_npv_if_rate_and_owner_value_supplied": optional_delta(econ),
        },
        "deltas_alternative_minus_baseline_hours": {
            "owner": delta("owner_hours"),
            "hired": delta("hired_hours"),
            "peak_owner_hours_above_capacity":
                (None if peak_excess(a) is None or peak_excess(b) is None
                 else peak_excess(a) - peak_excess(b)),
        },
        "source_claim_counts": {
            "baseline": b["source_event_counts"],
            "alternative": a["source_event_counts"],
        },
        "limits": (
            "Negative incremental funding gap means less month-end cash needed; "
            "positive operating-contribution delta is NOT after-tax profit. "
            "Site legality, real buyer orders, heat load, per-week work and "
            "crop-specific yields remain unverified. R/O/T/Q source tags alone "
            "do not verify source authenticity. No automatic winner."
        ),
    }
