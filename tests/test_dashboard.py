"""Offline SVG dashboard must agree with the model-only CSV snapshot."""
import csv
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "dashboard/index.html"
CSV = ROOT / "dashboard/data/screening-model-only.csv"
BUILDER = ROOT / "scripts/build_dashboard.py"


def run_dashboard(*args):
    return subprocess.run(
        [sys.executable, str(BUILDER), *map(str, args)],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_tracked_dashboard_is_fresh_and_svg_offline():
    result = run_dashboard("--csv", CSV, "--html", HTML, "--check")
    assert result.returncode == 0, result.stderr
    content = HTML.read_text(encoding="utf-8")
    assert content.count("<svg") == 2
    assert "<script src=" not in content
    assert "https://cdn." not in content
    assert 'data-model-paths>300</div>' in content
    assert 'data-model-window>recent10</div>' in content
    assert content.count("tm-node") > 2


def test_generation_from_csv_is_idempotent(tmp_path):
    generated = tmp_path / "dashboard.html"
    run = run_dashboard("--csv", CSV, "--html", HTML, "--output", generated)
    assert run.returncode == 0, run.stderr
    assert generated.read_bytes() == HTML.read_bytes()


def test_rejects_incomplete_scenario_table(tmp_path):
    with CSV.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    bad = tmp_path / "missing.csv"
    with bad.open("w", newline="", encoding="utf-8") as dest:
        writer = csv.DictWriter(dest, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows[:-1])
    run = run_dashboard("--csv", bad, "--html", HTML, "--check")
    assert run.returncode != 0
    assert "six scenarios" in run.stderr


def test_rejects_nonfinite_comparison_metric(tmp_path):
    with CSV.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    rows[0]["economic_npv_median"] = "NaN"
    bad = tmp_path / "nonfinite.csv"
    with bad.open("w", newline="", encoding="utf-8") as dest:
        writer = csv.DictWriter(dest, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    run = run_dashboard("--csv", bad, "--html", HTML, "--check")
    assert run.returncode != 0
    assert "Nonfinite" in run.stderr


def test_stale_dashboard_is_detected(tmp_path):
    altered = tmp_path / "altered.html"
    text = HTML.read_text(encoding="utf-8")
    altered.write_text(text.replace('data-model-paths>300</div>',
                                    'data-model-paths>999</div>'), encoding="utf-8")
    run = run_dashboard("--csv", CSV, "--html", altered, "--check")
    assert run.returncode != 0
    assert "stale" in (run.stdout + run.stderr).lower()
