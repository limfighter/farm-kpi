"""Validate a cautious sample of official 2022-2023 RDA web tables.

This is NOT a PDF-audited long-format income series: historical source
pages do not include labor hours / PDF source page metadata. Missing
response rows must never be turned into zero financial observations.
"""
import argparse
import csv
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data/reported/rda_web_2022_2023_sample.csv"
BASELINE = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
PAIRS = {
    "RDA2024-18": ("노지쪽파", "696031", "696002"),
    "RDA2024-24": ("시설오이", "696078", "696003"),
    "RDA2024-37": ("사과", "696054", "696004"),
}
YEARS = (2022, 2023)
INTEGERS = ("gross_receipts_krw_per_10a", "management_cost_krw_per_10a",
            "income_krw_per_10a", "yield_quantity", "reported_price_krw_per_kg")
EMPTY_FIELDS = INTEGERS + ("yield_unit",)
STATUSES = ("OBSERVED_WEB_TABLE", "NO_DETAIL_ROW_SHOWN")
FIXTURE = {
    ("2022", "RDA2024-37"): ("7065740", "3703532", "3362208"),
    ("2023", "RDA2024-37"): ("8852139", "3823247", "5028892"),
    ("2022", "RDA2024-18"): ("5286603", "2639349", "2647255"),
    ("2023", "RDA2024-18"): ("5381476", "2406276", "2975199"),
    ("2023", "RDA2024-24"): ("22729042", "12018109", "10710933"),
}


def load_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Invalid sample CSV header")
        return list(reader)


def check(path=SAMPLE):
    rows = load_rows(path)
    with BASELINE.open(encoding="utf-8-sig", newline="") as f:
        baseline = {r["crop_id"]: r for r in csv.DictReader(f)}
    actual_keys = set()
    present = 0
    for r in rows:
        key = (r["observation_year"], r["crop_id_2024_reference_only"])
        if key in actual_keys:
            raise ValueError("Duplicate observation or missingness row")
        actual_keys.add(key)
        if int(r["observation_year"]) not in YEARS:
            raise ValueError("Unsupported year")
        crop = PAIRS.get(r["crop_id_2024_reference_only"])
        if crop is None or tuple(r[k] for k in ("display_crop_system", "site_lower_code", "site_upper_code")) != crop:
            raise ValueError("Unreviewed crop ID or site classification")
        if baseline[r["crop_id_2024_reference_only"]]["crop"] != r["display_crop_system"]:
            raise ValueError("2024 ID-to-name crosswalk changed")
        if r["region"] != "NATIONAL":
            raise ValueError("Regional rows require separately verified source; national query cannot supply Jeonbuk")
        if r["source_kind"] != "R" or r["source_format"] != "OFFICIAL_RDA_WEB_TABLE":
            raise ValueError("Only official reported statistics accepted")
        if (r["pdf_crosscheck_status"] != "NOT_PDF_CROSSCHECKED"
                or r["labor_status"] != "NOT_CAPTURED"):
            raise ValueError("Do not claim unperformed PDF/labor verification")
        if r["cycle_years"] != "1" or not r["comparability_warning"]:
            raise ValueError("Period basis or inter-year comparability warning missing")
        u = urlsplit(r["source_url"])
        if (u.scheme != "https" or u.netloc not in {"nongsaro.go.kr", "www.nongsaro.go.kr"}
                or u.path != "/portal/ps/psb/psbf/agricultIncomeInfoLst.ps"):
            raise ValueError("Nonofficial crop source URL")
        query = parse_qs(u.query)
        for k, expected in {"year":r["observation_year"], "areaCode":"697001",
                            "lowerCode":r["site_lower_code"],
                            "upperCode":r["site_upper_code"]}.items():
            if query.get(k) != [expected]:
                raise ValueError("Source URL does not match the crop/year/national scope")
        if r["observation_status"] not in STATUSES:
            raise ValueError("Unknown observation status")
        if r["observation_status"] == "NO_DETAIL_ROW_SHOWN":
            if any(r[k] for k in EMPTY_FIELDS):
                raise ValueError("Unobserved row must keep every numeric field null")
            if key != ("2022", "RDA2024-24"):
                raise ValueError("Missing observation not independently checked")
            continue
        if r["yield_unit"] != "kg" or any(not r[k] for k in INTEGERS):
            raise ValueError("Observed row requires complete quoted web-table amounts")
        values = [int(r[k]) for k in INTEGERS]
        revenue, cost, income, qty, price = values
        if min(values) <= 0 or abs(revenue - cost - income) > 2:
            raise ValueError("Invalid crop income reconciliation")
        if key not in FIXTURE or tuple(r[k] for k in INTEGERS[:3]) != FIXTURE[key]:
            raise ValueError("Manual official web-table amounts differ from captured source")
        present += 1
    required = {(str(y), crop) for y in YEARS for crop in PAIRS}
    if actual_keys != required or present != len(FIXTURE):
        raise ValueError("Incomplete source coverage sample")
    return len(rows), present


def main():
    p = argparse.ArgumentParser(description="Audit incomplete official RDA web crop-history snapshots")
    p.add_argument("--check", action="store_true", required=True)
    args = p.parse_args()
    rows, observed = check()
    print(f"RDA web sample valid: {observed}/{rows} numeric observations; no regional or labor imputation")


if __name__ == "__main__":
    main()
