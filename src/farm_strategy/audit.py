"""Read-only audit of derived KMA ASOS files; no zero-filling of rainfall gaps.

Daily and annual CSVs are *derivatives*, not independently verified raw observations.
Weather damage, crop prices and pest probabilities are outside this audit.
"""
import argparse
import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import math
from pathlib import Path

ANNUAL_REQUIRED = (
    "year", "n_days", "valid_temp_days", "hot33_maysep", "frost0_marapr",
    "rain40_maysep", "annual_rain_known_mm", "rain_measured_hours",
)
DAILY_REQUIRED = (
    "date", "year", "month", "t_count", "tmax", "tmin",
    "rain_known_mm", "rain_measured_hours",
)


def read_csv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"Missing columns in {path}: {sorted(set(required) - set(reader.fieldnames or []))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty CSV: {path}")
    return rows


def exact_int(value, label):
    n = float(value)
    if not math.isfinite(n) or n != int(n):
        raise ValueError(f"Invalid integer {label}: {value!r}")
    return int(n)


def annual_audit(annual_path, daily_path=None, metadata_path=None):
    annual = read_csv(annual_path, ANNUAL_REQUIRED)
    years = [exact_int(row["year"], "year") for row in annual]
    if years != list(range(2006, 2026)):
        raise ValueError("Expected chronological unique years 2006..2025")
    for row in annual:
        y = int(row["year"])
        days = (date(y + 1, 1, 1) - date(y, 1, 1)).days
        if exact_int(row["n_days"], "n_days") != days:
            raise ValueError(f"Incomplete year {y}: n_days")
        valid = exact_int(row["valid_temp_days"], "valid_temp_days")
        if not 0 <= valid <= days:
            raise ValueError(f"Invalid valid_temp_days: {y}")
        for key in ("hot33_maysep", "frost0_marapr", "rain40_maysep", "rain_measured_hours"):
            if exact_int(row[key], key) < 0:
                raise ValueError(f"Negative count {key}: {y}")
        if not math.isfinite(float(row["annual_rain_known_mm"])) or float(row["annual_rain_known_mm"]) < 0:
            raise ValueError(f"Invalid recorded rainfall: {y}")
    periods = {}
    for lo, hi in ((2006, 2015), (2016, 2025)):
        subset = [row for row in annual if lo <= int(row["year"]) <= hi]
        periods[f"{lo}-{hi}"] = {
            k: round(sum(int(r[k]) for r in subset) / len(subset), 1)
            for k in ("hot33_maysep", "frost0_marapr", "rain40_maysep")
        }
    result = {
        "source_kind": "derived_observations_not_raw_hourly_data",
        "years": [years[0], years[-1]],
        "annual_records": len(annual),
        "days_from_annual": sum(int(row["n_days"]) for row in annual),
        "rain_numeric_hours": sum(int(row["rain_measured_hours"]) for row in annual),
        "precipitation_status": "RECORDED_LOWER_BOUND_NOT_CERTIFIED_DAILY_TOTAL",
        "period_means": periods,
        "daily_crosscheck": "NOT_PERFORMED",
        "hourly_qc": "NOT_RECHECKED_WITHOUT_ORIGINAL_HOURLY_CSV",
    }
    if daily_path:
        daily = read_csv(daily_path, DAILY_REQUIRED)
        by_year = defaultdict(list)
        prior = None
        for row in daily:
            day = date.fromisoformat(row["date"])
            if prior is not None and day != prior + timedelta(days=1):
                raise ValueError(f"Missing or repeated daily date near {day}")
            prior = day
            if int(row["year"]) != day.year or int(row["month"]) != day.month:
                raise ValueError(f"Date/year/month mismatch: {day}")
            if not 0 <= exact_int(row["rain_measured_hours"], "rain_measured_hours") <= 24:
                raise ValueError(f"Invalid rain_measured_hours: {day}")
            if not 0 <= exact_int(row["t_count"], "t_count") <= 24:
                raise ValueError(f"Invalid t_count: {day}")
            if float(row["rain_known_mm"]) < 0:
                raise ValueError(f"Negative recorded rain: {day}")
            by_year[day.year].append(row)
        if len(daily) != 7305 or date.fromisoformat(daily[0]["date"]) != date(2006, 1, 1) or prior != date(2025, 12, 31):
            raise ValueError("Daily series must cover 2006-01-01..2025-12-31")
        for row in annual:
            y = int(row["year"])
            daily_rows = by_year[y]
            if len(daily_rows) != int(row["n_days"]):
                raise ValueError(f"Daily counts differ in {y}")
            checks = {
                "valid_temp_days": sum(bool(d["tmax"]) for d in daily_rows),
                "hot33_maysep": sum(d["tmax"] != "" and 5 <= int(d["month"]) <= 9 and float(d["tmax"]) >= 33 for d in daily_rows),
                "frost0_marapr": sum(d["tmin"] != "" and int(d["month"]) in (3, 4) and float(d["tmin"]) <= 0 for d in daily_rows),
                "rain40_maysep": sum(5 <= int(d["month"]) <= 9 and float(d["rain_known_mm"]) >= 40 for d in daily_rows),
                "rain_measured_hours": sum(int(d["rain_measured_hours"]) for d in daily_rows),
            }
            for key, actual in checks.items():
                if actual != int(row[key]):
                    raise ValueError(f"Annual/daily mismatch {y} {key}: {actual} != {row[key]}")
            rain_sum = sum(float(d["rain_known_mm"]) for d in daily_rows)
            if not math.isclose(rain_sum, float(row["annual_rain_known_mm"]), abs_tol=0.1):
                raise ValueError(f"Annual/daily rain lower-bound mismatch: {y}")
        result["daily_crosscheck"] = "PASS_AGAINST_DERIVED_DAILY_NOT_ORIGINAL_HOURLY"
        result["daily_records"] = len(daily)
    if metadata_path:
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        if metadata.get("unique_hours") != 175319 or metadata.get("hours_expected") != 175320 or metadata.get("missing_hours") != ["2015-06-27T05:00:00"]:
            raise ValueError("Unexpected archived hourly audit metadata")
        result["hourly_qc"] = "ARCHIVED_AUDIT_ONLY_UNVERIFIED_WITHOUT_RAW"
        result["hourly_archive_claim"] = {k: metadata.get(k) for k in ("hours_expected", "unique_hours", "missing_hours", "duplicate_records", "conflicting_duplicate_fields")}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit existing derived ASOS files; not a raw station reprocessing")
    parser.add_argument("--annual", type=Path, required=True)
    parser.add_argument("--daily", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = annual_audit(args.annual, args.daily, args.metadata)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
