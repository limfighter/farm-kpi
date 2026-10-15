"""Synthetic examples only: no confidential receipts are checked into Git."""
from copy import deepcopy
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from farm_strategy.calibration import (
    calibrate_preview, read_reviewed_candidates, safe_output_directory,
    save_preview_outputs, staged_config,
)
from farm_strategy.model import read_config, read_weather

ROOT = Path(__file__).resolve().parents[1]
BASE = read_config(ROOT / "configs/base.json")
WEATHER = read_weather(ROOT / "data/processed/annual_weather.csv")
HEADERS = (
    "model_key", "source_kind", "observation_date", "period_label",
    "value_2026_constant", "unit", "reference_id", "scope_note",
    "normalization_note", "review_status",
)


def fake_row(**kwargs):
    row = {
        "model_key": "finance.potato_revenue",
        "source_kind": "T",
        "observation_date": "2025-10-01",
        "period_label": "fictional annual field harvest",
        "value_2026_constant": "300",
        "unit": "KRW_10000_2026_constant",
        "reference_id": "synthetic-local-ref-001",
        "scope_note": "Human-attested same-grade/same-area field crop scope",
        "normalization_note": "Synthetic net sales sum normalized to modeled field scale",
        "review_status": "reviewed",
    }
    row.update(kwargs)
    return row


def fixtures(tmp_path, rows=None, approve=None, manifest_patch=None):
    csv_path = tmp_path / "private-candidates.csv"
    rows = [fake_row()] if rows is None else rows
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    if approve is None:
        approve = [r["reference_id"] for r in rows]
    review = {
        "evidence_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "reviewer_id": "synthetic-local-reviewer",
        "reviewed_on": "2026-10-15",
        "approved_reference_ids": approve,
        "review_checklist": {
            "original_documents_checked": True,
            "area_grade_season_reconciled": True,
            "net_fees_reconciled": True,
            "constant_2026_currency_checked": True,
        },
    }
    review.update(manifest_patch or {})
    review_path = tmp_path / "private-review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")
    return csv_path, review_path


def test_reviewed_one_key_is_only_applied_to_a_deepcopy(tmp_path):
    source, review = fixtures(tmp_path)
    config_before = deepcopy(BASE)
    selected, digest, rows = read_reviewed_candidates(source, review)
    assert rows == 1 and len(digest) == 64
    updated, changes = staged_config(BASE, selected, digest)
    assert updated["finance"]["potato_revenue"] == 300
    assert updated["finance"]["scallion_revenue"] == BASE["finance"]["scallion_revenue"]
    assert BASE == config_before
    assert changes[0]["evidence_level"].startswith("HUMAN_REVIEW_ASSERTED")
    assert "synthetic-local-ref-001" not in str(changes)


def test_paired_impact_changes_revenue_and_preserves_baseline(tmp_path):
    source, review = fixtures(tmp_path)
    original = deepcopy(BASE)
    candidate, report = calibrate_preview(
        source, review, BASE, WEATHER, paths=6, seed=44)
    assert BASE == original
    assert candidate["finance"]["potato_revenue"] == 300
    assert report["baseline_unchanged"] is True
    assert report["approved_candidates"] == 1
    assert report["status"].startswith("HUMAN_ATTESTED_PRIVATE")
    assert "synthetic-local-ref-001" not in str(report)
    field = next(x for x in report["plan_impact"] if x["plan"] == "field_trial")
    assert field["metrics"]["economic_npv"][
        "candidate_minus_baseline_median"] > 0
    again = calibrate_preview(source, review, BASE, WEATHER, paths=6, seed=44)[1]
    assert again == report


@pytest.mark.parametrize("manifest_patch,error", [
    ({"evidence_sha256": "0" * 64}, "SHA256 mismatch"),
    ({"reviewer_id": ""}, "reviewer_id"),
    ({"reviewed_on": "not-a-date"}, "reviewed_on"),
    ({"reviewed_on": "2100-01-01"}, "future"),
    ({"approved_reference_ids": []}, "approved_reference_ids"),
    ({"approved_reference_ids": ["synthetic-local-ref-001"] * 2},
     "approved_reference_ids"),
    ({"approved_reference_ids": ["missing-id"]}, "Approved reference missing"),
    ({"review_checklist": {"original_documents_checked": True}},
     "checklist"),
])
def test_review_manifest_refuses_invalid_assertions(tmp_path, manifest_patch, error):
    source, review = fixtures(tmp_path, manifest_patch=manifest_patch)
    with pytest.raises(ValueError, match=error):
        read_reviewed_candidates(source, review)


@pytest.mark.parametrize("row_patch,error", [
    ({"source_kind": "Q"}, "Actual settled transaction"),
    ({"source_kind": "R"}, "Actual settled transaction"),
    ({"review_status": "pending"}, "review_status"),
    ({"scope_note": ""}, "scope_note"),
    ({"normalization_note": ""}, "normalization_note"),
    ({"value_2026_constant": "NaN"}, "Invalid value"),
    ({"value_2026_constant": "-1"}, "Invalid value"),
    ({"unit": "KRW"}, "Invalid units"),
])
def test_untrusted_unsupported_or_badly_scoped_rows_are_rejected(
    tmp_path, row_patch, error
):
    source, review = fixtures(tmp_path, rows=[fake_row(**row_patch)])
    with pytest.raises(ValueError, match=error):
        read_reviewed_candidates(source, review)


def test_written_capex_quote_allowed_but_not_misrepresented_as_transaction(tmp_path):
    row = fake_row(
        model_key="finance.new_house_capex", source_kind="Q",
        reference_id="synthetic-builder-quote",
        value_2026_constant="5000")
    source, review = fixtures(tmp_path, rows=[row])
    selected, _, _ = read_reviewed_candidates(source, review)
    assert selected["finance.new_house_capex"]["source_kind"] == "Q"
    candidate, report = calibrate_preview(
        source, review, BASE, WEATHER, paths=2)
    assert candidate["finance"]["new_house_capex"] == 5000
    assert report["changes"][0]["kind"] == "Q"
    assert "NOT_SOURCE_AUTHENTICATED" in report["changes"][0]["evidence_level"]


def test_duplicate_refs_and_ambiguous_model_keys_blocked(tmp_path):
    duplicate = fake_row(value_2026_constant="310")
    source, review = fixtures(tmp_path, rows=[fake_row(), duplicate],
                              approve=["synthetic-local-ref-001"])
    with pytest.raises(ValueError, match="Duplicate reference_id"):
        read_reviewed_candidates(source, review)
    another = fake_row(reference_id="another-ref", value_2026_constant="310")
    source, review = fixtures(tmp_path, rows=[fake_row(), another])
    with pytest.raises(ValueError, match="Multiple approved entries"):
        read_reviewed_candidates(source, review)


def test_only_manifest_approved_rows_are_staged(tmp_path):
    second = fake_row(model_key="finance.scallion_revenue",
                      reference_id="synthetic-second", value_2026_constant="180")
    source, review = fixtures(
        tmp_path, rows=[fake_row(), second], approve=["synthetic-local-ref-001"])
    selected, _, count = read_reviewed_candidates(source, review)
    assert count == 2 and list(selected) == ["finance.potato_revenue"]


def test_ignored_or_external_output_path_guard(tmp_path):
    assert safe_output_directory(ROOT / "output" / "private", ROOT).is_relative_to(ROOT)
    assert safe_output_directory(ROOT / "data/private/calibrations", ROOT).is_relative_to(ROOT)
    assert safe_output_directory(tmp_path / "what-if", ROOT) == (tmp_path / "what-if").resolve()
    with pytest.raises(ValueError, match="ignored"):
        safe_output_directory(ROOT / "configs", ROOT)
    with pytest.raises(ValueError, match="ignored"):
        safe_output_directory(ROOT / "dashboard", ROOT)


def test_local_preview_files_are_generated_without_committing_anything(tmp_path):
    source, review = fixtures(tmp_path)
    candidate, report = calibrate_preview(
        source, review, BASE, WEATHER, paths=2)
    config_path, report_path = save_preview_outputs(
        tmp_path / "local-output", candidate, report, ROOT)
    assert config_path.is_file() and report_path.is_file()
    loaded = json.loads(config_path.read_text(encoding="utf-8"))
    assert loaded["finance"]["potato_revenue"] == 300
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_cli_local_evidence_preview(tmp_path):
    source, review = fixtures(tmp_path)
    path = tmp_path / "preview"
    cmd = [
        sys.executable, "-m", "farm_strategy", "calibration-preview",
        "--file", str(source), "--review", str(review),
        "--output-dir", str(path), "--paths", "2", "--seed", "9"
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (path / "what-if-config.json").is_file()
    assert (path / "what-if-impact.json").is_file()
    assert "synthetic-local-ref-001" not in proc.stdout
