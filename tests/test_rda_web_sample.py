"""Regression guards for partial 2022-23 official crop income web-page snapshots."""
import csv
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_rda_web_sample import check, SAMPLE  # noqa: E402


def fixture(tmp_path, mutate):
    with SAMPLE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    mutate(rows)
    path = tmp_path / "mutated.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_official_web_source_snapshot_complete_but_incomplete_history():
    assert check() == (6, 5)
    result = subprocess.run([sys.executable, "scripts/check_rda_web_sample.py", "--check"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_absent_2022_cucumber_never_becomes_zero(tmp_path):
    def alter(rows):
        row = next(r for r in rows if r["observation_year"] == "2022" and r["site_lower_code"] == "696078")
        row["income_krw_per_10a"] = "0"
    with pytest.raises(ValueError, match="null"):
        check(fixture(tmp_path, alter))


def test_reuse_of_national_figure_for_jeonbuk_blocked(tmp_path):
    with pytest.raises(ValueError, match="Regional"):
        check(fixture(tmp_path, lambda rows: rows[0].update(region="JEONBUK")))


def test_observation_year_and_source_url_must_match(tmp_path):
    with pytest.raises(ValueError, match="Source URL"):
        check(fixture(tmp_path, lambda rows: rows[0].update(source_url=rows[0]["source_url"].replace("year=2022","year=2024"))))


def test_pdf_audit_cannot_be_claimed_without_record(tmp_path):
    with pytest.raises(ValueError, match="unperformed"):
        check(fixture(tmp_path, lambda rows: rows[0].update(pdf_crosscheck_status="VERIFIED")))


def test_income_modified_beyond_source_snapshot_rejected(tmp_path):
    with pytest.raises(ValueError, match="Manual official"):
        check(fixture(tmp_path, lambda rows: rows[0].update(income_krw_per_10a="3362209")))


@pytest.mark.parametrize("field", ["yield_quantity", "reported_price_krw_per_kg"])
@pytest.mark.parametrize("observed_index", range(5))
def test_each_observed_yield_and_price_stays_locked_to_source_snapshot(
        tmp_path, field, observed_index):
    def alter(rows):
        observed = [r for r in rows if r["observation_status"] == "OBSERVED_WEB_TABLE"]
        observed[observed_index][field] = "1"

    with pytest.raises(ValueError, match="Manual official"):
        check(fixture(tmp_path, alter))


def test_no_arbitrary_duplicates(tmp_path):
    with pytest.raises(ValueError, match="Duplicate"):
        check(fixture(tmp_path, lambda rows: rows.append(dict(rows[0]))))
