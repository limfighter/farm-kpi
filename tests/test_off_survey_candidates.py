"""No unreviewed off-survey discovery record may become verified income evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_off_survey_candidates import check  # noqa: E402


def candidate():
    return {
        "id": "OFF-0001",
        "crop_name": "Synthetic test crop",
        "cultivation_system": "synthetic test method",
        "discovery_source_url": "https://example.org/discovery",
        "discovery_source_title": "Synthetic test reference (not a real source)",
        "discovery_source_year": None,
        "source_available": False,
        "status": "PENDING_EVIDENCE",
        "missing_evidence": ["COMPARABLE_INCOME", "SITE_FEASIBILITY"],
    }


def registry_file(tmp_path, records):
    path = tmp_path / "off_survey.json"
    path.write_text(json.dumps({
        "schema_version": 1, "purpose": "Only discovery; no numeric data",
        "candidates": records,
    }), encoding="utf-8")
    return path


def test_empty_registry_is_explicit_not_a_zero_income_claim():
    assert check() == 0
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_off_survey_candidates.py"), "--check"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "0 pending candidates" in result.stdout


def test_pending_discovery_metadata_is_allowed(tmp_path):
    assert check(registry_file(tmp_path, [candidate()])) == 1


@pytest.mark.parametrize("alter, message", [
    (lambda c: c.update(source_available=True), "source_available"),
    (lambda c: c.update(status="VERIFIED_FEASIBLE"), "pending"),
    (lambda c: c.update(income_krw_per_10a=100), "numeric data"),
    (lambda c: c.update(missing_evidence=["SITE_FEASIBILITY"]), "COMPARABLE_INCOME"),
    (lambda c: c.update(discovery_source_url="http://example.org"), "HTTPS"),
    (lambda c: c.update(discovery_source_url="https://example.org/?token=private"), "secrets"),
    (lambda c: c.update(discovery_source_year=0), "year"),
    (lambda c: c.update(crop_name="  "), "crop_name"),
])
def test_unverified_claims_and_invalid_fields_are_rejected(tmp_path, alter, message):
    c = candidate()
    alter(c)
    with pytest.raises(ValueError, match=message):
        check(registry_file(tmp_path, [c]))


def test_duplicate_ids_and_crop_systems_are_rejected(tmp_path):
    c = candidate()
    with pytest.raises(ValueError, match="Duplicate off-survey ID"):
        check(registry_file(tmp_path, [c, copy.deepcopy(c)]))
    other = copy.deepcopy(c)
    other["id"] = "OFF-0002"
    with pytest.raises(ValueError, match="Duplicate off-survey crop-system"):
        check(registry_file(tmp_path, [c, other]))


def test_registry_structure_rejects_missing_keys(tmp_path):
    c = candidate()
    del c["discovery_source_title"]
    with pytest.raises(ValueError, match="missing or unexpected"):
        check(registry_file(tmp_path, [c]))
