"""Parcel intake never translates missing evidence into crop suitability."""
import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import pytest

from farm_strategy.site_intake import GATES, STATUS, check_site_file, save_site_summary

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/templates/private_site_intake_TEMPLATE.json"


def make_input(tmp_path, edit=None):
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if edit:
        edit(data)
    path = tmp_path / "local-site.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_template_explicitly_unknown_every_gate():
    report = check_site_file(TEMPLATE)
    assert report["schema_version"] == 1
    assert report["gate_counts"]["UNKNOWN"] == len(GATES) == 12
    assert report["owner_hours_months_recorded"] == 0
    assert report["usable_area_recorded"] is False
    assert len(report["unresolved_gates"]) == 12
    assert report["parcel_feasible"] is None
    assert report["crop_selected"] is False and report["facility_selected"] is False
    assert report["decision_readiness"] == "BLOCKED_EVIDENCE_INCOMPLETE"


def test_unknown_is_distinct_from_measured_zero(tmp_path):
    def update(d):
        d["operating_constraints"]["owner_hours_available_by_month"][0] = 0
        d["operating_constraints"]["max_buffer_tolerance_krw_10000"] = 0
        d["operating_constraints"]["usable_area_pyeong"] = 1500
    report = check_site_file(make_input(tmp_path, update))
    assert report["owner_hours_months_recorded"] == 1
    assert report["usable_area_recorded"] is True
    assert report["other_constraints_recorded"]["max_buffer_tolerance_krw_10000"] is True
    assert report["gate_counts"]["UNKNOWN"] == 12


def test_document_collected_does_not_imply_feasible(tmp_path):
    def update(d):
        d["site_gates"]["soil_and_drainage"] = {
            "status": "DOCUMENT_COLLECTED_UNVERIFIED",
            "source_kind": "O", "source_ref": "soil-sample-2026",
            "checked_on": "2026-10-15"}
    report = check_site_file(make_input(tmp_path, update))
    assert report["gate_counts"]["DOCUMENT_COLLECTED_UNVERIFIED"] == 1
    assert report["parcel_feasible"] is None
    assert "soil_and_drainage" in report["documents_collected_but_unverified"]
    assert "soil-sample-2026" not in str(report)


@pytest.mark.parametrize("edit,reason", [
    (lambda d: d.update({"precise_address": "somewhere"}), "Unexpected site file"),
    (lambda d: d.update({"approx_gross_area_pyeong": 0}), "positive"),
    (lambda d: d.update({"approx_gross_area_pyeong": True}), "number"),
    (lambda d: d["operating_constraints"].update({"usable_area_pyeong": 3001}), "gross land"),
    (lambda d: d["operating_constraints"].update({"available_capital_krw_10000": -1}), "range"),
    (lambda d: d["operating_constraints"].update({"owner_hours_available_by_month": [None] * 11}), "12 months"),
    (lambda d: d["operating_constraints"]["owner_hours_available_by_month"].__setitem__(0, 745), "range"),
    (lambda d: d["site_gates"]["irrigation_water"].update({"status": "VERIFIED_FEASIBLE"}), "unsupported status"),
    (lambda d: d["site_gates"]["soil_and_drainage"].update({"source_ref": "personal-contact"}), "only collected documents"),
    (lambda d: d["decisions"].update({"crop_selection": "시설오이"}), "UNDECIDED"),
])
def test_malformed_private_site_data_is_rejected(tmp_path, edit, reason):
    with pytest.raises(ValueError, match=reason):
        check_site_file(make_input(tmp_path, edit))


@pytest.mark.parametrize("patch,reason", [
    ({"source_kind": None}, "source category"),
    ({"source_ref": "BAD NAME WITH SPACES"}, "opaque local ID"),
    ({"checked_on": None}, "ISO date"),
    ({"checked_on": "3000-01-01"}, "future"),
])
def test_document_validation_strict(tmp_path, patch, reason):
    def update(d):
        d["site_gates"]["land_use_and_permits"] = {
            "status": "DOCUMENT_COLLECTED_UNVERIFIED", "source_kind": "R",
            "source_ref": "land-regulation-01", "checked_on": "2026-10-15",
        }
        d["site_gates"]["land_use_and_permits"].update(patch)
    with pytest.raises(ValueError, match=reason):
        check_site_file(make_input(tmp_path, update))


def test_private_report_output_guardrails(tmp_path):
    report = check_site_file(TEMPLATE)
    path = save_site_summary(tmp_path / "safe" / "summary.json", report, ROOT)
    assert json.loads(path.read_text(encoding="utf-8")) == report
    with pytest.raises(ValueError, match="ignored"):
        save_site_summary(ROOT / "configs/site-report.json", report, ROOT)


def test_cli_can_check_unfilled_template_without_weather(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "farm_strategy", "site-check",
         "--file", str(TEMPLATE), "--output", str(tmp_path / "report.json")],
        cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["gate_counts"]["UNKNOWN"] == len(GATES)
    assert "PRIVATE" not in proc.stdout
