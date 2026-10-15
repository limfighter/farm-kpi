# 데이터 계약·출처 분류·단위 참고표

**대상:** 파이프라인, 문서, 대시보드, CI 구현자. **현재 입력 구조 설명**이지 미확인 자료를 사실로 만드는 규칙이 아닙니다.

## 데이터 계층

| 파일/객체 | 출처·시점 | 단위/기간 | 의미·금지사항 |
| --- | --- | --- | --- |
| [2024년 51개 작목](../../data/reported/rda_2024_all_51_crop_candidates.csv) | RDA 2024 보고 통계 **R**, PDF 요약 17–19/노동 127–177쪽 | 명목 원/10a/작기, 노동 h/10a | 전국 단면, 실제 전주 필지 실적/ROI 아님 |
| [다년도 전국·지역 출처](../../data/metadata/rda_income_source_registry.json) 및 [장기형 현재 관측](../../data/reported/rda_income_long.csv) | 2022~2024 공식 출처 공표 존재 확인, 정확한 값은 2024 전국 51행만 전사 | 2024 명목 원/10a/작기, region=NATIONAL | 2022/2023 및 2024 전북 숫자 없음/미확인. 게시물 존재는 개별 전북 품목 값 존재 증명이 아님. [검증 기준](RDA_MULTYEAR_SOURCE_REGISTRY.md) |
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

- [데이터 갱신 절차](../how-to/UPDATE_REPORTED_DATA.md)
- [개발 환경 시작](../how-to/GET_STARTED.md)
- [RDA/현장정보 자세한 기준](../RDA_AUDIT_AND_SITE_INTAKE.md)
- [근본적인 회계 경계](../explanation/MODEL_BOUNDARIES.md)
