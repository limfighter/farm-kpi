"""Validate/refresh the 2024 RDA public statistics embedded in the offline crop explorer.

Does not calculate farm profitability or modify the five-plan simulation.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
HTML = ROOT / "dashboard/crop-discovery/index.html"
CATEGORIES = {"식량작물": 7, "노지채소": 12, "시설채소": 17,
              "노지과수": 9, "시설과수": 1, "화훼": 1, "특용·약용": 4}
NUMERIC_INT = ("revenue_krw_per_10a", "management_cost_krw_per_10a",
               "income_krw_per_10a", "yield_quantity", "cycle_years",
               "source_pdf_page", "source_printed_page",
               "labor_source_pdf_page", "labor_source_printed_page")
NUMERIC_FLOAT = ("income_rate_pct", "labor_owner_hours_per_10a",
                 "labor_hired_hours_per_10a", "labor_total_hours_per_10a")
BINDING = re.compile(r"(const DATA=)(\[.*?\])(;\s*\nconst cats=)", re.DOTALL)


def load_source(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
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
        if abs(d["revenue_krw_per_10a"] - d["management_cost_krw_per_10a"] -
               d["income_krw_per_10a"]) > 2:
            raise ValueError("Income reconciliation failed for "+d["crop"])
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


def process(csv_path=CSV, html_path=HTML, *, check=False):
    data = load_source(csv_path)
    path = Path(html_path)
    content = path.read_text(encoding="utf-8")
    found = BINDING.search(content)
    if found is None:
        raise ValueError("Embedded crop data slot was not found in HTML")
    old = json.loads(found.group(2))
    if check:
        if old != data:
            raise ValueError("Crop discovery HTML is STALE relative to the RDA CSV")
        return False
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    content = content[:found.start(2)] + encoded + content[found.end(2):]
    path.write_text(content, encoding="utf-8")
    return old != data


def main():
    p = argparse.ArgumentParser(description="Reconcile public RDA 2024 crop index")
    p.add_argument("--csv", type=Path, default=CSV)
    p.add_argument("--html", type=Path, default=HTML)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--refresh", action="store_true")
    args = p.parse_args()
    process(args.csv, args.html, check=args.check)
    print("RDA 2024 51-crop data valid; offline HTML " +
          ("current" if args.check else "refreshed"))


if __name__ == "__main__":
    main()
