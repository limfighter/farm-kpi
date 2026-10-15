# 새 세션 인수인계 | Farm KPI (2026-10-15)

이 문서는 **별도 ChatGPT 세션에서 이 저장소의 작업을 이어가기 위한 기준 문서**입니다.
최신 코드와 검증 상태는 항상 GitHub `main`, Actions, 이 문서의 링크 순서로 확인하세요.
이 문서는 정보 인계용이며 작물·시설·대출·투자를 승인하지 않습니다.

## 1. 프로젝트 목표 및 변하지 않는 원칙

- 저장소: `limfighter/farm-kpi`, 기본 브랜치 `main`.
- 목적: 전주 인근 별도 농지 **약 3,000평**에 대해 **작물, 재배방식, 면적 배분을 아직 정하지 않은 상태**에서 데이터로 옵션을 발굴·검증하고, 조건이 갖춰질 때만 비교·의사결정합니다.
- 기존 가족 배 과수원 및 별도 산림 버섯 사업은 이 농지 수익계산에서 제외합니다.
- **노지·시설 신축·시설 임대·과수·특용작물 등 모든 가능성을 열어둡니다.** `field_trial`, `pause_after_trial`, `new_cucumber_house`, `leased_cucumber_house`, `new_cucumber_premium`의 **5개 전략은 예시용**이고 선정 작물이 아닙니다.
- 데이터 출처 구분: `O` 관측값, `R` 외부 보고 통계, `T` 실제 정산된 거래, `Q` 서면 견적, `A` 가정. **UNKNOWN은 0점, 부적합 또는 0원과 다릅니다.**
- 공공 작목 통계를 실제 필지 매출이나 신규 시설 투자 NPV로 곧바로 환산하지 않습니다.
- 개인정보, 정확한 지번·좌표, 계약서·영수증, 은행정보, 원본 ASOS 시간자료는 Git에 넣지 않습니다.

## 2. 이번 병합 릴리스에 포함되는 구현

| 범위 | 실제 파일 및 사용법 | 검증 한계 |
| --- | --- | --- |
| 51개 작목 탐색 | `dashboard/crop-discovery/index.html`, `data/reported/rda_2024_all_51_crop_candidates.csv`; `python scripts/refresh_crop_discovery.py --check` | 2024 **전국** 농촌진흥청 10a/작기 보고자료 `R`, 전주 실측치가 아님 |
| 51개 현장 적합성 체크리스트 | `dashboard/feasibility/index.html`, `data/derived/crop_readiness_51.csv`; `python scripts/build_feasibility.py --check` | 작목별 **8개** 현장 검증 게이트는 현재 모두 미확인 |
| 농지·인력 실제 정보 수집 UI | `dashboard/site-intake/index.html`, `data/templates/private_site_intake_TEMPLATE.json`; `farm-strategy site-check --file data/private/site-facts.json --output output/site-status-redacted.json` | **12개** 농지 공통 조사 게이트, **12개월** 자가노동 시간; 문서 확보는 독립 검증 완료가 아님 |
| 원자료 대조 감사 | `scripts/verify_rda_pdf_source.py --check`, `data/metadata/rda_2024_source_verification.json`, `docs/RDA_AUDIT_AND_SITE_INTAKE.md` | 사용자가 제공한 2024년 **287쪽** 자료집에서 작목 **51개** 총수입/경영비/소득 수치와 노동시간 합계를 대조. PDF 자체는 Git 비포함. 통계·지역 적합성을 인증하지 않음 |
| 기상자료 | `data/processed/annual_asos_jeonju_2006_2025.csv`, `data/metadata/asos_v10_archive_audit.json`; `python -m farm_strategy.audit ...` | ASOS 기상관측은 작물별·필지별 실제 손실확률이 아님. 원본 시간별 자료의 추가 검증은 제한 있음 |
| 가정 기반 시뮬레이션 | `src/farm_strategy/model.py`, `cashflow.py`, `comparison.py`, `configs/base.json`; `farm-strategy compare --seed 42 --paths 300 --stress-matrix --csv output/compare.csv` | **5개 기존 예시** 전략에만 해당. 가상의 가격·병해충·공사비·대출·월별 정산시점; 결론/투자추천 불가 |
| 수익·유동성 HTML | `dashboard/index.html`, `scripts/build_dashboard.py`, `dashboard/data/screening-model-only.csv` | 브라운+세이지 오프라인 SVG; **모형 전용** 결과이며 실제 농지 성과 아님 |
| 민감한 증빙 가정 변경 미리보기 | `src/farm_strategy/calibration.py`, `evidence.py`, `docs/PRIVATE_CALIBRATION_PREVIEW.md` | 원본 검토를 인간이 확인하고 해시가 맞아야 **임시 복제 config**로 비교. 실제 원본 증빙 미제공, 모형 기본값 변경 없음 |

**중요 구분:** 현장 적합성 화면의 작목별 **8개 질문**과 농지 입력 화면의 공통 **12개 질문**은 역할이 다릅니다. 어느 쪽도 지금은 통과/적합을 주장할 수 없습니다.

**단위 주의:** RDA 2024는 **명목 원/10a/작기**, 현 시뮬레이션은 대체로 **2026년 불변 만원/연도**입니다. RDA 경영비에는 고용노동·시설 감가상각 등 항목이 들어 있어 별도 고용비·CAPEX 계산과 이중계상할 수 있습니다. `인삼(4년근)`의 4년 작기 수익을 무근거 연간소득으로 나누지 않습니다. 시설과수는 새 식재 후 성목까지의 기간을 따로 모델링해야 합니다.

## 3. 완료 / 아직 안 된 일

### 개발 완료

1. 51개 자료집 수치·노동시간 원본 대조, 출처 해시/페이지와 비정상 입력 검증.
2. 51개 작목 탐색 HTML 및 현장 적합성/체크리스트 오프라인 화면.
3. 농지의 12개 실사 항목, 유효 면적·월별 노동·투자 여력을 **null/UNKNOWN**으로 입력하고 로컬 JSON을 내려받는 화면과 `site-check` 명령.
4. 5개 **예시** 전략의 120개월 유동성·가상 위험 비교·검증용 CI.
5. 재현 가능한 빌더 및 회귀 테스트; GitHub Actions가 확인하는 데이터/HTML 동기화.

### 미완료 / 외부 자료 의존

1. **실제 필지 조사 미실시:** 경작 가능한 유효 면적, 토양검정, 배수, 관개수, 진입로, 전기, 침수·서리·제한구역·시설허가.
2. **영농 운영 제약 미정:** 월별 자가/고용 노동 공급, 투자 가능 자기자금과 최대 허용 현금 부족, 첫 정산까지 허용기간.
3. **지역·다년간 실측 미확보:** 전북 지역성과 국가 통계를 구분한 2020~2025년 수준의 작목별 시계열/수량/가격/소득 자료. 2024만으로 추세·실제 실패확률을 추정하지 말 것.
4. **실제 사업 거래조건 미확보:** 구매처, 등급/포장/운임/수수료/결제일, 서면 시설 신축·임대·관수·저장 견적, 계약금·잔금·대출 조건.
5. **범용 작목-재배시스템 현금흐름 모델 미구현:** 51개 작목을 단순히 기존 5개 감자·쪽파·오이 예시 모형에 매핑하지 말 것.
6. **투자·작물 선정 보류:** 면적 배분/시설 구축/대출/시험재배 여부까지 미결정.

## 4. 다음 세션의 정확한 착수 순서

**첫 순서 P1-01: 다년간 작목·지역 출처 검증 작업**을 권장합니다.

1. GitHub `main` 최신 상태 및 `.github/workflows/ci.yml` 성공 확인; `python -m pip install -e '.[dev]'`, `pytest -q`, 데이터/HTML `--check` 재실행.
2. 농촌진흥청 **농산물소득자료집/공식 소득정보 API**에서 2024년 이외 연도와 전북 지역 단위가 **실제로 제공되는지 검증**. 공개 API 코드표만으로 API 데이터가 있다고 추정 금지. 외부 조회가 불가하면 연도·지역 결측을 명시한 **출처 레지스트리부터 작성**.
3. 연도, 지역(전국/전북/미제공), 조사작기, 작물 코드·명칭, 시설/노지 분류, 총수입·경영비·소득·자가/고용시간, 단위, 페이지/URL, 출처 유형 `R`, 비교가능성 경고를 포함하는 **장기형 데이터 테이블** 설계·테스트.
4. 국가/지역 숫자를 섞거나 2024년만 복제하지 않는 누락값 테스트, 4년근 인삼/시설감가상각/작기 불일치 테스트를 추가한 다음 브라운/세이지 탐색기로 연결.
5. 동시에 농지 공통현장 조사표 사용자 입력이 준비되면 **로컬 민감파일**로만 검증. 입력이 없으면 시스템상 미확인 유지.
6. 다음 P1-02/P1-03으로 구매처 순정산 조건 및 시공/임대 서면 견적 설계. 확보한 것만 `Q/T`로 검토하고 미확보면 공란 유지.
7. 충분한 증빙·현장 조건이 갖춰진 뒤 P2 범용 모델과 다목적 후보 비교 수행.

**완료 조건:** 보고된 사실/가정/미확인을 일관되게 구분하며, CI 그린, 자료 CSV/HTML 재현 가능, 브랜치에서 PR→`main` 병합 전에 이용자 검토. 근거 없는 상위 5개 작물 또는 ROI 추천은 성공이 아닙니다.

## 5. 주요 링크 및 시작 명령

- 저장소: https://github.com/limfighter/farm-kpi
- 실행 로드맵: `docs/FARM_DECISION_EXECUTION_PLAN.md`
- 농지 실사: `docs/RDA_AUDIT_AND_SITE_INTAKE.md`
- 작목 발견: `docs/CROP_DISCOVERY_PROTOCOL.md`
- 지표 원가/출처 한계: `docs/RDA_2024_SOURCE_REVIEW.md`
- 기존 자금모형 기술: `docs/ASOS_AUDIT_AND_ROADMAP.md`
- CI: `.github/workflows/ci.yml`

```bash
python -m pip install -e '.[dev]'
pytest -q
python scripts/refresh_crop_discovery.py --check
python scripts/build_feasibility.py --check
python scripts/verify_rda_pdf_source.py --check
farm-strategy validate
# 로컬에 민감한 필지 자료를 별도 확보했을 때에만:
mkdir -p data/private output
cp data/templates/private_site_intake_TEMPLATE.json data/private/site-facts.json
farm-strategy site-check --file data/private/site-facts.json --output output/site-status-redacted.json
```

## 6. 새 세션에서 붙여넣을 요청

> GitHub 저장소 `limfighter/farm-kpi`의 `main` 브랜치를 읽고
> `docs/SESSION_HANDOFF_2026-10-15.md`와
> `docs/FARM_DECISION_EXECUTION_PLAN.md`를 기준으로 작업을 이어가 줘.
> 작물·시설·면적은 전부 미정이며, 노지/시설/과수/특용 모든 선택지를 열어둬.
> 먼저 P1-01 다년간·전북 지역 농산물소득 **공식 출처의 존재와 실제 이용가능성**
> 을 확인하고, 검증된 데이터만 출처/단위/작기/지역을 명시해 수집·테스트·대시보드
> 까지 업데이트해 줘. 검증 불가한 것은 미확인으로 표시하고,
> 실제 토지·거래정보나 모형 수익성을 지어내지 마. 새 PR에서 작업하고
> CI 확인 전에는 병합하지 마.
