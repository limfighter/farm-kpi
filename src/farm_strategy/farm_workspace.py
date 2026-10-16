"""One coherent, auditable farm plan from the existing specialist engines.

Architecture: one portfolio input, optional grade replacement, physical stage
check, optional explicit/derived financing, stress, and private CSV comparison.
Never sum independent module reports: ONE effective portfolio is authoritative
for farm cash. Specialised modules remain import-compatible regression engines.
"""
from copy import deepcopy
import math

from .execution_detail import assess_grades
from .farm_records_stress import read_farm_log, stress_portfolio
from .physical_operations import amortization_events, assess_daily_farm
from .portfolio import simulate_portfolio

WORKSPACE_FIELDS = {
    "schema_version", "disclaimer", "portfolio", "grade_lots_by_case",
    "physical_detail", "stress",
}


def _shape(value, required, label):
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{label}: expected exact fields {sorted(required)}")


def _graded_portfolio(portfolio, grades):
    """Replace, never add, sales; shared dispatch packing cash is paid once."""
    if not isinstance(grades, dict):
        raise ValueError("grade_lots_by_case must be a map")
    copy = deepcopy(portfolio)
    by_id = {p["case"]["id"]: p for p in copy["plantings"]}
    if len(by_id) != len(copy["plantings"]) or not set(grades).issubset(by_id):
        raise ValueError("Unknown/duplicate crop case ID in grade breakdown")
    reports = {}
    has_packing = {}
    for case_id, lots in grades.items():
        plant = by_id[case_id]
        case = plant["case"]
        # Reuse the same validation and conservation law as the standalone
        # grading engine, including no missing grade sales and matching units.
        reports[case_id] = assess_grades(case, lots)
        original_sales = case["sales"]
        by_sale = {}
        for lot in lots:
            by_sale.setdefault(lot["sale_index"], []).append(lot)
        transformed = []
        packed = False
        for i, sale in enumerate(original_sales):
            for j, lot in enumerate(by_sale[i]):
                transformed.append({
                    "name": sale["name"] + " / " + lot["grade"],
                    "year": sale["year"], "month": sale["month"],
                    "quantity_per_10a": lot["sold_quantity_per_10a"],
                    "quantity_unit": sale["quantity_unit"],
                    "marketable_fraction": 1.0,
                    "price_krw_per_unit": lot["price_krw_per_unit"],
                    "commission_fraction": lot["commission_fraction"],
                    "deduction_krw_per_unit": lot["buyer_deduction_krw_per_unit"],
                    "transport_krw_per_10a": sale["transport_krw_per_10a"] if j == 0 else 0.0,
                    "settlement_lag_months": sale["settlement_lag_months"],
                    "source_kind": lot["source_kind"], "source_ref": lot["source_ref"],
                })
                amount = (lot["sold_quantity_per_10a"] * case["area_m2"] / 1000.
                          * lot["packing_krw_per_unit"])
                packed = packed or amount > 0
                if amount:
                    copy["shared_facility_events"].append({
                        "name": case_id + " / " + sale["name"] + " / " + lot["grade"] + " packing",
                        "year": sale["year"], "month": sale["month"],
                        "kind": "OPERATING", "amount_krw": amount,
                        # Derived event is a model computation even when a
                        # written price source was supplied.
                        "source_kind": "A",
                        "source_ref": "CALCULATED_GRADE_PACKING",
                    })
        case["sales"] = transformed
        has_packing[case_id] = packed
    return copy, reports, has_packing


def _resource_summary(report):
    summary = {}
    for key, values in report["resource_and_labor_limits"].items():
        summary[key] = {
            "shortage_months": sum(v["shortage"] is not None and v["shortage"] > 0 for v in values),
            "unknown_supply_months": sum(v["available"] is None for v in values),
            "max_shortage": max((v["shortage"] for v in values if v["shortage"] is not None), default=None),
        }
    weekly = report["weekly_labor"]
    return {
        "monthly": summary,
        "weekly_labor_status": report["weekly_labor_status"],
        "owner_shortage_weeks": None if weekly is None else
            sum(v["owner_shortage"] is not None and v["owner_shortage"] > 0 for v in weekly),
        "hired_shortage_weeks": None if weekly is None else
            sum(v["hired_shortage"] is not None and v["hired_shortage"] > 0 for v in weekly),
        "unknown_owner_weeks": None if weekly is None else
            sum(v["owner_shortage"] is None for v in weekly),
        "unknown_hired_weeks": None if weekly is None else
            sum(v["hired_shortage"] is None for v in weekly),
    }


def run_farm_workspace(config, *, field_log=None):
    """Run one canonical model and return one report, never output raw CSV rows.

    field_log is a local Path passed only at runtime, NEVER encoded into the
    reusable workspace JSON. A/O/T provenance is user-stated, not authenticated.
    """
    _shape(config, WORKSPACE_FIELDS, "workspace")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unknown workspace schema_version")
    if not isinstance(config["disclaimer"], str) or not config["disclaimer"].strip():
        raise ValueError("Workspace disclaimer required")
    original = config["portfolio"]
    # Validate original before deriving anything; prevent a corrupt scenario
    # from becoming an apparently valid scenario through derived replacements.
    original_base = simulate_portfolio(original)
    effective, grade_reports, has_packing = _graded_portfolio(
        original, config["grade_lots_by_case"])
    physical_detail = config["physical_detail"]
    physical = None
    if physical_detail is not None:
        physical = assess_daily_farm(effective, physical_detail)
        terms = physical_detail["loan_terms"]
        if terms is not None:
            if effective["financing_events"]:
                raise ValueError("Cannot combine manual financing and generated amortization")
            derived = amortization_events(effective["site"], terms)
            effective["financing_events"] = derived["events"]
    primary = simulate_portfolio(effective)
    if physical is not None:
        if not math.isclose(primary["ending_cash_krw"],
                            physical["financed_ending_cash_krw"],
                            rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("Daily/portfolio financed cash ledger failed to reconcile")
    stress_definition = config["stress"]
    stress = None
    if stress_definition is not None:
        _shape(stress_definition, {"schema_version", "disclaimer", "scenarios"}, "stress")
        if type(stress_definition["schema_version"]) is not int or stress_definition["schema_version"] != 1:
            raise ValueError("Unsupported stress schema")
        if not isinstance(stress_definition["disclaimer"], str) or not stress_definition["disclaimer"].strip():
            raise ValueError("Stress disclaimer required")
        # Original stress engine holds shared facility cash fixed by design.
        # Graded packing varies with packed harvest; silently holding it fixed
        # in a lower-yield stress would overstate costs. Reject, not estimate.
        for s in stress_definition["scenarios"]:
            if isinstance(s, dict) and isinstance(s.get("case_factors"), dict):
                for cid, factors in s["case_factors"].items():
                    if (has_packing.get(cid) and isinstance(factors, dict)
                            and factors.get("yield_factor") != 1):
                        raise ValueError(
                            "Grade packing expense changes with stressed yield: "
                            "cannot use fixed packing cash for this combined shock")
        stress = stress_portfolio(effective, stress_definition["scenarios"])
        if not math.isclose(stress["baseline_ending_cash_krw"],
                            primary["ending_cash_krw"], rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("Stress and primary ledger disagree")
    log = None if field_log is None else read_farm_log(field_log, original)
    warnings = [
        "All numerical inputs are hypothetical until verified; source_kind R/O/T/Q/A labels alone do not authenticate evidence.",
        "MISSING site feasibility, soil/water permits, buyer contract or loan approval are UNKNOWN—not a passing model result.",
        "All grades REPLACE original sales. Packing paid at dispatch; transport charged once. Same sales must never be entered twice.",
        "Field log aggregation is PARTIAL and separate from plan cash; no automatic calibration of recorded evidence to forecast.",
        "A physical capacity shortage does not automatically change expected crop yield; risk needs explicit supported assumptions.",
    ]
    if physical_detail is None:
        warnings.append("Daily crop stages, turnaround, peak pump/power and amortization not checked in this workspace.")
    if stress_definition is None:
        warnings.append("Downside price/yield and supply stress was NOT evaluated.")
    if not grade_reports:
        warnings.append("Buyer grade-level settlement and packaging breakdown NOT evaluated.")
    if field_log is None:
        warnings.append("No farm log input; observed outcomes remain UNKNOWN.")
    return {
        "schema_version": 1,
        "status": "UNIFIED_ASSUMPTION_WORKSPACE_NOT_FARM_APPROVAL",
        "disclaimer": config["disclaimer"],
        "authoritative_portfolio": primary,
        "ungraded_baseline_ending_cash_krw": original_base["ending_cash_krw"],
        "grade_adjustments": grade_reports,
        "physical_operations": physical,
        "resource_and_labor_screen": _resource_summary(primary),
        "stress": stress,
        "field_log": log,
        "enabled_sections": {
            "grades": bool(grade_reports), "physical": physical is not None,
            "stress": stress is not None, "field_log": log is not None,
        },
        "warnings": warnings,
    }
