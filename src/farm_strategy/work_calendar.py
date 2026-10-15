"""Validate sourced crop-workflow calendar pointers, never financial observations.

This is a deliberately small metadata layer linking some of the locked 51
survey crop systems to RDA Nongsaro crop-work calendars. It records general
season windows, NOT site-ready field tasks or current crop-year cash.
"""
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs


CROP_KEYS = {
    "crop_id", "official_title", "source_url", "variant", "match_level",
    "region_scope", "reviewed_on", "source_kind", "source_year",
    "season_notes", "stages",
}
STAGE_KEYS = {
    "action", "window_months", "crosses_calendar_year",
    "precision", "source_data_only",
}
MATCH_LEVELS = {"CROP_SYSTEM_REFERENCE", "VARIANT_REFERENCE", "CROP_FAMILY_ONLY"}


def _text(v, field):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{field}: nonempty text is required")


def load_calendar_registry(path, crop_ids):
    """Return sparse references keyed by RDA2024 survey ID (never by label)."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(raw) != {"schema_version", "purpose", "reviewed_on",
                    "source_license_notice", "references"}:
        raise ValueError("Unexpected calendar registry schema")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("Unexpected calendar schema version")
    for field in ("purpose", "reviewed_on", "source_license_notice"):
        _text(raw[field], field)
    ids = set(crop_ids)
    if len(ids) != len(crop_ids) or not ids:
        raise ValueError("Expected unique source crop IDs")
    refs = raw["references"]
    if not isinstance(refs, list):
        raise ValueError("Expected calendar references list")
    indexed = {}
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != CROP_KEYS:
            raise ValueError("Calendar reference fields mismatch")
        cid = ref["crop_id"]
        if cid not in ids or cid in indexed:
            raise ValueError(f"Unknown or duplicate calendar crop_id {cid}")
        for field in ("official_title", "source_url", "variant",
                      "region_scope", "reviewed_on", "season_notes"):
            _text(ref[field], field)
        if (ref["source_kind"] != "R" or ref["source_year"] is not None
                or ref["match_level"] not in MATCH_LEVELS):
            raise ValueError("Calendar source must be R with unasserted publication year")
        parsed = urlparse(ref["source_url"])
        query = parse_qs(parsed.query)
        if (parsed.scheme != "https"
                or parsed.hostname != "www.nongsaro.go.kr"
                or parsed.path != "/portal/ps/psb/psbl/workScheduleDtl.ps"
                or not (len(query.get("cntntsNo", [])) == 1
                        and query["cntntsNo"][0].isdigit())
                or parsed.fragment or parsed.username or parsed.password):
            raise ValueError("Expected official RDA Nongsaro detailed work calendar URL")
        stages = ref["stages"]
        if not isinstance(stages, list) or not stages:
            raise ValueError("Calendar must describe at least one sourced work stage")
        actions = set()
        for stage in stages:
            if not isinstance(stage, dict) or set(stage) != STAGE_KEYS:
                raise ValueError("Calendar stage fields mismatch")
            _text(stage["action"], "action")
            if stage["action"] in actions:
                raise ValueError("Repeated crop work stage")
            actions.add(stage["action"])
            months = stage["window_months"]
            if (not isinstance(months, list)
                    or len(months) > 12
                    or len(set(months)) != len(months)
                    or any(type(m) is not int or not 1 <= m <= 12 for m in months)):
                raise ValueError("Invalid month window")
            crosses = stage["crosses_calendar_year"]
            if (type(crosses) is not bool
                    or stage["precision"] != "MONTH_WINDOW"
                    or stage["source_data_only"] is not True):
                raise ValueError("Calendar flags/precision mismatch")
            wrap = any(a > b for a, b in zip(months, months[1:]))
            if crosses != wrap:
                raise ValueError("Calendar year-wrap flag incorrect")
        indexed[cid] = ref
    return indexed
