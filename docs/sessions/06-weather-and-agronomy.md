# 세션 06 — 시간별 기상 원본과 작물별 영농 조건

**목적/대상:** 관측자료·영농 검토 담당자가 ASOS 원본의 한계와 작물별 현장 노출을 분리할 작업 지시서다.  
**연결:** 로드맵 P1-04. 전용 Issue는 현재 STATUS에 없으며 [#5](https://github.com/limfighter/farm-kpi/issues/5)의 현장 노출·[#7](https://github.com/limfighter/farm-kpi/issues/7)의 출처 검토와 연계한다.  
**문서 성격/책임:** 실행 계획. 실제 현황은 [STATUS](../STATUS.md)만 따르며 관측 담당이 QC, 영농 담당이 문헌/작기를 검토한다.

## 입력과 경계

- [기존 ASOS 감사 기록](../ASOS_AUDIT_AND_ROADMAP.md), [실행 로드맵](../FARM_DECISION_EXECUTION_PLAN.md), [모델 경계](../explanation/MODEL_BOUNDARIES.md)를 읽는다.
- 01~05 완료 없이 시작한다. 필지·작형 미확인이면 지역 관측/공개 영농 근거까지만 수집하며 필지 피해로 일반화하지 않는다.
- 기존 연간 파생자료 O와 과거 감사 보고를 원본 재검증으로 부르지 않는다. 원본 시간별 파일은 ignored `data/raw/`에 두고 이용조건을 확인한다.

## 실행 순서

1. 공식 KMA 시간별 ASOS 원본 또는 운영자가 제공한 원본의 관측소·기간·버전·다운로드일·해시·라이선스를 기록한다. 원본이 없으면 감사 재수행은 미완료다.
2. CP949·시간대·중복/충돌·결측 시간·QC 코드를 검사한다. 빈 강수와 QC8/QC9를 0으로 치환하지 않는다.
3. 공식 일강수량과 대조해 강수 합계·임계일수의 완전성을 확인한다. 시간별 유효 관측의 최대/최소를 공식 일 극값과 구별한다.
4. 기존 시간별 검사기는 원본 QC만 검사하며 일/연 집계를 재생성하지 않는다. 차이가 나면 원인·영향·재집계 필요를 기록하고 별도 구현 과제로 인계한다.
5. 농업기술센터·RDA 등 공식 영농자료에서 작물×작형×작기별 파종/수확창, 온도·용수·토양·윤작·병해충·난방 요구를 출처/쪽수와 함께 정리한다.
6. 관측소 날씨, 현장 침수/저온/열 노출 O, 문헌의 영농 요구 R, 모델 계수 A를 분리한다. 피해율·수량 탄력성·병해확률을 임의로 만들지 않는다.
7. 적용 범위와 검증 공백을 위험행렬로 인계한다. 담당기관 문의는 운영자의 별도 승인 범위에서 수행하고, 현장 적합성과 피해계수 보정은 별도 검토한다.

## 예상 산출물

- `output/hourly-audit.json`에 원본 시간 QC 결과, 비공개 `data/private/weather-source-review.md`에 원본/일자료 대사·한계를 기록한다.
- `output/agronomy-risk-matrix.md`에 작물/작형/작기·요구조건·문헌·현장 노출·미확인/적용 한계를 기록한다. 공개 가능한 출처/절차만 기존 ASOS 문서에 반영한다.
- 실제 근거 충족도만 STATUS에 반영한다. 기존 연간 CSV·손실계수·모델 설정 변경은 출처/재집계 검증을 갖춘 별도 PR로 제안한다.

## 검증 명령과 통과 기준

첫 명령은 원본이 있을 때만 실행한다. 원본 미제공이면 생략 사실을 기록하고 나머지 검사와 혼동하지 않는다.

```bash
python -m farm_strategy.hourly data/raw/OBS_ASOS_TIM_*.csv --output output/hourly-audit.json
python -m farm_strategy.audit --annual data/processed/annual_asos_jeonju_2006_2025.csv --metadata data/metadata/asos_v10_archive_audit.json
python -m pytest -q tests/test_hourly.py tests/test_audit.py
python scripts/check_docs.py --check
```

**통과:** 원본 범위/QC·일강수 대조 결과 또는 미확보 사유가 있고 영농 조건마다 출처·작형·작기가 있다. 기상 관측과 작물 피해 보정의 경계가 명확하다.  
**차단/인계:** 원본·현장 노출·피해 실측이 없으면 해당 검증은 UNKNOWN이다. 연간 검사 통과·기상 상관·Monte Carlo 횟수는 작물 피해확률/ROI 검증이 아니며 다른 근거 수집은 계속한다.

## 다음 세션 시작 프롬프트

```text
AGENTS.md와 필수 문서, docs/sessions/06-weather-and-agronomy.md를 읽고 P1-04를 진행해 줘. 공식 시간별 ASOS 원본의 출처/QC/강수 결측을 검토하고, 공식 일자료 대사와 작물×작형×작기별 영농 요구의 근거표를 분리해. 원본 미확보와 현장 노출 미확인은 그대로 보고하고 빈 강수를 0으로 바꾸거나 피해확률을 만들지 마. 원본은 비공개로 두고 관련 검사를 실행해 실제 검증 범위를 보고해.
```
