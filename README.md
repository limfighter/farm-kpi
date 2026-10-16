# Farm KPI | 전주 독립 농지 데이터 기반 작목 선택

약 **3,000평 규모의 전주 인근 독립 농지**에서 **작물·작부면적·노지/시설 신축/임대 여부를 아직 정하지 않은 상태**로 후보를 넓게 검증하기 위한 비공개 의사결정 지원 프로젝트입니다. 기존 가족 배 과수원과 별도 산림 버섯사업은 이 모델 범위에 포함하지 않습니다.

**현장 적합성·판매계약·투자수익·대출 가능성이 검증된 서비스가 아닙니다.** 감자·쪽파·오이를 대상으로 한 기존 다섯 전략 시뮬레이션은 예시이고 특정 작물 추천이 아닙니다. 농촌진흥청 2024년 작목 소득은 전국 보고 통계이지 해당 농지의 실제 실적이 아닙니다. **KAMIS는 제외**합니다.

## 여기서 시작

| 필요한 것 | 읽을 문서/실행 화면 |
| --- | --- |
| **전체 문서 탐색** | **[Farm KPI 문서 허브](docs/README.md)** |
| 현재 진행 상태·미확인 사항 | [STATUS — 현재 상태의 단일 기준](docs/STATUS.md) |
| 별도 세션에서 빠르게 재현 | [빠른 시작](docs/how-to/GET_STARTED.md) |
| 계획과 다음 개발 순서 | [8주 실행 로드맵](docs/FARM_DECISION_EXECUTION_PLAN.md) |
| 문서 추가·검증·PR 운영 | [기여 규칙](docs/CONTRIBUTING_DOCS.md) |
| 이전 세션 기록 | [2026-10-15 인수인계 스냅샷](docs/SESSION_HANDOFF_2026-10-15.md) |

개발 자동화·MCP 작업 규칙은 [루트 AGENTS.md](AGENTS.md)에 있습니다. 현재 결정 상태의 기준 문서는 [docs/STATUS.md](docs/STATUS.md)입니다.

## 현실 농사 변수·사업 이점

[현실 농사 변수·조건부 이점 51항목](docs/reference/FARM_REALISM_FACTORS.md)은 **작목 51종과 별개**로, 계산필드 23개·현장 체크리스트 10개·미구현 18개를 구분합니다. 토양·용수·법규·실수취가·피크 주간 노동·현금 위험을 검증하지 않은 작목에 수익 순위를 확정하지 않습니다. 23개 요인에 입력 기능이 있다는 사실은 실농가 데이터 검증을 뜻하지 않습니다.

**시설/방식별 이점의 계산:** 동일 작물·면적·기간을 대상으로 [증분 비용·매출·노동 비교](src/farm_strategy/option_tradeoffs.py)를 구현했습니다. 신축·임대 예제는 전부 가상이며 시설로 수량이 자동 증가하지 않습니다. `python scripts/compare_options.py --input data/templates/multiyear_scenarios_SYNTHETIC.json --output output/paired-option-deltas.json --html output/paired-option-deltas.html`로 결과를 확인합니다.

## 수확기 주간 노동 및 등급별 현금(가정형)

`src/farm_strategy/execution_detail.py`와 `scripts/assess_execution.py`가 작업별 실제 날짜를 ISO 주 단위로 나눠 **월별 노동합계와 주간 노동을 대조**하고, 등급별 수량·가격·공제·포장비로 기존 출하 현금을 **대체**합니다. 포장비는 출하월, 판매대금은 정산월에 기록합니다. 가용 노동시간 미입력은 UNKNOWN이며 실측 사례는 없습니다.

`python scripts/assess_execution.py --input data/templates/execution_detail_SYNTHETIC.json --output output/execution-detail-example.json --html output/execution-detail-example.html`

## 복수 작물·공유 농지·관수/전력·대출 포트폴리오

여러 작물을 같은 구획에 계절별로 재배하거나 별도 구획에서 동시 재배할 때, 면적 중복과 월별 물·전기 공급, 농장 전체 주간 노동 및 시설/대출을 함께 합산합니다. 기존 작물별 현금원장의 인위적인 수익 증분을 만들지 않습니다. 모든 사용·공급·금액은 A 가상 입력이며 현장 검증은 별도입니다.

python scripts/compare_portfolio.py --input data/templates/portfolio_SYNTHETIC.json --output output/portfolio-synthetic.json --html output/portfolio-synthetic.html

## 날짜별 작기·생육단계별 물과 전력·실질금리 가정 대출 상환

`src/farm_strategy/physical_operations.py`는 기존 `portfolio.py`를 **변경하지 않는 검증용 확장계층**입니다. 작형 전환일의 휴지기, 생육단계별 날짜/일 사용량과 기존 월별 물(m³)·전기(kWh) 사용량의 합계 대조, 펌프 m³/h × 실제 가동 가능 시간, 동시 최대 부하 kW, 입력한 **실질** 연이율·거치기간·월 단위 균등원금 상환 스케줄을 계산합니다.

현재 원장에선 같은 달 내 작물 전환은 여전히 허용되지 않으며, 월별 kWh ≠ 순간 kW입니다. 합성 입력의 생육단계 수요·장비 출력·실질금리 값은 **검증된 영농/금융조건이 아닙니다**. 실거래 명목 금리를 실질금리로 몰래 전용하면 안 됩니다. 은행 제시 상환표와 일치하는지 검증하는 기능도 아닙니다.

`python scripts/assess_physical_operations.py --input data/templates/physical_operations_SYNTHETIC.json --output output/physical-operations.json --html output/physical-operations.html`

## 영농기록 로컬 CSV와 가격·수확량·관수/전력 스트레스 테스트

영농 작업시간·수확량·실입금·지출·관수·전기 사용량을 **날짜별 비식별 CSV**로 가져오는 `src/farm_strategy/farm_records_stress.py`를 추가했습니다. 각 기록의 출처표시(O=관측, T=실제 정산, A=실험 가정)는 **자기 신고값**으로 독립 검증이 아니라는 경고를 유지합니다. 원본 정산서·계좌·연락처·주소는 Git에 올리지 않습니다. 실제 기록은 무조건 `data/private/` 같은 무추적 경로에만 보관하고, 샘플은 [가상 영농일지](data/templates/field_log_SYNTHETIC.csv)를 참고합니다.

가격과 수확량의 결합 하락 및 월별 관수·전력 공급 부족을 [가정형 스트레스 파일](data/templates/farm_stresses_SYNTHETIC.json)로 시험합니다. **관수 부족이 자동으로 수량 감소를 초래한다고 추론하지 않고**, 관련된 수량 감소를 사용자가 별도로 가정한 경우에만 반영합니다. 출력은 미래 수익확률·추천이나 과거 실측 검증이 아닙니다.

```bash
python scripts/analyze_farm_reality.py --portfolio data/templates/portfolio_SYNTHETIC.json --stress data/templates/farm_stresses_SYNTHETIC.json --log data/templates/field_log_SYNTHETIC.csv --output output/farm-reality.json --html output/farm-reality.html
```

실제 파일 사용 시 `--log data/private/my-redacted-log.csv`로 바꾸고 **로컬 컴퓨터에서만 실행**합니다. 기록 CSV가 없다면 `--log`를 빼고 가정 스트레스만 실행할 수 있습니다. 사적 파일의 원본·날짜별 거래·출처ID는 HTML/JSON에 복제하지 않고 작형별 합계만 출력합니다.

## 실제 영농 도입 전 P0 결함 점검

[실제 농장 준비도·결함 감사](docs/reference/FARM_READINESS_GAP_AUDIT.md)에 수정한 **중복 정산·누락 0 오해·민감한 활동 날짜·물/전력 부족 표시**와 미해결 토양·용수·거래처·자금 근거를 분리했습니다. 기능 수가 늘어도 이 도구는 가정/현장 관측 분리용이며 작물·시설 투자 승인 자료가 아닙니다.

## 오프라인 브라운·세이지 화면

- **[2022~2023 공식 웹 통계 검증 화면](dashboard/source-coverage/index.html)** — 3개 작목 표본의 정확한 원/10a 수치 5건과 결측 1건을 분리(원본 PDF·노동시간 미대조, 작목 추천 아님).
- **[전체 작목·시설 농작업 시뮬레이터](dashboard/universe/index.html)** — 51개 조사 작목 모두 검색, 새 작물 직접 추가, 노지/신축/임대/기존시설 등 비교, 작업 원가·입금 지연·월별 현금 입력·로컬 JSON 저장. **미입력 수익은 UNKNOWN, 입력한 수치는 가정 또는 개별 출처 자료**.
- **[51개 작목 탐색기](dashboard/crop-discovery/index.html)** — 농촌진흥청 2024 전국 작목의 소득·경영비·노동시간을 *보고 통계*로 표시.
- **[작목별 준비도](dashboard/feasibility/index.html)** — 51개 작목 각각의 8개 현장 확인 질문, 모두 미확인에서 시작.
- **[농지 현장정보 입력](dashboard/site-intake/index.html)** — 12개 공통 조사 항목 및 월별 가용시간을 로컬 JSON으로 저장. 외부 전송 없음.
- **[기존 모델 트리맵](dashboard/index.html)** — 가상 가격/피해/비용 가정으로 만든 5개 **예시** 전략의 현금흐름·위험 비교.

## 농작업 기반 작물·시설 비교 (가정형 첫 버전)

**사용자가 원하는 주요 방향:** 실제 농장의 작업흐름·시설/임대/노지·투입·노동·생산·선별·출하·입금·월별 필요자금을 작목별로 비교하는 것. 출처·현장검증은 결과 신뢰도의 입력이지 모델 구축을 중지시키는 이유가 아닙니다.

`src/farm_strategy/workflow.py`는 **작물 × 시설 × 실제 재배 면적**의 월별 운영활동/수익·비용 구성요소를 계산하는 독립 시뮬레이터입니다. 처음에는 완전히 **A(가정)**인 비교용 입력만 있습니다. 실제 감자/오이 수치, 견적, 작기, 수익 또는 적합성 판단이 **아닙니다**.

```bash
python scripts/compare_workflows.py --input data/templates/workflow_scenarios_SYNTHETIC.json --output output/workflow-example.json --html output/workflow-example.html
python scripts/build_crop_universe.py --check  # 51개 작목 및 20개 공식 작업 달력 참조의 정합성
# 이후 output/workflow-example.html 을 브라우저에서 오프라인으로 열기
```

대금 정산 지연과 보증금은 월별 현금으로 반영하되, 초기 투자비를 운영비로 재차 차감하지 않습니다. 출력의 운영 기여액은 **자기노동·세금·감가상각·대출을 반영한 순이익이 아니며**, 1년 작업+이후 미수금 수령만 추적하므로 단년 모델은 장기 시설 투자 회수/NPV를 계산하지 않으며 아래 다년 모델은 명시된 할인율을 입력받아 NPV를 계산합니다. 농사로 공식 농작업일정은 현재 51개 조사 작목 중 **20개 조사 작형에 참조 연결**했으며, 작형/지역의 상세 일치는 추가 검토 중입니다. 이 20개 작형의 실제 원가·현장 작업량·시설 견적과 나머지 31개 일정 자료를 확보하는 것이 다음 과제입니다. [상세 계약](docs/reference/DATA_CONTRACTS.md).

## 다년(1~10년) 작기 × 시설 현금흐름 실험

**단년 화면과 별도**로 `src/farm_strategy/lifecycle.py` + `scripts/compare_multiyear.py`가 명시적 `year`/`month`를 가진 작업·시설 투자·정산 이벤트를 1~10년에 걸쳐 계산합니다. 딸기처럼 연도를 넘긴 출하와 다년 인삼/신규 과수의 미수확 연도, 신축·임대의 투자·보증금 반환·잔존가를 연도별 현금장부로 분리합니다. **각 해 생산량과 가격은 명시 입력해야 하며, 모델이 동일 작물의 연소득을 복사하지 않습니다.**

```bash
python scripts/compare_multiyear.py --input data/templates/multiyear_scenarios_SYNTHETIC.json --output output/multiyear-model-only.json --html output/multiyear-model-only.html
```

두 예제는 특정 작물이 아닌 **가상 대안(A)**입니다. 명시한 실질 할인율로 계산한 NPV는 입력 가정에 대한 수학적 현금흐름이며, 검증된 농가 투자수익/세후 이익이 아닙니다. 자가노동 경제적 가치를 모르면 경제적 NPV는 `null`; 할인율 미설정이면 사업 NPV도 `null`. 동일한 물가 기준의 불변 원 단위 입력이 필요하며, 세금·차입·감가상각·공동 농지 면적/노동 배분과 다년 실제 영농 검증은 아직 미구현입니다.

## 개발 시작 및 검사

Python **3.11** 권장. 원본 영수증, 정확한 농지 주소/지번, 대출자료, API 키, ASOS 시간별 원자료는 Git에 올리지 않습니다.

\`\`\`bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/check_docs.py --check
python scripts/refresh_crop_discovery.py --check
python scripts/build_feasibility.py --check
python scripts/verify_rda_pdf_source.py --check
farm-strategy validate
\`\`\`

자세한 현장 데이터 입력, 보고 통계 갱신, 모형·단위의 한계는 [문서 허브](docs/README.md)를 따라가세요.

## 데이터·의사결정 원칙

**O** 관측 · **R** 외부 보고 통계 · **T** 실제 거래 · **Q** 서면 견적 · **A** 가정. 자료가 없으면 **UNKNOWN**, 수치 0이나 재배 부적합과는 다릅니다. 2024 명목 원/10a/작기 통계를 2026년 불변 만원 단위의 새 시설 투자 NPV로 자동 변환하지 않습니다.

현재 작물·시설·면적·금융 의사결정은 모두 미정/미승인입니다. 실물 투자/대출 판단은 검증된 현장·가격·판로·서면 견적과 별도 검토 후에만 진행합니다.
