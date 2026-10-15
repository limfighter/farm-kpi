"""Validate the locked national RDA 2024 survey, not parcel income or annual ROI.

The four-year ginseng cycle and published summary/labor page references are
part of this specific 51-crop source contract. Returned rows preserve source
order and text fields while normalizing the declared numeric columns.
"""
import csv
import math
from pathlib import Path

CATEGORIES = {"식량작물": 7, "노지채소": 12, "시설채소": 17,
              "노지과수": 9, "시설과수": 1, "화훼": 1, "특용·약용": 4}
NUMERIC_INT = ("revenue_krw_per_10a", "management_cost_krw_per_10a",
               "income_krw_per_10a", "yield_quantity", "cycle_years",
               "source_pdf_page", "source_printed_page",
               "labor_source_pdf_page", "labor_source_printed_page")
NUMERIC_FLOAT = ("income_rate_pct", "labor_owner_hours_per_10a",
                 "labor_hired_hours_per_10a", "labor_total_hours_per_10a")


def load_source(path):
    """Read and strictly validate the 51 reported crop observations at path."""
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return validate_rows(rows)


def validate_rows(rows):
    """Return normalized copies of source rows without modifying the input."""
    if len(rows) != 51 or len({r["crop_id"] for r in rows}) != 51:
        raise ValueError("Expected 51 unique RDA 2024 survey crops")
    if len({r["crop"] for r in rows}) != 51:
        raise ValueError("Duplicate crop label")
    if {k: sum(r["category"] == k for r in rows) for k in CATEGORIES} != CATEGORIES:
        raise ValueError("Survey categories/counts differ from 2024 book")
    out = []
    for r in rows:
        if r["data_kind"] != "R":
            raise ValueError("Crop discovery accepts reported R data only")
        d = dict(r)
        for k in NUMERIC_INT:
            d[k] = int(d[k])
        for k in NUMERIC_FLOAT:
            d[k] = float(d[k])
            if not math.isfinite(d[k]):
                raise ValueError("Nonfinite "+k)
        if any(d[k] <= 0 for k in (
                "revenue_krw_per_10a", "management_cost_krw_per_10a",
                "income_krw_per_10a", "yield_quantity", "cycle_years")):
            raise ValueError("Non-positive RDA amount/cycle/yield for "+d["crop"])
        if abs(d["revenue_krw_per_10a"] - d["management_cost_krw_per_10a"] -
               d["income_krw_per_10a"]) > 2:
            raise ValueError("Income reconciliation failed for "+d["crop"])
        percent_from_amounts = (
            100 * d["income_krw_per_10a"] / d["revenue_krw_per_10a"])
        if abs(percent_from_amounts - d["income_rate_pct"]) > 0.051:
            raise ValueError("RDA income rate not reconciled for "+d["crop"])
        if any(d[k] < 0 for k in (
                "labor_owner_hours_per_10a",
                "labor_hired_hours_per_10a",
                "labor_total_hours_per_10a")):
            raise ValueError("Negative labor hours for "+d["crop"])
        if (abs(d["labor_owner_hours_per_10a"] + d["labor_hired_hours_per_10a"] -
                d["labor_total_hours_per_10a"]) > .11):
            raise ValueError("Labor reconciliation failed for "+d["crop"])
        if d["source_pdf_page"] not in (17, 18, 19):
            raise ValueError("Unexpected summary page")
        if d["source_pdf_page"] - d["source_printed_page"] != 6:
            raise ValueError("Summary page mismatch")
        if not 127 <= d["labor_source_pdf_page"] <= 177:
            raise ValueError("Unexpected labor page")
        if d["labor_source_pdf_page"] - d["labor_source_printed_page"] != 6:
            raise ValueError("Labor page mismatch")
        out.append(d)
    multi = [(r["crop"], r["cycle_years"]) for r in out if r["cycle_years"] > 1]
    if multi != [("인삼(4년근)", 4)]:
        raise ValueError("Ginseng is a four-year cycle, not annual")
    return out
