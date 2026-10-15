"""Static 2024 reported RDA benchmarks: intentionally not model calibration."""
import csv
from pathlib import Path

from farm_strategy.model import read_config

ROOT = Path(__file__).resolve().parents[1]
REPORTED = ROOT / "data/reported/rda_2024_crop_income_10a.csv"
CODES = ROOT / "data/reported/rda_income_api_crop_crosswalk.csv"
EXPECTED = {"봄감자", "가을감자", "노지쪽파", "시설오이"}


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_reported_crop_rows_are_not_farm_transactions():
    rows = read_rows(REPORTED)
    assert len(rows) == 4
    assert {r["crop_label"] for r in rows} == EXPECTED
    assert all(r["reference_kind"] == "R" for r in rows)
    assert all(r["status"] == "READ_ONLY_REPORTED_STATISTIC" for r in rows)
    assert all(int(r["observation_year"]) == 2024 for r in rows)
    assert all(int(r["area_m2"]) == 1000 for r in rows)
    assert all(r["cropping_basis"] == "1_crop_per_year" for r in rows)
    assert all(int(r["report_pdf_page"]) > 0 for r in rows)


def test_reported_revenues_and_expenses_reconcile_with_rounding_tolerance():
    for row in read_rows(REPORTED):
        gross = int(row["revenue_krw_per_10a"])
        cost = int(row["management_cost_krw_per_10a"])
        income = int(row["income_krw_per_10a"])
        assert all(v > 0 for v in (gross, cost, income))
        assert abs(gross - cost - income) <= 1
        assert float(row["hired_hours_per_10a"]) > 0
        assert float(row["owner_hours_per_10a"]) > 0
        assert 0 < int(row["hired_labor_cost_krw_per_10a"]) < cost


def test_crop_api_codebook_is_codes_not_income_observations():
    rows = read_rows(CODES)
    assert len(rows) == 4
    assert {r["crop_label"] for r in rows} == EXPECTED
    assert all(r["data_status"] == "CODEBOOK_ONLY" for r in rows)
    assert all(r["region_code"] == "CM0145" for r in rows)
    assert len({r["crop_code"] for r in rows}) == 4
    expected_codes = {
        "봄감자": "FC05050100050101",
        "가을감자": "FC05050100050103",
        "노지쪽파": "VC04120200120202",
        "시설오이": "VC01090100090108",
    }
    for row in rows:
        assert row["crop_code"] == expected_codes[row["crop_label"]]


def test_2024_statistic_does_not_override_hypothetical_2026_model():
    config = read_config(ROOT / "configs/base.json")
    assert config["finance"]["cucumber_revenue_300p"] == 2497.55
    assert config["finance"]["potato_revenue"] == 220
    assert config["finance"]["scallion_revenue"] == 140
    assert config["metadata"]["currency"] == "KRW_10000_constant_2026"
    # Annual national 2024 nominal 10a figures have different basis and
    # must not silently be used as 2026-real 300-pyeong crop cash receipts.
