"""Local farm record intake and explicitly assumed price/yield/resource stress cases.

The two outputs have DIFFERENT epistemic status:
* Field log rows can be self-reported O (observed) / T (settled), or A demo
  assumptions. No raw invoice, buyer, contact, parcel, address is stored here.
* Stress cases are A assumptions even when a published reference motivates them.
No source code path upgrades observations into forecasts or recalibrates harvest
labor, commodity prices, weather losses or production functions automatically.
"""
import csv
from collections import defaultdict
from copy import deepcopy
from datetime import date
import math
from pathlib import Path
import re

from .portfolio import simulate_portfolio

LOG_HEADERS = (
    "date", "case_id", "kind", "category", "quantity", "unit",
    "amount_krw", "owner_hours", "hired_hours", "source_kind", "source_ref"
)
LOG_KINDS = {
    "WORK": {"O", "A"},
    "HARVEST": {"O", "A"},
    "SETTLEMENT": {"T", "A"},
    "EXPENSE": {"T", "A"},
    "WATER_USE": {"O", "A"},
    "POWER_USE": {"O", "A"},
}
EXPENSE_CATEGORIES = {
    "MATERIALS", "FERTILIZER", "PEST_CONTROL", "HIRED_LABOR",
    "PACKAGING", "FREIGHT", "UTILITIES", "REPAIR", "OTHER",
}
STRESS_FIELDS = {
    "id", "description", "case_factors", "water_supply_factor",
    "electricity_supply_factor", "months_affected", "source_kind", "source_ref",
}
CROP_FACTOR_FIELDS = {"yield_factor", "price_factor"}
SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9_-]{3,64}$")
MAX_LOG_ROWS = 100000


def _nonnegative(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name}: expected finite nonnegative number")
    return float(value)


def _multiplier(value, name):
    v = _nonnegative(value, name)
    if v > 3:
        raise ValueError(f"{name}: stress multiplier must not exceed 3")
    return v


def _numeric_csv(raw, name):
    if raw == "":
        return None
    try:
        value = float(raw)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{name}: not a number") from e
    return _nonnegative(value, name)


def _parse_date(value):
    try:
        d = date.fromisoformat(value)
        if d.isoformat() != value:
            raise ValueError("non-ISO")
        return d
    except (ValueError, TypeError) as e:
        raise ValueError("Log date must be ISO YYYY-MM-DD") from e


def _required_blank(row, keys, name):
    if any(row[k] != "" for k in keys):
        raise ValueError(f"{name}: unexpected value in unused numeric field")


def _source_id(raw):
    if not SAFE_REFERENCE.fullmatch(raw):
        raise ValueError("source_ref must be a redacted 3..64 character reference ID")


def read_farm_log(csv_path, portfolio):
    """Read ONLY redacted local records; aggregate; do not echo source IDs.

    Harvest and settlement are separate event types: settlement is ACTUAL bank
    receipt, not billed harvest revenue. Expenses are ACTUAL paid expenses.
    These partial aggregates must never be netted against a modeled whole-year
    profit as if coverage were complete.
    """
    model = simulate_portfolio(portfolio)
    case_ids = {p["case"]["id"] for p in portfolio["plantings"]}
    crop_unit = {
        p["case"]["id"]: {s["quantity_unit"] for s in p["case"]["sales"]}
        for p in portfolio["plantings"]
    }
    first_year = portfolio["site"]["start_year"]
    last_year = first_year + portfolio["site"]["horizon_years"] - 1
    observed = defaultdict(lambda: {
        "rows": 0, "source_counts": {"O": 0, "T": 0, "A": 0},
        "kind_rows": {name: 0 for name in LOG_KINDS},
        "_owner_hours_present": 0, "_hired_hours_present": 0,
        "owner_hours_recorded": 0., "hired_hours_recorded": 0.,
        "harvest_quantity_by_unit": {},
        "settled_quantity_by_unit": {}, "settled_cash_krw": 0.,
        "paid_expense_krw": 0., "expense_by_category_krw": {},
        "water_m3_recorded": 0., "electricity_kwh_recorded": 0.,
    })
    total = 0
    seen_rows = set()
    seen_settlements = set()
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, strict=True)
        if reader.fieldnames is None or tuple(reader.fieldnames) != LOG_HEADERS:
            raise ValueError("Log CSV requires exact documented columns")
        for i, row in enumerate(reader, 1):
            if i > MAX_LOG_ROWS:
                raise ValueError("Too many log rows")
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Unexpected extra/missing CSV columns")
            if any(v != v.strip() for v in row.values()):
                raise ValueError("CSV values must not have surrounding spaces")
            dt = _parse_date(row["date"])
            if not first_year <= dt.year <= last_year:
                raise ValueError("Log date outside case horizon")
            ident = row["case_id"]
            if ident not in case_ids:
                raise ValueError("Log crop case_id not in selected portfolio")
            kind = row["kind"]
            if kind not in LOG_KINDS or row["source_kind"] not in LOG_KINDS.get(kind, set()):
                raise ValueError("Log kind incompatible with claimed provenance class")
            _source_id(row["source_ref"])
            if row["source_kind"] in {"O", "T"} and dt > date.today():
                raise ValueError("Future-dated evidence cannot be O/T")
            q = _numeric_csv(row["quantity"], "quantity")
            amount = _numeric_csv(row["amount_krw"], "amount_krw")
            own = _numeric_csv(row["owner_hours"], "owner_hours")
            hired = _numeric_csv(row["hired_hours"], "hired_hours")
            category = row["category"]
            unit = row["unit"]
            if kind == "WORK":
                if category or unit or q is not None or amount is not None:
                    raise ValueError("WORK requires hours only")
                if own is None and hired is None:
                    raise ValueError("WORK requires at least one recorded hours field")
            elif kind in {"HARVEST", "SETTLEMENT"}:
                if category or unit not in crop_unit[ident] or q is None or own is not None or hired is not None:
                    raise ValueError("HARVEST/SETTLEMENT require known crop sale unit and quantity")
                if kind == "HARVEST" and amount is not None:
                    raise ValueError("HARVEST cannot claim cash collection")
                if kind == "SETTLEMENT" and amount is None:
                    raise ValueError("SETTLEMENT must record actual received net cash")
            elif kind == "EXPENSE":
                if category not in EXPENSE_CATEGORIES or unit or q is not None or amount is None or own is not None or hired is not None:
                    raise ValueError("EXPENSE requires category and actual paid amount")
            elif kind in {"WATER_USE", "POWER_USE"}:
                required = "m3" if kind == "WATER_USE" else "kWh"
                if category or unit != required or q is None or amount is not None or own is not None or hired is not None:
                    raise ValueError("Utility use requires correctly dimensioned quantity, not cash")
            fingerprint = tuple(row[name] for name in LOG_HEADERS)
            if fingerprint in seen_rows:
                raise ValueError("Duplicate farm log row; remove repeated imports")
            seen_rows.add(fingerprint)
            # A settled transfer must be a single booking per crop/day/reference/unit.
            # Different transfers from the same buyer need different local IDs.
            if kind == "SETTLEMENT":
                booking = (ident, row["date"], row["source_ref"], unit)
                if booking in seen_settlements:
                    raise ValueError("Duplicate settlement reference on the same crop and day")
                seen_settlements.add(booking)
            a = observed[ident]
            a["kind_rows"][kind] += 1
            a["rows"] += 1
            a["source_counts"][row["source_kind"]] += 1
            if kind == "WORK":
                a["_owner_hours_present"] += (own is not None)
                a["_hired_hours_present"] += (hired is not None)
                a["owner_hours_recorded"] += own or 0.
                a["hired_hours_recorded"] += hired or 0.
            elif kind == "HARVEST":
                a["harvest_quantity_by_unit"][unit] = a["harvest_quantity_by_unit"].get(unit, 0.) + q
            elif kind == "SETTLEMENT":
                a["settled_quantity_by_unit"][unit] = a["settled_quantity_by_unit"].get(unit, 0.) + q
                a["settled_cash_krw"] += amount
            elif kind == "EXPENSE":
                a["paid_expense_krw"] += amount
                a["expense_by_category_krw"][category] = a["expense_by_category_krw"].get(category, 0.) + amount
            elif kind == "WATER_USE":
                a["water_m3_recorded"] += q
            else:
                a["electricity_kwh_recorded"] += q
            total += 1
    forecasts = {p["id"]: p for p in model["per_crop"]}
    results = []
    for ident in sorted(case_ids):
        a = observed[ident]  # even absent crop gets a zero-row, NOT a 0 harvest
        # A zero can be reported ONLY if at least one relevant row explicitly
        # recorded that metric. No row -> null/UNKNOWN, not measured zero.
        counts = a["kind_rows"]
        recorded = {
            "owner_hours_recorded": (a["owner_hours_recorded"] if a["_owner_hours_present"] else None),
            "hired_hours_recorded": (a["hired_hours_recorded"] if a["_hired_hours_present"] else None),
            "harvest_quantity_by_unit": (a["harvest_quantity_by_unit"] if counts["HARVEST"] else None),
            "settled_quantity_by_unit": (a["settled_quantity_by_unit"] if counts["SETTLEMENT"] else None),
            "settled_cash_krw": (a["settled_cash_krw"] if counts["SETTLEMENT"] else None),
            "paid_expense_krw": (a["paid_expense_krw"] if counts["EXPENSE"] else None),
            "expense_by_category_krw": (a["expense_by_category_krw"] if counts["EXPENSE"] else None),
            "water_m3_recorded": (a["water_m3_recorded"] if counts["WATER_USE"] else None),
            "electricity_kwh_recorded": (a["electricity_kwh_recorded"] if counts["POWER_USE"] else None),
        }
        results.append({
            "case_id": ident, "recorded_rows": a["rows"],
            "coverage": "PARTIAL_UNVERIFIED" if a["rows"] else "NO_RECORDS_UNKNOWN",
            "record_kind_counts": counts,
            "provenance_claim_counts": a["source_counts"],
            "recorded": recorded,
            "scenario_forecast_net_settlement_krw": forecasts[ident]["net_expected_settlement_krw"],
        })
    return {
        "status": "LOCAL_REDACTED_FIELD_LOG_NOT_RECONCILED_FULL_FARM_ACCOUNTS",
        "rows": total, "cases": results,
        "unmodeled_logs_do_not_change_scenario_cash": True,
        "warning": "Only supplied rows were aggregated; unrecorded metrics export as null/UNKNOWN, explicit recorded zero stays 0. Duplicate rows/settlement references are rejected. A/O/T labels are self-reported and NOT externally verified. Do not subtract partial expenses from modeled proceeds. Even minimized reports contain crop case IDs; review before sharing. Do not post raw receipts, names, locations or account numbers.",
    }


def _site_factors(vector, scale, month_indices):
    if vector is None:
        return None
    return [None if v is None else v * scale if (i+1) in month_indices else v
            for i, v in enumerate(vector)]


def _shortfall_summary(r, key):
    values = r["resource_and_labor_limits"][key]
    return {
        "months_short": sum(x["shortage"] is not None and x["shortage"] > 0 for x in values),
        "months_supply_unknown": sum(x["available"] is None for x in values),
        "maximum_shortage": (max((x["shortage"] or 0. for x in values
                                  if x["shortage"] is not None), default=None)),
    }


def stress_portfolio(portfolio, cases):
    """Deterministic independent shocks: no invented price↔weather causal model."""
    baseline = simulate_portfolio(portfolio)
    if not isinstance(cases, list) or not cases:
        raise ValueError("At least one explicit stress scenario required")
    n = portfolio["site"]["horizon_years"] * 12
    known = {p["case"]["id"] for p in portfolio["plantings"]}
    outputs = []
    seen = set()
    for scenario in cases:
        if not isinstance(scenario, dict) or set(scenario) != STRESS_FIELDS:
            raise ValueError("Stress case requires exact fields")
        ident = scenario["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("Each stress scenario ID must be unique")
        seen.add(ident)
        if not isinstance(scenario["description"], str) or not scenario["description"].strip():
            raise ValueError("Stress description required")
        if scenario["source_kind"] != "A":
            raise ValueError("Scenario transformations are always A, never observed facts")
        _source_id(scenario["source_ref"])
        factors = scenario["case_factors"]
        if not isinstance(factors, dict) or not set(factors).issubset(known):
            raise ValueError("Unknown stress crop case ID")
        out = deepcopy(portfolio)
        applied = {}
        for plant in out["plantings"]:
            case_id = plant["case"]["id"]
            if case_id not in factors:
                continue
            factor = factors[case_id]
            if not isinstance(factor, dict) or set(factor) != CROP_FACTOR_FIELDS:
                raise ValueError("Crop shock requires yield_factor and price_factor")
            yf = _multiplier(factor["yield_factor"], "yield_factor")
            pf = _multiplier(factor["price_factor"], "price_factor")
            for sale in plant["case"]["sales"]:
                sale["quantity_per_10a"] *= yf
                sale["price_krw_per_unit"] *= pf
                sale["source_kind"] = "A"
                sale["source_ref"] = scenario["source_ref"]
            applied[case_id] = {"yield_factor": yf, "price_factor": pf}
        ws = _multiplier(scenario["water_supply_factor"], "water_supply_factor")
        es = _multiplier(scenario["electricity_supply_factor"], "electricity_supply_factor")
        affected = scenario["months_affected"]
        if not isinstance(affected, list) or not all(type(x) is int and 1 <= x <= n for x in affected):
            raise ValueError("months_affected must be 1-based month indices")
        if len(set(affected)) != len(affected):
            raise ValueError("Duplicate affected month")
        if not affected:
            affected = list(range(1, n+1))
        for field, scale in (("water_supply_m3_by_month", ws),
                             ("electricity_supply_kwh_by_month", es)):
            out["site"][field] = _site_factors(out["site"][field], scale, set(affected))
        stressed = simulate_portfolio(out)
        summaries = {
            key: {"baseline": _shortfall_summary(baseline, key),
                  "stressed": _shortfall_summary(stressed, key)}
            for key in ("irrigation_m3", "electricity_kwh")
        }
        # Financial deltas alone are not a viable planting plan: shortages
        # are operational blockers even when the model has no yield-loss link.
        if any(z["stressed"]["months_supply_unknown"] for z in summaries.values()):
            physical_supply_status = "SUPPLY_UNKNOWN_NOT_EVALUABLE"
        elif any(z["stressed"]["months_short"] for z in summaries.values()):
            physical_supply_status = "RESOURCE_DEFICIT_UNPRICED_YIELD_RISK"
        else:
            physical_supply_status = "NO_MODELED_MONTHLY_RESOURCE_DEFICIT"
        delta_settlements = sum(p["net_expected_settlement_krw"] for p in stressed["per_crop"]) - sum(
            p["net_expected_settlement_krw"] for p in baseline["per_crop"])
        delta_cash = stressed["ending_cash_krw"] - baseline["ending_cash_krw"]
        delta_npv = (None if baseline["unlevered_npv_if_rate_supplied_krw"] is None
                     else stressed["unlevered_npv_if_rate_supplied_krw"] -
                     baseline["unlevered_npv_if_rate_supplied_krw"])
        outputs.append({
            "id": ident, "description": scenario["description"],
            "source_kind": "A", "source_ref": scenario["source_ref"],
            "crop_factors": applied, "supply_month_indices": affected,
            "net_expected_settlement_delta_krw": delta_settlements,
            "unlevered_npv_delta_krw_if_rate_supplied": delta_npv,
            "ending_cash_delta_krw": delta_cash,
            "stressed_end_cash_krw": stressed["ending_cash_krw"],
            "stressed_peak_month_end_cash_shortfall_krw": stressed["maximum_month_end_cash_shortfall_krw"],
            "peak_month_end_cash_shortfall_delta_krw": (
                stressed["maximum_month_end_cash_shortfall_krw"] -
                baseline["maximum_month_end_cash_shortfall_krw"]),
            "scarcity": summaries,
            "physical_supply_status": physical_supply_status,
            "financial_result_is_conditional_not_feasibility_approval": True,
        })
    return {
        "status": "EXPLICIT_STRESS_NOT_PROBABILISTIC_YIELD_OR_CROP_RECOMMENDATION",
        "baseline_ending_cash_krw": baseline["ending_cash_krw"],
        "baseline_peak_month_end_cash_shortfall_krw": baseline["maximum_month_end_cash_shortfall_krw"],
        "scenarios": outputs,
        "warning": "Yield×price interact multiplicatively, but labor, crop quality, utility consumption, settlement timing and capital costs remain as input. Water/power shortages do NOT magically reduce yield; users must declare yield loss as a separate assumption. No scenario probabilities, actual weather or risk-adjusted ROI inferred.",
    }


def analyze_farm(portfolio, scenario_def, log_path=None):
    if not isinstance(scenario_def, dict) or set(scenario_def) != {"schema_version", "disclaimer", "scenarios"}:
        raise ValueError("Stress definition fields mismatch")
    if type(scenario_def["schema_version"]) is not int or scenario_def["schema_version"] != 1:
        raise ValueError("Stress schema_version must be 1")
    if not isinstance(scenario_def["disclaimer"], str) or not scenario_def["disclaimer"].strip():
        raise ValueError("Stress disclaimer required")
    result = {
        "stress": stress_portfolio(portfolio, scenario_def["scenarios"]),
        "field_log": None if log_path is None else read_farm_log(log_path, portfolio),
        "disclaimer": scenario_def["disclaimer"],
    }
    return result
