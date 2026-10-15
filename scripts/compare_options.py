"""Two-way same-crop option comparison HTML; synthetic data are not returns."""
import argparse
from html import escape
import json
from pathlib import Path

from farm_strategy.option_tradeoffs import compare_operating_options


def render_html(report):
    rows = report["deltas_alternative_minus_baseline_krw"]
    label = {
        "net_expected_settlement": "실수취 예상액 증분",
        "operating_cash_cost": "운영 현금비용 증분",
        "operating_contribution_before_owner_labor_tax_depreciation": "운영 기여액 증분¹",
        "capital_expenditure": "초기/추가 시설투자 증분",
        "end_of_horizon_cash_balance": "기말 현금 잔액 차이",
        "peak_month_end_funding_gap": "최대 월말 자금 부족액 차이",
        "project_npv_if_rate_supplied": "할인율 입력시 사업 NPV 차이²",
        "economic_npv_if_rate_and_owner_value_supplied": "자가노동 가치 입력시 경제 NPV 차이²",
    }
    data="".join("<tr><td>"+escape(label[k])+"</td><td>"+
                 ("UNKNOWN" if v is None else f"{v:+,.0f}원")+"</td></tr>"
                 for k,v in rows.items())
    h=report["deltas_alternative_minus_baseline_hours"]
    hours="".join("<tr><td>"+escape(k)+"</td><td>"+
                  ("UNKNOWN" if v is None else f"{v:+,.1f}시간")+"</td></tr>"
                  for k,v in h.items())
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 시설 대안 증분 경제성</title>
<style>:root{font:16px/1.5 system-ui,-apple-system,sans-serif;color:#293e32;background:#f5f7f2}
body{max-width:960px;margin:auto;padding:25px}header{background:#254a37;color:white;border-radius:12px;padding:23px}
.card{background:white;border:1px solid #d8e1d8;border-radius:12px;padding:20px;margin-top:17px}
.warning{background:#fff0d6;border-left:4px solid #b6894b;padding:12px}
table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #dae2d9;text-align:left}
td:last-child{font-variant-numeric:tabular-nums;text-align:right}small{color:#657a6a}
</style></head><body><header><small>FARM KPI / INCREMENTAL CHOICE</small>
<h1>같은 작물·면적의 시설 대안 비교</h1><p>기준: """+escape(report["baseline"]["system"])+"""<br>대안: """+escape(report["alternative"]["system"])+"""</p></header>
<div class=card><p class=warning><b>모두 입력 가정 기반 모형 차이입니다.</b>
실제 수익/시설 ROI 보장 아님. 양(+)의 기여액 차이만으로 추천하지 않으며
자금 부족액 차이(+)는 오히려 더 큰 위험입니다.</p>
<h2>대안 − 기준 (증분)</h2><table>"""+data+"""</table>
<h2>노동 투입 및 초과</h2><table>"""+hours+"""</table>
<p><small>¹ 자가 노동의 기회비용, 세금, 감가상각 제외.
² 할인율/자가노동 시간이 명시되고 비용과 수입이 동일한 불변 원화 기준일 때만 계산됩니다.
다른 작물·면적·기간·자금가정은 비교를 거부합니다.</small></p></div></body></html>"""


def main():
    parser=argparse.ArgumentParser(description="One crop, two explicit operating options")
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--html",type=Path)
    args=parser.parse_args()
    payload=json.loads(args.input.read_text(encoding="utf-8"))
    if (set(payload)!={"schema_version","disclaimer","cases"}
            or payload["schema_version"]!=2
            or not isinstance(payload["disclaimer"],str)
            or not payload["disclaimer"].strip()
            or not isinstance(payload["cases"],list) or len(payload["cases"])!=2):
        raise ValueError("Expected exactly two complete version-2 cases")
    report=compare_operating_options(*payload["cases"])
    report["disclaimer"]=payload["disclaimer"]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(render_html(report),encoding="utf-8")
    print("Compared paired options as synthetic differences; not a crop recommendation")


if __name__=="__main__":
    main()
