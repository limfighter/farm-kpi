"""Derived ASOS consistency tests; these are not raw-hourly/QC checks."""
import csv
from pathlib import Path
import pytest
from farm_strategy.audit import annual_audit

ROOT = Path(__file__).resolve().parents[1]


def test_missing_required_columns(tmp_path):
    incomplete = tmp_path / "incomplete.csv"
    incomplete.write_text("year,n_days\n2006,365\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing columns"):
        annual_audit(incomplete)


@pytest.mark.skipif(not (ROOT / "data/processed/daily_asos_jeonju_2006_2025.csv").exists(), reason="optional derived daily v10 archive not in git")
def test_v10_annual_and_daily_consistent():
    base = ROOT / "data/processed"
    result = annual_audit(base / "annual_asos_jeonju_2006_2025.csv", base / "daily_asos_jeonju_2006_2025.csv")
    assert result["annual_records"] == 20
    assert result["daily_records"] == 7305
    assert result["period_means"]["2006-2015"]["hot33_maysep"] == 14.9
    assert result["period_means"]["2016-2025"]["hot33_maysep"] == 19.7
    assert result["period_means"]["2006-2015"]["frost0_marapr"] == 12.7
    assert result["period_means"]["2016-2025"]["frost0_marapr"] == 4.7
    assert result["period_means"]["2006-2015"]["rain40_maysep"] == 7.7
    assert result["period_means"]["2016-2025"]["rain40_maysep"] == 7.4


@pytest.mark.skipif(not (ROOT / "data/processed/daily_asos_jeonju_2006_2025.csv").exists(), reason="optional derived daily v10 archive not in git")
def test_rejects_annual_daily_mismatch(tmp_path):
    src = ROOT / "data/processed/annual_asos_jeonju_2006_2025.csv"
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))
    rows[0]["rain40_maysep"] = str(int(rows[0]["rain40_maysep"]) + 1)
    bad = tmp_path / "altered.csv"
    with bad.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(ValueError, match="Annual/daily mismatch"):
        annual_audit(bad, ROOT / "data/processed/daily_asos_jeonju_2006_2025.csv")


def test_annual_yearly_and_period_stats():
    result = annual_audit(ROOT / "data/processed/annual_asos_jeonju_2006_2025.csv")
    assert result["annual_records"] == 20
    assert result["days_from_annual"] == 7305
    assert result["rain_numeric_hours"] == 18329
    assert result["period_means"]["2016-2025"]["hot33_maysep"] == 19.7
    assert result["daily_crosscheck"] == "NOT_PERFORMED"



def test_simulation_weather_is_identical_to_matching_v10_annual_features():
    """The Monte Carlo input must not silently diverge from derived v10 ASOS."""
    legacy = ROOT / "data/processed/annual_weather.csv"
    derived = ROOT / "data/processed/annual_asos_jeonju_2006_2025.csv"
    with legacy.open(encoding="utf-8-sig", newline="") as handle:
        older = list(csv.DictReader(handle))
    with derived.open(encoding="utf-8-sig", newline="") as handle:
        newer = list(csv.DictReader(handle))
    assert len(older) == len(newer) == 20
    assert set(older[0]).issubset(newer[0])
    for old, new in zip(older, newer):
        assert old["year"] == new["year"]
        for column in old:
            assert float(old[column]) == float(new[column]), (
                f"ASOS input drift in {old['year']} {column}"
            )
