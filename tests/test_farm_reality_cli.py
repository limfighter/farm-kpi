"""Reports reproduce expected stress and never embed raw private evidence."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def run_cli(tmp_path,with_log):
    js,html=tmp_path/"report.json",tmp_path/"report.html"
    cmd=[sys.executable,str(ROOT/"scripts/analyze_farm_reality.py"),
       "--portfolio",str(ROOT/"data/templates/portfolio_SYNTHETIC.json"),
       "--stress",str(ROOT/"data/templates/farm_stresses_SYNTHETIC.json"),
       "--output",str(js),"--html",str(html)]
    if with_log:
        cmd+=["--log",str(ROOT/"data/templates/field_log_SYNTHETIC.csv")]
    result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    return json.loads(js.read_text(encoding="utf-8")),html.read_text(encoding="utf-8")


def test_synthetic_log_and_stresses_export(tmp_path):
    result,html=run_cli(tmp_path,True)
    assert len(result["stress"]["scenarios"])==3
    assert result["field_log"]["rows"]==9
    assert "DEMO_BANK_01" not in json.dumps(result)
    assert "스트레스 결과" in html
    assert "영농기록 CSV" in html
    assert "관수 부족" in html
    assert "부분 집계" in html


def test_no_log_is_unknown_not_a_harvest_failure(tmp_path):
    result,html=run_cli(tmp_path,False)
    assert result["field_log"] is None
    assert "전달되지 않았습니다" in html
    assert result["stress"]["scenarios"][0]["ending_cash_delta_krw"]==0
