"""Offline multi-crop land, resource and debt cash preview (never site approval)."""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from farm_strategy.portfolio import simulate_portfolio  # noqa: E402


def number(v,unit=""):
    return "UNKNOWN" if v is None else f"{v:,.0f}{unit}"


def render_html(r):
    crop_rows="".join(
        "<tr><td>"+escape(x["crop"])+"</td><td>"+escape(x["plot_id"])+"</td><td>"+
        number(x["area_m2"],"㎡")+"</td><td>"+str(x["occupied_months"])+"</td><td>"+
        number(x["net_expected_settlement_krw"],"원")+"</td></tr>"
        for x in r["per_crop"])
    months="".join(
        "<tr><td>"+str(x["year"])+"-"+str(x["month"]).zfill(2)+"</td><td>"+
        number(x["water_m3"],"m³")+"</td><td>"+number(x["electricity_kwh"],"kWh")+
        "</td><td>"+number(x["owner_hours"],"h")+"</td><td>"+
        number(x["unlevered_cash_krw"],"원")+"</td><td>"+
        number(x["financed_cash_krw"],"원")+"</td><td>"+
        number(x["balance_after_financing_krw"],"원")+"</td></tr>"
        for x in r["monthly"][:r["horizon_years"]*12])
    def constraint(label,data):
        peaks=[x for x in data if x["shortage"] is not None and x["shortage"]>0]
        unknown=sum(x["shortage"] is None for x in data)
        return ("<tr><td>"+escape(label)+"</td><td>"+str(len(peaks))+
                "</td><td>"+str(unknown)+"</td><td>"+
                number(max((x["shortage"] for x in peaks),default=0))+"</td></tr>")
    constrained="".join(constraint(k,v) for k,v in r["resource_and_labor_limits"].items())
    weekly=r["weekly_labor"]
    week_rows="" if weekly is None else "".join(
        "<tr><td>"+x["week_start"]+"</td><td>"+
        number(x["owner_required_hours"],"h")+"</td><td>"+
        number(x["owner_shortage"],"h")+"</td><td>"+
        number(x["hired_shortage"],"h")+"</td></tr>" for x in weekly)
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI — 복수 작물·자원·대출 현금흐름</title>
<style>:root{font:15px/1.5 system-ui,-apple-system,sans-serif;color:#273f32;background:#f6f8f4}
*{box-sizing:border-box}body{max-width:1280px;margin:auto;padding:24px}
header{padding:24px;background:#244935;color:#fff;border-radius:14px}
h1{font-size:clamp(22px,3vw,35px);margin:4px 0}
section{background:white;padding:18px;margin:17px 0;border:1px solid #dae4d9;border-radius:12px}
.note{border-left:5px solid #af8043;background:#fff2dd;padding:12px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.metric{padding:12px;background:#eaf1e6;border-radius:9px}.metric strong{font-size:23px;display:block}
.scroller{overflow:auto}table{border-collapse:collapse;width:100%;min-width:690px}
th,td{padding:10px;border-bottom:1px solid #e1e8e0;white-space:nowrap;font-size:13px;text-align:right}
th{background:#ebf1e7}th:first-child,td:first-child{text-align:left}
small{color:#647c6e}</style></head><body>
<header><small>FARM KPI · FARM-LEVEL REALISM / MODEL INPUTS</small>
<h1>복수 작물 · 공유 농지 · 월별 자원·현금</h1><p>각 작물의 작기와 면적·가용 인력을 함께 계산하고, 시설비·대출을 단 한 번 반영</p></header>
<section><p class=note><b>합성(A) 가정 자료입니다.</b>
실제 농지 관수·전력 인입·대출 심사·판로가 검증된 농가 영업자료가 아닙니다.
월별 kWh는 순간 전력 kW나 전기인입 용량이 아닙니다.
주간 노동 공급을 미입력한 경우는 부족 0이 아니라 UNKNOWN입니다.</p>
<div class=metrics>
<div class=metric>총 유효 경작 면적<strong>"""+number(r["total_usable_area_m2"],"㎡")+"""</strong></div>
<div class=metric>구획 미배분 면적<strong>"""+number(r["unallocated_area_m2"],"㎡")+"""</strong></div>
<div class=metric>최대 월말 부족자금<strong>"""+number(r["maximum_month_end_cash_shortfall_krw"],"원")+"""</strong></div>
<div class=metric>대출 원금 잔액<strong>"""+number(r["financing"]["outstanding_principal_krw"],"원")+"""</strong></div>
</div></section>
<section><h2>작목별 작기·구획</h2><div class=scroller><table><thead>
<tr><th>작물(합성)</th><th>구획</th><th>경작면적</th><th>점유 월수</th><th>예상 순정산액</th></tr>
</thead><tbody>"""+crop_rows+"""</tbody></table></div></section>
<section><h2>공동 자원 사용량과 미충족 월</h2><div class=scroller><table>
<thead><tr><th>자원</th><th>부족 발생 월</th><th>공급 미확인 월</th><th>최대 부족량</th></tr></thead>
<tbody>"""+constrained+"""</tbody></table></div>
<h3>주간 노동 부족</h3><p><small>"""+escape(r["weekly_labor_status"])+"""</small></p><div class=scroller>
<table><thead><tr><th>월요일 주 시작</th><th>자가 필요</th><th>자가 부족</th><th>고용 부족</th>
</tr></thead><tbody>"""+week_rows+"""</tbody></table></div></section>
<section><h2>월별 통합 현금</h2><p><small>Unlevered=영농사업 현금, Financed=대출 인출·이자·원금상환 포함. 대출 여부와 원리금 스케줄은 명시된 합성 입력만 반영. 이는 사업 영업이익 또는 은행 승인 결과가 아닙니다.</small></p>
<div class=scroller><table><thead><tr>
<th>월</th><th>관수 사용</th><th>전력 사용</th><th>자가 노동</th>
<th>사업 현금</th><th>대출 포함 현금</th><th>누적 잔액</th></tr></thead>
<tbody>"""+months+"""</tbody></table></div></section>
</body></html>"""


def main():
    p=argparse.ArgumentParser(description="Model explicit farm portfolio resources and financing")
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--html",type=Path)
    a=p.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8"))
    result=simulate_portfolio(data)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.html:
        a.html.parent.mkdir(parents=True,exist_ok=True)
        a.html.write_text(render_html(result),encoding="utf-8")
    print(f"{len(result['per_crop'])} synthetic crops modeled with explicit plot/resource/financing assumptions")


if __name__=="__main__":
    main()
