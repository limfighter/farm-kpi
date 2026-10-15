"""Test generated execution detail reports and their provenance notes."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_weekly_grade_cli_outputs(tmp_path):
    js,html=tmp_path/"detail.json",tmp_path/"detail.html"
    proc=subprocess.run([
        sys.executable,str(ROOT/"scripts/assess_execution.py"),
        "--input",str(ROOT/"data/templates/execution_detail_SYNTHETIC.json"),
        "--output",str(js),"--html",str(html)
    ],cwd=ROOT,capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    report=json.loads(js.read_text(encoding="utf-8"))
    assert report["weekly"]["weeks_exceeding_owner_capacity"]
    assert report["grading"]["replaced_sale_count"]==1
    assert report["grading"]["cash_deltas_alternative_minus_baseline_krw"]["net_expected_settlement_krw"]<0
    h=html.read_text(encoding="utf-8")
    assert "주간 노동 병목" in h
    assert "등급별 출하 대체" in h
    assert "UNKNOWN" in h
    assert "가정" in h
