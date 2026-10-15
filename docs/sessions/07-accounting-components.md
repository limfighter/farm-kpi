# 세션 07 — 이름 있는 비용 구성요소와 회계 정합성

**목표:** 기존 다섯 예시 계획의 연간 모형과 월별 장부에 중복된 비용 규칙을 정리해 이후 범용 모형의 회계 기반을 만듭니다. **대상/책임:** 개발·모델 담당. **로드맵:** P2-01 사전 정비. 진행 상태는 [STATUS](../STATUS.md)를 따릅니다.

## 입력·선행조건

- [코드 구조](../explanation/CODE_STRUCTURE.md), [모델 경계](../explanation/MODEL_BOUNDARIES.md), `model.py`, `cashflow.py`, `configs/base.json`과 기존 재무 회귀 테스트.
- 실제 농지 자료 없이 수행 가능합니다. 기존 설정을 실제 견적/수익으로 바꾸지 않습니다. 이번 작업은 계산 동작을 보존하는 구조 개선입니다.

## 실행 순서

1. 변경 전 동일 seed의 계획·시나리오·기상창별 상세 월/연간 결과와 비교 요약을 ignored `output/`에 저장합니다. 어느 비용이 두 파일에 중복되어 있는지 목록화합니다.
2. 노지·유휴·신축·임대·프리미엄·시설 수리, 고용노동, 세금/보험의 **명시적 구성요소**와 합계를 구별하는 회귀 검사를 먼저 만듭니다. 수리 없는 경우와 수리 있는 경우, 보증금 반환·명목/실질 부채를 포함합니다.
3. 공통 구성요소의 책임·인터페이스를 작은 범위로 설계한 뒤 패키지에 추출합니다. 연간 합계와 월별 배분이 참조할 금액을 이름으로 연결하고, 기존 난수 소비 순서·부동소수점 연산 순서를 유지합니다.
4. 월별↔연간 독립 정합성 검사와 설명되지 않은 잔차의 오류 처리는 남깁니다. 남는 금액을 수리/세금/특정 월에 자동 배정하지 않습니다.
5. 저장한 변경 전 결과와 정확 일치를 확인하고 코드 구조·데이터 계약에 변경 경계를 기록합니다. 스크립트 패키징이나 작목 추가는 별도 범위로 둡니다.

## 산출물·완료 기준

- `src/farm_strategy/`의 비용 구성요소 분리, `tests/test_monthly_cashflow.py`, `tests/test_finance_regressions.py`와 필요한 회귀 검사, 코드 구조 문서 갱신.
- 기존 정상 입력의 JSON/CSV와 월별 합계가 보존되고, 잔차·이중 계산을 탐지합니다. 결과가 달라지면 원인·계약 변경을 별도 제안하고 구조 변경 완료로 처리하지 않습니다.
- 새 실제 숫자·현장 적합성·대출 승인 주장은 산출물에 포함하지 않습니다.

## 검증

```bash
python -m pytest -q tests/test_model.py tests/test_comparison.py tests/test_monthly_cashflow.py tests/test_finance_regressions.py
python -m pytest -q
python scripts/check_docs.py --check
```

최종 PR에서는 공통 [세션 종료 규칙](README.md)에 따라 최신 HEAD의 출처/대시보드 검사와 push·PR CI까지 확인합니다.

## 재개 프롬프트

> AGENTS.md, docs/STATUS.md, docs/sessions/07-accounting-components.md를 읽고 최신 main/PR/CI를 확인해. 연간/월간 비용 중복을 이름 있는 구성요소로 정리할 작은 범위를 선정하고 변경 전 결과를 저장해. 난수·회계 의미와 정확한 결과를 보존하며 구현·회귀 검증하고, 잔차는 오류로 남겨.
