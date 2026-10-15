"""Full command generation stays separate from source/audit datasets."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_example_builds_json_and_offline_html(tmp_path):
    out = tmp_path / "result.json"
    page = tmp_path / "preview.html"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/compare_workflows.py"),
         "--input", str(ROOT / "data/templates/workflow_scenarios_SYNTHETIC.json"),
         "--output", str(out), "--html", str(page)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["cases"]) == 3
    assert all(r["status"] == "ILLUSTRATIVE_MODEL_NOT_VALIDATED_FARM_RETURN"
               for r in report["cases"])
    assert all(r["source_event_counts"]["A"] > 0 for r in report["cases"])
    assert "가상" in page.read_text(encoding="utf-8")
    assert "월별 농작업과 현금흐름" in page.read_text(encoding="utf-8")
