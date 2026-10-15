undefined
## 농작업 기반 작목×시설 월별 시뮬레이터 (가정형 1차)

- 코드: `src/farm_strategy/workflow.py` / 실행: `scripts/compare_workflows.py`.
- 입력 양식: [가상 3대안](../../data/templates/workflow_scenarios_SYNTHETIC.json). **작업월·수확량·판매가·자재비·노동비·시설비는 모두 검증되지 않은 A**이며 실제 작물 추천이나 전주 농가 실적이 아닙니다.
- `cases[]`: `id`, `crop`, `facility`, `region`, `basis_year`(단일 명목 원화 기준연도), `area_m2`(모형상의 실제 운영 면적), `owner_available_hours_by_month`(12값 또는 `null`), `operations[]`, `harvests[]`, `facility_events[]`.
- 작업별 `operations[]`: 작업명·월·자가/고용 노동 `h/10a`, 고용 단가 `KRW/h`, 자재비·외주비 `KRW/10a`, 출처 분류/참조. 자가노동의 경제적 기회비용은 현재 결과에 **미포함**.
- 판매별 `harvests[]`: 수확월, 생산량 `kg/10a`, 상품화 비율, 가격 `KRW/kg`, 위탁수수료율·공제액 `KRW/kg`, 운송비 `KRW/10a`, 정산 지연(0~6개월), 출처. 출하 시 운송비 지출, 순정산액은 **입금월**에 기록. 연말 미수금은 매출 0이 아님.
- `facility_events[]`: `OPERATING`(운영 지출), `CAPEX`(투자), `DEPOSIT_PAID`, `DEPOSIT_RETURN` 별도 기록. 반환액은 이미 지급한 보증금 이하여야 하고, 보증금·CAPEX는 운영 기여액 비용으로 중복 반영하지 않음.
- 출력: `operating_contribution_before_owner_labor_tax_depreciation_krw`(**회계상 순이익 아님**), `december_cash_balance_krw`, `unsettled_receivables_after_december_krw`, `peak_month_end_funding_gap_krw`, 자가/고용 노동, 출처 사건 계수와 월별 원장. 잔액은 **초기 현금 0·차입 0이라는 계산 기준**으로 본 월말 누적치이며 실금융 필요액을 확정하지 않음.
- 제한: 연도별 물가·장기 시설 잔존가/감가상각/세금·보험/대출/연작·작부체계 중첩/재배 리스크/하루 안의 현금 격차/필지 적합성은 **미구현**. 서로 다른 명목 기준연도 사례는 비교 거부. 이 1년형 사례를 시설 투자 회수기간이나 ROI로 변환 금지.
- 모든 운영/판매/시설 사건은 `source_kind`(`R/O/T/Q/A`)와 `source_ref`(개인정보 없는 참조ID)를 가짐. 분류 표시는 원문 검증을 대체하지 않으며 실제 소득 근거 심사는 별도 수행.

```bash
python -m pytest -q tests/test_workflow.py tests/test_workflow_cli.py
python scripts/compare_workflows.py --input data/templates/workflow_scenarios_SYNTHETIC.json --output output/workflow-example.json --html output/workflow-example.html
```
