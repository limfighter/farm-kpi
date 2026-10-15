# 데이터 계약·출처 분류·단위 참고표

**대상:** 파이프라인, 문서, 대시보드, CI 구현자. **현재 입력 구조 설명**이지 미확인 자료를 사실로 만드는 규칙이 아닙니다.

## 데이터 계층

| 파일/객체 | 출처·시점 | 단위/기간 | 의미·금지사항 |
| --- | --- | --- | --- |
| [2024년 51개 작목](../../data/reported/rda_2024_all_51_crop_candidates.csv) | RDA 2024 보고 통계 **R**, PDF 요약 17–19/노동 127–177쪽 | 명목 원/10a/작기, 노동 h/10a | 전국 단면, 실제 전주 필지 실적/ROI 아님 |
| [다년도 전국·지역 출처](../../data/metadata/rda_income_source_registry.json) 및 [장기형 현재 관측](../../data/reported/rda_income_long.csv) | 2022~2024 공식 출처 공표 존재 확인, 정확한 값은 2024 전국 51행만 전사 | 2024 명목 원/10a/작기, region=NATIONAL | 2022/2023 및 2024 전북 숫자 없음/미확인. 게시물 존재는 개별 전북 품목 값 존재 증명이 아님. [검증 기준](RDA_MULTYEAR_SOURCE_REGISTRY.md) |
| [조사 밖 후보 등록부](../../data/metadata/off_survey_candidate_registry.json) | 2024년 RDA 51개 조사 작목 외 잠재 후보의 발견 메타데이터; 기본 **0개** | 작목명·재배체계·출처 URL, 수치 없음 | `source_available=false`, `status=PENDING_EVIDENCE`만 허용. 조사 통계 R·현장 적합성·소득 검증이 아니며 51개 잠금 데이터와 병합 금지 |
| [2022~2023 웹 원문 정밀 수치 표본](../../data/reported/rda_web_2022_2023_sample.csv) | 공식 농사로 공개 작목별 HTML 표시값 **R**; [검증 절차](RDA_WEB_EVIDENCE_SAMPLE.md) | 명목 원/10a/해당 작기, 5행 표시·1개 조회 코드 공백 | PDF/노동시간 독립 대조 미완료; 2022 시설오이 화면 공백은 0원 아님. 기존 2024 잠금 통계 또는 실제 농지 수익과 미혼합 |
| [원본 대조 메타데이터](../../data/metadata/rda_2024_source_verification.json) | 사용자가 준 2024년 PDF의 SHA256 + 51개 행 해시 | 해시/정수 | 전사 정합성만 확인. 통계 작성기관 서명·정확도 인증 아님 |
| [작목 준비도](../../data/derived/crop_readiness_51.csv) | 위 보고 통계에서 분류 기반 파생 | 8개 필지 조건 상태 값 | 현장 실제 자료 없음, 모든 게이트 UNKNOWN |
| [비공개 농지 입력 양식](../../data/templates/private_site_intake_TEMPLATE.json) | 사용자 현장정보용 **빈 양식** | 대략 평, 만원, h/월, null | 12개 게이트, 작물과 시설 미정. 정확한 주소·좌표 비허용 |
| [ASOS 파생 연간 자료](../../data/processed/annual_asos_jeonju_2006_2025.csv) | KMA ASOS 전주 관측 파생 **O**, 2006–2025 | 연/기상 특성 | 필지/작목별 생산손실 확률 아님 |
| [가정 재무 설정](../../configs/base.json) | **A**, 2027–2036 모델 가정 | 대체로 2026 불변 만원 | 실제 영수증·공사계약·대출 승인 수치 아님 |
| [가정 기반 5전략 비교](../../dashboard/data/screening-model-only.csv) | 합성 경로 seed 42, paths 300 | 2026 불변 만원, 일부 명목부채 | 6시나리오 × 5예시 계획, 51개 작물 투자 순위 아님 |

## 증거 상태 표

| 값 | 뜻 | 자동 확정 가능? |
| --- | --- | --- |
| O | 원본 자료에 근거한 관측 | 해당 관측 범위 한정 |
| R | 기관/제3자가 보고한 통계 | 필지 사실이 되지 않음 |
| T | 실제 정산 거래 | 원본·작목·기간·면적 검토 필요 |
| Q | 서면 견적 | 거래·계약·현금 지급이 아님 |
| A | 시뮬레이션 가정 | 관측 확률이나 확정 가격 아님 |
| UNKNOWN/null | 자료를 확인하지 못함 | 숫자 0·부적합과 다름 |

## 51개 작목 CSV 필수 의미

| 필드 | 뜻 |
| --- | --- |
| \`crop_id\`, \`crop\`, \`category\` | 행 식별자, 공표 작목·재배방식 명칭, 7개 부류 |
| \`revenue_krw_per_10a\` | 해당 작기의 명목 총수입 |
| \`management_cost_krw_per_10a\` | 해당 작기의 명목 경영비, 고용노동·시설 감가상각 등 포함 가능 |
| \`income_krw_per_10a\`, \`income_rate_pct\` | 수입-경영비 소득 및 수입 대비 비율 |
| \`yield_quantity\`, \`yield_unit\` | 단위·작기와 결합해야 의미 있는 생산량 |
| \`cycle_years\` | 작기 연수. **인삼(4년근)=4**, 나머지 자료 작기는 원본 요약 관행과 일치 |
| \`labor_owner_hours_per_10a\`, \`labor_hired_hours_per_10a\`, \`labor_total_hours_per_10a\` | 자가, 고용, 합계 시간. 현장 월별 노동이 아님 |
| \`source_pdf_page\`, \`labor_source_pdf_page\`, \`data_kind\` | PDF 페이지(0이 아닌 실제 책 쪽)와 \`R\` 출처 구분 |

원본 소득 2024와 시뮬레이션을 합산하려면 **조사 작기, 10a↔실제 경작지, 2024 명목↔2026 실질, 비용의 감가상각↔현금 투자**를 별도 조정해야 합니다. 현재 자동 조정하지 않습니다.

## 비공개 입력 계약

- \`site_gates\`: 공통 **12개**. \`UNKNOWN\`, \`FOLLOWUP_NEEDED\`, \`DOCUMENT_COLLECTED_UNVERIFIED\`, \`USER_REPORTED_CONSTRAINT\`만 입력 가능. **VERIFIED_FEASIBLE 자동 금지.**
- \`operating_constraints\`: \`usable_area_pyeong\` 등 4개 nullable 수치와 \`owner_hours_available_by_month\` 12개 nullable 값.
- \`decisions\`: \`crop_selection=UNDECIDED\`, \`facility_choice=UNDECIDED\`.
- \`source_kind\` 수집 시 원본 문서 유형 \`O/R/Q/T\`와 **비식별 로컬 참조ID** 사용.
- 실측 값을 입력했더라도 해당 값은 기록/형식 검증만 되며 **외부 자료의 진위·필지 적합성을 승인하지 않습니다.**

## 사용법과 검증

2024 전국 51작목의 파싱·검증 규칙은 `farm_strategy.reported`에서 공유합니다. 탐색기·준비도·장기형 이력 검사에 같은 수치·노동·PDF 페이지·작기 조건을 적용하며, 준비도 출력의 기존 필드 표현은 유지합니다. 2022~2023 웹 표본은 별도 검증기로 수입·경영비·소득·수량·가격 다섯 캡처 수치를 비교합니다. 이 검사는 기존 기록의 변경을 탐지하며 원문 진위나 PDF/노동시간 검증을 대신하지 않습니다.

- [데이터 갱신 절차](../how-to/UPDATE_REPORTED_DATA.md)
- [개발 환경 시작](../how-to/GET_STARTED.md)
- [RDA/현장정보 자세한 기준](../RDA_AUDIT_AND_SITE_INTAKE.md)
- [근본적인 회계 경계](../explanation/MODEL_BOUNDARIES.md)

## 조사 밖 후보 등록부 계약 (세션 01)

`data/metadata/off_survey_candidate_registry.json`은 RDA 2024 전국 51개 작목·장기형 자료와 **분리된 후보 발견 메타데이터**입니다. `schema_version=1`, `purpose`, `candidates` 배열을 사용합니다. 후보는 `id`(`OFF-0001` 형식), `crop_name`, `cultivation_system`, `discovery_source_url`(공개 HTTPS), `discovery_source_title`, `discovery_source_year`(출처 게시연도 또는 `null`), `source_available=false`, `status=PENDING_EVIDENCE`, `missing_evidence`를 반드시 가집니다. 게시연도는 **작물 소득 조사연도와 다릅니다**.

`missing_evidence`에는 반드시 `COMPARABLE_INCOME`이 포함되며, 필요하면 `CROP_CYCLE_AND_UNITS`, `REGIONAL_COMPARABILITY`, `SITE_FEASIBILITY`, `BUYER_TERMS`, `FACILITY_QUOTES`, `MONTHLY_LABOR`를 추가합니다. 현 스키마는 수익·수량·필지 적합성·검증 완료 값을 허용하지 않습니다. 실제 비교 가능한 수치가 확보되더라도 **독립적인 출처/원문/단위/지역/작기/노동 검토와 스키마 변경** 없이 이 등록부를 재무 순위에 투입하지 않습니다. 허가/판로/실측 자료가 없다는 뜻은 `UNKNOWN`이지 부적합이나 0이 아닙니다.

```bash
python scripts/check_off_survey_candidates.py --check
python -m pytest -q tests/test_off_survey_candidates.py
```

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

### 51작목 전체·조사 밖 후보 탐색과 워크플로우 입력

- [범용 오프라인 작물×시설 입력 화면](../../dashboard/universe/index.html)은 [원본 51작목 보고 통계](../../data/reported/rda_2024_all_51_crop_candidates.csv)로 생성합니다. `python scripts/build_crop_universe.py --check`로 목록·단위·PDF 페이지의 잠금 및 화면 일치를 검사합니다.
- 최초 목록에 **51개 RDA 조사 작형을 전부 포함**하며, [별도 등록부](../../data/metadata/off_survey_candidate_registry.json)에 공개 정보로 등재된 조사 밖 작목은 UNKNOWN으로 함께 표시합니다. HTML에서 직접 추가한 후보는 브라우저 내에서만 만들며 원본 CSV/통계에 혼합하지 않습니다.
- RDA 2024 전국 `income`, 노동 h/10a/작기, `yield_unit`, 소득·노동 PDF 쪽수는 **참고 정보(R)**입니다. 이를 아래 재무 사례의 노동·판매·운영비에 **자동 복사하지 않습니다**.
- UI에서는 작업별 `operations[]`, 출하 `harvests[]`, 시설/보증금 `facility_events[]`의 숫자를 필수로 입력해야 계산합니다. 빈 값은 0으로 채우지 않으며 입력 사례는 로컬 JSON으로 내보내 `scripts/compare_workflows.py`에 전달할 수 있습니다. JSON 파일에 주소·계좌·거래처 실명을 넣어 Git에 커밋하지 않습니다.
- `harvests[]`는 기존 kg 전용 형식도 유지하고, 신규 범용 형식의 `yield_quantity_per_10a`, `yield_unit`, `price_krw_per_unit`, `buyer_deduction_krw_per_unit`을 추가 지원합니다. **수확수량의 단위와 판매/공제 단위는 반드시 동일**해야 하며 자동 kg 환산은 하지 않습니다. 단위 입력은 시뮬레이터가 단위의 진실성을 인증하는 것은 아닙니다.
- **다년 작기/작기 미확인** 후보는 1년 입력 화면에서 현금흐름 계산을 막고, **과수 신규 식재**는 성목 보고 수익을 신설 첫해 매출로 취급하지 않도록 기본 차단합니다. 기존 성목 포장이라는 사용자의 별도 확인 없이는 과수 단년 계산을 허용하지 않습니다. 다년 작기·신규 과수의 생육/비생산 연도와 시설 수명/감가상각을 추적할 범용 다년 모델은 아직 **미구현**입니다.
- 이 탐색/계산 화면은 현재 브라우저 안에서만 처리하며 서버 전송이 없습니다. RDA 출처의 공식 2024 전국값은 전주 필지 성과나 작목 선정 추천 결과가 아닙니다.

## 작목별 농작업 일정의 출처 근거 (비수치 참조)

- [작업일정 출처 레지스트리](../../data/metadata/crop_work_calendar_sources.json)는 위 2024년 RDA 51개 품목 식별자와 10개 농사로 작목별 작업일정 원문을 **별도로 연결**합니다. 41개 조사 작목은 여전히 일정 미검토입니다. 등록이 없는 것은 작목 부재나 부적합이 아니라 자료 미검토 상태입니다.
- `official_title` / `source_url` / `variant` / `match_level` / `region_scope` / `reviewed_on` / `season_notes` / `stages[]`는 **원문 재배력/작형 설명을 간략화한 참조**입니다. 원문 발행연도 확인 전에는 `source_year=null`로 둡니다. 화면은 2024년 소득 조사시점과 재배력 게시연도를 동일하다고 표시하지 않습니다.
- `stages[].window_months`는 원문에 달이 명시된 경우에만 목록으로 기록합니다. 미기재 월은 `[]`로 남깁니다. `crosses_calendar_year=true`면 다음 연도까지 걸친 작기(시설딸기 11~5월 등)로, 현 단년 HTML에 한 작기 수확량을 자동 생성하지 않습니다. 비교적 긴 기간은 월별 작업량 분배 자료가 **아닙니다**.
- `match_level`: `CROP_SYSTEM_REFERENCE`(작목/노지·시설 분류 참조), `VARIANT_REFERENCE`(작형 변형 중 하나), `CROP_FAMILY_ONLY`(작물 일치하지만 작형/토양·수경 등을 별도 확인해야 함). 이 세 값 모두 실제 농가 작형·지역·필지 적합성 인증은 아닙니다.
- 원문에는 **KOGL 공공누리 2유형(출처표시 + 상업적 이용금지)** 조건을 표시한 페이지가 있습니다. 프로젝트는 짧은 단계명/월 범위와 URL·검토 메타데이터만 관리하고, 원문 PDF/표/그림을 재배포하지 않습니다. 향후 상품화 전에 개별 원문의 라이선스와 사용허가를 검토합니다.
- 사용자가 원문 단계 이름으로 새 입력 행을 생성해도 **자가·고용 노동, 자재·외주비, 생산량, 가격, 시설비는 자동 입력되지 않고 UNKNOWN**입니다. 새 행의 `source_kind=A`는 사용자가 나중에 입력할 재무값의 출처 분류이며, 농사로 단계 자체의 출처는 `source_ref`로 연결합니다.
- 수동 또는 승인 받은 API 방식의 향후 일정 갱신 후보: [농촌진흥청 농작업일정 정보 공공데이터](https://www.data.go.kr/data/15033498/openapi.do)와 [농사로 공개 API 목록](https://www.nongsaro.go.kr/portal/ps/psn/psnj/openApiLst.ps?menuId=PS65428). 인증·개별 이용조건·작형 매핑 전에는 자동 수집하거나 라이선스 미확인 원문을 저장하지 않습니다.

실행 검사: `python -m pytest -q tests/test_work_calendar.py tests/test_crop_universe.py` / `python scripts/build_crop_universe.py --check`.

## 다년 농작업·시설·작기 현금흐름 계약 (합성 모형)

- `src/farm_strategy/lifecycle.py`, `scripts/compare_multiyear.py`, [전체 가상 예시](../../data/templates/multiyear_scenarios_SYNTHETIC.json)는 기존 단년 `workflow.py`와 **독립**인 명시 이벤트 기반 계산입니다. 버전 2 최상위 키는 `schema_version=2`, `disclaimer`, `cases`이며 1~10년만 지원합니다.
- 각 사례는 `id`, `crop`, `system`, `region`, `start_year`, `horizon_years`, `area_m2`, `annual_real_discount_rate` (실질 연 할인율, `null` 가능), `owner_hour_value_krw` (`null` 가능), `owner_available_hours_by_month` (전체 모델 월 수 길이 또는 `null`), `no_sales_reason`, `operations`, `sales`, `facility_events`를 반드시 제공해야 합니다.
- 모든 `operations`, `sales`, `facility_events` 이벤트는 **1부터 시작하는 재배연도 `year`**와 **1~12월 `month`**를 직접 표시합니다. 이벤트가 없으면 자동으로 매해 반복하지 않으며, 이미 수확한 성목의 소득을 미수확 연도에 복사하지 않습니다. `sales=[]`이면 `no_sales_reason=PRE_PRODUCTIVE_WINDOW`(명시한 미생산 기간) 또는 `DOCUMENTED_NO_SALES`를 필수 지정해 결측을 무의미한 수익 0으로 변환하지 않습니다.
- 작업별 면적비 = `area_m2 / 1000` (10a=1,000㎡). 개별 작업은 자가·고용 `h/10a`, 고용 `KRW/h`, 자재·외주 `KRW/10a`. 출하는 수량/10a, 단위, 상품화율, 판매가·공제액/단위, 운송원가/10a, 수수료율과 0~6개월 실제 입금 지연을 분리합니다. `quantity_unit`은 명시하되 kg, 개, 본 등을 자동 환산하지 않습니다.
- 시설 사건 `CAPEX` / `OPERATING` / `DEPOSIT_PAID` / `DEPOSIT_RETURN` / `SALVAGE_RECEIPT`는 독립 현금 종류입니다. 반환 보증금이 기지급액을 넘거나 원장에 나타나지 않은 금액을 보정하려 하면 오류. 시뮬레이션은 세금·대출·감가상각/장부가·실제 시설 수명·손실 확률·현장 적합성을 **추론하지 않습니다**.
- 각 이벤트 `source_kind`는 R/O/T/Q/A 중 하나이고 `source_ref`는 개인정보 없는 참조 문자열. 가정으로 만든 합성 이벤트는 모두 A로 기록. 전체 입력 금액은 `start_year` **불변 원** 기준으로 이미 동일하게 환산되었다고 가정하며, 실제 명목 다년도 현금과 섞지 않습니다. 연간 `annual_real_discount_rate=null`일 때 사업 NPV도 `null`; 자가노동 시간가치 `null`이면 경제적 NPV는 계산하지 않습니다.
- 출력의 `operating_contribution_before_owner_labor_tax_depreciation_krw`는 회계상 순이익이 아닙니다. `peak_month_end_funding_gap_krw`는 월말 기준 초기 잔고 0에서의 최대 누적 부족액. `unsettled_settlement_after_horizon_krw`는 마지막 해 이후 들어올 정산액을 매출 0으로 처리하지 않습니다.
- 비교는 같은 `start_year`, `horizon_years`, 할인율 입력일 때만 허용합니다. 다년 모델의 프로젝트 NPV나 운영 기여액은 근거 수치가 전부 실측되지 않은 상황에서 작목별 수익성 순위를 자동 결정할 수 없습니다.

실행: `python -m pytest -q tests/test_lifecycle.py tests/test_multiyear_cli.py` 후 `python scripts/compare_multiyear.py --input data/templates/multiyear_scenarios_SYNTHETIC.json --output output/multiyear-model-only.json --html output/multiyear-model-only.html`.

## 현실 농사·변수 감사(신뢰도와 별개의 기능 커버리지)

[51개 실제 농사 검토 요인](../../data/metadata/decision_factor_registry.json)은 소득 수치/기상값/필지 실측이 아니라 구현 기능 감사 목록입니다. MODELED는 실제 다년 모델 입력키, INTAKE_ONLY는 현장 조사 게이트·운영제약 키, NOT_MODELED는 새 모델 미지원으로 표기합니다. 검증 스크립트는 코드 필드에 실제 매핑하는지 검사합니다. 시설비 숫자를 넣는 기능은 난방·관수·토양을 계산하는 과학모형과 다릅니다. 51요인은 RDA 전국 51작목과 별개이며, 각 항목 P0/P1/P2, 필수조건/경영/위험/조건부 이점을 구별합니다. [해석·근거](FARM_REALISM_FACTORS.md) 참고.
