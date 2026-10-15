"""Execution realism: explicit weekly labor and grade-specific cash replacement.

Does not infer working calendars or prices. Reconciles weekly labor to each
named operation in the existing multiyear ledger. Grade lots REPLACE generic
sale events; they never add a second stream of revenue. Packing is paid in the
dispatch month, sale proceeds arrive after the existing buyer settlement lag.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
import math

from .lifecycle import simulate_multiyear

SOURCES = {"A", "O", "T", "Q", "R"}
LOT_FIELDS = {"sale_index", "grade", "sold_quantity_per_10a", "quantity_unit",
              "price_krw_per_unit", "commission_fraction",
              "buyer_deduction_krw_per_unit", "packing_krw_per_unit",
              "source_kind", "source_ref"}
WORK_FIELDS = {"operation_index", "work_date", "owner_hours", "hired_hours"}
CAP_FIELDS = {"week_start", "owner_available_hours", "hired_available_hours"}
COMPARE_KEYS = ("net_expected_settlement_krw", "operating_cash_cost_krw",
                "operating_contribution_before_owner_labor_tax_depreciation_krw",
                "cash_after_last_settlement_krw", "peak_month_end_funding_gap_krw",
                "project_npv_krw_if_rate_supplied")


def _shape(row, expected, context):
    if not isinstance(row, dict) or set(row) != expected:
        raise ValueError(f"{context}: unexpected fields or missing required field")


def _num(v, context, upper=None):
    if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
        raise ValueError(f"{context}: finite nonnegative input required")
    if upper is not None and v > upper:
        raise ValueError(f"{context}: exceeds {upper}")
    return float(v)


def _text(v, context):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{context}: nonempty text required")
    return v


def _source(row, context):
    if row["source_kind"] not in SOURCES:
        raise ValueError(f"{context}: unknown source R/O/T/Q/A")
    _text(row["source_ref"], f"{context}.source_ref")


def _reconciles(observed, expected, label):
    # 1e-8 relative tolerance covers harmless floating-point multiplication,
    # not material changes or an unallocated full day's work.
    if not math.isclose(observed, expected, rel_tol=1e-8, abs_tol=1e-7):
        raise ValueError(f"{label}: detail does not reconcile with scenario")


def _week(dt):
    return (dt-timedelta(days=dt.weekday())).isoformat()


def assess_weekly_labor(case, allocations, capacity):
    """Return peak week labor and shortages; missing capacity is UNKNOWN."""
    simulate_multiyear(case)  # validate full scenario first
    if not isinstance(allocations, list) or not isinstance(capacity, list):
        raise ValueError("Weekly labor allocations and capacities must be arrays")
    ops = case["operations"]
    totals = defaultdict(lambda: [0., 0.])
    weeks = defaultdict(lambda: [0., 0.])
    if not allocations and any(op["owner_hours_per_10a"] or
                               op["hired_hours_per_10a"] for op in ops):
        raise ValueError("Operations with labor require complete weekly allocation")
    for idx, row in enumerate(allocations):
        label = f"weekly allocation {idx+1}"
        _shape(row, WORK_FIELDS, label)
        i = row["operation_index"]
        if type(i) is not int or not 0 <= i < len(ops):
            raise ValueError("Unknown operation_index")
        _text(row["work_date"], label)
        try:
            dt = date.fromisoformat(row["work_date"])
        except ValueError as exc:
            raise ValueError("Invalid work_date") from exc
        op = ops[i]
        expected_year = case["start_year"] + op["year"]-1
        if dt.year != expected_year or dt.month != op["month"]:
            raise ValueError("Work date must occur within operation's declared month/year")
        owner = _num(row["owner_hours"], label)
        hired = _num(row["hired_hours"], label)
        totals[i][0] += owner
        totals[i][1] += hired
        weeks[_week(dt)][0] += owner
        weeks[_week(dt)][1] += hired
    m = case["area_m2"] / 1000.
    for i, op in enumerate(ops):
        _reconciles(totals[i][0], op["owner_hours_per_10a"] * m, f"owner operation {i}")
        _reconciles(totals[i][1], op["hired_hours_per_10a"] * m, f"hired operation {i}")
    by_week = {}
    for j, c in enumerate(capacity):
        label = f"weekly capacity {j+1}"
        _shape(c, CAP_FIELDS, label)
        _text(c["week_start"], label)
        try:
            dt = date.fromisoformat(c["week_start"])
        except ValueError as exc:
            raise ValueError("Invalid week_start") from exc
        if dt.weekday() != 0:
            raise ValueError("week_start must be Monday")
        if c["week_start"] in by_week:
            raise ValueError("Duplicate week_start")
        if c["week_start"] not in weeks:
            raise ValueError("Capacity week has no allocated labor")
        by_week[c["week_start"]] = {
            "owner": (None if c["owner_available_hours"] is None else
                      _num(c["owner_available_hours"], "owner week capacity")),
            "hired": (None if c["hired_available_hours"] is None else
                      _num(c["hired_available_hours"], "hired week capacity"))
        }
    detail = []
    for week in sorted(weeks):
        owner, hired = weeks[week]
        cap = by_week.get(week, {})
        ac, hc = cap.get("owner"), cap.get("hired")
        detail.append({
            "week_start": week, "owner_required_hours": owner,
            "hired_required_hours": hired,
            "owner_available_hours": ac, "hired_available_hours": hc,
            "owner_shortage_hours": None if ac is None else max(0., owner-ac),
            "hired_shortage_hours": None if hc is None else max(0., hired-hc),
        })
    return {
        "status": "LABOR_TIMING_ASSUMPTIONS_NOT_VERIFIED_STAFFING",
        "weeks": detail,
        "peak_owner_week_hours": max((x["owner_required_hours"] for x in detail), default=0.),
        "peak_hired_week_hours": max((x["hired_required_hours"] for x in detail), default=0.),
        "weeks_with_unknown_owner_capacity": sum(x["owner_available_hours"] is None for x in detail),
        "weeks_with_unknown_hired_capacity": sum(x["hired_available_hours"] is None for x in detail),
        "weeks_exceeding_owner_capacity": [x["week_start"] for x in detail if x["owner_shortage_hours"] is not None and x["owner_shortage_hours"] > 0],
        "weeks_exceeding_hired_capacity": [x["week_start"] for x in detail if x["hired_shortage_hours"] is not None and x["hired_shortage_hours"] > 0],
        "unverified_weekly_dates_and_staff": True,
    }


def assess_grades(case, lots):
    """Substitute each generic sale with complete, graded dispatches, reconcile."""
    baseline = simulate_multiyear(case)
    if not isinstance(lots, list) or not lots or not case["sales"]:
        raise ValueError("Every modeled sale requires grade lots")
    grouped = defaultdict(list)
    seen = set()
    for j, lot in enumerate(lots):
        label = f"grade lot {j+1}"
        _shape(lot, LOT_FIELDS, label)
        i = lot["sale_index"]
        if type(i) is not int or not 0 <= i < len(case["sales"]):
            raise ValueError("Unknown sale_index")
        grade = _text(lot["grade"], label)
        if (i,grade) in seen:
            raise ValueError("Duplicate sale grade")
        seen.add((i,grade))
        sale=case["sales"][i]
        unit=_text(lot["quantity_unit"], label)
        if unit != sale["quantity_unit"]:
            raise ValueError("Sale grade quantity units must match")
        for key in ("sold_quantity_per_10a","price_krw_per_unit",
                    "buyer_deduction_krw_per_unit","packing_krw_per_unit"):
            _num(lot[key], key)
        _num(lot["commission_fraction"], label, 1.0)
        _source(lot, label)
        grouped[i].append(lot)
    if set(grouped) != set(range(len(case["sales"]))):
        raise ValueError("All sales must have complete grade breakdown")
    new=deepcopy(case)
    new["id"]=case["id"]+"-GRADE-COUNTERFACTUAL"
    new["sales"]=[]
    extra=[]
    for i, sale in enumerate(case["sales"]):
        grades=grouped[i]
        expected=sale["quantity_per_10a"]*sale["marketable_fraction"]
        qty=sum(l["sold_quantity_per_10a"] for l in grades)
        _reconciles(qty,expected,f"sale {i} sold grade quantity")
        for j, lot in enumerate(grades):
            new["sales"].append({
                "name": sale["name"]+" / "+lot["grade"],"year":sale["year"],
                "month":sale["month"],
                "quantity_per_10a":lot["sold_quantity_per_10a"],
                "quantity_unit":lot["quantity_unit"],
                "marketable_fraction":1.,
                "price_krw_per_unit":lot["price_krw_per_unit"],
                "commission_fraction":lot["commission_fraction"],
                "deduction_krw_per_unit":lot["buyer_deduction_krw_per_unit"],
                "transport_krw_per_10a":sale["transport_krw_per_10a"] if j==0 else 0.,
                "settlement_lag_months":sale["settlement_lag_months"],
                "source_kind":lot["source_kind"],"source_ref":lot["source_ref"],
            })
            packing=lot["sold_quantity_per_10a"] * case["area_m2"]/1000. * lot["packing_krw_per_unit"]
            extra.append({
                "name": sale["name"]+" / "+lot["grade"]+" packing",
                "year": sale["year"], "month": sale["month"],
                "kind": "OPERATING", "amount_krw": packing,
                "source_kind": lot["source_kind"], "source_ref":lot["source_ref"],
            })
    new["facility_events"].extend(extra)
    graded=simulate_multiyear(new)
    changes={k:(None if baseline[k] is None or graded[k] is None
                else graded[k]-baseline[k]) for k in COMPARE_KEYS}
    b={ (m["year"],m["month"]):m["net_cash_krw"] for m in baseline["months"]}
    g={ (m["year"],m["month"]):m["net_cash_krw"] for m in graded["months"]}
    return {
        "status":"GRADED_REPLACEMENT_ASSUMPTIONS_NOT_REAL_SETTLEMENT",
        "baseline_id":case["id"],"replaced_sale_count":len(case["sales"]),
        "grade_lot_count":len(lots),
        "cash_deltas_alternative_minus_baseline_krw":changes,
        "monthly_net_cash_deltas_krw":[
            {"year":year,"month":month,"delta_krw":g.get((year,month),0.)-b.get((year,month),0.)}
            for year,month in sorted(set(b)|set(g))
            if not math.isclose(g.get((year,month),0.),b.get((year,month),0.),abs_tol=1e-8)
        ],
        "packing_is_expense_at_dispatch":True,
        "sourced_grade_details_do_not_validate_prices":True,
        "warning":"All generic sales were REPLACED (not duplicated); packed lots are modeled purchases, not buyer fee deductions. Grades/packing must be supported by real settlement records.",
    }


def assess_execution(case, detail):
    if not isinstance(detail,dict) or set(detail) != {"schema_version","disclaimer","grade_lots","weekly_allocations","weekly_capacity"}:
        raise ValueError("Execution detail schema differs")
    if type(detail["schema_version"]) is not int or detail["schema_version"]!=1:
        raise ValueError("Execution detail version must be 1")
    _text(detail["disclaimer"],"disclaimer")
    return {
        "status":"EXPLICIT_OPERATIONAL_DETAIL_NOT_SITE_VERIFIED",
        "id":case["id"],
        "weekly":assess_weekly_labor(case,detail["weekly_allocations"],detail["weekly_capacity"]),
        "grading":assess_grades(case,detail["grade_lots"]),
        "disclaimer":detail["disclaimer"],
    }
