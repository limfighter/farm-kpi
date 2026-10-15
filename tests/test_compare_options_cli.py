"""Paired alternative CLI emits inspectable offline incremental economics."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_cli_generates_pairwise_html_and_json(tmp_path):
    js,html=tmp_path/"options.json",tmp_path/"options.html"
    x=subprocess.run([
        sys.executable,str(ROOT/"scripts/compare_options.py"),
        "--input",str(ROOT/"data/templates/multiyear_scenarios_SYNTHETIC.json"),
        "--output",str(js),"--html",str(html)
    ],cwd=ROOT,capture_output=True,text=True)
    assert x.returncode==0,x.stderr
    report=json.loads(js.read_text(encoding="utf-8"))
    assert report["status"]=="SIMULATED_PAIRED_OPTION_DELTAS_NOT_VERIFIED_ADVANTAGE"
    assert report["deltas_alternative_minus_baseline_krw"]["net_expected_settlement"]==0
    page=html.read_text(encoding="utf-8")
    assert "가정 기반 모형" in page
    assert "양(+)의 기여액" in page
