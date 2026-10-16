"""One CLI produces one single-screen report and one authoritative JSON."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_unified_cli_with_optional_private_log(tmp_path):
    out,html=tmp_path/"integrated.json",tmp_path/"integrated.html"
    args=[sys.executable,str(ROOT/"scripts/run_farm_workspace.py"),
          "--input",str(ROOT/"data/templates/farm_workspace_SYNTHETIC.json"),
          "--log",str(ROOT/"data/templates/field_log_SYNTHETIC.csv"),
          "--output",str(out),"--html",str(html)]
    r=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    report=json.loads(out.read_text(encoding="utf-8"))
    assert report["authoritative_portfolio"]["financing"]["drawn_krw"]==1000000
    assert report["enabled_sections"]["physical"] is True
    assert report["field_log"]["rows"]==9
    html_text=html.read_text(encoding="utf-8")
    for label in ("농장 통합 워크스페이스","하나의 농장 통합 현금원장",
                  "작물 × 시설 × 구획", "가격·수량·공급 위험", "개인 로컬 영농기록",
                  "공통 자원·노동 제약", "등급별 판매와 포장비"):
        assert label in html_text
    assert "DEMO_BANK_01" not in html_text
    assert "DEMO_WORK_01" not in html_text


def test_only_one_cash_value_is_authoritative(tmp_path):
    out=tmp_path/"run.json"
    r=subprocess.run([sys.executable,str(ROOT/"scripts/run_farm_workspace.py"),
                      "--input",str(ROOT/"data/templates/farm_workspace_SYNTHETIC.json"),
                      "--output",str(out)],cwd=ROOT,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    data=json.loads(out.read_text(encoding="utf-8"))
    assert data["field_log"] is None
    assert data["stress"]["baseline_ending_cash_krw"]==data["authoritative_portfolio"]["ending_cash_krw"]
