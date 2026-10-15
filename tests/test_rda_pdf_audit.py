"""Uploaded RDA PDF's official reference tables vs our R-only crop index."""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_rda_pdf_source.py"
CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
METADATA = ROOT / "data/metadata/rda_2024_source_verification.json"
REFRESH = ROOT / "scripts/refresh_crop_discovery.py"
spec = importlib.util.spec_from_file_location("rda_pdf_crosscheck", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run_check(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str,args)],
                          cwd=ROOT, capture_output=True, text=True)


def altered_csv(tmp_path, key, value):
    with CSV.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rows[0][key] = value
    out = tmp_path / "mutated.csv"
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return out


def test_locked_51_crop_transcription_metadata_is_current():
    verified = module.check_metadata()
    assert verified["source_kind"] == "R_REPORTED_NATIONAL_NOT_PARCEL"
    assert verified["crop_records"] == 51
    assert verified["matching_overview_amount_triplets"] == 51
    assert verified["matching_labor_page_summary_values"] == 51
    assert len(verified["pdf_sha256"]) == 64
    assert verified["timing_exception"].startswith("인삼")
    result = run_check("--check")
    assert result.returncode == 0, result.stderr


def test_crosscheck_three_amounts_and_labor_are_order_sensitive():
    example = {
        "revenue_krw_per_10a": "2693175",
        "management_cost_krw_per_10a": "1443511",
        "income_krw_per_10a": "1249665",
        "labor_owner_hours_per_10a": "34.4",
        "labor_hired_hours_per_10a": "23.1",
        "labor_total_hours_per_10a": "57.5",
    }
    assert module.overview_matches("농산물\n2,693,175\n1,443,511\n1,249,665\n", example)
    assert not module.overview_matches("1,443,511 2,693,175 1,249,665", example)
    assert module.labor_matches("합계\n34.4\n23.1\n57.5", example)
    assert not module.labor_matches("합계\n34.4\n23.1\n57.6", example)


def test_any_edit_to_rda_rows_invalidates_pdf_audit_lock(tmp_path):
    mutated = altered_csv(tmp_path, "income_rate_pct", "99.9")
    run = run_check("--check", "--csv", mutated)
    assert run.returncode != 0
    assert "Stale RDA PDF crosscheck" in run.stderr


@pytest.mark.parametrize("key,value,reason", [
    ("income_rate_pct", "99.9", "income rate"),
    ("labor_owner_hours_per_10a", "-2", "Negative labor"),
    ("yield_quantity", "0", "Non-positive"),
])
def test_data_cannot_mutate_into_inconsistent_or_negative_values(tmp_path,key,value,reason):
    mutated = altered_csv(tmp_path, key, value)
    result = subprocess.run(
        [sys.executable, str(REFRESH), "--check", "--csv", str(mutated)],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert reason in result.stderr


def test_local_pdf_folder_is_gitignored_not_forbidden():
    # Users may legitimately keep their original source PDF locally.
    # Tests must not fail just because the ignored raw file exists.
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/raw/" in ignore
    assert "*.pdf" in ignore
    assert METADATA.is_file()
