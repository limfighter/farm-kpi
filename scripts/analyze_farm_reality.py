"""Compare explicit farm stress assumptions and optional LOCAL redacted farm logs."""
import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from farm_strategy.farm_records_stress import analyze_farm  # noqa: E402


def fmt(value,unit=""):
    if value is None:
        return "UNKNOWN"
    return f"{value:+,.0f}{unit}"


def render_html(result):
    z=result["stress"]
    rows=[]
    for s in z["scenarios"]:
        water=s["scarcity"]["irrigation_m3"]["stressed"]
        electric=s["scarcity"]["electricity_kwh"]["stressed"]
        rows.append("<tr>"+
            "<td>"+escape(s["id"])+"</td>"+
            "<td>"+escape(s["description"])+"</td>"+
            "<td>"+fmt(s["net_expected_settlement_delta_krw"],"원")+"</td>"+
            "<td>"+fmt(s["unlevered_npv_delta_krw_if_rate_supplied"],"원")+"</td>"+
            "<td>"+fmt(s["ending_cash_delta_krw"],"원")+"</td>"+
            "<td>"+fmt(s["peak_month_end_cash_shortfall_delta_krw"],"원")+"</td>"+
            "<td>"+str(water["months_short"])+"/"+str(water["months_supply_unknown"])+"</td>"+
            "<td>"+str(electric["months_short"])+"/"+str(electric["months_supply_unknown"])+"</td>"+
            "</tr>")
    log=result["field_log"]
    logged="""
        <p class=notice>실제 영농기록은 전달되지 않았습니다. 표의 수익 차이는 모두 모형 가정입니다.
        사용자는 민감정보를 제거한 CSV를 컴퓨터에서만 입력하고 결과를 검토할 수 있습니다.</p>"""
    if log is not None:
        detail=""
        for v in log["cases"]:
            o=v["recorded"]
            detail+=(
                "<tr><td>"+escape(v["case_id"])+"</td>"+
                "<td>"+escape(v["coverage"])+"</td>"+
                "<td>"+str(v["recorded_rows"])+"</td>"+
                "<td>"+fmt(o["owner_hours_recorded"],"h")+"</td>"+
                "<td>"+fmt(o["settled_cash_krw"],"원")+"</td>"+
                "<td>"+fmt(o["paid_expense_krw"],"원")+"</td>"+
                "<td>"+fmt(o["water_m3_recorded"],"m³")+"</td>"+
                "<td>"+fmt(o["electricity_kwh_recorded"],"kWh")+"</td></tr>")
        logged=(
          "<p class=notice>CSV 행 "+str(log["rows"])+"개를 부분 집계했습니다. "+
          "예측값과 직접 차감해 검증된 순이익으로 만들지 않습니다. "+
          "원본 파일·실거래증빙·출처ID는 이 HTML/JSON에 복제되지 않습니다.</p>"+
          "<div class=scroll><table><thead><tr>"+
          "<th>작형 시나리오</th><th>기록 상태</th><th>행 수</th><th>기록 작업시간</th>"+
          "<th>실입금 또는 A 예시</th><th>기록 지급액</th><th>물량</th><th>전력</th>"+
          "</tr></thead><tbody>"+detail+"</tbody></table></div>"
        )
    return ("""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 영농기록과 스트레스 비교</title><style>
:root{font:15px/1.6 system-ui,-apple-system,sans-serif;background:#f5f7f2;color:#254136}
*{box-sizing:border-box}body{max-width:1340px;margin:auto;padding:25px 18px}
header{background:#28513b;color:#fff;padding:24px;border-radius:14px}
h1{font-size:clamp(24px,3.2vw,36px);margin:5px 0}
section{margin-top:18px;background:#fff;padding:20px;border:1px solid #dce7d9;border-radius:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:11px}
.cards div{background:#eaf1e8;padding:14px;border-radius:10px}.cards b{display:block;font-size:23px}
.notice{padding:13px;border-left:4px solid #b18850;background:#faf2e1}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:1020px}
td,th{border-bottom:1px solid #e0e7dc;padding:10px;text-align:right;font-size:12px}
td:first-child,th:first-child,td:nth-child(2),th:nth-child(2){text-align:left}
th{background:#e9efe7}small{color:#617666}
footer{margin:25px 0;color:#5b7563}
</style></head><body>
<header><small>FARM KPI · ACTUAL RECORDS ≠ MODEL SCENARIOS</small>
<h1>영농기록 입력 · 가격·수확량·자원 스트레스</h1>
<p>실제 입금·지출·수확·작업기록은 별도 집계, 계획별 재무 위험은 가정 기반 차액으로 표시합니다.</p></header>
<section><p class=notice><strong>합성 가정(A) 자료의 예시 화면입니다.</strong>
농가 실제 판로·생산량·판매가격·기상피해·관수 및 전력 공급 확인 결과가 아닙니다.
아래 스트레스에는 확률이나 품목별 피해 예측이 포함되지 않습니다.</p>
<div class=cards><div>기준 농장 기말 현금<b>"""+fmt(z["baseline_ending_cash_krw"],"원")+"""</b></div>
<div>기준 최대 월말 자금부족<b>"""+fmt(z["baseline_peak_month_end_cash_shortfall_krw"],"원")+"""</b></div>
<div>가정 스트레스 시나리오<b>"""+str(len(z["scenarios"]))+"""개</b></div></div></section>
<section><h2>스트레스 결과 — 기준 대비 변화</h2>
<p class=notice>가격×수확량은 함께 매출에 작용합니다. **관수·전력 공급 부족은 자동으로 수확량을 깎지 않습니다.**
노동·품질·단기 전력 kW·정산기간도 시나리오에서 별도 변화시키지 않습니다.
각 항목은 사용자가 명시한 가정만 반영됩니다. 부족월/미확인월을 함께 표시합니다.</p>
<div class=scroll><table><thead><tr><th>상황</th><th>가정 설명</th><th>예상 순정산액 차이</th>
<th>무차입 NPV 차이</th><th>기말 현금 차이</th><th>필요자금 최고치 차이</th>
<th>관수 부족/미확인 월</th><th>전기 부족/미확인 월</th></tr></thead><tbody>"""+
"".join(rows)+"""</tbody></table></div></section>
<section><h2>영농기록 CSV — 별도 집계</h2>"""+logged+"""</section>
<footer>보고 상태: """+escape(z["status"])+""". 수치 단위와 미확인 값은 본래 입력 기준입니다.
토양/수질/법적 허가/판로/금융 심사·정밀 기상확률은 별도 확인해야 합니다.</footer></body></html>""")


def main():
    parser=argparse.ArgumentParser(description="Redacted farm log and explicitly declared scenario stresses")
    parser.add_argument("--portfolio",type=Path,required=True)
    parser.add_argument("--stress",type=Path,required=True)
    parser.add_argument("--log",type=Path,help="Optional local CSV; keep private")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args()
    portfolio=json.loads(args.portfolio.read_text(encoding="utf-8"))
    scenario=json.loads(args.stress.read_text(encoding="utf-8"))
    result=analyze_farm(portfolio,scenario,args.log)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(result),encoding="utf-8")
    print(f"Stress assumptions: {len(result['stress']['scenarios'])}; local log rows: "+
          ("not supplied" if result["field_log"] is None else str(result["field_log"]["rows"])))


if __name__=="__main__":
    main()
