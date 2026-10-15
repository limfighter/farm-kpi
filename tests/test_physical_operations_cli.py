"""Offline daily utilization HTML is generated from auditable source JSON."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_daily_cli_produces_stage_and_amortization_preview(tmp_path):
    out,html=tmp_path/"daily.json",tmp_path/"daily.html"
    run=subprocess.run([sys.executable,str(ROOT/"scripts/assess_physical_operations.py"),
        "--input",str(ROOT/"data/templates/physical_operations_SYNTHETIC.json"),
        "--output",str(out),"--html",str(html)],
        cwd=ROOT,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    r=json.loads(out.read_text(encoding="utf-8"))
    assert r["crop_count"]==2
    assert len(r["loan_schedule"]["events"])==27
    page=html.read_text(encoding="utf-8")
    assert "작기 전환 날짜" in page
    assert "펌프 소요시간" in page
    assert "무차입 사업 NPV" in page
    assert "가정" in page
