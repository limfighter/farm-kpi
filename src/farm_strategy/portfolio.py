"""Multi-crop farm portfolio: shared land, labor, irrigation, power and cash.

Requires explicit occupation windows and resource quantities for every candidate;
no field measurement, crop calendars, utilities, prices or loans are inferred.
Cases remain the v2 1–10y lifecycle schema. Portfolio events are shared ONCE.
All monetary inputs must already be in constant KRW of the start year.
"""
from collections import defaultdict
from datetime import date
import math

from .lifecycle import simulate_multiyear, FACILITY_FIELDS, FACILITY_KINDS, SOURCE_KINDS
from .execution_detail import assess_weekly_labor

SITE_FIELDS = {
    "region", "start_year", "horizon_years", "usable_area_m2",
    "annual_real_discount_rate", "initial_unrestricted_cash_krw",
    "owner_hours_available_by_month", "hired_hours_available_by_month",
    "water_supply_m3_by_month", "electricity_supply_kwh_by_month",
}
PLOT_FIELDS = {"id", "area_m2"}
PLANT_FIELDS = {"plot_id", "case", "occupancies", "resources", "weekly_allocations"}
OCCUPANCY_FIELDS = {"start_year", "start_month", "end_year", "end_month"}
RESOURCE_FIELDS = {
    "year", "month", "water_m3", "electricity_kwh", "water_cost_krw",
    "electricity_cost_krw", "source_kind", "source_ref",
}
FINANCE_FIELDS = {
    "name", "year", "month", "kind", "amount_krw", "source_kind", "source_ref",
}
FINANCE_KINDS = {"DRAW", "INTEREST", "PRINCIPAL"}
PORTFOLIO_FIELDS = {
    "schema_version", "disclaimer", "site", "plots", "plantings",
    "shared_facility_events", "financing_events", "weekly_capacity",
}
WEEKLY_CAPACITY_FIELDS = {"week_start", "owner_available_hours", "hired_available_hours"}


def _fields(x, fields, what):
    if not isinstance(x, dict) or set(x) != fields:
        raise ValueError(f"{what}: schema fields mismatch")


def _text(x, what):
    if not isinstance(x, str) or not x.strip():
        raise ValueError(f"{what}: nonempty text required")


def _number(x, what):
    if type(x) not in (int, float) or not math.isfinite(x) or x < 0:
        raise ValueError(f"{what}: finite nonnegative number required")
    return float(x)


def _period(y, m, years):
    if type(y) is not int or not 1 <= y <= years:
        raise ValueError("Year outside the common horizon")
    if type(m) is not int or not 1 <= m <= 12:
        raise ValueError("Month must be 1..12")
    return (y-1)*12 + m-1


def _source(item):
    if item["source_kind"] not in SOURCE_KINDS:
        raise ValueError("Expected sourced event R/O/T/Q/A")
    _text(item["source_ref"], "source_ref")


def _vector(value, n, name):
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != n:
        raise ValueError(f"{name}: all months required or null")
    return [_number(v, name) if v is not None else None for v in value]


def _monthly_check(demand, capacity):
    if capacity is None:
        return [{"month_index": i+1, "required": v, "available": None,
                 "shortage": None} for i, v in enumerate(demand)]
    return [
        {"month_index": i+1, "required": v, "available": capacity[i],
         "shortage": None if capacity[i] is None else max(0., v-capacity[i])}
        for i, v in enumerate(demand)
    ]


def simulate_portfolio(payload):
    """A complete, opt-in 1–10 year hypothetical farm plan (not farm approval)."""
    _fields(payload, PORTFOLIO_FIELDS, "portfolio")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise ValueError("Portfolio schema_version must be 1")
    _text(payload["disclaimer"], "disclaimer")
    site = payload["site"]
    _fields(site, SITE_FIELDS, "site")
    _text(site["region"], "site.region")
    start, years = site["start_year"], site["horizon_years"]
    if (type(start) is not int or not 2000 <= start <= 2100
            or type(years) is not int or not 1 <= years <= 10
            or start+years > 2101):
        raise ValueError("Portfolio timeline must be valid 1..10 years")
    months = years*12
    area = _number(site["usable_area_m2"], "usable_area_m2")
    if area == 0:
        raise ValueError("Usable area cannot be zero/UNKNOWN")
    cash_initial = _number(site["initial_unrestricted_cash_krw"], "initial cash")
    rate = site["annual_real_discount_rate"]
    if rate is not None and _number(rate, "annual_real_discount_rate") > 1:
        raise ValueError("Real discount rate must be <= 1")
    capacity = {
        "owner": _vector(site["owner_hours_available_by_month"], months, "owner availability"),
        "hired": _vector(site["hired_hours_available_by_month"], months, "hired availability"),
        "water": _vector(site["water_supply_m3_by_month"], months, "water supply"),
        "power": _vector(site["electricity_supply_kwh_by_month"], months, "electricity supply"),
    }
    plots = payload["plots"]
    if not isinstance(plots, list) or not plots:
        raise ValueError("At least one physical plot required")
    capacities = {}
    for plot in plots:
        _fields(plot, PLOT_FIELDS, "plot")
        label = plot["id"]
        _text(label, "plot.id")
        if label in capacities:
            raise ValueError("Duplicate plot identifier")
        v = _number(plot["area_m2"], "plot area")
        if v == 0:
            raise ValueError("Plot area cannot be zero")
        capacities[label] = v
    if sum(capacities.values()) > area+1e-7:
        raise ValueError("Sum of plot areas exceeds usable farm area")
    plantings = payload["plantings"]
    if not isinstance(plantings, list) or not plantings:
        raise ValueError("At least one planted crop scenario required")
    plots_used = {key: [0.] * months for key in capacities}
    owner = [0.] * months
    hired = [0.] * months
    water = [0.] * months
    power = [0.] * months
    bills = [0.] * months
    per_crop = []
    case_ids = set()
    week_demands = defaultdict(lambda: [0., 0.])
    week_detail_complete = True
    month_cash = [0.] * (months+6)
    for plant in plantings:
        _fields(plant, PLANT_FIELDS, "planting")
        if plant["plot_id"] not in capacities:
            raise ValueError("Unknown planting plot")
        case = plant["case"]
        result = simulate_multiyear(case)
        if case["id"] in case_ids:
            raise ValueError("Duplicate crop case ID")
        case_ids.add(case["id"])
        if (case["region"] != site["region"]
                or case["start_year"] != start
                or case["horizon_years"] != years
                or case["annual_real_discount_rate"] != rate):
            raise ValueError("Crop cases must share region/years/discount rate")
        if case["owner_available_hours_by_month"] is not None:
            raise ValueError("Portfolio owns labor capacity; crop-level capacity must be null")
        if case["facility_events"]:
            raise ValueError("To prevent shared cost double counting, case facility_events must be empty")
        if case["area_m2"] > capacities[plant["plot_id"]]+1e-7:
            raise ValueError("Planting area exceeds its plot")
        occ = plant["occupancies"]
        if not isinstance(occ, list) or not occ:
            raise ValueError("Every crop needs explicit land occupation windows")
        occupied = set()
        for window in occ:
            _fields(window, OCCUPANCY_FIELDS, "occupation")
            first = _period(window["start_year"], window["start_month"], years)
            last = _period(window["end_year"], window["end_month"], years)
            if first > last:
                raise ValueError("Occupation cannot end before it starts")
            if any(p in occupied for p in range(first, last+1)):
                raise ValueError("Overlapping occupation windows within a single crop")
            occupied.update(range(first, last+1))
        if any(plots_used[plant["plot_id"]][p] + case["area_m2"] > capacities[plant["plot_id"]] + 1e-7 for p in occupied):
            raise ValueError("Overlapping crop land exceeds available plot area")
        for event in case["operations"]+case["sales"]:
            if _period(event["year"], event["month"], years) not in occupied:
                raise ValueError("Every field operation and crop dispatch must fit its plot occupation")
        for p in occupied:
            plots_used[plant["plot_id"]][p] += case["area_m2"]
        resources = plant["resources"]
        if not isinstance(resources, list):
            raise ValueError("resources must be a list with explicit months")
        resource_months = set()
        for rec in resources:
            _fields(rec, RESOURCE_FIELDS, "resource")
            _source(rec)
            p = _period(rec["year"], rec["month"], years)
            if p in resource_months:
                raise ValueError("Duplicate crop resource month")
            resource_months.add(p)
            if p not in occupied:
                raise ValueError("Resources must be assigned during occupation")
            water[p] += _number(rec["water_m3"], "water_m3")
            power[p] += _number(rec["electricity_kwh"], "electricity_kwh")
            bills[p] += (_number(rec["water_cost_krw"], "water_cost_krw")
                         + _number(rec["electricity_cost_krw"], "electricity_cost_krw"))
        # An absence of resource months is UNKNOWN, never a verified zero.
        if resource_months != occupied:
            raise ValueError("Every occupied crop month needs explicit water/power quantities or data")
        for p, row in enumerate(result["months"]):
            month_cash[p] += row["net_cash_krw"]
            if p < months:
                owner[p] += row["owner_hours"]
                hired[p] += row["hired_hours"]
        allocations = plant["weekly_allocations"]
        if allocations is None:
            week_detail_complete = False
        else:
            weekly = assess_weekly_labor(case, allocations, [])
            for line in weekly["weeks"]:
                week_demands[line["week_start"]][0] += line["owner_required_hours"]
                week_demands[line["week_start"]][1] += line["hired_required_hours"]
        per_crop.append({
            "id": case["id"], "crop": case["crop"], "system": case["system"],
            "plot_id": plant["plot_id"], "area_m2": case["area_m2"],
            "occupied_months": len(occupied),
            "net_expected_settlement_krw": result["net_expected_settlement_krw"],
            "operating_contribution_krw": result[
                "operating_contribution_before_owner_labor_tax_depreciation_krw"],
        })
    occupancy_violations = []
    for key, values in plots_used.items():
        for p, used in enumerate(values):
            if used > capacities[key] + 1e-7:
                occupancy_violations.append({
                    "plot_id": key, "year": start+p//12, "month": p%12+1,
                    "used_m2": used, "plot_m2": capacities[key],
                })
    if occupancy_violations:
        raise ValueError("Overlapping crop land exceeds available plot area")
    share = payload["shared_facility_events"]
    if not isinstance(share, list):
        raise ValueError("shared_facility_events must be list")
    outstanding_deposit = 0.
    shared_capex = 0.
    for p, idx, item in sorted(
        (_period(e["year"], e["month"], years), i, e)
        for i, e in enumerate(share)
    ):
        _fields(item, FACILITY_FIELDS, "shared facility")
        _source(item)
        _text(item["name"], "shared facility name")
        kind, amount = item["kind"], _number(item["amount_krw"], "shared amount")
        if kind not in FACILITY_KINDS:
            raise ValueError("Unknown shared facility event type")
        if kind == "DEPOSIT_PAID":
            outstanding_deposit += amount
            month_cash[p] -= amount
        elif kind == "DEPOSIT_RETURN":
            if amount > outstanding_deposit+1e-7:
                raise ValueError("Returned deposit exceeds paid deposit")
            outstanding_deposit -= amount
            month_cash[p] += amount
        elif kind == "CAPEX":
            shared_capex += amount
            month_cash[p] -= amount
        elif kind == "OPERATING":
            month_cash[p] -= amount
        elif kind == "SALVAGE_RECEIPT":
            month_cash[p] += amount
    for p in range(months):
        month_cash[p] -= bills[p]
    unlevered = month_cash.copy()
    # A financing ledger is NOT a credit quote/approval; never infer interest.
    debt = 0.
    drawn = principal_paid = interest_paid = 0.
    financing = payload["financing_events"]
    if not isinstance(financing, list):
        raise ValueError("financing_events must be list")
    finance_order = {"DRAW":0,"INTEREST":1,"PRINCIPAL":2}
    finance_rows = []
    for i, item in enumerate(financing):
        _fields(item, FINANCE_FIELDS, "financing")
        _source(item)
        _text(item["name"], "financing event")
        if item["kind"] not in FINANCE_KINDS:
            raise ValueError("Unknown financing kind")
        p = _period(item["year"], item["month"], years)
        amount = _number(item["amount_krw"], "financing amount")
        finance_rows.append((p,finance_order[item["kind"]],i,item,amount))
    if any(e[3]["kind"]=="DRAW" and e[4]>0 for e in finance_rows) and not any(
        e[3]["kind"]=="INTEREST" for e in finance_rows
    ):
        raise ValueError("Loans require explicit interest cash events (even for zero interest)")
    for p, _, _, item, amount in sorted(finance_rows):
        kind = item["kind"]
        if kind == "DRAW":
            debt += amount
            drawn += amount
            month_cash[p] += amount
        elif kind == "PRINCIPAL":
            if amount > debt+1e-7:
                raise ValueError("Principal payment exceeds outstanding principal")
            debt -= amount
            principal_paid += amount
            month_cash[p] -= amount
        else:
            interest_paid += amount
            month_cash[p] -= amount
    capacities_report = {
        "owner_hours": _monthly_check(owner,capacity["owner"]),
        "hired_hours": _monthly_check(hired,capacity["hired"]),
        "irrigation_m3": _monthly_check(water,capacity["water"]),
        "electricity_kwh": _monthly_check(power,capacity["power"]),
    }
    weeks = payload["weekly_capacity"]
    if not isinstance(weeks, list):
        raise ValueError("weekly_capacity must be a list")
    week_cap = {}
    for v in weeks:
        _fields(v, WEEKLY_CAPACITY_FIELDS, "weekly_capacity")
        _text(v["week_start"],"week_start")
        try:
            wd=date.fromisoformat(v["week_start"])
        except ValueError as exc:
            raise ValueError("Bad ISO week_start") from exc
        if wd.weekday()!=0 or v["week_start"] in week_cap:
            raise ValueError("Weekly capacity must use unique Mondays")
        week_cap[v["week_start"]]={
            "owner": None if v["owner_available_hours"] is None else _number(v["owner_available_hours"],"weekly owner"),
            "hired": None if v["hired_available_hours"] is None else _number(v["hired_available_hours"],"weekly hired"),
        }
    # Do not compute apparent staffing sufficiency with only a subset of crops.
    weekly_report = None
    if week_detail_complete:
        weekly_report = []
        if set(week_cap) - set(week_demands):
            raise ValueError("Weekly capacity provided for a week with no work")
        for w in sorted(week_demands):
            needed=week_demands[w]
            c=week_cap.get(w,{})
            ca,cb=c.get("owner"),c.get("hired")
            weekly_report.append({
                "week_start":w,"owner_required_hours":needed[0],
                "hired_required_hours":needed[1],
                "owner_available_hours":ca,"hired_available_hours":cb,
                "owner_shortage":None if ca is None else max(0.,needed[0]-ca),
                "hired_shortage":None if cb is None else max(0.,needed[1]-cb),
            })
    elif weeks:
        raise ValueError("Cannot apply shared weekly capacities with partial crop work schedules")
    cumulative = cash_initial
    bottom = min(0.,cumulative)
    month_rows = []
    unlev_npv = 0.
    for p, value in enumerate(month_cash):
        cumulative += value
        bottom = min(bottom,cumulative)
        if rate is not None:
            unlev_npv += unlevered[p]/((1+rate)**((p+1)/12))
        month_rows.append({
            "year":start+p//12,"month":p%12+1,"month_index":p+1,
            "water_m3":water[p] if p<months else 0.,
            "electricity_kwh":power[p] if p<months else 0.,
            "owner_hours":owner[p] if p<months else 0.,
            "hired_hours":hired[p] if p<months else 0.,
            "unlevered_cash_krw":unlevered[p],
            "financed_cash_krw":value,"balance_after_financing_krw":cumulative,
        })
    return {
        "status":"HYPOTHETICAL_MULTI_CROP_NOT_SITE_OR_CREDIT_APPROVAL",
        "disclaimer":payload["disclaimer"],
        "start_year":start,"horizon_years":years,
        "total_usable_area_m2":area,
        "plot_area_m2":sum(capacities.values()),
        "unallocated_area_m2":area-sum(capacities.values()),
        "per_crop":per_crop,
        "land_occupancy_m2_by_plot":plots_used,
        "resource_and_labor_limits":capacities_report,
        "weekly_labor":weekly_report,
        "weekly_labor_status":"COMPLETE_FOR_ENTERED_CROPS" if week_detail_complete else "UNKNOWN_PARTIAL_WORK_DATES",
        "shared_capex_krw":shared_capex,
        "shared_unreturned_deposit_krw":outstanding_deposit,
        "financing":{"status":"EXPLICIT_UNVERIFIED_SCHEDULE" if financing else "NOT_ENTERED_UNKNOWN",
                     "drawn_krw":drawn,"principal_repaid_krw":principal_paid,
                     "interest_paid_krw":interest_paid,
                     "outstanding_principal_krw":debt},
        "monthly":month_rows,
        "unlevered_npv_if_rate_supplied_krw":unlev_npv if rate is not None else None,
        "ending_cash_krw":cumulative,
        "maximum_month_end_cash_shortfall_krw":max(0.,-bottom),
        "caveat":"Site permits/soil, water quality, peak flow/electric kW, full loan amortization and climate crop yields remain UNKNOWN.",
    }
