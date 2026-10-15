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

## 오프라인 브라운·세이지 화면

- **[2022~2023 공식 웹 통계 검증 화면](dashboard/source-coverage/index.html)** — 3개 작목 표본의 정확한 원/10a 수치 5건과 결측 1건을 분리(원본 PDF·노동시간 미대조, 작목 추천 아님).
- **[51개 작목 탐색기](dashboard/crop-discovery/index.html)** — 농촌진흥청 2024 전국 작목의 소득·경영비·노동시간을 *보고 통계*로 표시.
- **[작목별 준비도](dashboard/feasibility/index.html)** — 51개 작목 각각의 8개 현장 확인 질문, 모두 미확인에서 시작.
- **[농지 현장정보 입력](dashboard/site-intake/index.html)** — 12개 공통 조사 항목 및 월별 가용시간을 로컬 JSON으로 저장. 외부 전송 없음.
- **[기존 모델 트리맵](dashboard/index.html)** — 가상 가격/피해/비용 가정으로 만든 5개 **예시** 전략의 현금흐름·위험 비교.

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
