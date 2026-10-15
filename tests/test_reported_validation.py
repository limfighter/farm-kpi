"""Shared RDA guards must reach readiness without changing its public row types."""
import csv
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
LEGACY_INTS = (
    "revenue_krw_per_10a", "management_cost_krw_per_10a",
    "income_krw_per_10a", "cycle_years",
)
LEGACY_FLOATS = (
    "labor_total_hours_per_10a", "labor_hired_hours_per_10a",
    "labor_owner_hours_per_10a",
)


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_rows():
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def altered_source(tmp_path, key, value):
    rows = raw_rows()
    rows[0][key] = value
    path = tmp_path / "source.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.mark.parametrize("key,value", [
    ("source_pdf_page", "0"),
    ("source_printed_page", "0"),
    ("labor_source_pdf_page", "0"),
    ("labor_source_printed_page", "0"),
    ("income_rate_pct", "NaN"),
    ("income_rate_pct", "inf"),
    ("income_rate_pct", "99.9"),
    ("yield_quantity", "0"),
    ("yield_quantity", "NaN"),
    ("labor_owner_hours_per_10a", "NaN"),
    ("labor_hired_hours_per_10a", "-1"),
    ("labor_total_hours_per_10a", "9999"),
])
def test_readiness_rejects_invalid_reported_source(tmp_path, key, value):
    builder = load_script("build_feasibility")
    with pytest.raises(ValueError):
        builder.read_crops(altered_source(tmp_path, key, value))


def test_readiness_retains_legacy_numeric_types_and_source_text():
    builder = load_script("build_feasibility")
    expected = raw_rows()
    for row in expected:
        for key in LEGACY_INTS:
            row[key] = int(row[key])
        for key in LEGACY_FLOATS:
            row[key] = float(row[key])
    actual = builder.read_crops()
    assert actual == expected
    for row, original in zip(actual, expected):
        assert {key: type(value) for key, value in row.items()} == {
            key: type(value) for key, value in original.items()
        }


@pytest.mark.parametrize("key,value,reason", [
    ("data_kind", "O", "reported R"),
    ("data_kind", "A", "reported R"),
    ("revenue_krw_per_10a", "0", "Non-positive"),
    ("management_cost_krw_per_10a", "-1", "Non-positive"),
    ("income_krw_per_10a", "999999", "Income reconciliation"),
    ("yield_quantity", "0", "Non-positive"),
    ("cycle_years", "0", "Non-positive"),
    ("cycle_years", "2", "four-year cycle"),
    ("source_pdf_page", "0", "summary page"),
    ("source_printed_page", "0", "Summary page mismatch"),
    ("labor_source_pdf_page", "0", "labor page"),
    ("labor_source_printed_page", "0", "Labor page mismatch"),
    ("income_rate_pct", "NaN", "Nonfinite"),
    ("income_rate_pct", "inf", "Nonfinite"),
    ("income_rate_pct", "99.9", "income rate"),
    ("labor_owner_hours_per_10a", "NaN", "Nonfinite"),
    ("labor_hired_hours_per_10a", "inf", "Nonfinite"),
    ("labor_total_hours_per_10a", "-inf", "Nonfinite"),
    ("labor_total_hours_per_10a", "-1", "Negative labor"),
    ("labor_total_hours_per_10a", "9999", "Labor reconciliation"),
])
def test_package_loader_rejects_invalid_reported_values(tmp_path, key, value, reason):
    reported = importlib.import_module("farm_strategy.reported")
    with pytest.raises(ValueError, match=reason):
        reported.load_source(altered_source(tmp_path, key, value))


def test_package_loader_retains_source_order_and_four_year_ginseng():
    reported = importlib.import_module("farm_strategy.reported")
    original = raw_rows()
    expected = [dict(row) for row in original]
    for row in expected:
        for key in reported.NUMERIC_INT:
            row[key] = int(row[key])
        for key in reported.NUMERIC_FLOAT:
            row[key] = float(row[key])
    assert reported.load_source(SOURCE) == expected
    assert reported.validate_rows(original) == expected
    assert original == raw_rows()  # validation leaves input values untouched
    assert [(row["crop"], row["cycle_years"]) for row in expected
            if row["cycle_years"] > 1] == [("인삼(4년근)", 4)]


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "51 unique"),
    ("duplicate_id", "51 unique"),
    ("duplicate_crop", "Duplicate crop label"),
    ("category", "categories/counts"),
    ("ginseng_annualized", "four-year cycle"),
])
def test_package_validator_retains_survey_composition_and_cycle_guards(mutation, reason):
    reported = importlib.import_module("farm_strategy.reported")
    rows = raw_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate_id":
        rows[1]["crop_id"] = rows[0]["crop_id"]
    elif mutation == "duplicate_crop":
        rows[1]["crop"] = rows[0]["crop"]
    elif mutation == "category":
        rows[0]["category"] = "UNKNOWN"
    else:
        next(row for row in rows if row["crop"] == "인삼(4년근)")["cycle_years"] = "1"
    with pytest.raises(ValueError, match=reason):
        reported.validate_rows(rows)


def test_package_and_history_import_without_scripts_on_module_path(tmp_path):
    installed = tmp_path / "installed"
    shutil.copytree(ROOT / "src/farm_strategy", installed / "farm_strategy",
                    ignore=shutil.ignore_patterns("__pycache__"))
    code = """
import importlib.util
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from farm_strategy.reported import load_source
assert len(load_source(sys.argv[2])) == 51
spec = importlib.util.spec_from_file_location('history', sys.argv[3])
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)
assert history.check() == 51
assert 'refresh_crop_discovery' not in sys.modules
assert not any(Path(path).name == 'scripts' for path in sys.path)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", code, str(installed), str(SOURCE),
         str(ROOT / "scripts/check_crop_income_history.py")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_discovery_refresh_preserves_generated_html_bytes(tmp_path):
    discovery = load_script("refresh_crop_discovery")
    original = discovery.HTML.read_bytes()
    target = tmp_path / "discovery.html"
    target.write_bytes(original)
    assert discovery.process(html_path=target) is False
    assert target.read_bytes() == original


def test_readiness_output_retains_exact_cached_bytes():
    builder = load_script("build_feasibility")
    rows, html = builder.content()
    assert builder.csv_bytes(rows) == builder.READINESS.read_bytes()
    assert html.encode("utf-8") == builder.HTML.read_bytes()
    assert json.loads(html.split('<script id="data" type="application/json">')[1]
                      .split("</script>")[0]) == rows
