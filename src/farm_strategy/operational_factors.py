"""Audit farm-realism decision factors without inventing parcel feasibility.

MODELED means the engine accepts a field / generic cash event, NOT that its
value was measured or source-calibrated. Each factor's model binding is checked
against the *actual* Python model/site-intake schemas to prevent stale claims.
"""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

from farm_strategy import lifecycle, site_intake, execution_detail

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/metadata/decision_factor_registry.json"
GROUPS = {
    "LAND_SITE", "WATER_CLIMATE", "FACILITY_ENERGY", "OPERATIONS_LABOR",
    "PRODUCTION_QUALITY", "MARKET_LOGISTICS", "FINANCE_RESILIENCE", "ADVANTAGE",
}
ROLES = {"HARD_GATE", "ECONOMIC_DRIVER", "RISK", "ADVANTAGE"}
PRIORITIES = {"P0", "P1", "P2"}
IMPLEMENTATIONS = {"MODELED", "INTAKE_ONLY", "NOT_MODELED"}
BINDINGS = {
    "lifecycle.case": lifecycle.CASE_FIELDS,
    "lifecycle.operations": lifecycle.OP_FIELDS,
    "lifecycle.sales": lifecycle.SALE_FIELDS,
    "lifecycle.facility_events": lifecycle.FACILITY_FIELDS,
    "execution.weekly_allocations": execution_detail.WORK_FIELDS,
    "execution.grade_lots": execution_detail.LOT_FIELDS,
    "site.gate": set(site_intake.GATES),
    "site.constraint": set(site_intake.NUMERIC_FIELDS) | {"owner_hours_available_by_month"},
}
FIELDS = {
    "id", "group", "label", "role", "priority", "implementation",
    "model_binding", "evidence_needed", "conditional_benefit", "caveat",
}
TOP = {"schema_version", "as_of", "scope", "caveat", "source_links", "factors"}
GROUP_FIELDS = {"ko", "official_url", "focus"}


def _required_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: required nonempty string")


def audit(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != TOP:
        raise ValueError("Unexpected factor registry structure")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported factor registry version")
    for key in ("as_of", "scope", "caveat"):
        _required_text(data[key], key)
    groups = data["source_links"]
    if not isinstance(groups, dict) or set(groups) != GROUPS:
        raise ValueError("Factor category coverage differs")
    for key, group in groups.items():
        if not isinstance(group, dict) or set(group) != GROUP_FIELDS:
            raise ValueError(f"{key}: category source fields differ")
        for sub in ("ko", "official_url", "focus"):
            _required_text(group[sub], sub)
        if not (group["official_url"].startswith("https://")
                and " " not in group["official_url"]):
            raise ValueError("Expected public https methodology reference")
    factors = data["factors"]
    if not isinstance(factors, list) or not factors:
        raise ValueError("Expected nonempty factors")
    seen = set()
    for row in factors:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("Factor fields differ")
        for key in ("id", "label", "evidence_needed", "conditional_benefit", "caveat"):
            _required_text(row[key], key)
        if row["id"] in seen:
            raise ValueError("Duplicate factor id")
        seen.add(row["id"])
        if row["group"] not in GROUPS or row["role"] not in ROLES:
            raise ValueError("Invalid factor group or role")
        if row["priority"] not in PRIORITIES or row["implementation"] not in IMPLEMENTATIONS:
            raise ValueError("Invalid factor priority or implementation")
        binding = row["model_binding"]
        if row["implementation"] == "NOT_MODELED":
            if binding is not None:
                raise ValueError("Unimplemented factor must not claim a model binding")
        else:
            _required_text(binding, "model_binding")
            namespace, separator, field = binding.rpartition(".")
            if (not separator or namespace not in BINDINGS
                    or field not in BINDINGS[namespace]):
                raise ValueError(f"Unknown field binding {binding}")
            if (row["implementation"] == "MODELED") != namespace.startswith(("lifecycle.", "execution.")):
                raise ValueError("Modeled and intake-only must use their own actual fields")
    groups_summary = {
        key: {"total":sum(x["group"] == key for x in factors),
              **{state:sum(x["group"] == key and x["implementation"] == state for x in factors)
                 for state in IMPLEMENTATIONS}}
        for key in sorted(GROUPS)
    }
    return {
        "status": "REPOSITORY_CAPABILITY_AUDIT_NOT_FIELD_VALIDATION",
        "as_of": data["as_of"],
        "factors_total": len(factors),
        "implementation_counts": {s:sum(x["implementation"] == s for x in factors)
                                  for s in sorted(IMPLEMENTATIONS)},
        "hard_gate_count": sum(x["role"] == "HARD_GATE" for x in factors),
        "p0_count": sum(x["priority"] == "P0" for x in factors),
        "advantage_count": sum(x["role"] == "ADVANTAGE" for x in factors),
        "p0_unmodeled": [x["id"] for x in factors
                        if x["priority"] == "P0" and x["implementation"] == "NOT_MODELED"],
        "groups": groups_summary,
        "factors": factors,
        "source_links": groups,
        "warning": data["caveat"],
    }


def render_html(report):
    refs = report["source_links"]
    stats = report["implementation_counts"]
    head = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm KPI | 현실 농사 변수·이점 감사</title><style>
:root{font:15px/1.55 system-ui,-apple-system,sans-serif;color:#263d32;background:#f6f7f3}
*{box-sizing:border-box}body{max-width:1400px;margin:auto;padding:28px 18px}
header{background:#254a37;color:#fff;border-radius:14px;padding:24px}
header h1{margin:3px 0;font-size:clamp(25px,4vw,38px)}
header p{max-width:1050px;color:#e1eee4}
section{background:white;border:1px solid #dce4d9;border-radius:12px;padding:20px;margin-top:17px}
.numbers{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:16px}
.metric{background:#eaf1e8;border-radius:9px;padding:13px}.metric b{font-size:26px;display:block}
.warn{border-left:5px solid #b48a4e;background:#fbf2e1;padding:13px}
table{width:100%;border-collapse:collapse;min-width:980px}th,td{border-bottom:1px solid #e2eae2;padding:9px 8px;text-align:left;vertical-align:top;font-size:12px}
th{background:#e9f0e8;position:sticky;top:0}.scroll{overflow-x:auto}
input,select{font:inherit;border:1px solid #a7bdae;border-radius:7px;padding:9px;min-height:39px}
.filters{display:flex;flex-wrap:wrap;gap:9px;margin:12px 0}
button{font:inherit;cursor:pointer;background:#315d45;color:white;border:0;border-radius:6px;padding:9px 13px}
a{color:#266441}.muted{color:#627568;font-size:12px}
</style></head><body><header><small>FARM KPI · FIELD-REALISM AUDIT</small>
<h1>실제 농사 변수·이점 점검</h1>
<p>실측·농가 정산 증거가 아니라 저장소에서 무엇을 계산하고, 무엇을 조사만 하고, 무엇을 놓치고 있는지 구분한 설계 감사입니다. 작목 수익 순위와 현장 적합성을 인증하지 않습니다.</p>
</header><div class=numbers>"""
    metrics = [("검토 요인", report["factors_total"]), ("계산 입력", stats["MODELED"]),
               ("현장 체크리스트만", stats["INTAKE_ONLY"]),
               ("계산 미지원", stats["NOT_MODELED"]),
               ("필수 확인 항목", report["hard_gate_count"]),
               ("조건부 이점", report["advantage_count"])]
    result = head + "".join(
        '<div class=metric><b>'+str(value)+'</b>'+escape(key)+'</div>'
        for key, value in metrics)
    result += """</div><section><p class=warn><b>읽는 법:</b> 계산 입력이 있다는 것은 검증됐다는 뜻이 아닙니다.
예: 시설 난방비는 임의 금액의 OPERATING 사건으로 입력 가능하지만 난방 부하·전력 수급은 계산하지 않습니다.
필지의 토양·법규·관수·노동·실구매처 검증 전에는 작목·시설 추천을 보류합니다.
장점은 추가 매출·원가 절감이 유지비·인건비·자금 압박·실패 위험을 넘는 경우에만 인정합니다.</p>
<div class=filters><input id=q placeholder="변수명·효과·제약 검색" aria-label="검색">
<select id=group><option value="">전체 분야</option>"""
    result += "".join('<option value="'+escape(k)+'">'+escape(v["ko"])+'</option>'
                      for k, v in refs.items())
    result += """</select><select id=state><option value="">모든 구현 상태</option>
<option value=MODELED>계산 입력</option><option value=INTAKE_ONLY>조사 체크리스트</option>
<option value=NOT_MODELED>계산 미지원</option></select>
<select id=priority><option value="">전체 우선순위</option><option>P0</option><option>P1</option><option>P2</option></select></div>
<div class=muted id=count></div><div class=scroll><table><thead><tr>
<th>우선</th><th>분야</th><th>변수 / 이점</th><th>역할</th><th>모델 상태</th>
<th>필요한 현장 근거</th><th>가능한 가치</th><th>주의점</th></tr></thead><tbody>"""
    for f in report["factors"]:
        result += (
            '<tr data-group="'+escape(f["group"])+'" data-state="'+escape(f["implementation"]) +
            '" data-priority="'+escape(f["priority"])+'"><td>'+escape(f["priority"])+
            '</td><td>'+escape(refs[f["group"]]["ko"])+'</td><td>'+escape(f["label"])+
            '</td><td>'+escape(f["role"])+'</td><td>'+escape(f["implementation"])+
            '</td><td>'+escape(f["evidence_needed"])+'</td><td>'+escape(f["conditional_benefit"])+
            '</td><td>'+escape(f["caveat"])+'</td></tr>')
    result += """</tbody></table></div></section><section><h2>공식 확인 경로</h2>"""
    for k, group in refs.items():
        result += '<p><a href="'+escape(group["official_url"])+'" rel="noopener noreferrer" target="_blank">'+escape(group["ko"])+'</a> — '+escape(group["focus"])+'</p>'
    result += """<p class=muted>출처 사이트는 조사방법을 제공할 뿐, 이 농장에 적용한 실측이 아닙니다. 이 문서에는 사적 위치·견적·계약·금융자료가 없습니다.</p></section>
<script>"use strict";
const q=document.getElementById("q"),g=document.getElementById("group"),
s=document.getElementById("state"),p=document.getElementById("priority");
const rows=[...document.querySelectorAll("tbody tr")],count=document.getElementById("count");
function update(){let n=0;for(const r of rows){const yes=(!g.value||r.dataset.group===g.value)
&&(!s.value||r.dataset.state===s.value)&&(!p.value||r.dataset.priority===p.value)
&&r.textContent.toLowerCase().includes(q.value.trim().toLowerCase());r.hidden=!yes;if(yes)n++;}
count.textContent=n+" / "+rows.length+"개 표시";}
for(const el of [q,g,s,p])el.addEventListener("input",update);update();
</script></body></html>"""
    return result


def main():
    parser = argparse.ArgumentParser(description="Audit farm decision factors and upside levers")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                               encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(report), encoding="utf-8")
    print(f"{report['factors_total']} factors: {report['implementation_counts']} "
          f"(hard gates {report['hard_gate_count']}, conditional advantages {report['advantage_count']}); "
          "no parcel or crop investment validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
