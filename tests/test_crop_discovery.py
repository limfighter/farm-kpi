"""Reported RDA 2024 crop universe is independent from five modeled strategies."""
import csv
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
HTML = ROOT / "dashboard/crop-discovery/index.html"
REFRESH = ROOT / "scripts/refresh_crop_discovery.py"


def run(*args):
    return subprocess.run([sys.executable, str(REFRESH), *map(str, args)],
                          cwd=ROOT, text=True, capture_output=True)


def test_all_categories_and_distinct_names():
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 51
    assert len({r["crop"] for r in rows}) == 51
    assert set(r["category"] for r in rows) == {
        "식량작물", "노지채소", "시설채소", "노지과수",
        "시설과수", "화훼", "특용·약용",
    }
    assert {r["data_kind"] for r in rows} == {"R"}
    assert next(r for r in rows if r["crop"] == "시설오이")["income_krw_per_10a"] == "12883641"
    assert next(r for r in rows if r["crop"] == "노지쪽파")["labor_total_hours_per_10a"] == "159.6"
    assert [(r["crop"], r["cycle_years"]) for r in rows if r["cycle_years"] != "1"] == [
        ("인삼(4년근)", "4")
    ]


def test_offline_explorer_matches_source():
    out = run("--check")
    assert out.returncode == 0, out.stderr
    page = HTML.read_text(encoding="utf-8")
    assert '<svg id="scatter"' in page
    assert 'https://cdn' not in page
    assert page.count('"crop_id":"RDA2024-') == 51
    assert 'const DATA=[' in page
    assert "4년 1기작" in page


def test_missing_crop_rejected(tmp_path):
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    dest = tmp_path / "bad.csv"
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows[:-1])
    out = run("--check", "--csv", dest)
    assert out.returncode != 0
    assert "51" in out.stderr


def test_mutated_income_rejected(tmp_path):
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    rows[0]["income_krw_per_10a"] = "9999999"
    dest = tmp_path / "bad.csv"
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    out = run("--check", "--csv", dest)
    assert out.returncode != 0
    assert "Income reconciliation" in out.stderr


def test_stale_html_detected_and_can_be_refreshed(tmp_path):
    page = tmp_path / "explorer.html"
    original = HTML.read_text(encoding="utf-8")
    page.write_text(original.replace('"income_rate_pct":26.5', '"income_rate_pct":99.0', 1),
                    encoding="utf-8")
    assert run("--check", "--html", page).returncode != 0
    updated = run("--refresh", "--html", page)
    assert updated.returncode == 0, updated.stderr
    assert run("--check", "--html", page).returncode == 0
    assert "99.0" not in page.read_text(encoding="utf-8").split('const DATA=')[1].split(';\nconst cats=')[0]
