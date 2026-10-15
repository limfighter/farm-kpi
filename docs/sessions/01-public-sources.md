# 세션 01 — 다년도·전북 공개 근거 검증

**목적/대상:** 자료 조사·검증 담당자가 전국 통계를 지역·연도별 비교 가능한 근거로 확장할 작업 지시서다.  
**연결:** 로드맵 P1-01 · [Issue #7](https://github.com/limfighter/farm-kpi/issues/7). **문서 성격:** 실행 계획이며 실제 현황은 [STATUS](../STATUS.md)만 따른다.  
**책임:** 조사 담당이 전사하고 별도 검토자가 원문·단위·라이선스를 대조한다. 기한은 원문 확보에 따른다.

## 입력과 경계

- [실행 로드맵](../FARM_DECISION_EXECUTION_PLAN.md), [후보 발굴 원칙](../CROP_DISCOVERY_PROTOCOL.md), [공식 정보처](../how-to/P0_P1_OFFICIAL_SOURCE_PLAYBOOK.md), [출처 등록부](../reference/RDA_MULTYEAR_SOURCE_REGISTRY.md), [갱신 절차](../how-to/UPDATE_REPORTED_DATA.md)를 읽는다.
- 2024 전국 51행과 기존 이력 잠금은 유지한다. 2022~2023 웹 표본은 PDF·노동시간 미대조 상태로 분리한다.
- 다른 세션 02~06의 완료 없이 시작한다. 현장자료 미확인은 이 수집을 막지 않으며 해당 후보의 후속 재무평가만 보류한다.

## 실행 순서

1. 2022~2024 전국·지역 자료집부터 확인하고, 추가 공표연도를 찾아 가능하면 3~5년 이상 범위를 만든다. 미공표·접근불가 사유도 기록한다.
2. 공식 원문별 발행/조사연도, 수정판, URL, 파일 해시, 재사용 조건을 확인한다. API 코드북·방법론 공고를 실적 행으로 세지 않는다.
3. 전북 개별 행의 존재와 작목·작형·표본·작기 정의를 확인한다. 전국값의 지역 복사와 웹 그래프 반올림값 역산은 금지한다.
4. 원/10a/작기, 명목 통화연도, 생산량·등급·가격 단위, 자가/고용/합계 노동 및 PDF 쪽수를 원문과 대조한다.
5. 총수입−경영비≈소득, 노동 합계와 작목 ID 대응을 검토한다. 4년근 인삼과 성목/신규 식재의 시간 차이는 별도로 남긴다.
6. 비교 가능/불가/미확인을 구분한다. 가격이 도매인지 농가수취인지 표시하고, 출처 R을 T·필지 성과로 승격하지 않는다.
7. 새 행은 별도 검토 후에만 이력 스키마·검사기 변경 PR로 제안한다. 기존 잠금 해시를 우회 갱신하거나 가정 재무설정을 덮어쓰지 않는다.
8. 51개 조사 작목 밖의 작물·재배체계 후보를 별도 등록부로 관리한다. 후보 ID·명칭·체계·발견 출처·비교 근거 유무·미확인 사유를 기록하며, 비교 가능한 수치 근거를 확보·검토하기 전에는 `source_available=false`와 pending을 유지한다. 생산량·소득·지역 적합성을 지어내지 않는다.

## 예상 산출물

- 기존 `data/metadata/rda_income_source_registry.json`과 [출처 등록부](../reference/RDA_MULTYEAR_SOURCE_REGISTRY.md)에 출처·커버리지·결측 사유를 갱신한다.
- 검토 전 전사표/PDF는 ignored `data/private/`·`data/raw/`에 둔다. 재배포 허용·독립 검토·스키마 검증을 통과한 새 관측만 `data/reported/rda_income_long.csv`에 제안한다.
- 기존 웹 표본은 [별도 기록](../reference/RDA_WEB_EVIDENCE_SAMPLE.md)에 검증 수준을 유지한다. 실제 바뀐 근거 충족도만 STATUS와 #7에 비식별 요약한다.
- 조사 밖 후보의 비식별 메타데이터 등록부를 `data/metadata/off_survey_candidate_registry.json`(신규 제안 경로)에 마련하고 데이터 계약에 필드 의미를 기록한다. 잠금 51행/장기형과 병합하지 않으며 [세션 08](08-evidence-gated-model.md)에 근거가 있는 후보와 pending 후보를 함께 인계한다.

## 검증 명령과 통과 기준

저장소 루트에서 실행하며, 아래 검사는 기록 정합성 검사이고 새 원문의 진위 확인은 별도다.

```bash
python scripts/verify_rda_pdf_source.py --check
python scripts/check_crop_income_history.py --check
python scripts/check_rda_web_sample.py --check
python scripts/build_rda_web_sample_board.py --check
python scripts/check_docs.py --check
```

**통과:** 확보한 각 행에 연도·지역·작형·분모·작기·통화연도·쪽수·R·검토자가 있고 기존 51행 잠금이 보존된다. 미확보 범위와 비교 제약을 재현할 수 있다. 조사 밖 후보는 별도 등록하며 근거 없는 수치/재배 가능 판정을 포함하지 않는다.  
**차단/인계:** 원문·라이선스·전북 행·노동 대조가 없으면 그 행은 미승격/UNKNOWN으로 둔다. 3~5년 확보 실패를 완료로 포장하거나 #7을 자동 종료하지 않는다.

## 다음 세션 시작 프롬프트

```text
AGENTS.md와 필수 문서, docs/sessions/01-public-sources.md를 읽고 P1-01/#7을 실행해 줘. 현재 STATUS와 기존 51행 잠금을 기준으로 공식 다년도·전북 원문/쪽수/노동/라이선스를 검증하고, 미확인 웹 표본을 분리해. 가능한 범위와 막힌 범위를 출처 등록부에 남기고 관련 검사를 실행해. 원본 PDF·개인정보를 커밋하거나 근거 없이 재무값을 바꾸지 말고, 실제 확보와 미완료를 구분해 보고해.
```
