"""Workflow-based, single-year crop x facility cash simulator.

All values are caller-supplied and explicitly source-tagged; this engine does
not infer a farm plan or calibrate prices, yield, farm suitability, or risk.
No loan, depreciation, taxes, or multi-year NPV is claimed.
"""
import math

SOURCES = {"A", "O", "R", "T", "Q"}
CASE_FIELDS = {
    "id", "crop", "facility", "region", "basis_year", "area_m2",
    "owner_available_hours_by_month", "operations", "harvests", "facility_events",
}
OPERATIONS = {
    "name", "month", "owner_hours_per_10a", "hired_hours_per_10a",
    "hired_wage_krw_per_hour", "materials_krw_per_10a",
    "contractor_krw_per_10a", "source_kind", "source_ref",
}
HARVESTS = {
    "name", "month", "yield_kg_per_10a", "marketable_fraction",
    "price_krw_per_kg", "commission_fraction",
    "buyer_deduction_krw_per_kg", "transport_krw_per_10a",
    "settlement_lag_months", "source_kind", "source_ref",
}
# Version 2 keeps yield/price units explicit for grains, flowers, fruits and
# individually counted harvests; the old kg-only case shape remains valid.
HARVESTS_UNITS = {
    "name", "month", "yield_quantity_per_10a", "yield_unit",
    "marketable_fraction", "price_krw_per_unit", "commission_fraction",
    "buyer_deduction_krw_per_unit", "transport_krw_per_10a",
    "settlement_lag_months", "source_kind", "source_ref",
}
FACILITIES = {"name", "month", "kind", "amount_krw", "source_kind", "source_ref"}
FACILITY_KINDS = {"OPERATING", "CAPEX", "DEPOSIT_PAID", "DEPOSIT_RETURN"}


def _exact(obj, fields, label):
    if not isinstance(obj, dict) or set(obj) != fields:
        raise ValueError(f"{label}: required fields differ; unexpected values cannot be ignored")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: nonempty text required")


def _num(value, label, *, cap=None):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label}: finite nonnegative number required")
    if cap is not None and value > cap:
        raise ValueError(f"{label}: value exceeds {cap}")
    return float(value)


def _month(value, label):
    if type(value) is not int or not 1 <= value <= 12:
        raise ValueError(f"{label}: expected month 1..12")
    return value


def _source(row, label):
    if row["source_kind"] not in SOURCES:
        raise ValueError(f"{label}: unknown source kind (R/O/T/Q/A)")
    _text(row["source_ref"], f"{label}.source_ref")


def _ledger_month(month, year):
    return {
        "year": year + (month - 1) // 12,
        "month": (month - 1) % 12 + 1,
        "month_index": month,
        "net_settlement_received_krw": 0.0,
        "operating_cash_out_krw": 0.0,
        "capital_cash_out_krw": 0.0,
        "deposit_paid_krw": 0.0,
        "deposit_returned_krw": 0.0,
        "owner_hours": 0.0,
        "hired_hours": 0.0,
        "activities": [],
    }


def simulate_workflow(case):
    """Return named monthly cash components for ONE independent system/area.

    Crop revenues are receivables from harvest and cash only at settlement.
    CAPEX/deposits affect liquidity but not operating contribution. Results
    are **model outputs**, never observed or statistically calibrated returns.
    """
    _exact(case, CASE_FIELDS, "case")
    for key in ("id", "crop", "facility", "region"):
        _text(case[key], key)
    year = case["basis_year"]
    if type(year) is not int or not 2000 <= year <= 2100:
        raise ValueError("basis_year: expected year 2000..2100")
    area = _num(case["area_m2"], "area_m2")
    if area <= 0:
        raise ValueError("area_m2: actual modeled area must be positive")
    area_factor = area / 1000.0   # 10 a = 1,000 m², never gross 3,000 pyeong.
    available = case["owner_available_hours_by_month"]
    if available is not None:
        if not isinstance(available, list) or len(available) != 12:
            raise ValueError("Owner availability must be 12 monthly values or null")
        available = [_num(v, f"owner availability {i+1}")
                     for i, v in enumerate(available)]
    for key in ("operations", "harvests", "facility_events"):
        if not isinstance(case[key], list):
            raise ValueError(f"{key}: expected list")

    horizon = 12
    for index, sale in enumerate(case["harvests"], 1):
        label = f"harvest {index}"
        if set(sale) not in (HARVESTS, HARVESTS_UNITS):
            raise ValueError(f"{label}: required fields differ")
        if set(sale) == HARVESTS_UNITS:
            _text(sale["yield_unit"], f"{label}.yield_unit")
        _text(sale["name"], label)
        _source(sale, label)
        m = _month(sale["month"], label)
        lag = sale["settlement_lag_months"]
        if type(lag) is not int or not 0 <= lag <= 6:
            raise ValueError(f"{label}: settlement lag must be 0..6 months")
        horizon = max(horizon, m + lag)
    ledger = [_ledger_month(i, year) for i in range(1, horizon+1)]
    kinds = {key: 0.0 for key in SOURCES}
    gross_receipts = net_receivables = operating_cost = 0.0
    owner_total = hired_total = capex_total = 0.0
    deposit_outstanding = 0.0
    for index, task in enumerate(case["operations"], 1):
        label = f"operation {index}"
        _exact(task, OPERATIONS, label)
        _text(task["name"], label)
        _source(task, label)
        m = _month(task["month"], label)
        own = _num(task["owner_hours_per_10a"], label) * area_factor
        hired = _num(task["hired_hours_per_10a"], label) * area_factor
        wage = _num(task["hired_wage_krw_per_hour"], label)
        materials = _num(task["materials_krw_per_10a"], label) * area_factor
        contractor = _num(task["contractor_krw_per_10a"], label) * area_factor
        amount = hired*wage + materials + contractor
        row = ledger[m-1]
        row["operating_cash_out_krw"] += amount
        row["owner_hours"] += own
        row["hired_hours"] += hired
        row["activities"].append(task["name"])
        owner_total += own
        hired_total += hired
        operating_cost += amount
        kinds[task["source_kind"]] += 1
    for index, sale in enumerate(case["harvests"], 1):
        label = f"harvest {index}"
        m = sale["month"]
        units_based = set(sale) == HARVESTS_UNITS
        quantity_key = "yield_quantity_per_10a" if units_based else "yield_kg_per_10a"
        price_key = "price_krw_per_unit" if units_based else "price_krw_per_kg"
        deduct_key = "buyer_deduction_krw_per_unit" if units_based else "buyer_deduction_krw_per_kg"
        marketable_qty = _num(sale[quantity_key], label) * area_factor * _num(
            sale["marketable_fraction"], label, cap=1.0)
        price = _num(sale[price_key], label)
        commission = _num(sale["commission_fraction"], label, cap=1.0)
        deduction = _num(sale[deduct_key], label)
        transport = _num(sale["transport_krw_per_10a"], label) * area_factor
        gross = marketable_qty * price
        net = gross * (1 - commission) - marketable_qty * deduction
        if net < 0:
            raise ValueError(f"{label}: negative buyer settlement; revise deductions")
        # Freight is paid at dispatch, while the buyer's fee is deducted
        # from settlement. Never conceal a timing difference.
        ledger[m-1]["operating_cash_out_krw"] += transport
        ledger[m-1]["activities"].append(sale["name"] + " (shipment)")
        ledger[m + sale["settlement_lag_months"]-1]["net_settlement_received_krw"] += net
        gross_receipts += gross
        net_receivables += net
        operating_cost += transport
        kinds[sale["source_kind"]] += 1
    # Stable ordering: collect all deposits by month before refund checks.
    events = sorted(case["facility_events"], key=lambda e: e.get("month", 0))
    for index, event in enumerate(events, 1):
        label = f"facility event {index}"
        _exact(event, FACILITIES, label)
        _text(event["name"], label)
        _source(event, label)
        m = _month(event["month"], label)
        kind = event["kind"]
        if kind not in FACILITY_KINDS:
            raise ValueError(f"{label}: unknown facility event kind")
        amount = _num(event["amount_krw"], label)
        row = ledger[m-1]
        row["activities"].append(event["name"])
        if kind == "OPERATING":
            row["operating_cash_out_krw"] += amount
            operating_cost += amount
        elif kind == "CAPEX":
            row["capital_cash_out_krw"] += amount
            capex_total += amount
        elif kind == "DEPOSIT_PAID":
            row["deposit_paid_krw"] += amount
            deposit_outstanding += amount
        else:
            if amount > deposit_outstanding + 1e-7:
                raise ValueError("Deposit refund cannot exceed prior paid deposits")
            row["deposit_returned_krw"] += amount
            deposit_outstanding -= amount
        kinds[event["source_kind"]] += 1
    cumulative = lowest = 0.0
    for row in ledger:
        row["net_cash_krw"] = (
            row["net_settlement_received_krw"] + row["deposit_returned_krw"]
            - row["operating_cash_out_krw"] - row["capital_cash_out_krw"]
            - row["deposit_paid_krw"]
        )
        cumulative += row["net_cash_krw"]
        row["cumulative_cash_krw"] = cumulative
        lowest = min(lowest, cumulative)
    year_cash = sum(r["net_cash_krw"] for r in ledger[:12])
    receivable_dec31 = sum(r["net_settlement_received_krw"] for r in ledger[12:])
    owner_overflow = (None if available is None else
                      [max(0.0, row["owner_hours"] - available[i])
                       for i, row in enumerate(ledger[:12])])
    return {
        "id": case["id"], "crop": case["crop"], "facility": case["facility"],
        "region": case["region"], "basis_year": year, "area_m2": area,
        "unit": "nominal KRW of input basis_year; months 13-18 retain input-year values",
        "status": "ILLUSTRATIVE_MODEL_NOT_VALIDATED_FARM_RETURN",
        "gross_receipts_krw": gross_receipts,
        "net_receivables_krw": net_receivables,
        "operating_cash_cost_krw": operating_cost,
        "operating_contribution_before_owner_labor_tax_depreciation_krw":
            net_receivables - operating_cost,
        "upfront_capex_krw": capex_total,
        "deposit_outstanding_krw": deposit_outstanding,
        "december_cash_balance_krw": year_cash,
        "unsettled_receivables_after_december_krw": receivable_dec31,
        "cash_after_last_settlement_krw": cumulative,
        "peak_month_end_funding_gap_krw": -lowest,
        "owner_hours": owner_total, "hired_hours": hired_total,
        "owner_hours_over_capacity_by_month": owner_overflow,
        "source_event_counts": {kind: int(count) for kind, count in kinds.items()},
        "months": ledger,
    }


def compare_workflows(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError("Provide at least one crop x facility case")
    ids = [case.get("id") if isinstance(case, dict) else None for case in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate workflow case IDs")
    outputs = [simulate_workflow(case) for case in cases]
    years = {r["basis_year"] for r in outputs}
    if len(years) != 1:
        raise ValueError("Do not compare different nominal basis years without conversion")
    return {"status": "EXPLORATORY_NOT_A_RECOMMENDATION",
            "comparison_rule": "No automatic ranking: different costs, dates, labor and funding gaps must be compared jointly",
            "cases": outputs}
