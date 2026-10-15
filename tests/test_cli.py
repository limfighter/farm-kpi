"""Exercise CLI contracts with real model inputs and private-schema templates."""
import csv
import json
from pathlib import Path

import pytest

from farm_strategy import cli


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_TEMPLATE = ROOT / "data/templates/private_evidence_TEMPLATE.csv"
SITE_TEMPLATE = ROOT / "data/templates/private_site_intake_TEMPLATE.json"


def test_validate_uses_global_inputs_and_prints_utf8_json(tmp_path, capsys):
    config = json.loads((ROOT / "configs/base.json").read_text(encoding="utf-8"))
    config["metadata"]["price_source"] = "가정 가격; 검증되지 않음"
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    weather_path = tmp_path / "weather.csv"
    weather_path.write_bytes((ROOT / "data/processed/annual_weather.csv").read_bytes())

    assert cli.main(["--config", str(config_path), "--weather", str(weather_path),
                     "validate"]) == 0

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert captured.err == ""
    assert captured.out.startswith('{\n  "n_weather_years": 20,\n')
    assert captured.out.endswith("\n") and not captured.out.endswith("\n\n")
    assert "가정 가격; 검증되지 않음" in captured.out
    assert report == {
        "n_weather_years": 20,
        "years": list(range(2006, 2026)),
        "weather_source": config["metadata"]["weather_source"],
        "price_source": "가정 가격; 검증되지 않음",
        "damage_parameters_status": config["metadata"]["damage_parameters_status"],
        "tax_insurance_status": config["tax_and_insurance"]["status"],
        "monthly_cashflow_status": config["monthly_cashflow"]["status"],
        "assumed_annual_inflation_rate": config["finance"]["assumed_annual_inflation_rate"],
    }


def test_forecast_flags_and_file_output_match_stdout(tmp_path, capsys):
    command = ["forecast", "--plan", "field_trial", "--scenario", "price_down_15",
               "--window", "all20", "--seed", "9", "--paths", "2",
               "--monthly-details"]
    assert cli.main(command) == 0
    stdout = capsys.readouterr()
    result = json.loads(stdout.out)
    assert stdout.err == ""
    assert {key: result[key] for key in ("plan", "scenario", "window", "seed", "paths")} == {
        "plan": "field_trial", "scenario": "price_down_15", "window": "all20",
        "seed": 9, "paths": 2,
    }
    assert len(result["illustrative_monthly_path"]["months"]) == 120
    assert result["metrics"]["project_npv"]["p10"] <= result["metrics"]["project_npv"]["p90"]

    output = tmp_path / "nested" / "forecast.json"
    assert cli.main(command + ["--output", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"Wrote {output}\n"
    assert captured.err == ""
    assert output.read_text(encoding="utf-8") == stdout.out
    assert stdout.out.endswith("\n") and not stdout.out.endswith("\n\n")


def test_compare_writes_every_stress_scenario_to_json_and_csv(tmp_path, capsys):
    output = tmp_path / "json" / "comparison.json"
    csv_output = tmp_path / "csv" / "comparison.csv"
    assert cli.main([
        "compare", "--scenario", "severe_damage", "--window", "all20",
        "--paths", "2", "--seed", "17", "--stress-matrix",
        "--output", str(output), "--csv", str(csv_output),
    ]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"Wrote {output}\n"
    assert captured.err == ""
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["comparison_method"] == "PAIRED_COMMON_RANDOM_NUMBERS"
    assert (result["paths"], result["seed"], result["window"]) == (2, 17, "all20")
    assert [case["scenario"] for case in result["scenarios"]] == list(cli.SCENARIOS)
    assert [run["plan"] for run in result["runs"]] == list(cli.PLANS)
    assert all(run["scenario"] == "severe_damage" for run in result["runs"])
    with csv_output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(cli.SCENARIOS) * len(cli.PLANS)
    assert {(row["scenario"], row["plan"]) for row in rows} == {
        (scenario, plan) for scenario in cli.SCENARIOS for plan in cli.PLANS
    }
    assert all((row["paths"], row["seed"], row["window"]) == ("2", "17", "all20")
               for row in rows)


@pytest.mark.parametrize("command,source", [
    ("evidence-check", EVIDENCE_TEMPLATE),
    ("site-check", SITE_TEMPLATE),
])
@pytest.mark.parametrize("write_output", [False, True])
def test_schema_commands_work_without_model_files(
    tmp_path, capsys, command, source, write_output
):
    missing_config = tmp_path / "missing-config.json"
    missing_weather = tmp_path / "missing-weather.csv"
    assert not missing_config.exists() and not missing_weather.exists()
    args = ["--config", str(missing_config), "--weather", str(missing_weather),
            command, "--file", str(source)]
    output = tmp_path / "nested" / "summary.json"
    if write_output:
        args.extend(["--output", str(output)])

    assert cli.main(args) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    if write_output:
        expected_message = (f"Redacted site evidence status written: {output.resolve()}\n"
                            if command == "site-check" else f"Wrote {output}\n")
        assert captured.out == expected_message
        text = output.read_text(encoding="utf-8")
    else:
        text = captured.out
    assert text.startswith("{\n  ")
    assert text.endswith("\n") and not text.endswith("\n\n")
    report = json.loads(text)
    if command == "evidence-check":
        assert report["evidence_rows"] == 0
        assert report["application"] == "NONE; base.json and simulations left unchanged"
    else:
        assert report["parcel_feasible"] is None
        assert report["gate_counts"]["UNKNOWN"] == 12
        assert report["decision_readiness"] == "BLOCKED_EVIDENCE_INCOMPLETE"


def test_site_output_keeps_private_path_guard(capsys):
    with pytest.raises(ValueError, match="ignored"):
        cli.main(["site-check", "--file", str(SITE_TEMPLATE),
                  "--output", str(ROOT / "configs/site-summary.json")])
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("args,error", [
    ([], "the following arguments are required: cmd"),
    (["evidence-check"], "the following arguments are required: --file"),
    (["site-check"], "the following arguments are required: --file"),
    (["calibration-preview", "--file", "input.csv"],
     "the following arguments are required: --review, --output-dir"),
    (["forecast", "--scenario", "unknown"], "invalid choice: 'unknown'"),
    (["forecast", "--window", "unknown"], "invalid choice: 'unknown'"),
    (["forecast", "--plan", "unknown"], "invalid choice: 'unknown'"),
    (["compare", "--paths", "many"], "invalid int value: 'many'"),
    (["validate", "--output", "report.json"], "unrecognized arguments: --output report.json"),
    (["forecast", "--config", "config.json"], "unrecognized arguments: --config config.json"),
    (["compare", "--weather", "weather.csv"], "unrecognized arguments: --weather weather.csv"),
    (["compare", "--monthly-details"], "unrecognized arguments: --monthly-details"),
    (["forecast", "--stress-matrix"], "unrecognized arguments: --stress-matrix"),
])
def test_invalid_arguments_keep_argparse_exit_status(args, error, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(args)
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert error in captured.err


@pytest.mark.parametrize("command,expected", [
    (["validate"], {"cmd": "validate"}),
    (["forecast"], {"cmd": "forecast", "scenario": "base", "window": "recent10",
                    "seed": 42, "paths": 1000, "output": None,
                    "plan": "new_cucumber_house", "monthly_details": False}),
    (["compare"], {"cmd": "compare", "scenario": "base", "window": "recent10",
                   "seed": 42, "paths": 1000, "output": None,
                   "stress_matrix": False, "csv": None}),
    (["evidence-check", "--file", "evidence.csv"],
     {"cmd": "evidence-check", "file": Path("evidence.csv"), "output": None}),
    (["site-check", "--file", "site.json"],
     {"cmd": "site-check", "file": Path("site.json"), "output": None}),
    (["calibration-preview", "--file", "evidence.csv", "--review", "review.json",
      "--output-dir", "output/local"],
     {"cmd": "calibration-preview", "file": Path("evidence.csv"),
      "review": Path("review.json"), "output_dir": Path("output/local"),
      "paths": 100, "seed": 42, "scenario": "base", "window": "recent10"}),
])
def test_build_parser_exposes_existing_defaults_without_running_commands(command, expected):
    args = cli.build_parser().parse_args(command)
    assert args.config == ROOT / "configs/base.json"
    assert args.weather == ROOT / "data/processed/annual_weather.csv"
    assert {name: getattr(args, name) for name in expected} == expected
