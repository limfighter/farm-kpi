"""Official crop calendar pointers are a sparse subset, not assumed 51 crop workflows."""
import json
from pathlib import Path
import copy
import pytest

from farm_strategy.work_calendar import load_calendar_registry
from farm_strategy.reported import load_source

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data/metadata/crop_work_calendar_sources.json"
CROP_IDS = [r["crop_id"] for r in load_source(
    ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv")]


def test_sparse_official_calendar_coverage_never_populates_assumed_finances():
    refs = load_calendar_registry(FILE, CROP_IDS)
    assert len(CROP_IDS) == 51
    assert len(refs) == 20
    assert set(refs) <= set(CROP_IDS)
    assert refs["RDA2024-06"]["source_url"].endswith("menuId=PS00087")
    assert refs["RDA2024-22"]["stages"][-1]["crosses_calendar_year"] is True
    assert refs["RDA2024-19"]["stages"][0]["window_months"] == []  # UNKNOWN month, not 0
    assert refs["RDA2024-47"]["stages"][-1]["window_months"] == list(range(1, 13))
    assert all(x["source_kind"] == "R" and x["source_year"] is None
               for x in refs.values())
    assert all("cost" not in k and "price" not in k and "yield_quantity" not in k
               for x in refs.values() for s in x["stages"] for k in s)


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["references"][0].update(crop_id="RDA2024-NO"), "Unknown or duplicate"),
    (lambda d: d["references"].append(copy.deepcopy(d["references"][0])), "Unknown or duplicate"),
    (lambda d: d["references"][0].update(source_url="http://fake.com"), "official RDA"),
    (lambda d: d["references"][0]["stages"][0].update(window_months=[0]), "Invalid month"),
    (lambda d: d["references"][0]["stages"][0].update(window_months=[2, 2]), "Invalid month"),
    (lambda d: d["references"][0]["stages"][0].update(source_data_only=False), "flags"),
    (lambda d: d["references"][0]["stages"][0].update(hired_cost_krw=100), "fields mismatch"),
    (lambda d: d["references"][0].update(source_year=2024), "unasserted"),
    (lambda d: d["references"][0].update(match_level="EXACT_PARCEL"), "unasserted"),
])
def test_bad_calendar_rejected(tmp_path, mutate, needle):
    d = json.loads(FILE.read_text(encoding="utf-8"))
    mutate(d)
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(ValueError, match=needle):
        load_calendar_registry(p, CROP_IDS)


def test_2024_survey_not_modified_by_calendars():
    refs = load_calendar_registry(FILE, CROP_IDS)
    assert "RDA2024-49" not in refs  # four-year ginseng, no annual schedule made up
    assert "RDA2024-37" not in refs  # no false new-orchard calendar


def test_added_calendars_do_not_create_fictitious_income_or_site_suitability():
    refs = load_calendar_registry(FILE, CROP_IDS)
    paprika = refs["RDA2024-31"]
    assert paprika["official_title"] == "파프리카"
    assert paprika["stages"][-1]["window_months"] == [11,12,1,2,3,4,5,6,7]
    assert paprika["stages"][-1]["crosses_calendar_year"]
    eggplant = refs["RDA2024-30"]
    assert eggplant["stages"][0]["crosses_calendar_year"]
    assert eggplant["stages"][0]["window_months"] == [12,1]
    potato_fall = refs["RDA2024-07"]
    assert "전주" in potato_fall["season_notes"]  # explicitly unverified
    assert potato_fall["region_scope"] == "제주도, 남부 해안지대"
    cabbage = refs["RDA2024-16"]
    assert cabbage["stages"][-1]["window_months"] == []  # unverified month not zero
    blueberry = refs["RDA2024-44"]
    assert "1~2년" in blueberry["season_notes"]
    assert all("KRW" not in str(v) and "actual_profit" not in str(v)
               for v in refs.values())
