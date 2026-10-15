"""The 51-crop readiness checklist is a data collection workflow, not a score."""
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts/build_feasibility.py'
CROPS = ROOT / 'data/reported/rda_2024_all_51_crop_candidates.csv'
READINESS = ROOT / 'data/derived/crop_readiness_51.csv'
HTML = ROOT / 'dashboard/feasibility/index.html'
EXPLORER = ROOT / 'dashboard/crop-discovery/index.html'
spec = importlib.util.spec_from_file_location('build_feasibility', BUILDER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_source_unchanged_and_all_51_have_only_unknown_parcel_status():
    original = module.read_crops()
    rows = module.build_rows(original)
    assert len(rows) == len(original) == 51
    assert [r['crop_id'] for r in rows] == [r['crop_id'] for r in original]
    assert {r['evidence_level'] for r in rows} == {'R_REPORTED_NATIONAL_NOT_PARCEL'}
    assert {r['land_ownership_status'] for r in rows} == {module.STATUS}
    for gate in module.GATES:
        assert {r[gate] for r in rows} == {module.STATUS}
    assert 'investment_rank' not in rows[0] and 'suitability_score' not in rows[0]
    assert all(x['reporting_year'] == 2024 for x in rows)
    assert all(x['reported_income_krw_per_10a'] == int(orig['income_krw_per_10a'])
               for x, orig in zip(rows, original))


def test_conditional_review_flags_are_never_a_suitability_decision():
    rows = module.build_rows(module.read_crops())
    facility = [r for r in rows if r['facility_infrastructure'] == 'REVIEW_REQUIRED']
    orchards = [r for r in rows if r['perennial_establishment'] == 'REVIEW_REQUIRED']
    multi = [r for r in rows if r['multi_year_cycle'] == 'REVIEW_REQUIRED']
    assert len(facility) == 19  # 17 protected veg + 1 fruit + 1 facility rose
    assert len(orchards) == 10  # 9 field + 1 protected orchard
    assert [(x['crop'], x['cycle_years']) for x in multi] == [('인삼(4년근)', 4)]
    assert next(x for x in rows if x['crop'] == '시설오이')['facility_infrastructure'] == 'REVIEW_REQUIRED'
    assert next(x for x in rows if x['crop'] == '봄감자')['facility_infrastructure'] == 'CATEGORY_NOT_FLAGGED'


def test_cached_files_match_generator_and_support_offline_navigation():
    assert module.build(check=True) is False
    html = HTML.read_text(encoding='utf-8')
    assert 'https://cdn' not in html
    assert '<script id="data" type="application/json">' in html
    assert html.count('"crop_id":"RDA2024-') == 51
    assert '자료 확보(검증 전)' in html
    assert 'document.createElement' in html
    assert '../feasibility/index.html' in EXPLORER.read_text(encoding='utf-8')
    with READINESS.open(encoding='utf-8', newline='') as inp:
        rows = list(csv.DictReader(inp))
    assert len(rows) == 51
    assert set(rows[0]) >= set(module.GATES)


def test_changed_generated_report_fails_check(tmp_path):
    stale_html = tmp_path / 'bad.html'
    stale_html.write_text(HTML.read_text(encoding='utf-8') + '<!-- stale -->', encoding='utf-8')
    run = subprocess.run([sys.executable, str(BUILDER), '--check',
                          '--html', str(stale_html)], capture_output=True, text=True)
    assert run.returncode != 0
    assert 'STALE' in run.stderr


def test_missing_crop_blocks_build(tmp_path):
    with CROPS.open(encoding='utf-8', newline='') as inp:
        rows = list(csv.DictReader(inp))
    fewer = tmp_path / 'less.csv'
    with fewer.open('w', encoding='utf-8', newline='') as out:
        wr = csv.DictWriter(out, fieldnames=list(rows[0])); wr.writeheader();wr.writerows(rows[:-1])
    run = subprocess.run([sys.executable, str(BUILDER), '--check',
                          '--crops', str(fewer)], capture_output=True, text=True)
    assert run.returncode != 0
    assert '51 unique' in run.stderr


def test_income_mutation_requires_source_reconciliation(tmp_path):
    with CROPS.open(encoding='utf-8', newline='') as inp:
        rows = list(csv.DictReader(inp))
    rows[0]['income_krw_per_10a'] = '999999'
    bad = tmp_path / 'bad.csv'
    with bad.open('w', encoding='utf-8', newline='') as out:
        wr=csv.DictWriter(out,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    run=subprocess.run([sys.executable,str(BUILDER),'--check','--crops',str(bad)],capture_output=True,text=True)
    assert run.returncode!=0
    assert 'Income not reconciled' in run.stderr