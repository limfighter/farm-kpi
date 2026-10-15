"""Render explicit multi-year crop/facility scenario cashflows as JSON & offline HTML.

Never turns RDA crop income into a real parcel forecast.
"""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.lifecycle import compare_multiyear  # noqa: E402


def money(v):
    return f"{v:,.0f}" if v is not None else "UNKNOWN"


def render_html(result):
    cases = result["cases"]
    rows = []
    for x in cases:
        cols = [escape(x["crop"] + " / " + x["system"]),
                str(x["horizon_years"]) + "년",
                money(x["net_expected_settlement_krw"]),
                money(x["operating_contribution_before_owner_labor_tax_depreciation_krw"]),
                money(x["capital_expenditure_krw"]),
                money(x["peak_month_end_funding_gap_krw"]),
                money(x["unsettled_settlement_after_horizon_krw"]),
                money(x["project_npv_krw_if_rate_supplied"])]
        rows.append("<tr>" + "".join(f"<td>{v}</td>" for v in cols) + "</tr>")
    years_html = []
    for x in cases:
        lines = []
        for v in x["years"]:
            cols = [str(v["year"]), money(v["received_krw"]),
                    money(v["operating_expense_krw"]), money(v["capex_krw"]),
                    money(v["net_cash_krw"]), f'{v["owner_hours"]:.1f}',
                    f'{v["hired_hours"]:.1f}']
            lines.append("<tr>" + "".join(f"<td>{a}</td>" for a in cols) + "</tr>")
        years_html.append(
            "<details><summary>" + escape(x["crop"] + " / " + x["system"]) +
            " — 연도별 운영 흐름</summary><div class=scroll><table><thead>" +
            "".join(f"<th>{v}</th>" for v in ("연도","정산입금","운영비","시설투자",
                                              "순현금","자가(h)","고용(h)")) +
            "</thead><tbody>" + "".join(lines) +
            "</tbody></table></div></details>"
        )
    html = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Farm KPI | 다년 농장 현금흐름 실험</title>
<style>
:root{font:16px/1.5 system-ui,-apple-system,sans-serif;color:#304437;background:#f7f8f3}
body{margin:auto;max-width:1280px;padding:25px}
h1{font-size:clamp(24px,4vw,38px)}.warn{background:#faeed8;border-left:4px solid #b8894d;padding:16px}
.panel{border:1px solid #dce4db;background:white;border-radius:12px;padding:18px;margin-top:20px}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:940px}
td,th{border-bottom:1px solid #dfe8dc;padding:11px;text-align:right;font-variant-numeric:tabular-nums;font-size:13px}
td:first-child,th:first-child{text-align:left}th{background:#eaf1e8}
summary{cursor:pointer;font-weight:600;padding:10px}details{border:1px solid #dce4db;margin:10px 0;border-radius:9px}
small{color:#5d7061}
</style></head><body><div><small>FARM KPI · MULTIYEAR MODEL — ILLUSTRATIVE</small>
<h1>농장 작기·시설별 다년 현금흐름</h1>
<p class="warn"><strong>전체 금액·노동·작업월이 모델 가정(A)인 합성 예제입니다.</strong>
특정 작물의 재배 적합성이나 실제 시설투자 ROI가 아닙니다. 할인율은 명시적으로 입력한 가정이며,
자가노동 경제적 가치가 미입력이면 경제적 NPV를 계산하지 않습니다.</p></div>
<section class=panel><h2>다년 작물 × 시설 대안</h2><div class=scroll><table><thead><tr>""" + "".join(
        f"<th>{h}</th>" for h in ("대안","기간","총 순정산예정액","운영기여액¹",
                                "시설투자 현금","최대 월말 자금부족",
                                "만기후 미수금","사업 NPV²")
    ) + "</tr></thead><tbody>" + "".join(rows) + """</tbody></table></div>
<p><small>모든 금액은 입력 기준연도의 불변 원. ¹영업 기여액은 자기노동, 세금, 감가상각, 대출 제외.
²명시한 연 실질할인율을 월말에 적용. 보증금과 잔존가 현금은 별도 항목이며 비용 중복 없음.
NPV 역시 가상 입력에서 나온 수학적 출력이지 검증된 ROI가 아닙니다.</small></p></section>
<section class=panel><h2>연도별 운영 현금흐름</h2>""" + "".join(years_html) + """</section>
</body></html>"""
    return html


def main():
    p = argparse.ArgumentParser(description="Multi-year explicit-input crop/facility ledger")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--html", type=Path)
    args = p.parse_args()
    input_data = json.loads(args.input.read_text(encoding="utf-8"))
    if (set(input_data) != {"schema_version","disclaimer","cases"}
            or input_data["schema_version"] != 2
            or not isinstance(input_data["disclaimer"], str)
            or not input_data["disclaimer"].strip()):
        raise ValueError("Expected version 2 with nonempty disclaimer and cases")
    result = compare_multiyear(input_data["cases"])
    result["disclaimer"] = input_data["disclaimer"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(result), encoding="utf-8")
    print(f"{len(result['cases'])} synthetic multi-year inputs simulated; not a farm forecast")


if __name__ == "__main__":
    main()
