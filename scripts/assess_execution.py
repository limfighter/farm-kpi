"""Render auditable weekly labor bottlenecks and grade-level cash changes."""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from farm_strategy.execution_detail import assess_execution  # noqa: E402


def show(v,unit=""):
    return "UNKNOWN" if v is None else f"{v:,.1f}{unit}"


def render_html(report):
    weekly=report["weekly"]
    grading=report["grading"]
    rows=[]
    for w in weekly["weeks"]:
        vals=[w["week_start"],show(w["owner_required_hours"]," h"),
              show(w["owner_available_hours"]," h"),
              show(w["owner_shortage_hours"]," h"),
              show(w["hired_required_hours"]," h"),
              show(w["hired_available_hours"]," h"),
              show(w["hired_shortage_hours"]," h")]
        rows.append("<tr>"+"".join("<td>"+escape(x)+"</td>" for x in vals)+"</tr>")
    deltas=grading["cash_deltas_alternative_minus_baseline_krw"]
    translated={
        "net_expected_settlement_krw":"순수취 판매대금",
        "operating_cash_cost_krw":"운영 현금원가(포장비 포함)",
        "operating_contribution_before_owner_labor_tax_depreciation_krw":"운영 기여",
        "cash_after_last_settlement_krw":"마지막 입금 후 현금",
        "peak_month_end_funding_gap_krw":"최대 월말 자금 부족",
        "project_npv_krw_if_rate_supplied":"입력 할인율 기준 사업 NPV",
    }
    items="".join("<tr><td>"+escape(translated[k])+"</td><td>"+
                  escape(show(v,"원"))+"</td></tr>" for k,v in deltas.items())
    months="".join("<tr><td>"+f'{v["year"]}-{v["month"]:02d}'+"</td><td>"+
                   escape(show(v["delta_krw"],"원"))+"</td></tr>"
                   for v in grading["monthly_net_cash_deltas_krw"])
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 주간 노동 및 상품 등급</title>
<style>:root{font:15px/1.5 system-ui,-apple-system,sans-serif;color:#273d31;background:#f6f7f2}
body{margin:auto;max-width:1180px;padding:24px}header{background:#2b503d;color:white;border-radius:12px;padding:21px}
section{background:white;border:1px solid #dce4d7;border-radius:10px;padding:20px;margin-top:15px}
.alert{border-left:5px solid #b88a41;background:#fbefda;padding:13px}
.table{overflow:auto}table{border-collapse:collapse;width:100%;min-width:740px}
td,th{border-bottom:1px solid #e0e8df;padding:10px;text-align:left;white-space:nowrap;font-size:13px}
td:not(:first-child){text-align:right}th{background:#e8f1e7}
small{color:#607766}</style></head><body>
<header><small>FARM KPI · OPERATION DETAIL / SYNTHETIC</small>
<h1>수확기 주간 노동 + 등급별 실수취</h1>
<p>동일한 다년 농장 원장에 세부 작업·등급을 연결한 별도 검증</p></header>
<section><p class=alert><strong>입력값 전부 합성 가정(A)입니다.</strong>
실제 고용 가능 인원, 수확량, 등급별 정산 가격, 포장비 또는 농가 수익을 검증한 결과가 아닙니다.
UNKNOWN을 0으로 처리하지 않으며, 한 주의 노동시간 부족을 월별 평균으로 숨기지 않습니다.</p>
<h2>주간 노동 병목</h2><div class=table><table><thead><tr>
<th>주 시작일</th><th>자가 필요</th><th>자가 가용</th><th>자가 부족</th>
<th>고용 필요</th><th>고용 가용</th><th>고용 부족</th></tr></thead><tbody>"""+ "".join(rows)+"""</tbody></table></div></section>
<section><h2>등급별 출하 대체 시 차액</h2>
<p><small>등급 판매는 기존 수익을 대체합니다. 판매대금 정산은 원래 정산월에,
포장비는 출하월에 별도로 지출합니다. 차액 = 등급별 대체 − 기존 단일 등급 가정.</small></p>
<div class=table><table><tbody>"""+items+"""</tbody></table></div>
<h3>해당 월별 순현금 차액</h3><div class=table><table><thead><tr><th>월</th><th>증분 현금</th></tr></thead><tbody>"""+months+"""</tbody></table></div>
<p><small>사업 NPV는 가정된 할인율을 입력한 경우에만 표시. 포장 선지급·수확주 노동·현장 구매처/농지 조건의 실제 검증은 별도입니다.</small></p></section></body></html>"""


def main():
    p=argparse.ArgumentParser(description="Audit explicit weekly work and graded cash")
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--html",type=Path)
    a=p.parse_args()
    raw=json.loads(a.input.read_text(encoding="utf-8"))
    if not isinstance(raw,dict) or set(raw)!={"schema_version","case","detail"} or raw["schema_version"]!=1:
        raise ValueError("Expected exact execution-detail schema version 1")
    result=assess_execution(raw["case"],raw["detail"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.html:
        a.html.parent.mkdir(parents=True,exist_ok=True)
        a.html.write_text(render_html(result),encoding="utf-8")
    print("Weekly labor and grade receipt example computed; synthetic assumptions only")


if __name__=="__main__":
    main()
