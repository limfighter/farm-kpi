"""Privacy-conscious parcel and operations intake: UNKNOWN is never a zero.

This is an evidence checklist and data-quality report, NOT automatic parcel
feasibility, source authentication, crop selection or farm income calibration.
Raw parcel entries must remain in data/private/ or another private directory.
"""
from datetime import date
import json
import math
from pathlib import Path
import re

from .calibration import safe_output_directory

SCHEMA_VERSION = 1
GATES = (
    "soil_and_drainage",
    "irrigation_water",
    "local_weather_exposure",
    "land_use_and_permits",
    "electricity_supply",
    "road_access",
    "existing_facility",
    "storage_and_logistics",
    "startup_capex_quotes",
    "peak_monthly_labor",
    "buyer_and_settlement",
    "plantable_area_and_rotation",
)
STATUS = (
    "UNKNOWN",
    "FOLLOWUP_NEEDED",
    "DOCUMENT_COLLECTED_UNVERIFIED",
    "USER_REPORTED_CONSTRAINT",
)
DOCUMENT_KINDS = ("O", "R", "Q", "T")
NUMERIC_FIELDS = (
    "usable_area_pyeong",
    "available_capital_krw_10000",
    "max_buffer_tolerance_krw_10000",
    "max_months_until_first_receipt",
)
SOURCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,79}$")


def _optional_number(value, label, maximum=None):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} requires a number or null")
    if not math.isfinite(value) or value < 0 or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f"{label} out of range")
    return value


def _date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} requires an ISO date")
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} invalid ISO date") from exc
    if d > date.today():
        raise ValueError(f"{label} cannot be future dated")


def _validate_gate(name, value):
    if not isinstance(value, dict) or set(value) != {
        "status", "source_kind", "source_ref", "checked_on"
    }:
        raise ValueError(f"{name}: expected status/source_kind/source_ref/checked_on")
    state = value["status"]
    if state not in STATUS:
        raise ValueError(f"{name}: unsupported status, do not claim VERIFIED automatically")
    kind, ref, checked = value["source_kind"], value["source_ref"], value["checked_on"]
    if state == "DOCUMENT_COLLECTED_UNVERIFIED":
        if kind not in DOCUMENT_KINDS:
            raise ValueError(f"{name}: collected document needs O/R/Q/T source category")
        if not isinstance(ref, str) or SOURCE_PATTERN.fullmatch(ref) is None:
            raise ValueError(f"{name}: source_ref must be opaque local ID, no raw personal data")
        _date(checked, f"{name}.checked_on")
    else:
        if kind is not None or ref is not None or checked is not None:
            raise ValueError(f"{name}: only collected documents may hold source metadata")
    return state


def check_site_file(path):
    """Validate input; return deliberately redacted, non-decision summary."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {
        "schema_version", "approx_gross_area_pyeong", "site_gates",
        "operating_constraints", "decisions"
    }:
        raise ValueError("Unexpected site file structure; private location fields not supported")
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported site schema version")
    area = _optional_number(data["approx_gross_area_pyeong"], "approx_gross_area_pyeong")
    if area is None or area <= 0:
        raise ValueError("approx_gross_area_pyeong must be positive")
    gates = data["site_gates"]
    if not isinstance(gates, dict) or set(gates) != set(GATES):
        raise ValueError("Site gates must contain the full standard set")
    states = {name: _validate_gate(name, gates[name]) for name in GATES}
    constraints = data["operating_constraints"]
    if not isinstance(constraints, dict) or set(constraints) != set(NUMERIC_FIELDS) | {
        "owner_hours_available_by_month"
    }:
        raise ValueError("Operating constraints must use the supported fields")
    nums = {k: _optional_number(constraints[k], k) for k in NUMERIC_FIELDS}
    if nums["usable_area_pyeong"] is not None and nums["usable_area_pyeong"] > area:
        raise ValueError("usable_area_pyeong cannot exceed gross land")
    hours = constraints["owner_hours_available_by_month"]
    if not isinstance(hours, list) or len(hours) != 12:
        raise ValueError("owner_hours_available_by_month must have exactly 12 months")
    for i, hour in enumerate(hours, 1):
        _optional_number(hour, f"owner hours month {i}", maximum=744)
    decisions = data["decisions"]
    if decisions != {"crop_selection": "UNDECIDED", "facility_choice": "UNDECIDED"}:
        raise ValueError("This intake is pre-decision; crop and facility must be UNDECIDED")

    counts = {state: sum(s == state for s in states.values()) for state in STATUS}
    return {
        "schema_version": SCHEMA_VERSION,
        "report_kind": "SELF_REPORTED_METADATA_NOT_PARCEL_VERIFICATION",
        "parcel_feasible": None,
        "crop_selected": False,
        "facility_selected": False,
        "approx_gross_area_recorded": True,
        "usable_area_recorded": nums["usable_area_pyeong"] is not None,
        "owner_hours_months_recorded": sum(v is not None for v in hours),
        "other_constraints_recorded": {
            k: nums[k] is not None for k in NUMERIC_FIELDS if k != "usable_area_pyeong"
        },
        "gate_counts": counts,
        "unresolved_gates": [k for k, v in states.items() if v != "DOCUMENT_COLLECTED_UNVERIFIED"],
        "documents_collected_but_unverified": [
            k for k, v in states.items() if v == "DOCUMENT_COLLECTED_UNVERIFIED"
        ],
        "decision_readiness": "BLOCKED_EVIDENCE_INCOMPLETE",
        "warning": (
            "No source document has been authenticated; collected is not verified. "
            "No exact parcel location, bank amount, source IDs, or private notes "
            "are echoed. No crop/site suitability or profitability is inferred."
        ),
    }


def save_site_summary(path, report, repo_root):
    """Keep the exported summary in ignored local paths; no repository config edits."""
    dest = safe_output_directory(path, repo_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise ValueError("Refuse symlinked output")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return dest
