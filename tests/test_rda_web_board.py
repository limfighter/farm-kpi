"""Offline historical web-source evidence board regression checks."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_rda_web_sample_board.py"
HTML = ROOT / "dashboard/source-coverage/index.html"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          cwd=ROOT, text=True, capture_output=True)


def test_dashboard_matches_checked_provenance():
    result = run("--check")
    assert result.returncode == 0, result.stderr
    page = HTML.read_text(encoding="utf-8")
    assert page.count('data-year="2022"') == 3
    assert page.count('data-year="2023"') == 3
    assert "상세 행 미표시 (0원 아님)" in page
    assert "7,065,740" in page
    assert "https://cdn" not in page
    assert "fetch(" not in page
    assert "PDF 미대조" in page


def test_stale_html_detected(tmp_path):
    path = tmp_path / "board.html"
    path.write_text(HTML.read_text(encoding="utf-8").replace("7,065,740", "9,999,999"),
                    encoding="utf-8")
    assert run("--check", "--html", path).returncode != 0
    assert run("--refresh", "--html", path).returncode == 0
    assert run("--check", "--html", path).returncode == 0
