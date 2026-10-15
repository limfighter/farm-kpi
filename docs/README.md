# Farm KPI 문서 허브

**처음 방문했다면 [프로젝트 상태](STATUS.md) → [빠른 시작](how-to/GET_STARTED.md) → [다음 연구 과제](FARM_DECISION_EXECUTION_PLAN.md) 순으로 읽으세요.**

이 문서는 **찾아가기 위한 단일 입구**입니다. 각 사실·명령·근거는 링크된 문서 한 곳에서 관리합니다. `README.md`에는 프로젝트 소개만, 여기에는 찾는 경로만 둡니다.

## 지금 무엇을 해야 하나?

| 목적 | 바로가기 |
| --- | --- |
| 현재 완료/미완료와 다음 PR 범위 | [프로젝트 상태 — 유일한 현재 상태 기준](STATUS.md) |
| 새 세션/개발자 시작 | [빠른 시작과 CI 명령](how-to/GET_STARTED.md) |
| 농지·자금·통계·판로의 실제 확인처는? | [P0/P1 공식 정보처·해결 절차](how-to/P0_P1_OFFICIAL_SOURCE_PLAYBOOK.md) — 지번·계약·계좌는 GitHub에 올리지 않음 |
| 작목은 어떻게 정하나? | [51개 작목 탐색 원칙](CROP_DISCOVERY_PROTOCOL.md) |
| 농지 조사를 어디에 입력하나? | [현장정보 입력 가이드](RDA_AUDIT_AND_SITE_INTAKE.md) · [오프라인 양식](../dashboard/site-intake/index.html) |
| 보고자료를 고쳐야 하나? | [보고 통계 갱신 절차](how-to/UPDATE_REPORTED_DATA.md) |
| 출처·통화·단위와 파일 규약 | [데이터 계약과 신뢰도](reference/DATA_CONTRACTS.md) · [2022~2024 전국·지역 출처 등록부](reference/RDA_MULTYEAR_SOURCE_REGISTRY.md) · [2022~2023 실제 웹 표본 숫자](reference/RDA_WEB_EVIDENCE_SAMPLE.md) |
| 기존 시뮬레이션 실행 및 결과 해석 | [전략 비교·증빙](STRATEGY_COMPARISON_AND_EVIDENCE.md) |
| 공식 수치가 얼마나 검증되었나? | [오프라인 출처 커버리지 화면](../dashboard/source-coverage/index.html) — 예비 웹 통계 5행/결측 1행, **투자 순위 아님** |
| 새 문서를 작성하거나 바꾸나? | [문서 운영 규칙](CONTRIBUTING_DOCS.md) · [ADR 목록](decisions/README.md) |

## 문서의 네 가지 용도

[Diátaxis](https://diataxis.fr/)의 읽는 사람 중심 구분을 **기존 파일명 변경 없이** 적용합니다.

| 사용 의도 | 문서 | 규칙 |
| --- | --- | --- |
| **배우기 (Tutorial)** | [새 세션·개발 환경 시작](how-to/GET_STARTED.md) | 직접 재현 가능한 첫 실행 |
| **문제 해결 (How-to)** | [RDA 갱신](how-to/UPDATE_REPORTED_DATA.md), [현장정보 입력](RDA_AUDIT_AND_SITE_INTAKE.md), [비공개 증빙 미리보기](PRIVATE_CALIBRATION_PREVIEW.md) | 목표·선행조건·명령·완료 기준 |
| **정확한 정보 (Reference)** | [데이터 계약](reference/DATA_CONTRACTS.md), [실행 계획](FARM_DECISION_EXECUTION_PLAN.md), [ASOS 감사](ASOS_AUDIT_AND_ROADMAP.md), [2024 원본 검토](RDA_2024_SOURCE_REVIEW.md) | 단위·출처·관측/가정의 구분 |
| **배경 이해 (Explanation)** | [모델 경계와 회계 선택](explanation/MODEL_BOUNDARIES.md), [작목 검증 이유](CROP_SITE_READINESS.md), [ADR](decisions/README.md), [자료 정리 참고 근거](explanation/DOCS_DESIGN_SOURCES.md) | 왜 그렇게 하는지, 대안과 한계 |

## 기존 전문 문서 — 삭제·이동하지 않는 안정 경로

- [작목 발굴 프로토콜](CROP_DISCOVERY_PROTOCOL.md)
- [51개 작목의 현장 적합성 검토](CROP_SITE_READINESS.md)
- [RDA 2024 원본 출처 검토](RDA_2024_SOURCE_REVIEW.md)
- [RDA 데이터 대조·현장 입력](RDA_AUDIT_AND_SITE_INTAKE.md)
- [ASOS 데이터 감사와 기존 로드맵](ASOS_AUDIT_AND_ROADMAP.md)
- [모델 비교·증빙](STRATEGY_COMPARISON_AND_EVIDENCE.md)
- [비공개 보정 미리보기](PRIVATE_CALIBRATION_PREVIEW.md)
- [8주 실행 계획](FARM_DECISION_EXECUTION_PLAN.md)
- [2026-10-15 이전 세션 인수인계 (기록, 현재 상태 아님)](SESSION_HANDOFF_2026-10-15.md)

## 쓰고 검증하는 규칙

- **현재 상태는 [STATUS.md](STATUS.md) 한 곳**에서만 갱신합니다. 완료되지 않은 현장/시장/대출 검증은 UNKNOWN으로 기록합니다.
- 중요한 방식 선택은 [ADR](decisions/README.md)로 남깁니다. 작물·시설 선정과는 구별합니다.
- 모든 문서는 [카탈로그](catalog.json)에 경로·목적·유지관리 책임을 기록합니다. 작성자는 [문서 기여 규칙](CONTRIBUTING_DOCS.md)을 따릅니다.
- 변경은 PR에서 검토하고 `python scripts/check_docs.py --check`와 기존 `pytest -q`를 통과시킵니다.
- 데이터 변경과 문서 변경을 연결하되 **2024 국가 통계를 2026 필지 실적이라고 바꾸지 않습니다**.
