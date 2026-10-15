import csv
from farm_strategy.hourly import audit_hourly


def test_asos_cp949_qc_missing_and_duplicate(tmp_path):
    path = tmp_path / "OBS_ASOS_TIM_test.csv"
    keys = ["지점", "일시", "기온(°C)", "기온 QC플래그", "습도(%)", "습도 QC플래그", "풍속(m/s)", "풍속 QC플래그", "강수량(mm)", "강수량 QC플래그"]
    rows = [
        ["146", "2020-01-01 00:00", "2", "0", "60", "0", "1", "0", "", ""],
        ["146", "2020-01-01 01:00", "3", "0", "50", "0", "2", "0", "10", "9"],
        ["146", "2020-01-01 01:00", "3", "0", "50", "0", "2", "0", "", ""],
        ["147", "2020-01-01 02:00", "5", "0", "50", "0", "1", "0", "8", "0"],
    ]
    with path.open("w", encoding="cp949", newline="") as h:
        w = csv.writer(h)
        w.writerow(keys)
        w.writerows(rows)
    report = audit_hourly([path], start="2020-01-01 00:00", end="2020-01-01 02:00")
    assert report["unique_hours"] == 2
    assert report["missing_hours"] == ["2020-01-01T02:00:00"]
    assert report["duplicate_records"] == 1
    assert report["valid_value_hours"]["rain"] == 0
    assert report["qc_rejections_in_source_rows"]["rain"] == 1



def test_duplicate_hours_merge_complementary_values_and_report_conflicts(tmp_path):
    """The raw extracts can duplicate an hour with different valid fields."""
    path = tmp_path / "OBS_ASOS_TIM_complementary.csv"
    keys = ["지점", "일시", "기온(°C)", "기온 QC플래그",
            "습도(%)", "습도 QC플래그", "풍속(m/s)", "풍속 QC플래그",
            "강수량(mm)", "강수량 QC플래그"]
    rows = [
        ["146", "2020-01-01 00:00", "2", "0", "", "", "", "", "", ""],
        ["146", "2020-01-01 00:00", "", "", "", "", "1", "0", "6", "0"],
        ["146", "2020-01-01 00:00", "5", "0", "", "", "", "", "", ""],
    ]
    with path.open("w", encoding="cp949", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(keys)
        writer.writerows(rows)
    report = audit_hourly([path], start="2020-01-01 00:00", end="2020-01-01 00:00")
    assert report["unique_hours"] == 1
    assert report["duplicate_records"] == 2
    assert report["valid_value_hours"]["temperature"] == 1
    assert report["valid_value_hours"]["wind"] == 1
    assert report["valid_value_hours"]["rain"] == 1
    assert report["conflicting_duplicate_fields"] == {"temperature": 1}


def test_nonfinite_hourly_values_are_rejected(tmp_path):
    import pytest

    path = tmp_path / "OBS_ASOS_TIM_nonfinite.csv"
    with path.open("w", encoding="cp949", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["지점", "일시", "기온(°C)", "기온 QC플래그",
                         "습도(%)", "습도 QC플래그", "풍속(m/s)", "풍속 QC플래그",
                         "강수량(mm)", "강수량 QC플래그"])
        writer.writerow(["146", "2020-01-01 00:00", "NaN", "0",
                         "60", "0", "1", "0", "", ""])
    with pytest.raises(ValueError, match="Nonfinite ASOS temperature"):
        audit_hourly([path], start="2020-01-01 00:00", end="2020-01-01 00:00")
