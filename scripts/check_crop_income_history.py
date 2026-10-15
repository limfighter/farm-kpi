"""Audit a provenance-tagged long-form RDA crop history table.

2022/2023 and regional PDF availability does not authorize fabricated rows.
Existing 2024 national data remains an immutable independently checked input.
"""
import argparse
import csv
import json
from pathlib import Path
from refresh_crop_discovery import load_source

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
SOURCES = ROOT / "data/metadata/rda_income_source_registry.json"
LONG = ROOT / "data/reported/rda_income_long.csv"
PREFIX = ("observation_year", "region", "source_id", "period_basis", "comparison_review")
REVIEW = "NOT_COMPARABLE_WITH_OTHER_YEARS_REGIONS_OR_NEW_BUILDS_WITHOUT_REVIEW"
PERIOD = "REPORTED_CROP_CYCLE_PER_10A"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Invalid or duplicate CSV columns")
        return list(reader.fieldnames), list(reader)


def expected_2024():
    load_source(BASE)  # prior locked 51-row accounting, pages and labor assertions
    original_fields, rows = read_csv(BASE)
    out = []
    for source_row in rows:
        row = dict(zip(PREFIX, ("2024", "NATIONAL", "rda-2024-national", PERIOD, REVIEW)))
        row.update(source_row)
        out.append(row)
    return list(PREFIX) + original_fields, out


def check(source_path=SOURCES, data_path=LONG):
    registry = json.loads(Path(source_path).read_text(encoding="utf-8"))
    if registry.get("schema_version") != 1:
        raise ValueError("Unsupported source registry schema")
    sources = registry.get("sources", [])
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("Duplicate source IDs")
    indexed = {s["id"]: s for s in sources}
    for s in sources:
        if not s["url"].startswith("https://www.nongsaro.go.kr/"):
            raise ValueError("Source must link to the official publication page")
        if s["publication_status"] != "OFFICIAL_ATTACHMENT_CONFIRMED":
            raise ValueError("Unconfirmed publication")
        if s["scope"] not in {"NATIONAL", "REGIONAL_PUBLICATION"}:
            raise ValueError("Unexpected source geographic scope")
    expected_fields, baseline = expected_2024()
    fields, observations = read_csv(data_path)
    if fields != expected_fields:
        raise ValueError("Long-form field order or contract changed")
    seen = set()
    counts = {s["id"]: 0 for s in sources}
    for r in observations:
        source = indexed.get(r["source_id"])
        if source is None:
            raise ValueError("Observation with unknown source ID")
        if source["transcription_status"] == "NOT_TRANSCRIBED":
            raise ValueError("Cannot publish values from an untranscribed source")
        if int(r["observation_year"]) != source["year"]:
            raise ValueError("Year disagrees with source")
        if r["region"] == "NATIONAL":
            if source["scope"] != "NATIONAL":
                raise ValueError("National value from regional source")
        elif r["region"] == "JEONBUK":
            if source["scope"] != "REGIONAL_PUBLICATION":
                raise ValueError("Jeonbuk value from national source")
        else:
            raise ValueError("Region must be NATIONAL or explicitly reviewed JEONBUK")
        if r["data_kind"] != "R" or r["period_basis"] != PERIOD or r["comparison_review"] != REVIEW:
            raise ValueError("Observed / modeled accounting or comparability label missing")
        cycle = int(r["cycle_years"])
        if cycle != (4 if r["crop"] == "인삼(4년근)" else 1):
            raise ValueError("Invalid 4-year ginseng or crop-cycle basis")
        if any(not r[k] for k in ("crop_id", "crop", "category", "source_pdf_page",
                                  "labor_source_pdf_page", "yield_unit")):
            raise ValueError("Required crop, unit or source page missing")
        revenue, cost, income = (int(r[k]) for k in
            ("revenue_krw_per_10a", "management_cost_krw_per_10a", "income_krw_per_10a"))
        if min(revenue, cost, income) <= 0 or abs(revenue - cost - income) > 2:
            raise ValueError("Income reconciliation failed")
        own, hired, total = (float(r[k]) for k in
            ("labor_owner_hours_per_10a", "labor_hired_hours_per_10a", "labor_total_hours_per_10a"))
        if min(own, hired, total) < 0 or abs(own + hired - total) > .11:
            raise ValueError("Labor reconciliation failed")
        key = (r["observation_year"], r["region"], r["crop_id"], r["crop"])
        if key in seen:
            raise ValueError("Duplicate crop-year-region-system observation")
        seen.add(key)
        counts[r["source_id"]] += 1

    base = {r["crop_id"]: r for r in baseline}
    actual = {r["crop_id"]: r for r in observations
              if r["observation_year"] == "2024" and r["region"] == "NATIONAL"}
    if actual != base:
        raise ValueError("2024 national 51-row transcription drift or missing values")
    for s in sources:
        if counts[s["id"]] != s["verified_observation_rows"]:
            raise ValueError("Source observation count mismatch: " + s["id"])
    return len(observations)


def main():
    parser = argparse.ArgumentParser(description="Check source-tagged RDA crop-year coverage")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-baseline", action="store_true")
    args = parser.parse_args()
    if args.check == args.refresh_baseline:
        parser.error("Specify exactly one of --check or --refresh-baseline")
    if args.refresh_baseline:
        # Never overwrite any newly verified multi-year rows.
        if LONG.exists():
            _, existing = read_csv(LONG)
            if any(r.get("source_id") != "rda-2024-national" for r in existing):
                raise ValueError("Refusing to overwrite independently transcribed historical rows")
        fields, rows = expected_2024()
        with LONG.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\\n")
            writer.writeheader()
            writer.writerows(rows)
    n = check()
    print(f"Source provenance and {n} observed crop-year-region rows valid; missing years stay absent")


if __name__ == "__main__":
    main()
