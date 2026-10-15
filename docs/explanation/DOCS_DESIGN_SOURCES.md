# 외부 팀의 문서 운영 방식 → Farm KPI 적용 근거

**조사일:** 2026-10-15  
**범위:** GitLab, Stripe 공개 저장소/문서, Google Cloud ADR 안내, Diátaxis 문서 프레임워크. **유명 기업의 운영 방식 일부를 참고한 것이지, 이 프로젝트가 그 회사만큼 성숙하거나 데이터 품질이 같다는 주장이 아닙니다.**

| 공개된 원전과 확인된 관행 | Farm KPI에 적용한 변형 | 생략한 것 |
| --- | --- | --- |
| [GitLab 문서 스타일·SSoT](https://docs.gitlab.com/development/documentation/styleguide/) — 문서를 제품 사용의 기준으로 유지하며 변경과 함께 갱신, [handbook-first/MR](https://handbook.gitlab.com/handbook/about/editing-handbook/) | \`docs/STATUS.md\`를 진행 상태 기준으로, 코드+문서 PR, \`docs/README.md\` 허브 | 공개 핸드북 전체 운영 및 조직 구조. 농지 관련 원본 개인정보는 비공개 |
| [Diátaxis](https://diataxis.fr/) — Tutorial / How-to / Reference / Explanation 각각 사용자 목적이 다름 | 현 파일을 다 옮기지 않고 허브에서 분류. 바로 실행할 두 how-to, 단위 레퍼런스, 회계 이유 설명만 작성 | 비어있는 4개 디렉터리 대량 생성, 페이지의 기계적인 전면 이사 |
| [Google Cloud: ADR](https://docs.cloud.google.com/architecture/architecture-decision-records) — 결정의 옵션/요구/근거를 코드와 함께 Markdown으로 기록 | \`docs/decisions/\`에 **기술·정보 정책** ADR 2개, 템플릿/목록. 작물 선택/시설 승인과 구분 | 리뷰 기록 없이 ‘적합/투자 확정’ ADR 생성 |
| [Stripe Node 저장소](https://github.com/stripe/stripe-node) — README/CONTRIBUTING/CHANGELOG 및 [버전별 마이그레이션 안내](https://github.com/stripe/stripe-node/wiki) 제공 | README 짧은 입구, 실무 변경 가이드, 기록 스냅샷·단위 구분. 변경 시 산출물 동기화 검사 | 농업 현장 데이터에 소프트웨어 API 버전 규칙을 그대로 강제하거나 매번 긴 변경 로그 작성 |

## 선정 기준

1. **발견 가능성:** 새 세션에서 '지금 어디까지 왔지?'를 단일 문서로 확인.
2. **신뢰성:** 숫자마다 관측/보고/견적/거래/가정을 분리하고 단위와 원문을 묶기.
3. **변경 비용:** 작은 프로젝트에 불필요한 문서 플랫폼·홈페이지 배포·복잡한 승인 체계 도입 금지.
4. **검증 가능성:** 표준 라이브러리 기반 로컬 문서 링크/인벤토리 검사로 CI와 연결.
5. **개인정보:** 저장소가 private여도 비식별 레퍼런스만 커밋. 개인정보/원본 농지·거래문서 격리.

## 적용된 파일

- **입구·현재 상태:** [문서 허브](../README.md), [진행 상태](../STATUS.md).
- **실행:** [새 세션 시작](../how-to/GET_STARTED.md), [RDA 갱신](../how-to/UPDATE_REPORTED_DATA.md).
- **참고·설명:** [데이터 계약](../reference/DATA_CONTRACTS.md), [모델 경계](MODEL_BOUNDARIES.md).
- **판단 기록:** [ADR 목록](../decisions/README.md).
- **유지관리:** [기여 규칙](../CONTRIBUTING_DOCS.md), [catalog.json](../catalog.json), [문서 검사 코드](../../scripts/check_docs.py).

**외부 근거 한계:** 원전의 공개 문서에서 확인한 *작성/구조화 방침*만 차용합니다. 특정 기업의 내부 문서 최신 상태나 운영성과를 직접 검증한 것은 아닙니다.
