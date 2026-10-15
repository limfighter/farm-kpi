"""Offline physical execution: day-level planting, peak water/power and credit."""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from farm_strategy.physical_operations import assess_daily_farm  # noqa: E402


def show(v,unit=""):
    return "UNKNOWN" if v is None else f"{v:,.2f}{unit}"


def render_html(r):
    d=r["daily_capacity"]
    table="".join(
        "<tr><td>"+v["date"]+"</td><td>"+show(v["water_m3"],"m³")+
        "</td><td>"+show(v["pump_hours_needed"],"h")+
        "</td><td>"+show(v["pump_hours_shortage"],"h")+
        "</td><td>"+show(v["electricity_kwh"],"kWh")+
        "</td><td>"+show(v["sum_simultaneous_peak_kw"],"kW")+
        "</td><td>"+show(v["peak_kw_shortage"],"kW")+"</td></tr>" for v in d)
    tr="".join(
        "<tr><td>"+escape(t["plot_id"])+"</td><td>"+escape(t["previous"])+
        "</td><td>"+escape(t["next"])+"</td><td>"+str(t["free_days_between"])+
        "</td><td>"+str(t["minimum_required_days"])+"</td></tr>" for t in r["date_turnarounds"])
    loan=r["loan_schedule"]
    finance="" if loan is None else "".join(
        "<tr><td>"+str(v["year"])+"-"+str(v["month"]).zfill(2)+
        "</td><td>"+escape(v["kind"])+"</td><td>"+
        show(v["amount_krw"],"원")+"</td></tr>"
        for v in loan["events"])
    summary="" if loan is None else (
        "미상환 원금 "+show(r["financing_summary"]["outstanding_principal_krw"],"원")+
        ", 만기 기간 초과 여부 "+str(loan["maturity_extends_beyond_horizon"]))
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 일별 농장 운영·시설 한계</title>
<style>:root{font:15px/1.5 system-ui,-apple-system,sans-serif;color:#294333;background:#f7f8f4}
body{margin:auto;max-width:1260px;padding:25px}
header{background:#254a36;color:white;border-radius:12px;padding:24px}
h1{font-size:clamp(23px,4vw,36px)}section{background:white;padding:18px;border:1px solid #dce5d8;border-radius:12px;margin-top:17px}
.warn{background:#fff2dd;border-left:4px solid #ae7d43;padding:13px}
.wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:710px}
th,td{padding:8px;border-bottom:1px solid #e4eae0;font-size:12px;text-align:right}
th:first-child,td:first-child{text-align:left}th{background:#edf3e8}
small{color:#66796c}</style></head><body>
<header><small>FARM KPI · DAILY EXECUTION / ILLUSTRATIVE</small>
<h1>생육단계·날짜별 관수 / 펌프 / 전력 / 대출</h1></header>
<section><p class=warn><b>모든 수치는 합성 가정입니다.</b> 실제 관정 유량·수질·전기 인입·작물의 생육단계별 필요수분·신용심사·대출약정 증빙이 없습니다.
실질 연이율을 기준으로 단순 월 단위 상환액을 생성한 실험이며 은행 대출상품·금융 승인을 표현하지 않습니다.</p>
<p>작물 수: """+str(r["crop_count"])+""", 명시된 생육단계 구간: """+str(r["growth_stage_count"])+"""</p>
<p>일별 펌프 공급 한계 초과: """+str(len(r["days_exceeding_pump_window"]))+"""일;
일별 순간전력 한계 초과: """+str(len(r["days_exceeding_peak_kw"]))+"""일;
용량 미확인 시 UNKNOWN</p></section>
<section><h2>작기 전환 날짜</h2><div class=wrap><table><thead><tr><th>구획</th><th>선행 작형</th>
<th>후행 작형</th><th>간격(일)</th><th>필요 간격(일)</th></tr></thead><tbody>"""+tr+"""</tbody></table></div></section>
<section><h2>일별 수요·공급 제약</h2><div class=wrap><table><thead><tr>
<th>날짜</th><th>관수량</th><th>펌프 소요시간</th><th>펌프 시간부족</th>
<th>전기 사용량</th><th>동시 피크 부하</th><th>피크 kW 부족</th></tr></thead>
<tbody>"""+table+"""</tbody></table></div></section>
<section><h2>금융 현금 원장 (사업 현금흐름과 별도)</h2><p>"""+summary+"""</p>
<div class=wrap><table><thead><tr><th>연월</th><th>사건</th><th>금액</th></tr></thead>
<tbody>"""+finance+"""</tbody></table></div>
<p>무차입 사업 NPV: """+show(r["unlevered_npv_krw_if_discount_set"],"원")+""";
대출 포함 기말 현금: """+show(r["financed_ending_cash_krw"],"원")+"""</p>
<small>원리금은 가정된 실질 이율로 계산됩니다. 명목 대출금리·인플레이션·세금, 변동금리는 자동 처리하지 않습니다.
일별 동시 최대 부하는 보수적으로 동시에 발생한다고 가정. 같은 달 내 작기 전환은 기존 월 단위 충돌 규칙이 선행하여 아직 허용하지 않습니다.</small></section></body></html>"""


def main():
    p=argparse.ArgumentParser(description="Daily farm physical & finance scenario")
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--html",type=Path)
    args=p.parse_args()
    inp=json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(inp,dict) or set(inp)!={"schema_version","portfolio","detail"} or inp["schema_version"]!=1:
        raise ValueError("Expected complete daily physical overlay version 1")
    r=assess_daily_farm(inp["portfolio"],inp["detail"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(r),encoding="utf-8")
    print(f"{r['crop_count']} crops / {len(r['daily_capacity'])} explicit calendar days audited; hypothetical only")


if __name__=="__main__":
    main()
