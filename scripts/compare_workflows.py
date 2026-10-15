"""Produce audit-friendly JSON and self-contained HTML from workflow scenarios."""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.workflow import compare_workflows  # noqa: E402


def _won(x):
    return f"{x:,.0f}"


def render_html(result):
    cases = result["cases"]
    headers = ("작물 / 시설", "순정산 예정액", "운영 기여액¹", "초기 투자",
               "12월 현금잔고", "연말 미수금", "최대 월말 필요자금", "자가 / 고용 노동(h)")
    cells = []
    for r in cases:
        values = [
            f'{escape(r["crop"])}<small>{escape(r["facility"])}</small>',
            _won(r["net_receivables_krw"]),
            _won(r["operating_contribution_before_owner_labor_tax_depreciation_krw"]),
            _won(r["upfront_capex_krw"]), _won(r["december_cash_balance_krw"]),
            _won(r["unsettled_receivables_after_december_krw"]),
            _won(r["peak_month_end_funding_gap_krw"]),
            f'{r["owner_hours"]:.1f} / {r["hired_hours"]:.1f}'
        ]
        cells.append("<tr>" + "".join(f"<td>{v}</td>" for v in values) + "</tr>")
    details = []
    for r in cases:
        rows = []
        for m in r["months"]:
            if not m["activities"] and m["net_cash_krw"] == 0:
                continue
            row = [
                f'{m["year"]}-{m["month"]:02}',
                escape(", ".join(m["activities"])) or "정산",
                _won(m["net_settlement_received_krw"]),
                _won(m["operating_cash_out_krw"]),
                _won(m["capital_cash_out_krw"]),
                _won(m["deposit_paid_krw"]-m["deposit_returned_krw"]),
                _won(m["net_cash_krw"]), _won(m["cumulative_cash_krw"]),
            ]
            rows.append("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>")
        details.append(
            '<details><summary>' + escape(r["crop"]+" / "+r["facility"]) + ' — 월별 작업·현금 흐름</summary>'
            '<div class="scroll"><table><thead><tr>' +
            "".join(f"<th>{x}</th>" for x in ("월", "작업·시설", "정산 입금", "운영 지출",
                          "시설 투자", "보증금 순지급", "월 순현금", "누적 현금")) +
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div></details>"
        )
    return ("""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Farm KPI | 농작업 기반 손익 시뮬레이션 실험</title>
<style>
:root{color-scheme:light;background:#f7f7f2;color:#27382e;font-family:system-ui,-apple-system,sans-serif}
body{max-width:1260px;margin:0 auto;padding:32px 20px 64px;line-height:1.55}
h1{font-size:clamp(26px,4vw,38px);margin:4px 0 8px}p{max-width:960px}
.eyebrow{font-size:13px;color:#536b5d;letter-spacing:.08em;font-weight:700}
.warning{background:#f4ebd7;border-left:5px solid #ae8047;padding:18px;border-radius:6px}
.card{margin-top:26px;background:white;border:1px solid #dce2d8;border-radius:12px;padding:20px}
.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px;white-space:nowrap}
td,th{text-align:right;padding:13px 10px;border-bottom:1px solid #e5e8e0;font-variant-numeric:tabular-nums}
td:first-child,th:first-child{text-align:left}th{background:#e7eee6}
small{display:block;color:#63806a;font-size:12px}summary{cursor:pointer;font-weight:650;padding:15px}
details{border:1px solid #dce2d8;border-radius:9px;margin:12px 0;background:white}
details[open]{padding-bottom:12px}.note{color:#5d6d60;font-size:13px}
a{color:#336444}
</style></head><body>
<p class="eyebrow">FARM KPI / WORKFLOW UNIT ECONOMICS · EXPERIMENT</p>
<h1>작물 × 시설 운영 수익 시뮬레이션</h1>
<p>각 작업의 자재·외주·고용노동, 생산·출하, 수수료와 입금 지연, 시설 투자·임대 보증금을 월별로 계산합니다.</p>
<div class="warning"><strong>전부 가상 예시(A)입니다.</strong> 작물별 실제 작업월, 수량, 가격, 시설 견적, 인건비를 확인한 데이터가 아닙니다. 숫자가 높다고 해당 작물을 추천하거나 투자 결정을 승인하는 것이 아닙니다.</div>
<section class="card"><h2>작물·시설 대안 비교</h2><div class="scroll"><table><thead><tr>""" +
            "".join(f"<th>{x}</th>" for x in headers) +
            "</tr></thead><tbody>" + "".join(cells) + """</tbody></table></div>
<p class="note">단위: 원(가정한 동일 기준연도 명목원). ¹운영 기여액 = 예상 순정산액 − 자재·고용·외주·운송·시설운영 지출. 자기노동 가치·감가상각·세금·대출이 제외되어 회계상 순이익이 아닙니다. 최대 필요자금은 월말 기준 누적 현금의 최저값이며, 일중 자금압박은 포함하지 않습니다.</p>
</section><section class="card"><h2>월별 농작업과 현금흐름</h2>""" +
            "".join(details) + """</section>
<p class="note">이 화면은 정적 생성물이며 외부 데이터 수집·전송이 없습니다. 농작업 검증 출처는 <a href="https://www.nongsaro.go.kr/portal/ps/psb/psbl/workScheduleLst.ps?menuId=PS00087">농사로 농작업일정</a>을 조사할 예정이며 아직 월별 예시값으로 재현하지 않았습니다.</p>
</body></html>""")


def main():
    parser = argparse.ArgumentParser(description="Illustrative crop/facility workflow comparisons")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if set(payload) != {"schema_version", "disclaimer", "cases"} or payload["schema_version"] != 1:
        raise ValueError("Expected schema_version=1, disclaimer and cases")
    if not isinstance(payload["disclaimer"], str) or not payload["disclaimer"].strip():
        raise ValueError("A nonempty simulation disclaimer is mandatory")
    result = compare_workflows(payload["cases"])
    result["disclaimer"] = payload["disclaimer"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(result), encoding="utf-8")
    print(f"Simulated {len(result['cases'])} illustrative workflow cases; not verified farm returns")


if __name__ == "__main__":
    main()
