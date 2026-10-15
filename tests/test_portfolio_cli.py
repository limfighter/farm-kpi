"""Offline real-world constraint report must not certify a synthetic farm."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_portfolio_command_generates_reproducible_reports(tmp_path):
    j,h=tmp_path/"cash.json",tmp_path/"report.html"
    r=subprocess.run([sys.executable,str(ROOT/"scripts/compare_portfolio.py"),
       "--input",str(ROOT/"data/templates/portfolio_SYNTHETIC.json"),
       "--output",str(j),"--html",str(h)],
       cwd=ROOT,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    data=json.loads(j.read_text(encoding="utf-8"))
    assert data["status"]=="HYPOTHETICAL_MULTI_CROP_NOT_SITE_OR_CREDIT_APPROVAL"
    assert data["financing"]["outstanding_principal_krw"]==750000
    html=h.read_text(encoding="utf-8")
    assert "주간 노동 부족" in html
    assert "대출 원금 잔액" in html
    assert "UNKNOWN" in html
    assert "월별 통합 현금" in html
