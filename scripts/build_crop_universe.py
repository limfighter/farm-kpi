"""Build reproducible offline all-crop workflow interface from locked RDA data."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.reported import load_source  # noqa: E402
from farm_strategy.work_calendar import load_calendar_registry  # noqa: E402

CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
OFF = ROOT / "data/metadata/off_survey_candidate_registry.json"
CALENDAR = ROOT / "data/metadata/crop_work_calendar_sources.json"
TEMPLATE = ROOT / "dashboard/universe/template.html"
HTML = ROOT / "dashboard/universe/index.html"
URL = "https://www.nongsaro.go.kr/portal/ps/pst/pstb/pstbc/mngmtDtaDtl.ps?menuId=PS03213&nttSn=842"


def catalog(csv_path=CSV, off_path=OFF, calendar_path=CALENDAR):
    rows = load_source(csv_path)
    cal = load_calendar_registry(calendar_path, [r['crop_id'] for r in rows])
    off = json.loads(Path(off_path).read_text(encoding="utf-8"))
    if off.get("schema_version") != 1 or not isinstance(off.get("candidates"), list):
        raise ValueError("Invalid off-survey registry")
    result = [{
        "id": r["crop_id"], "name": r["crop"], "category": r["category"],
        "cycle_years": r["cycle_years"], "yield_unit": r["yield_unit"],
        "income": r["income_krw_per_10a"], "labor_owner": str(r["labor_owner_hours_per_10a"]),
        "labor_hired": str(r["labor_hired_hours_per_10a"]),
        "pdf_page": r["source_pdf_page"], "labor_page": r["labor_source_pdf_page"],
        "source_kind": "R", "year": 2024, "region": "NATIONAL", "url": URL,
        "calendar": cal.get(r["crop_id"]),
    } for r in rows]
    for r in off["candidates"]:
        if r.get("status") != "PENDING_EVIDENCE" or r.get("source_available") is not False:
            raise ValueError("Off-survey candidate must remain pending")
        result.append({
            "id": r["id"], "name": r["crop_name"], "category": "조사 밖 후보",
            "cycle_years": None, "yield_unit": None, "income": None,
            "labor_owner": None, "labor_hired": None, "pdf_page": None,
            "labor_page": None, "source_kind": None, "year": None,
            "region": None, "url": r["discovery_source_url"], "calendar": None,
        })
    if len(result) != 51 + len(off["candidates"]):
        raise ValueError("Candidate coverage mismatch")
    return result


def render(csv_path=CSV, off_path=OFF, template_path=TEMPLATE,
           calendar_path=CALENDAR):
    text = Path(template_path).read_text(encoding="utf-8")
    slot = "__CROP_CATALOG_JSON__"
    if text.count(slot) != 1:
        raise ValueError("Expected exactly one catalog slot")
    packed = json.dumps(catalog(csv_path, off_path, calendar_path), ensure_ascii=False,
                        separators=(",", ":")).replace("<", "\\u003c")
    return text.replace(slot, packed)


def main():
    parser = argparse.ArgumentParser(description="Build/check offline all-crop workflow UI")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--build", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not HTML.exists() or HTML.read_text(encoding="utf-8") != expected:
            raise ValueError("Offline all-crop UI differs from validated source")
        print("All-crop browser matches 51 RDA entries and pending extras")
    else:
        HTML.parent.mkdir(parents=True, exist_ok=True)
        HTML.write_text(expected, encoding="utf-8")
        print("All-crop browser generated")


if __name__ == "__main__":
    main()
