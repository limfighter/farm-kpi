"""Regression guards for RDA multi-year source provenance and missingness."""
import csv
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_crop_income_history import check, LONG, SOURCES  # noqa: E402


def snapshot(tmp_path, mutate):
    with LONG.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields, records = reader.fieldnames, list(reader)
    mutate(records)
    file = tmp_path / "history.csv"
    with file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    return file


def test_checked_history_is_only_2024_national():
    assert check() == 51
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_crop_income_history.py"), "--check"],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_missing_row_does_not_silently_count_as_zero(tmp_path):
    file = snapshot(tmp_path, lambda rows: rows.pop())
    with pytest.raises(ValueError, match="2024 national"):
        check(SOURCES, file)


def test_untranscribed_2023_values_rejected(tmp_path):
    def alter(rows):
        rows[0]["source_id"] = "rda-2023-national"
        rows[0]["observation_year"] = "2023"
    file = snapshot(tmp_path, alter)
    with pytest.raises(ValueError, match="untranscribed source"):
        check(SOURCES, file)


def test_regional_observation_cannot_reuse_national_source(tmp_path):
    def alter(rows):
        rows[0]["region"] = "JEONBUK"
    file = snapshot(tmp_path, alter)
    with pytest.raises(ValueError, match="regional source"):
        check(SOURCES, file)


def test_four_year_ginseng_cannot_be_annualized(tmp_path):
    def alter(rows):
        ginseng = next(r for r in rows if r["crop"] == "인삼(4년근)")
        ginseng["cycle_years"] = "1"
    file = snapshot(tmp_path, alter)
    with pytest.raises(ValueError, match="ginseng"):
        check(SOURCES, file)


def test_duplicate_observation_rejected(tmp_path):
    def alter(rows):
        rows.append(dict(rows[0]))
    file = snapshot(tmp_path, alter)
    with pytest.raises(ValueError, match="Duplicate"):
        check(SOURCES, file)
