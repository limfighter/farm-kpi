"""Build and audit evidence-gated farm-option explorer; never score unknown feasibility.

2024 RDA published crop summaries are *reported* data, not parcel evidence.
Only categorical study requirements are derived from the source crop labels.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROPS = ROOT / 'data/reported/rda_2024_all_51_crop_candidates.csv'
READINESS = ROOT / 'data/derived/crop_readiness_51.csv'
TEMPLATE = ROOT / 'dashboard/feasibility/template.html'
HTML = ROOT / 'dashboard/feasibility/index.html'
CATS = {'식량작물': 7, '노지채소': 12, '시설채소': 17,
        '노지과수': 9, '시설과수': 1, '화훼': 1, '특용·약용': 4}
GATES = (
    'soil_and_drainage',
    'water_supply',
    'local_weather_crop_fit',
    'land_use_and_permits',
    'startup_capex',
    'peak_monthly_labor',
    'buyer_and_settlement',
    'planting_area_and_rotation',
)
OPTIONAL = ('facility_infrastructure', 'perennial_establishment', 'multi_year_cycle')
STATUS = 'UNKNOWN_NOT_EVALUATED'


def read_crops(path=CROPS):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        data = list(csv.DictReader(handle))
    if len(data) != 51 or len({x['crop_id'] for x in data}) != 51:
        raise ValueError('Expected 51 unique crop IDs')
    if {c: sum(x['category'] == c for x in data) for c in CATS} != CATS:
        raise ValueError('RDA 2024 category composition changed')
    out = []
    for x in data:
        if x['data_kind'] != 'R':
            raise ValueError('Only reported RDA crop sources are supported')
        if not x['crop'].strip():
            raise ValueError('Crop name missing')
        row = dict(x)
        for key in ('revenue_krw_per_10a', 'management_cost_krw_per_10a',
                    'income_krw_per_10a', 'cycle_years'):
            try:
                row[key] = int(x[key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f'Invalid {key}') from exc
        for key in ('labor_total_hours_per_10a', 'labor_hired_hours_per_10a',
                    'labor_owner_hours_per_10a'):
            row[key] = float(x[key])
            if not math.isfinite(row[key]) or row[key] < 0:
                raise ValueError('Invalid labor input')
        if abs(row['revenue_krw_per_10a'] - row['management_cost_krw_per_10a'] -
               row['income_krw_per_10a']) > 2:
            raise ValueError('Income not reconciled')
        if abs(row['labor_owner_hours_per_10a'] + row['labor_hired_hours_per_10a'] -
               row['labor_total_hours_per_10a']) > 0.11:
            raise ValueError('Labor not reconciled')
        if row['cycle_years'] not in (1, 4):
            raise ValueError('Unexpected crop cycle year value')
        out.append(row)
    if [x['crop'] for x in out if x['cycle_years'] == 4] != ['인삼(4년근)']:
        raise ValueError('Four-year ginseng must be retained as its own cycle')
    return out


def study_flags(crop):
    # Published category labels determine *which question to investigate*.
    # They do not establish actual on-site feasibility or existing assets.
    cat = crop['category']
    return {
        'facility_infrastructure': 'REVIEW_REQUIRED' if cat.startswith('시설') or cat == '화훼' else 'CATEGORY_NOT_FLAGGED',
        'perennial_establishment': 'REVIEW_REQUIRED' if cat.endswith('과수') else 'CATEGORY_NOT_FLAGGED',
        'multi_year_cycle': 'REVIEW_REQUIRED' if crop['cycle_years'] > 1 else 'CATEGORY_NOT_FLAGGED',
    }


def build_rows(crops):
    data = []
    for crop in crops:
        flags = study_flags(crop)
        item = {
            'crop_id': crop['crop_id'], 'crop': crop['crop'],
            'category': crop['category'], 'cycle_years': crop['cycle_years'],
            'reported_income_krw_per_10a': crop['income_krw_per_10a'],
            'reported_management_cost_krw_per_10a': crop['management_cost_krw_per_10a'],
            'reported_labor_hours_per_10a': crop['labor_total_hours_per_10a'],
            'reporting_year': 2024,
            'income_source_pdf_page': int(crop['source_pdf_page']),
            'labor_source_pdf_page': int(crop['labor_source_pdf_page']),
            'evidence_level': 'R_REPORTED_NATIONAL_NOT_PARCEL',
            'land_ownership_status': STATUS,
        }
        item.update({g: STATUS for g in GATES})
        item.update(flags)
        data.append(item)
    return data


def content(crops_path=CROPS, template_path=TEMPLATE):
    raw = Path(crops_path).read_bytes()
    crops = read_crops(crops_path)
    rows = build_rows(crops)
    template = Path(template_path).read_text(encoding='utf-8')
    if template.count('__EMBEDDED_FEASIBILITY__') != 1:
        raise ValueError('Template requires exactly one embedded data slot')
    safe = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    payload = template.replace('__EMBEDDED_FEASIBILITY__', safe)
    payload = payload.replace('__SOURCE_SHA256__', hashlib.sha256(raw).hexdigest())
    return rows, payload


def csv_bytes(rows):
    import io
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8')


def build(*, check=False, crop_path=CROPS, template_path=TEMPLATE,
          csv_path=READINESS, html_path=HTML):
    rows, html = content(crop_path, template_path)
    csv_target, html_target = Path(csv_path), Path(html_path)
    if check:
        if not csv_target.is_file() or csv_target.read_bytes() != csv_bytes(rows):
            raise ValueError('Crop readiness CSV missing or STALE')
        if not html_target.is_file() or html_target.read_text(encoding='utf-8') != html:
            raise ValueError('Feasibility HTML missing or STALE')
        return False
    for path in (csv_target, html_target):
        path.parent.mkdir(parents=True, exist_ok=True)
    csv_target.write_bytes(csv_bytes(rows))
    html_target.write_text(html, encoding='utf-8')
    return True


def main():
    parser = argparse.ArgumentParser(description='Validate/build unknown-first farm crop feasibility explorer')
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check', action='store_true')
    modes.add_argument('--refresh', action='store_true')
    parser.add_argument('--crops', type=Path, default=CROPS)
    parser.add_argument('--template', type=Path, default=TEMPLATE)
    parser.add_argument('--csv', type=Path, default=READINESS)
    parser.add_argument('--html', type=Path, default=HTML)
    a = parser.parse_args()
    build(check=a.check, crop_path=a.crops, template_path=a.template,
          csv_path=a.csv, html_path=a.html)
    print('51-crop feasibility: %s; all parcel-specific gates remain unknown' %
          ('VALID' if a.check else 'REBUILT'))


if __name__ == '__main__':
    main()
