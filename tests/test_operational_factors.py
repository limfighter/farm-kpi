"""Protect decisions from a false sense of feature count or verification."""
import copy
import json
from pathlib import Path

import pytest

from farm_strategy.operational_factors import audit, render_html

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/metadata/decision_factor_registry.json"


def test_all_factors_are_bound_to_actual_model_fields_or_explicitly_missing():
    r = audit()
    assert r["factors_total"] == 51  # NOT the number of researched crop systems
    assert r["implementation_counts"] == {
        "INTAKE_ONLY": 10, "MODELED": 23, "NOT_MODELED": 18
    }
    assert r["hard_gate_count"] == 17
    assert r["advantage_count"] == 9
    assert r["status"] == "REPOSITORY_CAPABILITY_AUDIT_NOT_FIELD_VALIDATION"


def test_top_unmodeled_farm_risks_are_visible():
    r = audit()
    unresolved = set(r["p0_unmodeled"])
    assert {"water_quality", "flood_damage", "crop_loss"} <= unresolved
    rows = {f["id"]: f for f in r["factors"]}
    assert rows["usable_area"]["implementation"] == "MODELED"
    assert rows["soil_ph_ec"]["implementation"] == "INTAKE_ONLY"
    assert rows["grade_mix"]["implementation"] == "MODELED"
    assert rows["grade_mix"]["model_binding"] == "execution.grade_lots.sold_quantity_per_10a"
    assert rows["peak_week"]["implementation"] == "MODELED"
    assert rows["risk_diversification"]["role"] == "ADVANTAGE"
    assert rows["financing"]["model_binding"] == "portfolio.financing_events.amount_krw"
    assert rows["multiple_cropping"]["implementation"] == "MODELED"
    assert rows["facility_energy"]["model_binding"] == "lifecycle.facility_events.amount_krw"


def test_html_is_offline_and_emphasizes_evidence_not_rank():
    report = audit()
    html = render_html(report)
    assert html.count("<tr data-group=") == 51
    assert "현장 근거" in html
    assert "51" in html and "조건부 이점" in html
    assert "직접 구매" in html
    assert "작목·시설 추천을 보류" in html
    assert "https://soil.rda.go.kr" in html
    assert "fetch(" not in html
    assert "iframe" not in html


@pytest.mark.parametrize("mutate,expected", [
    (lambda d: d["factors"][0].update(model_binding="lifecycle.case.fake_field"), "Unknown field"),
    (lambda d: d["factors"][0].update(implementation="NOT_MODELED"), "must not claim"),
    (lambda d: d["factors"][0].update(implementation="INTAKE_ONLY"), "own actual fields"),
    (lambda d: d["factors"].append(copy.deepcopy(d["factors"][0])), "Duplicate"),
    (lambda d: d["factors"][0].update(assumed_profitable=True), "fields differ"),
    (lambda d: d["factors"][0].update(priority="ALREADY_VERIFIED"), "priority"),
    (lambda d: d["source_links"]["LAND_SITE"].update(official_url="file:///secret"), "public https"),
])
def test_bad_claims_are_rejected(tmp_path, mutate, expected):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    mutate(data)
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        audit(p)
