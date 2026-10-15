"""The site-intake HTML stays offline and exports backend-compatible local JSON."""
import re
from pathlib import Path

from farm_strategy.site_intake import GATES, STATUS

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "dashboard/site-intake/index.html"


def test_local_browser_form_is_offline_and_has_no_external_data_transmission():
    page = PAGE.read_text(encoding="utf-8")
    assert "<!doctype html>" in page.lower()
    assert "<script>" in page
    assert "<script src" not in page.lower()
    assert "fetch(" not in page
    assert "XMLHttpRequest" not in page
    assert "localStorage" not in page
    assert 'type="file"' in page
    assert "URL.createObjectURL" in page
    assert "file.text()" in page
    assert "--file data/private/site-facts.json" in page


def test_browser_and_backend_share_12_site_gates_and_exact_status_names():
    page = PAGE.read_text(encoding="utf-8")
    groups = page.split("const keys = [", 1)[1].split("];", 1)[0]
    keys = re.findall(r'\["([a-z_]+)","', groups)
    assert tuple(keys) == GATES
    labels = page.split("const states = [", 1)[1].split("];", 1)[0]
    statuses = re.findall(r'\["([A-Z_]+)","', labels)
    assert tuple(statuses) == STATUS
    assert "VERIFIED_FEASIBLE" not in page


def test_browser_keeps_crop_and_facility_undecided():
    page = PAGE.read_text(encoding="utf-8")
    assert 'crop_selection:"UNDECIDED"' in page
    assert 'facility_choice:"UNDECIDED"' in page
    assert 'approx_gross_area_pyeong:gross' in page
    assert 'owner_hours_available_by_month:hours' in page
    assert "비식별" in page
