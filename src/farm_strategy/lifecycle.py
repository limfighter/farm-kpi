"""Explicit multi-year crop × facility cash ledger, not a profit forecast.

Every operation, sale and facility cash event must state its own relative year,
month, amount, unit and source. NO implicit annual repetition, site feasibility,
loans, tax, inflation adjustment, depreciation or observed risk distributions.
All cash amounts use constant KRW of the declared start year.
"""
import math

SOURCE_KINDS = {"A", "R", "O", "T", "Q"}
NO_SALES = {"PRE_PRODUCTIVE_WINDOW", "DOCUMENTED_NO_SALES"}
CASE_FIELDS = {
    "id", "crop", "system", "region", "start_year", "horizon_years",
    "area_m2", "annual_real_discount_rate", "owner_hour_value_krw",
    "owner_available_hours_by_month", "no_sales_reason",
    "operations", "sales", "facility_events",
}
OP_FIELDS = {
    "name", "year", "month", "owner_hours_per_10a", "hired_hours_per_10a",
    "hired_hour_wage_krw", "materials_krw_per_10a",
    "contractor_krw_per_10a", "source_kind", "source_ref",
}
SALE_FIELDS = {
    "name", "year", "month", "quantity_per_10a", "quantity_unit",
    "marketable_fraction", "price_krw_per_unit",
    "commission_fraction", "deduction_krw_per_unit", "transport_krw_per_10a",
    "settlement_lag_months", "source_kind", "source_ref",
}
FACILITY_FIELDS = {
    "name", "year", "month", "kind", "amount_krw", "source_kind", "source_ref",
}
FACILITY_KINDS = {
    "OPERATING", "CAPEX", "DEPOSIT_PAID", "DEPOSIT_RETURN", "SALVAGE_RECEIPT",
}


def _shape(item, fields, label):
    if not isinstance(item, dict) or set(item) != fields:
        raise ValueError(f"{label}: required fields differ; no silent fallbacks")


def _text(s, label):
    if not isinstance(s, str) or not s.strip():
        raise ValueError(f"{label}: expected nonempty text")
    return s


def _money(x, label, cap=None):
    if type(x) not in (int, float) or not math.isfinite(x) or x < 0:
        raise ValueError(f"{label}: expected finite nonnegative input")
    if cap is not None and x > cap:
        raise ValueError(f"{label}: value exceeds {cap}")
    return float(x)


def _year_month(item, limit, label):
    y, m = item["year"], item["month"]
    if type(y) is not int or not 1 <= y <= limit:
        raise ValueError(f"{label}: expected year 1..{limit}")
    if type(m) is not int or not 1 <= m <= 12:
        raise ValueError(f"{label}: expected month 1..12")
    return (y - 1) * 12 + m - 1


def _provenance(item, label):
    if item["source_kind"] not in SOURCE_KINDS:
        raise ValueError(f"{label}: expected source R/O/T/Q/A")
    _text(item["source_ref"], f"{label}.source_ref")


def _month_entry(index, start_year):
    return {
        "year": start_year + index // 12, "month": index % 12 + 1,
        "period_index": index + 1, "activities": [],
        "settled_sales_received_krw": 0.0,
        "operating_expense_krw": 0.0,
        "capital_expenditure_krw": 0.0,
        "deposit_paid_krw": 0.0,
        "deposit_return_krw": 0.0,
        "salvage_received_krw": 0.0,
        "owner_hours": 0.0, "hired_hours": 0.0,
    }


def simulate_multiyear(case):
    """Simulate 1–10 explicit years plus tail settlements, no repeated annual rows.

    Prices and costs in constant start-year KRW. The annual discount rate is an
    optional **input assumption**; absent -> NPV is null, never an implicit 0%.
    """
    _shape(case, CASE_FIELDS, "case")
    for field in ("id", "crop", "system", "region"):
        _text(case[field], field)
    y0, years = case["start_year"], case["horizon_years"]
    if (type(y0) is not int or not 2000 <= y0 <= 2100
            or type(years) is not int or not 1 <= years <= 10
            or y0 + years > 2101):
        raise ValueError("Start year/horizon_years must define 1–10 years by 2100")
    months = years * 12
    area = _money(case["area_m2"], "area_m2")
    if not area:
        raise ValueError("area_m2 must be positive; UNKNOWN is not zero")
    multiplier = area / 1000.0
    rate = case["annual_real_discount_rate"]
    if rate is not None:
        rate = _money(rate, "annual_real_discount_rate", cap=1.0)
    owner_value = case["owner_hour_value_krw"]
    if owner_value is not None:
        owner_value = _money(owner_value, "owner_hour_value_krw")
    availability = case["owner_available_hours_by_month"]
    if availability is not None:
        if not isinstance(availability, list) or len(availability) != months:
            raise ValueError("Owner availability must cover every modeled month or be null")
        availability = [_money(v, "owner availability") for v in availability]
    reason = case["no_sales_reason"]
    for key in ("operations", "sales", "facility_events"):
        if not isinstance(case[key], list):
            raise ValueError(f"{key} must be a list")
    if not case["operations"] and not case["facility_events"]:
        raise ValueError("Model needs explicit operations or facility events")
    if case["sales"]:
        if reason is not None:
            raise ValueError("no_sales_reason must be null with sales")
    elif reason not in NO_SALES:
        raise ValueError("Empty sales require explicit PRE_PRODUCTIVE_WINDOW or DOCUMENTED_NO_SALES")
    sale_periods = []
    for i, sale in enumerate(case["sales"], 1):
        label = f"sale {i}"
        _shape(sale, SALE_FIELDS, label)
        _text(sale["name"], label)
        _text(sale["quantity_unit"], f"{label}.quantity_unit")
        _provenance(sale, label)
        period = _year_month(sale, years, label)
        lag = sale["settlement_lag_months"]
        if type(lag) is not int or not 0 <= lag <= 6:
            raise ValueError(f"{label}: settlement lag must be 0..6 months")
        sale_periods.append(period + lag)
    timeline = [_month_entry(i, y0)
                for i in range(max(months, max(sale_periods, default=-1) + 1))]
    totals = {kind: 0 for kind in SOURCE_KINDS}
    gross = net_expected = operating = capex = 0.0
    owner_total = hired_total = deposit = salvage = 0.0

    for i, op in enumerate(case["operations"], 1):
        label = f"operation {i}"
        _shape(op, OP_FIELDS, label)
        _text(op["name"], label)
        _provenance(op, label)
        p = _year_month(op, years, label)
        owner = _money(op["owner_hours_per_10a"], label) * multiplier
        hired = _money(op["hired_hours_per_10a"], label) * multiplier
        wage = _money(op["hired_hour_wage_krw"], label)
        materials = _money(op["materials_krw_per_10a"], label) * multiplier
        contractors = _money(op["contractor_krw_per_10a"], label) * multiplier
        expense = hired * wage + materials + contractors
        row = timeline[p]
        row["activities"].append(op["name"])
        row["operating_expense_krw"] += expense
        row["owner_hours"] += owner
        row["hired_hours"] += hired
        owner_total += owner
        hired_total += hired
        operating += expense
        totals[op["source_kind"]] += 1

    for i, sale in enumerate(case["sales"], 1):
        label = f"sale {i}"
        p = _year_month(sale, years, label)
        qty = (_money(sale["quantity_per_10a"], label)
               * multiplier * _money(sale["marketable_fraction"], label, cap=1.0))
        price = _money(sale["price_krw_per_unit"], label)
        commission = _money(sale["commission_fraction"], label, cap=1.0)
        deduction = _money(sale["deduction_krw_per_unit"], label)
        transport = _money(sale["transport_krw_per_10a"], label) * multiplier
        gross_sale = qty * price
        settlement = gross_sale * (1.0 - commission) - qty * deduction
        if settlement < 0:
            raise ValueError(f"{label}: invalid negative buyer settlement")
        timeline[p]["operating_expense_krw"] += transport
        timeline[p]["activities"].append(sale["name"] + " (dispatch)")
        timeline[p + sale["settlement_lag_months"]][
            "settled_sales_received_krw"] += settlement
        gross += gross_sale
        net_expected += settlement
        operating += transport
        totals[sale["source_kind"]] += 1

    ordered = []
    for i, e in enumerate(case["facility_events"], 1):
        label = f"facility {i}"
        _shape(e, FACILITY_FIELDS, label)
        _text(e["name"], label)
        _provenance(e, label)
        p = _year_month(e, years, label)
        if e["kind"] not in FACILITY_KINDS:
            raise ValueError(f"{label}: unknown facility event")
        ordered.append((p, i, e))
    for p, _, e in sorted(ordered):
        amount = _money(e["amount_krw"], "facility.amount_krw")
        row = timeline[p]
        row["activities"].append(e["name"])
        kind = e["kind"]
        if kind == "OPERATING":
            row["operating_expense_krw"] += amount
            operating += amount
        elif kind == "CAPEX":
            row["capital_expenditure_krw"] += amount
            capex += amount
        elif kind == "DEPOSIT_PAID":
            row["deposit_paid_krw"] += amount
            deposit += amount
        elif kind == "DEPOSIT_RETURN":
            if amount > deposit + 1e-7:
                raise ValueError("Deposit return exceeds prior deposits")
            row["deposit_return_krw"] += amount
            deposit -= amount
        else:
            row["salvage_received_krw"] += amount
            salvage += amount
        totals[e["source_kind"]] += 1
    cumulative = lowest = 0.0
    project_npv = economic_npv = 0.0
    for i, row in enumerate(timeline):
        cash = (row["settled_sales_received_krw"]
                + row["deposit_return_krw"] + row["salvage_received_krw"]
                - row["operating_expense_krw"] - row["capital_expenditure_krw"]
                - row["deposit_paid_krw"])
        row["net_cash_krw"] = cash
        cumulative += cash
        row["cumulative_cash_krw"] = cumulative
        lowest = min(lowest, cumulative)
        if rate is not None:
            discount = (1.0 + rate) ** ((i + 1) / 12)
            project_npv += cash / discount
            if owner_value is not None:
                economic_npv += (cash - row["owner_hours"] * owner_value) / discount
    during = timeline[:months]
    tail = timeline[months:]
    op_contribution = net_expected - operating
    overcapacity = (None if availability is None else [
        max(0.0, during[i]["owner_hours"] - available)
        for i, available in enumerate(availability)
    ])
    yearly = []
    for y in range(years):
        rows = during[y*12:(y+1)*12]
        yearly.append({
            "year": y0+y, "operating_expense_krw": sum(v["operating_expense_krw"] for v in rows),
            "received_krw": sum(v["settled_sales_received_krw"] for v in rows),
            "capex_krw": sum(v["capital_expenditure_krw"] for v in rows),
            "net_cash_krw": sum(v["net_cash_krw"] for v in rows),
            "owner_hours": sum(v["owner_hours"] for v in rows),
            "hired_hours": sum(v["hired_hours"] for v in rows),
        })
    return {
        "id": case["id"], "crop": case["crop"], "system": case["system"],
        "region": case["region"], "start_year": y0, "horizon_years": years,
        "area_m2": area, "unit": "constant start_year KRW, not inflation-adjusted transactions",
        "source_event_counts": totals, "no_sales_reason": reason,
        "status": "EXPLICIT_INPUTS_MODEL_NOT_VALIDATED_PROFIT_FORECAST",
        "gross_expected_revenue_krw": gross,
        "net_expected_settlement_krw": net_expected,
        "operating_cash_cost_krw": operating,
        "operating_contribution_before_owner_labor_tax_depreciation_krw": op_contribution,
        "capital_expenditure_krw": capex,
        "salvage_received_krw": salvage, "deposit_outstanding_krw": deposit,
        "owner_hours": owner_total, "hired_hours": hired_total,
        "owner_hours_over_capacity_by_month": overcapacity,
        "cash_end_of_horizon_krw": sum(v["net_cash_krw"] for v in during),
        "unsettled_settlement_after_horizon_krw": sum(
            v["settled_sales_received_krw"] for v in tail),
        "cash_after_last_settlement_krw": cumulative,
        "peak_month_end_funding_gap_krw": -lowest,
        "annual_real_discount_rate_input": rate,
        "project_npv_krw_if_rate_supplied": project_npv if rate is not None else None,
        "economic_npv_krw_if_owner_value_and_rate_supplied":
            economic_npv if rate is not None and owner_value is not None else None,
        "years": yearly, "months": timeline,
    }


def compare_multiyear(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError("Expected nonempty list of crop × system multi-year plans")
    results = [simulate_multiyear(case) for case in cases]
    if len({x["id"] for x in results}) != len(results):
        raise ValueError("Scenario IDs must be unique")
    if len({(x["start_year"], x["horizon_years"],
             x["annual_real_discount_rate_input"]) for x in results}) != 1:
        raise ValueError("Cannot compare mismatched time windows/discount assumptions")
    return {
        "status": "EXPLORATORY_NOT_INVESTMENT_APPROVAL",
        "comparison_rule": "No automatic crop recommendation; crop, facility, area and uncertainty differ",
        "cases": results,
    }
