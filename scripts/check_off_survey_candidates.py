"""Validate discovery-only candidates outside the locked RDA 2024 survey.

This registry is deliberately separate from audited RDA observations and the
cash-flow model. A discovery URL is NOT comparable income evidence.
"""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/metadata/off_survey_candidate_registry.json"
TOP_FIELDS = {"schema_version", "purpose", "candidates"}
FIELDS = {
    "id", "crop_name", "cultivation_system", "discovery_source_url",
    "discovery_source_title", "discovery_source_year",
    "source_available", "status", "missing_evidence",
}
MISSING_TYPES = {
    "COMPARABLE_INCOME", "CROP_CYCLE_AND_UNITS", "REGIONAL_COMPARABILITY",
    "SITE_FEASIBILITY", "BUYER_TERMS", "FACILITY_QUOTES", "MONTHLY_LABOR",
}
SENSITIVE_URL_FIELDS = {"token", "key", "apikey", "api_key", "secret", "password", "auth", "signature", "sig"}


def check(path=REGISTRY):
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or set(registry) != TOP_FIELDS:
        raise ValueError("Off-survey registry has missing or unexpected top-level fields")
    if type(registry["schema_version"]) is not int or registry["schema_version"] != 1:
        raise ValueError("Unsupported off-survey registry schema")
    if not isinstance(registry["purpose"], str) or not registry["purpose"].strip():
        raise ValueError("Registry purpose is required")
    candidates = registry["candidates"]
    if not isinstance(candidates, list):
        raise ValueError("Off-survey candidates must be a list")
    seen_ids = set()
    seen_systems = set()
    for index, candidate in enumerate(candidates, 1):
        if not isinstance(candidate, dict) or set(candidate) != FIELDS:
            raise ValueError(f"Candidate {index}: missing or unexpected fields; no numeric data is allowed")
        ident = candidate["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"OFF-[0-9]{4,}", ident):
            raise ValueError(f"Candidate {index}: invalid off-survey ID")
        if ident in seen_ids:
            raise ValueError(f"Duplicate off-survey ID: {ident}")
        seen_ids.add(ident)
        for key in ("crop_name", "cultivation_system", "discovery_source_title"):
            value = candidate[key]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{ident}: {key} must be nonempty")
        system = (candidate["crop_name"].strip().casefold(),
                  candidate["cultivation_system"].strip().casefold())
        if system in seen_systems:
            raise ValueError(f"Duplicate off-survey crop-system: {ident}")
        seen_systems.add(system)

        url = candidate["discovery_source_url"]
        if not isinstance(url, str):
            raise ValueError(f"{ident}: discovery URL is required")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or
                "." not in parsed.hostname or parsed.username or parsed.password or
                parsed.fragment or any(key.casefold() in SENSITIVE_URL_FIELDS
                                       for key, _ in parse_qsl(parsed.query))):
            raise ValueError(f"{ident}: source URL must be a public HTTPS page without secrets")
        year = candidate["discovery_source_year"]
        if year is not None and (type(year) is not int or not 1900 <= year <= 2100):
            raise ValueError(f"{ident}: discovery publication year must be an integer or null")
        if candidate["source_available"] is not False:
            raise ValueError(f"{ident}: source_available must remain false pending independent review")
        if candidate["status"] != "PENDING_EVIDENCE":
            raise ValueError(f"{ident}: pending candidate cannot be marked verified or feasible")
        missing = candidate["missing_evidence"]
        if (not isinstance(missing, list) or not missing or
                any(not isinstance(v, str) or v not in MISSING_TYPES for v in missing) or
                len(set(missing)) != len(missing) or "COMPARABLE_INCOME" not in missing):
            raise ValueError(f"{ident}: missing evidence must include COMPARABLE_INCOME")
    return len(candidates)


def main():
    parser = argparse.ArgumentParser(description="Check pending non-survey crop discovery metadata")
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    count = check()
    print(f"Off-survey candidate registry valid: {count} pending candidates; no comparable income claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
