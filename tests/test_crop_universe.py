"""All surveyed crop systems must be searchable without becoming model inputs."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_crop_universe import catalog, render, HTML, CSV, OFF, TEMPLATE  # noqa: E402


def test_51_complete_survey_not_three_preselected_crops():
    c = catalog()
    assert len(c) == 51
    assert len({r["id"] for r in c}) == 51
    assert len({r["name"] for r in c}) == 51
    assert {r["category"] for r in c} == {
        "식량작물", "노지채소", "시설채소", "노지과수", "시설과수", "화훼", "특용·약용"
    }
    assert all(r["source_kind"] == "R" and r["region"] == "NATIONAL" and r["year"] == 2024
               for r in c)
    assert next(r for r in c if r["name"] == "인삼(4년근)")["cycle_years"] == 4
    assert next(r for r in c if r["name"] == "시설장미")["yield_unit"] == "본"
    assert "봄감자" in {r["name"] for r in c}
    assert "시설딸기(수경)" in {r["name"] for r in c}


def test_reproducible_offline_html_and_live_check():
    page = HTML.read_text(encoding="utf-8")
    assert render() == page
    assert page.count('"id":"RDA2024-') == 51
    assert "const CATALOG=" in page
    assert 'id="addExtra"' in page
    assert 'id="export"' in page
    assert 'id="import"' in page
    assert "yield_quantity_per_10a" in page
    assert "source_kind" in page
    assert "신규 과수" in page
    assert "작기 1년" in page
    assert "https://cdn" not in page
    assert "__CROP_CATALOG_JSON__" not in page
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_crop_universe.py"), "--check"],
        cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_report_rows_are_never_given_a_default_cash_workflow():
    page = HTML.read_text(encoding="utf-8")
    assert '"operations":' not in page.split("const CATALOG=")[1].split(";")[0]
    assert '"harvests":' not in page.split("const CATALOG=")[1].split(";")[0]
    assert '"facility_events":' not in page.split("const CATALOG=")[1].split(";")[0]


def test_offsurvey_pending_candidate_gets_no_numeric_facts(tmp_path):
    r = json.loads(OFF.read_text(encoding="utf-8"))
    r["candidates"].append({
        "id": "OFF-0071", "crop_name": "Unsurveyed test crop",
        "cultivation_system": "test-only cultivation",
        "discovery_source_title": "Test fixture, no verified facts",
        "discovery_source_url": "https://example.org/test-reference",
        "discovery_source_year": None, "source_available": False,
        "status": "PENDING_EVIDENCE",
        "missing_evidence": ["COMPARABLE_INCOME"],
    })
    p = tmp_path / "off.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    c = catalog(CSV, p)
    assert len(c) == 52
    extra = c[-1]
    assert extra["source_kind"] is None
    assert extra["cycle_years"] is None
    assert extra["income"] is None
    assert extra["labor_owner"] is None
    assert extra["region"] is None
    assert extra["url"] == "https://example.org/test-reference"


def test_invalid_template_slot_and_bad_source_fail(tmp_path):
    p = tmp_path / "no-slot.html"
    p.write_text("<html>no catalog slot</html>", encoding="utf-8")
    with pytest.raises(ValueError, match="catalog slot"):
        render(template_path=p)
    broken = tmp_path / "broken.csv"
    original = CSV.read_text(encoding="utf-8")
    broken.write_text(original.replace("RDA2024-01", "BROKEN", 1).splitlines()[0]+"\n",
                      encoding="utf-8")
    with pytest.raises(ValueError):
        catalog(broken, OFF)
