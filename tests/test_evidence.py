"""Evidence format checks cannot authenticate receipts or quotes."""
import csv
from pathlib import Path

import pytest

from farm_strategy.evidence import validate_evidence

TEMPLATE = (Path(__file__).resolve().parents[1] /
            "data/templates/private_evidence_TEMPLATE.csv")
HEADERS = ["model_key", "source_kind", "observation_date", "period_label",
           "value_2026_constant", "unit", "reference_id"]


def make_row(**patch):
    base = dict(model_key="finance.potato_revenue", source_kind="T",
                observation_date="2025-10-01", period_label="2025 potato season",
                value_2026_constant="240",
                unit="KRW_10000_2026_constant", reference_id="receipt-opaque-1")
    base.update(patch)
    return base


def make_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def test_blank_template_reports_all_requirements_unmet():
    status = validate_evidence(TEMPLATE)
    assert status["evidence_rows"] == 0
    assert status["missing_model_keys"]
    assert status["data_quality"] == "METADATA_FORMAT_ONLY_NOT_SOURCE_AUTHENTICATION"
    assert status["application"].startswith("NONE")


def test_candidate_receipt_is_only_schema_checked_without_echoing_value(tmp_path):
    p = tmp_path / "synthetic-private.csv"
    make_csv(p, [make_row()])
    report = validate_evidence(p)
    assert report["evidence_rows"] == 1
    assert report["source_kind_counts"]["T"] == 1
    assert report["coverage_counts"]["finance.potato_revenue"] == 1
    assert "240" not in str(report)
    assert "receipt-opaque-1" not in str(report)


@pytest.mark.parametrize("patch,reason", [
    ({"model_key": "finance.not_a_key"}, "Unsupported model key"),
    ({"source_kind": "approved"}, "Invalid source kind"),
    ({"observation_date": "2026-99-99"}, "Invalid observation date"),
    ({"value_2026_constant": "NaN"}, "Invalid value"),
    ({"value_2026_constant": "-3"}, "Invalid value"),
    ({"unit": "KRW"}, "Invalid units"),
    ({"reference_id": ""}, "Missing period/reference"),
])
def test_invalid_or_misleading_evidence_metadata_is_rejected(tmp_path, patch, reason):
    p = tmp_path / "bad.csv"
    make_csv(p, [make_row(**patch)])
    with pytest.raises(ValueError, match=reason):
        validate_evidence(p)


def test_hired_labor_unit_is_per_hour(tmp_path):
    p = tmp_path / "hourly.csv"
    make_csv(p, [make_row(model_key="finance.hired_hour_rate",
                           unit="KRW_10000_per_hour_2026_constant",
                           value_2026_constant="2.0", source_kind="Q")])
    report = validate_evidence(p)
    assert report["coverage_counts"]["finance.hired_hour_rate"] == 1
    assert report["source_kind_counts"]["Q"] == 1
