"""Farm KPI's single planning command: one input -> one authoritative report."""
import argparse
from html import escape as e
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.farm_workspace import run_farm_workspace  # noqa: E402


def val(number, unit="원"):
    return "UNKNOWN" if number is None else f"{number:,.0f}{unit}"


def cell(text):
    return "<td>" + e(str(text)) + "</td>"


def table(headers, data, *, wide=False):
    head = "<tr>" + "".join("<th>" + e(str(x)) + "</th>" for x in headers) + "</tr>"
    body = "".join("<tr>" + "".join(cell(x) for x in row) + "</tr>" for row in data)
    if not body:
        body = '<tr><td colspan="' + str(len(headers)) + '">미입력 / UNKNOWN</td></tr>'
    return '<div class="scroll"><table class="' + ("wide" if wide else "") + '"><thead>' + head + '</thead><tbody>' + body + "</tbody></table></div>"


def section(name, content):
    return '<section id="' + e(name[0]) + '"><h2>' + e(name[1]) + "</h2>" + content + "</section>"


def render_html(result):
    main = result["authoritative_portfolio"]
    status = result["resource_and_labor_screen"]
    flags = result["enabled_sections"]
    crops = table(
        ["작물", "시설/방식", "구획", "면적", "판매 순수취(가정)", "운영기여(자가노동 제외)"],
        [(v["crop"], v["system"], v["plot_id"], val(v["area_m2"], "㎡"),
          val(v["net_expected_settlement_krw"]),
          val(v["operating_contribution_krw"])) for v in main["per_crop"]],
    )
    months = table(
        ["연월", "사업 현금", "금융 포함 현금", "월말 잔고",
         "물(m³)", "전력(kWh)", "자가(h)", "고용(h)"],
        [(f'{m["year"]}-{m["month"]:02d}', val(m["unlevered_cash_krw"]),
          val(m["financed_cash_krw"]), val(m["balance_after_financing_krw"]),
          val(m["water_m3"], "m³"), val(m["electricity_kwh"], "kWh"),
          val(m["owner_hours"], "h"), val(m["hired_hours"], "h"))
         for m in main["monthly"]], wide=True,
    )
    resources = table(
        ["자원", "부족 발생 월수", "공급 미확인 월수", "최대 부족량"],
        [(key, v["shortage_months"], v["unknown_supply_months"],
          val(v["max_shortage"], "")) for key, v in status["monthly"].items()],
    )
    weekly = '<p>주간 노동: <strong>' + e(status["weekly_labor_status"]) + "</strong> · 자가 부족 " + e(str(status["owner_shortage_weeks"]) if status["owner_shortage_weeks"] is not None else "UNKNOWN") + "주 · 고용 부족 " + e(str(status["hired_shortage_weeks"]) if status["hired_shortage_weeks"] is not None else "UNKNOWN") + "주</p>"
    grades = '<p class="quiet">등급별 판매 미입력. 원매출을 그대로 유지합니다.</p>'
    if flags["grades"]:
        grades = table(
            ["작형 ID", "판매건 교체", "등급 수", "순수취 증감", "운영비 증감"],
            [(key, v["replaced_sale_count"], v["grade_lot_count"],
              val(v["cash_deltas_alternative_minus_baseline_krw"]["net_expected_settlement_krw"]),
              val(v["cash_deltas_alternative_minus_baseline_krw"]["operating_cash_cost_krw"]))
             for key, v in result["grade_adjustments"].items()],
        ) + '<p class="quiet">등급별 출하는 기존 판매를 대체합니다. 포장비는 출하월에 반영되어 있으며 아래 농장 전체 원장에도 이미 포함됐습니다.</p>'
    physical = result["physical_operations"]
    physical_html = '<p class="unknown">일별 재배력/관수 펌프/순간 전력 미입력: UNKNOWN</p>'
    if physical is not None:
        cap = table(["검증 항목", "결과"], [
            ("명시된 생육단계", physical["growth_stage_count"]),
            ("작기 전환 간격", len(physical["date_turnarounds"])),
            ("펌프 가동시간 초과 일수", len(physical["days_exceeding_pump_window"])),
            ("피크 전력 초과 일수", len(physical["days_exceeding_peak_kw"])),
            ("펌프 용량 미확인 일수", physical["days_with_unknown_pump_capacity"]),
            ("전력 용량 미확인 일수", physical["days_with_unknown_electric_peak_capacity"]),
            ("명시 대출 상환표", "가정형 생성" if physical["loan_schedule"] is not None else "별도 생성 안 함"),
        ])
        physical_html = cap + "<p class=quiet>월별 kWh는 순간 kW가 아닙니다. 명시된 피크값은 동시 가동을 보수적으로 가정합니다.</p>"
    stress = result["stress"]
    stress_html = '<p class="unknown">가격·수량·자원 스트레스 미입력: UNKNOWN</p>'
    if stress is not None:
        stress_html = table(
            ["가정", "순정산 변화", "기말현금 변화", "최대 자금부족 변화", "실행 제약 상태"],
            [(s["id"], val(s["net_expected_settlement_delta_krw"]),
              val(s["ending_cash_delta_krw"]),
              val(s["peak_month_end_cash_shortfall_delta_krw"]),
              s["physical_supply_status"]) for s in stress["scenarios"]],
            wide=True,
        ) + '<p class="quiet">관수·전력 부족은 자동으로 수확량 감소를 만들지 않습니다. 매출 변화 0원 ≠ 재배 가능 확인.</p>'
    log = result["field_log"]
    log_html = '<p class="unknown">실제 영농일지 미입력: UNKNOWN</p>'
    if log is not None:
        log_html = table(
            ["작형", "기록 상태", "입력 행", "정산 입금 합계", "지급 비용 합계", "자가 작업시간"],
            [(r["case_id"], r["coverage"], r["recorded_rows"],
              val(r["recorded"]["settled_cash_krw"]),
              val(r["recorded"]["paid_expense_krw"]),
              val(r["recorded"]["owner_hours_recorded"], "h"))
             for r in log["cases"]],
        ) + '<p class="quiet">일지는 부분 합계만 보여줍니다. 위 시뮬레이션의 현금흐름에 다시 더하거나 전체 실제 수익으로 보지 않습니다.</p>'
    notices = "".join("<li>" + e(w) + "</li>" for w in result["warnings"])
    finance = main["financing"]
    nav = "".join('<a href="#'+key+'">'+label+"</a>" for key, label in (
        ("overview", "개요"), ("crops", "작물·시설"), ("cash", "현금"),
        ("resources", "농장 제약"), ("grades", "판매등급"), ("physical", "일별 운영"),
        ("stress", "위험"), ("records", "영농기록")))
    sections = (
        section(("crops", "작물 × 시설 × 구획"), crops)
        + section(("cash", "하나의 농장 통합 현금원장"), months)
        + section(("resources", "공통 자원·노동 제약"), resources + weekly)
        + section(("grades", "등급별 판매와 포장비"), grades)
        + section(("physical", "생육단계와 물리적 실행"), physical_html)
        + section(("stress", "가격·수량·공급 위험"), stress_html)
        + section(("records", "개인 로컬 영농기록(별도)"), log_html)
    )
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 통합 농장 경영 워크스페이스</title>
<style>
:root{font:15px/1.55 system-ui,-apple-system,sans-serif;color:#263d33;background:#f5f7f2}
*{box-sizing:border-box}body{margin:0}.layout{max-width:1360px;margin:auto;display:grid;grid-template-columns:220px 1fr;gap:24px;padding:26px}
aside{position:sticky;top:22px;align-self:start;border-radius:15px;background:#193f31;color:white;padding:18px}
aside strong{font-size:21px}nav{display:grid;gap:4px;margin-top:18px}nav a{color:#e2eee5;text-decoration:none;padding:10px;border-radius:7px}nav a:hover{background:#315d48}
main{min-width:0}header,section{border:1px solid #dae5da;background:white;border-radius:14px;padding:21px;margin-bottom:16px}
header{background:#e8f0e5}h1{font-size:clamp(25px,3vw,36px);margin:0}h2{font-size:20px;margin:0 0 14px}
.muted,.quiet{color:#667b6e;font-size:13px}.warning,.unknown{border-left:4px solid #b5894e;background:#fcf0da;padding:12px;border-radius:4px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;margin:17px 0}
.metric{background:white;border-radius:10px;padding:13px;border:1px solid #d3e0d3}
.metric small{display:block;color:#5d7866}.metric strong{display:block;font-size:23px}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:630px}
table.wide{min-width:930px}td,th{border-bottom:1px solid #e1e9df;padding:9px;text-align:right;white-space:nowrap;font-size:12px}
td:first-child,th:first-child{text-align:left}thead{background:#ecf3ea}
ul{padding-left:20px}.subtle{font-size:12px;color:#668072}
@media(max-width:850px){.layout{display:block;padding:12px}aside{position:static;margin-bottom:13px}nav{grid-template-columns:repeat(4,1fr)}nav a{padding:7px;font-size:12px}section{padding:15px}}
</style></head><body><div class="layout">
<aside><strong>Farm KPI</strong><p class="subtle">ONE FARM · ONE LEDGER</p><nav>"""+nav+"""</nav><p class="subtle">실제 농지·금융 승인을 뜻하지 않습니다.</p></aside>
<main><header id="overview"><p class="muted">여러 계산기 대신 하나의 입력 → 하나의 농장 경영 결과</p>
<h1>농장 통합 워크스페이스</h1>
<p class="warning"><strong>가정 기반 탐색</strong> — 작물별 수익·시설·판로·관수·전력·인력·정산 근거가
개별 농지에 대해 입증되지 않았습니다. 이 화면의 금액은 실제 수익/대출 승인이 아닙니다.</p>
<div class="metrics">
<div class="metric"><small>가상 유효 경작면적</small><strong>"""+val(main["total_usable_area_m2"],"㎡")+"""</strong></div>
<div class="metric"><small>합산 기말 현금(가정)</small><strong>"""+val(main["ending_cash_krw"])+"""</strong></div>
<div class="metric"><small>최대 월말 자금부족(가정)</small><strong>"""+val(main["maximum_month_end_cash_shortfall_krw"])+"""</strong></div>
<div class="metric"><small>대출 원금 잔액(가정)</small><strong>"""+val(finance["outstanding_principal_krw"])+"""</strong></div>
</div><p class="muted">현재 작물 수: """+str(len(main["per_crop"]))+""" | 물리적 현장·시장·대출 검증은 별도입니다.
입력된 판매등급·자금·시설비는 통합 장부에 단 한 번만 반영했습니다.</p></header>"""+sections+"""
<section><h2>검증 및 미확인 사항</h2><ul>"""+notices+"""</ul>
<p class="quiet">본 통합 화면은 명시적인 입력 사례를 Python 계산기에 통합 실행한 오프라인 HTML입니다.
새 작물·면적·가격 등의 계산값을 바꾸려면 공통 JSON을 수정하고 통합 명령을 다시 실행해야 합니다.
기존 탐색·현장 양식은 레거시 참고 화면이며 현재 이 원장과 자동 양방향 동기화되지는 않습니다.</p></section>
</main></div></body></html>"""


def main():
    p=argparse.ArgumentParser(description="Unified farm workspace: one input -> JSON + HTML")
    p.add_argument("--input",type=Path,required=True,help="One complete workspace JSON")
    p.add_argument("--log",type=Path,help="Optional redacted LOCAL CSV; never included in workspace input")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--html",type=Path)
    args=p.parse_args()
    config=json.loads(args.input.read_text(encoding="utf-8"))
    result=run_farm_workspace(config,field_log=args.log)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(result),encoding="utf-8")
    print("Farm KPI unified workspace: one authoritative portfolio, "
          f"{len(result['authoritative_portfolio']['per_crop'])} crop plans; "
          "results are not verified farm profit")


if __name__ == "__main__":
    main()
