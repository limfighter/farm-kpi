"""Validate PRIVATE candidate evidence metadata; never auto-apply cost overrides.

Input values and local references are NOT authenticated by this parser.
The caller must separately reconcile currency, farm area, crop grade,
net settlement fees and invoice periods before modifying base.json.
"""
import argparse
import csv
from datetime import date
import json
import math
from pathlib import Path

MODEL_KEYS = (
    "finance.potato_revenue",
    "finance.scallion_revenue",
    "finance.cucumber_revenue_300p",
    "finance.potato_operating_cost_excluding_hired_labor",
    "finance.scallion_operating_cost_excluding_hired_labor",
    "finance.cucumber_operating_cost_excluding_hired_labor",
    "finance.hired_hour_rate",
    "finance.new_house_capex",
    "finance.rent_deposit",
    "finance.rent_fitout",
    "finance.rent_yearly",
)
REQUIRED = (
    "model_key", "source_kind", "observation_date", "period_label",
    "value_2026_constant", "unit", "reference_id",
)
UNITS = {
    "cash": "KRW_10000_2026_constant",
    "labor": "KRW_10000_per_hour_2026_constant",
}


def validate_evidence(path):
    """Return completeness metadata, not an approved or verified valuation."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError("Evidence CSV missing required columns")
        counts = {key: 0 for key in MODEL_KEYS}
        kinds = {"O": 0, "R": 0, "T": 0, "Q": 0}
        for row_number, row in enumerate(reader, start=2):
            key = row["model_key"].strip()
            kind = row["source_kind"].strip().upper()
            if key not in counts:
                raise ValueError(f"Unsupported model key on CSV row {row_number}")
            if kind not in kinds:
                raise ValueError(f"Invalid source kind on CSV row {row_number}")
            try:
                date.fromisoformat(row["observation_date"].strip())
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"Invalid observation date on CSV row {row_number}") from exc
            if not row["period_label"].strip() or not row["reference_id"].strip():
                raise ValueError(f"Missing period/reference on CSV row {row_number}")
            expected_unit = UNITS["labor" if key == "finance.hired_hour_rate" else "cash"]
            if row["unit"].strip() != expected_unit:
                raise ValueError(f"Invalid units for {key} on CSV row {row_number}")
            try:
                value = float(row["value_2026_constant"])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Non-numeric evidence on CSV row {row_number}") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid value on CSV row {row_number}")
            counts[key] += 1
            kinds[kind] += 1

    return {
        "evidence_rows": sum(counts.values()),
        "coverage_counts": counts,
        "missing_model_keys": [k for k, count in counts.items() if not count],
        "source_kind_counts": kinds,
        "data_quality": "METADATA_FORMAT_ONLY_NOT_SOURCE_AUTHENTICATION",
        "application": "NONE; base.json and simulations left unchanged",
        "warning": ("Actual farm receipts, written quotes, farmer observations "
                    "and reported statistics have different evidentiary strength. "
                    "No candidate values are imported into the financial model "
                    "until source/area/season/currency verification."),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check private evidence file schema without importing values")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = validate_evidence(args.file)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(exist_ok=True, parents=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
