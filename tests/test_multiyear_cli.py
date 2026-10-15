"""Run synthetic multiyear CLI and verify offline outputs."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_cli_creates_audit_json_and_html(tmp_path):
    output = tmp_path / "result.json"
    html = tmp_path / "result.html"
    proc = subprocess.run([
        sys.executable, str(ROOT / "scripts/compare_multiyear.py"),
        "--input", str(ROOT / "data/templates/multiyear_scenarios_SYNTHETIC.json"),
        "--output", str(output), "--html", str(html)
    ], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(report["cases"]) == 2
    assert all(r["horizon_years"] == 3 for r in report["cases"])
    assert all(r["source_event_counts"]["A"] > 0 for r in report["cases"])
    assert all(r["project_npv_krw_if_rate_supplied"] is not None for r in report["cases"])
    page = html.read_text(encoding="utf-8")
    assert "합성 예제" in page
    assert "월말" in page
    assert "연도별 운영 현금흐름" in page
