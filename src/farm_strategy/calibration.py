"""Private, self-attested evidence-to-scenario preview.

This module does NOT authenticate receipts or quotes and NEVER modifies base.json.
Only explicitly reviewed, SHA-locked, model-normalized candidates can be used
in an ignored local what-if configuration. All sample runs are MODEL ONLY.
"""
import copy
import csv
from datetime import date
import hashlib
import json
import math
from pathlib import Path

from .comparison import compare_plans
from .evidence import MODEL_KEYS, UNITS, validate_evidence

EXTRA_FIELDS = ("scope_note", "normalization_note", "review_status")
ATTESTATIONS = (
    "original_documents_checked",
    "area_grade_season_reconciled",
    "net_fees_reconciled",
    "constant_2026_currency_checked",
)
# Financial income/expenses require actual settled transactions;
# written price quotes may only inform explicitly non-revenue procurement items.
TRANSACTION_ONLY = {
    "finance.potato_revenue",
    "finance.scallion_revenue",
    "finance.cucumber_revenue_300p",
    "finance.potato_operating_cost_excluding_hired_labor",
    "finance.scallion_operating_cost_excluding_hired_labor",
    "finance.cucumber_operating_cost_excluding_hired_labor",
}
QUOTE_OR_TRANSACTION = set(MODEL_KEYS) - TRANSACTION_ONLY
METRICS = (
    "project_npv",
    "economic_npv",
    "equity_terminal_liability_adjusted_npv",
    "monthly_liquidity_buffer_required",
)


def read_reviewed_candidates(csv_path, review_path):
    """Require a separate human review manifest bound to exact CSV bytes."""
    csv_path, review_path = Path(csv_path), Path(review_path)
    validate_evidence(csv_path)  # schema and numeric guardrails; NOT authenticity

    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(EXTRA_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("Calibration CSV missing extra review/scope columns")
        candidates = list(reader)
    if not candidates:
        raise ValueError("No evidence candidates supplied")

    manifest = json.loads(review_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Review manifest must be a JSON object")
    actual_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if manifest.get("evidence_sha256") != actual_sha:
        raise ValueError("Evidence SHA256 mismatch: re-review the exact file bytes")
    if not isinstance(manifest.get("reviewer_id"), str) or not manifest["reviewer_id"].strip():
        raise ValueError("Missing human reviewer_id in manifest")
    try:
        reviewed_on = date.fromisoformat(manifest["reviewed_on"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid reviewed_on in manifest") from exc
    if reviewed_on > date.today():
        raise ValueError("Review date cannot be in the future")
    checklist = manifest.get("review_checklist")
    if not isinstance(checklist, dict) or any(checklist.get(k) is not True for k in ATTESTATIONS):
        raise ValueError("All manual review checklist assertions must be true")
    approved = manifest.get("approved_reference_ids")
    if (not isinstance(approved, list) or not approved
            or any(not isinstance(ref, str) or not ref.strip() for ref in approved)
            or len(approved) != len(set(approved))):
        raise ValueError("approved_reference_ids must be a nonempty unique list")

    reference_rows = {}
    for row in candidates:
        ref = row["reference_id"].strip()
        if ref in reference_rows:
            raise ValueError("Duplicate reference_id; aggregate and reconcile privately first")
        reference_rows[ref] = row
    if not set(approved).issubset(reference_rows):
        raise ValueError("Approved reference missing from evidence CSV")

    selected = {}
    for ref in approved:
        row = reference_rows[ref]
        key = row["model_key"].strip()
        if key in selected:
            raise ValueError("Multiple approved entries for one model_key are ambiguous")
        if row["review_status"].strip() != "reviewed":
            raise ValueError("Candidate must have review_status=reviewed")
        for column in ("scope_note", "normalization_note"):
            if not row[column] or not row[column].strip():
                raise ValueError(f"Missing {column} for approved candidate")
        kind = row["source_kind"].strip().upper()
        if key in TRANSACTION_ONLY and kind != "T":
            raise ValueError("Actual settled transaction T required for crop revenues/costs")
        if key in QUOTE_OR_TRANSACTION and kind not in ("T", "Q"):
            raise ValueError("Only transaction T or written quote Q can inform this cost")
        value = float(row["value_2026_constant"])
        if not math.isfinite(value) or value < 0:
            raise ValueError("Nonfinite or negative candidate")
        selected[key] = {"value": value, "source_kind": kind}
    return selected, actual_sha, len(candidates)


def staged_config(base_config, selected, evidence_sha):
    """Copy only supported finance scalar keys, without touching original config."""
    config = copy.deepcopy(base_config)
    modifications = []
    for key, candidate in selected.items():
        section, field = key.split(".", 1)
        if section != "finance" or field not in config["finance"]:
            raise ValueError(f"Not a supported finance field: {key}")
        current = config[section][field]
        if isinstance(current, bool) or not isinstance(current, (int, float)):
            raise ValueError(f"Only numeric scalar fields can be overridden: {key}")
        config[section][field] = candidate["value"]
        modifications.append({
            "model_key": key,
            "before_2026_constant": current,
            "preview_2026_constant": candidate["value"],
            "kind": candidate["source_kind"],
            "evidence_level": "HUMAN_REVIEW_ASSERTED_NOT_SOURCE_AUTHENTICATED",
        })
    config.setdefault("metadata", {})["calibration_status"] = (
        "LOCAL_STAGED_WHAT_IF_NOT_REAL_WORLD_VALIDATED")
    config["metadata"]["calibration_evidence_sha256"] = evidence_sha
    return config, modifications


def calibrate_preview(csv_path, review_path, base_config, weather, *,
                      seed=42, paths=100, window="recent10", scenario="base"):
    """Paired base vs staged analysis; never update the repository baseline."""
    selected, digest, total_rows = read_reviewed_candidates(csv_path, review_path)
    candidate_config, modifications = staged_config(base_config, selected, digest)
    baseline = compare_plans(weather, base_config, seed=seed, paths=paths,
                             scenario=scenario, window=window)
    candidate = compare_plans(weather, candidate_config, seed=seed, paths=paths,
                              scenario=scenario, window=window)
    before = {item["plan"]: item for item in baseline["runs"]}
    deltas = []
    for item in candidate["runs"]:
        plan = item["plan"]
        metric_deltas = {}
        for key in METRICS:
            a = before[plan]["metrics"][key]
            b = item["metrics"][key]
            metric_deltas[key] = {
                "baseline_median": a["median"],
                "candidate_median": b["median"],
                "candidate_minus_baseline_median": round(b["median"] - a["median"], 2),
                "baseline_p90": a["p90"],
                "candidate_p90": b["p90"],
            }
        deltas.append({"plan": plan, "metrics": metric_deltas})
    report = {
        "status": "HUMAN_ATTESTED_PRIVATE_WHAT_IF_NOT_VERIFIED_FARM_PERFORMANCE",
        "baseline_unchanged": True,
        "evidence_sha256": digest,
        "candidates_in_csv": total_rows,
        "approved_candidates": len(modifications),
        "seed": seed,
        "paths": paths,
        "scenario": scenario,
        "window": window,
        "units": "2026-constant KRW 10000 except hours and nominal loan principal",
        "changes": modifications,  # Private; persist ONLY in ignored local output.
        "plan_impact": deltas,
        "warning": (
            "Review assertions are self-attested metadata, NOT original receipt "
            "authentication. Quote Q is not a transaction. Both baselines remain "
            "illustrative simulations. No Git-tracked config or dashboard updated."
        ),
    }
    return candidate_config, report


def safe_output_directory(path, repo_root):
    """Block writing private scenario reports into tracked project folders."""
    dest = Path(path).resolve()
    root = Path(repo_root).resolve()
    try:
        rel = dest.relative_to(root)
    except ValueError:
        return dest
    if not rel.parts or rel.parts[0] not in ("output", "private"):
        if len(rel.parts) < 2 or rel.parts[:2] != ("data", "private"):
            raise ValueError("Within the repository use only ignored output/ or data/private/")
    return dest


def save_preview_outputs(output_dir, config, report, repo_root):
    dest = safe_output_directory(output_dir, repo_root)
    dest.mkdir(parents=True, exist_ok=True)
    config_path = dest / "what-if-config.json"
    report_path = dest / "what-if-impact.json"
    for path, value in ((config_path, config), (report_path, report)):
        if path.is_symlink():
            raise ValueError("Refuse to overwrite symlinked preview output")
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return config_path, report_path
