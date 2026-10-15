"""Build a reproducible offline RDA source-coverage page (not crop rankings)."""
import argparse
import csv
from html import escape
from pathlib import Path

from check_rda_web_sample import check

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/reported/rda_web_2022_2023_sample.csv"
OUTPUT = ROOT / "dashboard/source-coverage/index.html"


def build(csv_path=INPUT):
    checked, observed = check(csv_path)
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    cards = (
        f'<div class="stats"><div><b>{checked}</b><span>조회 대상 조합</span></div>'
        f'<div><b>{observed}</b><span>정밀 숫자 확인(웹 표)</span></div>'
        f'<div><b>{checked-observed}</b><span>상세 행 미표시</span></div></div>'
    )
    trs = []
    for r in rows:
        available = r["observation_status"] == "OBSERVED_WEB_TABLE"
        status = "웹 수치 확인 · PDF 미대조" if available else "상세 행 미표시 (0원 아님)"
        money = lambda k: f'{int(r[k]):,}' if available else '미확인'
        link = escape(r["source_url"], quote=True)
        cells = [r["observation_year"], r["display_crop_system"], r["region"],
                 money("gross_receipts_krw_per_10a"),
                 money("management_cost_krw_per_10a"),
                 money("income_krw_per_10a"), status]
        td = "".join(f"<td>{escape(c)}</td>" for c in cells)
        trs.append(f'<tr data-year="{escape(r["observation_year"])}" data-crop="{escape(r["display_crop_system"])}">'
                   f'{td}<td><a target="_blank" rel="noopener noreferrer" href="{link}">농사로 원문</a></td></tr>')
    tr_html = "\n".join(trs)
    html = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>농산물소득 보고 수치 확인 현황 — Farm KPI</title>
<style>
:root{--brown:#4b3528;--sage:#546b55;--bg:#f8f5ef;--border:#d9d0c2;--muted:#574f48}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--brown);font:16px/1.55 system-ui,-apple-system,sans-serif}
header{background:var(--brown);color:white;padding:1.5rem max(1rem,calc((100vw - 1120px)/2))}
main{max-width:1120px;margin:auto;padding:1.4rem 1rem 3rem}
a{color:var(--sage);text-decoration:underline;text-underline-offset:2px}header a{color:white}
h1{margin:.2rem 0;font-size:clamp(1.4rem,3vw,2rem)}
h2{font-size:1.18rem;margin:1.6rem 0 .5rem}
p{max-width:85ch}.notice{border-left:4px solid var(--sage);padding:.8rem 1rem;background:#e8eee7}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:1.4rem 0}
.stats>div{padding:1rem;background:white;border:1px solid var(--border);border-radius:12px;display:grid}
.stats b{font-size:2rem;line-height:1.2}.stats span{color:var(--muted);font-size:.86rem}
.controls{display:flex;gap:.8rem;flex-wrap:wrap;margin:1rem 0}
label{display:grid;gap:.25rem;font-weight:650}select{font:inherit;padding:.5rem;background:white;border:1px solid #8f9589;border-radius:6px;color:var(--brown)}
.table{overflow-x:auto;border:1px solid var(--border);border-radius:9px;background:white}
table{border-collapse:collapse;min-width:850px;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:.75rem;text-align:left;border-bottom:1px solid #eae4db;white-space:nowrap;font-size:.88rem}
th{background:#e3e8dc;position:sticky;top:0}tbody tr:hover{background:#f6f8f3}
small,footer{color:var(--muted)}footer{border-top:1px solid var(--border);padding:1rem 0;margin-top:2rem}
@media(max-width:550px){.stats{grid-template-columns:1fr}.stats>div{grid-template-columns:auto 1fr;align-items:center;gap:.8rem}}
</style></head><body>
<header><h1>농촌진흥청 보고 통계 · 다년도 확인 현황</h1>
<div>Farm KPI · 2022–2023 전국 3개 작목 표본 확인 · 작목 선정 아님</div></header>
<main><p class="notice"><strong>주의:</strong> 이 표는 기관 웹 화면에 표시된 수치를 옮긴 <strong>예비 검토 표본</strong>입니다.
PDF 쪽수·노동시간 독립 대조는 미완료이며, 실제 전북 농지의 적합성·영농 수익·투자 수익률을 나타내지 않습니다.
사과 통계는 성목 과원 결과로 새 식재 초기 현금흐름이 아닙니다.</p>
""" + cards + """
<h2>작목 · 조사연도별 공개 상세 행</h2>
<p>전국(NATIONAL) · 명목 원/10a/해당 작기. 시설·노지 구성과 조사방법 변화는 별도 확인 필요.
상세 행이 없으면 <strong>미확인</strong>으로 표시하며, 숫자 0으로 대체하지 않습니다.</p>
<div class="controls">
<label>조사연도<select id="year"><option value="">모든 연도</option><option>2022</option><option>2023</option></select></label>
<label>작목(검증용 표본)<select id="crop"><option value="">모든 작목</option><option>사과</option><option>노지쪽파</option><option>시설오이</option></select></label>
</div><div class="table"><table><thead><tr><th>연도</th><th>작목</th><th>지역</th><th>총수입(원)</th><th>경영비(원)</th><th>소득(원)</th><th>자료 상태</th><th>근거</th></tr></thead>
<tbody>
""" + tr_html + """
</tbody></table></div>
<p id="visible-count" aria-live="polite"></p>
<h2>다음 자료 수집 단계</h2>
<p>2022·2023 공식 PDF별 조사 정의·실제 페이지·노동시간 및 전북 작목별 정밀 값을 개별 확인한 뒤에만 장기형 검증 자료로 승격합니다.
2022년 시설오이는 이 조회 코드에서 상세 값이 나타나지 않았으며, 당시 다른 재배방식 코드 존재 가능성을 조사해야 합니다.</p>
<footer>출처: 농촌진흥청 농사로. 공공누리 제2유형(출처표시·상업적 이용금지) 조건은 원문별 재확인.
이 페이지는 외부 JS·API 호출 없이 동작합니다.</footer></main>
<script>
"use strict";
const year=document.getElementById("year"),crop=document.getElementById("crop");
const entries=[...document.querySelectorAll("tbody tr")];
function apply(){let n=0;for(const r of entries){let show=(!year.value||r.dataset.year===year.value)&&(!crop.value||r.dataset.crop===crop.value);r.hidden=!show;if(show)n++;}
document.getElementById("visible-count").textContent=n+"개 조회 조합 표시"; }
year.addEventListener("change",apply);crop.addEventListener("change",apply);apply();
</script></body></html>
"""
    return html


def main():
    p = argparse.ArgumentParser(description="Create/check offline historic RDA source page")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    p.add_argument("--html", type=Path, default=OUTPUT)
    args = p.parse_args()
    expected = build()
    if args.check:
        if not args.html.is_file() or args.html.read_text(encoding="utf-8") != expected:
            raise SystemExit("RDA source coverage HTML is STALE")
    else:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(expected, encoding="utf-8")
    print("Official RDA web-sample coverage HTML " + ("current" if args.check else "refreshed"))


if __name__ == "__main__":
    main()
