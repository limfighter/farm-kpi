"""Refresh the offline SVG Farm KPI dashboard from model-only comparison CSV.

No external JS/CSS/network assets are loaded. The source snapshot remains a
hypothetical model output, not farm accounting or investment advice.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
from pathlib import Path

PLANS = (
    "field_trial", "pause_after_trial", "new_cucumber_house",
    "leased_cucumber_house", "new_cucumber_premium",
)
SCENARIOS = (
    "base", "weak_damage", "severe_damage", "price_down_15",
    "wage_up_30", "capex_up_20",
)
PLAN_NAME = {
    "field_trial": "노지 감자·쪽파 지속",
    "pause_after_trial": "시험재배 후 중단",
    "new_cucumber_house": "오이 하우스 신축",
    "leased_cucumber_house": "오이 하우스 임대",
    "new_cucumber_premium": "프리미엄 오이 하우스",
}
PLAN_ICON = {
    "field_trial": "🌱", "pause_after_trial": "⏸️",
    "new_cucumber_house": "🏗️", "leased_cucumber_house": "📄",
    "new_cucumber_premium": "⭐",
}
PLAN_DESC = {
    "field_trial": "노지 작물(감자·쪽파)을 계속 운영하는 기준 전략",
    "pause_after_trial": "시험재배 뒤 운영을 멈추는 보수적 전략",
    "new_cucumber_house": "2028년 하우스를 신축해 오이 재배로 전환",
    "leased_cucumber_house": "하우스를 임대해 오이 재배로 운영",
    "new_cucumber_premium": "프리미엄 매출 uplift를 가정한 신축 오이 전략",
}
SCENARIO_NAME = {
    "base": "기본", "weak_damage": "약한 피해",
    "severe_damage": "심한 피해", "price_down_15": "가격 -15%",
    "wage_up_30": "인건비 +30%", "capex_up_20": "투자비 +20%",
}
METRICS = (
    ("economic_npv_median", "경제적 NPV 중앙값"),
    ("monthly_liquidity_buffer_required_p90", "월별 필요자금 P90"),
    ("cash_2030_after_debt_median", "2030 부채후 현금 중앙값"),
)
CARD_METRICS = (
    "economic_npv_median", "project_npv_median",
    "monthly_liquidity_buffer_required_p90", "cash_2030_after_debt_median",
    "hired_hours_2030_median", "debt_end_nominal_median",
)


def read_comparison_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        needed = {"scenario", "plan", "seed", "paths", "window", *CARD_METRICS}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError(f"Missing comparison CSV columns: {sorted(needed - set(reader.fieldnames or []))}")
        raw = list(reader)
    if len(raw) != len(PLANS) * len(SCENARIOS):
        raise ValueError("Expected exactly six scenarios x five farm plans")
    rows = {}
    seeds, counts, windows = set(), set(), set()
    for original in raw:
        scenario, plan = original["scenario"], original["plan"]
        if scenario not in SCENARIOS or plan not in PLANS or (scenario, plan) in rows:
            raise ValueError(f"Unknown or duplicate scenario/plan: {scenario}/{plan}")
        try:
            seed, count = int(original["seed"]), int(original["paths"])
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid seed or path count") from exc
        if count < 1:
            raise ValueError("paths must be positive")
        row = dict(original)
        for metric in CARD_METRICS:
            value = float(row[metric])
            if not math.isfinite(value):
                raise ValueError(f"Nonfinite comparison metric: {metric}")
            row[metric] = value
        rows[(scenario, plan)] = row
        seeds.add(seed)
        counts.add(count)
        windows.add(row["window"])
    if len(seeds) != 1 or len(counts) != 1 or len(windows) != 1:
        raise ValueError("All rows must use one consistent seed, path count and weather window")
    if set(rows) != {(scenario, plan) for scenario in SCENARIOS for plan in PLANS}:
        raise ValueError("Missing scenario/plan")
    return rows, next(iter(seeds)), next(iter(counts)), next(iter(windows))


def color_mix(left: str, right: str, position: float):
    lo = tuple(int(left[idx:idx + 2], 16) for idx in (1, 3, 5))
    hi = tuple(int(right[idx:idx + 2], 16) for idx in (1, 3, 5))
    pos = max(0, min(1, position))
    values = tuple(round(a + pos * (b - a)) for a, b in zip(lo, hi))
    return '#{:02x}{:02x}{:02x}'.format(*values)


def render_tables(rows):
    order = sorted(PLANS, key=lambda p: -rows[("base", p)]["economic_npv_median"])
    blocks = []
    for metric, title in METRICS:
        figures = [row[metric] for row in rows.values()]
        low, high = min(figures), max(figures)
        is_buffer = metric == "monthly_liquidity_buffer_required_p90"
        blocks.append(f'<div class="metric-table metric-{metric}" style="display:none">')
        blocks.append('<div class="matrix-head">')
        blocks.append(f'<h3>{html.escape(title)}</h3><p>만원, 2026 불변가 · 모형 가정</p>')
        blocks.append('</div><div class="table-wrap"><table><thead><tr><th>시나리오</th>')
        for plan in order:
            blocks.append(f'<th>{html.escape(PLAN_ICON[plan])} {html.escape(PLAN_NAME[plan])}</th>')
        blocks.append('</tr></thead><tbody>')
        for scenario in SCENARIOS:
            blocks.append(f'<tr><th>{html.escape(SCENARIO_NAME[scenario])}</th>')
            for plan in order:
                value = rows[(scenario, plan)][metric]
                pos = 0.5 if low == high else (value - low) / (high - low)
                bg = color_mix('#EFE3D8', '#7A5A43', pos) if is_buffer else color_mix('#EDF2EA', '#80997E', pos)
                blocks.append(f'<td style="background:{bg}">{value:,.0f}</td>')
            blocks.append('</tr>')
        blocks.append('</tbody></table></div></div>')
    return '\n    '.join(blocks)


def render_scenario_data(rows):
    results = {}
    for scenario in SCENARIOS:
        order = sorted(PLANS, key=lambda p: -rows[(scenario, p)]["economic_npv_median"])
        results[scenario] = []
        for plan in order:
            record = rows[(scenario, plan)]
            item = {
                "plan": plan,
                "plan_ko": PLAN_NAME[plan],
                "icon": PLAN_ICON[plan],
                "desc": PLAN_DESC[plan],
                **{metric: record[metric] for metric in CARD_METRICS},
            }
            results[scenario].append(item)
    # Avoid treating the JSON as executable JS or breaking out of a script tag.
    return json.dumps(results, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def replace_once(source, start, end, replacement):
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Missing or duplicated dashboard markers: {start}, {end}")
    start_index = source.index(start) + len(start)
    end_index = source.index(end)
    if end_index <= start_index:
        raise ValueError("Dashboard marker order invalid")
    return source[:start_index] + '\n' + replacement + '\n' + source[end_index:]


def build_html(template, rows, paths, window):
    source = replace_once(template, '<!-- DASHBOARD_TABLE_START -->',
                          '<!-- DASHBOARD_TABLE_END -->', '    ' + render_tables(rows))
    source = replace_once(source, '// DASHBOARD_DATA_START',
                          '// DASHBOARD_DATA_END',
                          'const scenarioData = ' + render_scenario_data(rows) + ';')
    for tag, value in (("data-model-paths", paths), ("data-model-window", window)):
        pattern = rf'(<div class="value" {tag}>).*?(</div>)'
        source, n = re.subn(pattern, lambda m: m.group(1) + html.escape(str(value)) + m.group(2), source)
        if n != 1:
            raise ValueError(f"Missing or duplicate model label: {tag}")
    return source


def main(argv=None):
    parser = argparse.ArgumentParser(description="Refresh/verify offline Farm KPI HTML dashboard snapshot")
    parser.add_argument('--csv', type=Path, required=True)
    parser.add_argument('--html', type=Path, required=True, help="Existing annotated HTML template")
    parser.add_argument('--output', type=Path, help="Write refreshed HTML to another location")
    parser.add_argument('--check', action='store_true', help="Fail if the tracked HTML is stale")
    args = parser.parse_args(argv)
    if args.output and args.check:
        parser.error("Use either --output or --check")
    rows, seed, paths, window = read_comparison_csv(args.csv)
    current = args.html.read_text(encoding="utf-8")
    updated = build_html(current, rows, paths, window)
    if args.check:
        if current != updated:
            raise SystemExit("Dashboard is stale. Run builder to refresh from the matched comparison CSV.")
        print(f"Dashboard snapshot verified: {len(rows)} rows, seed {seed}, {paths} paths, {window}")
        return 0
    destination = args.output or args.html
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(updated, encoding="utf-8")
    print(f"Wrote {destination} from {len(rows)} model-only rows (seed={seed}, paths={paths}, window={window})")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
