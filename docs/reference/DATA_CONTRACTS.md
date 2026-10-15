undefined

### 51작목 전체·조사 밖 후보 탐색과 워크플로우 입력

- [범용 오프라인 작물×시설 입력 화면](../../dashboard/universe/index.html)은 [원본 51작목 보고 통계](../../data/reported/rda_2024_all_51_crop_candidates.csv)로 생성합니다. `python scripts/build_crop_universe.py --check`로 목록·단위·PDF 페이지의 잠금 및 화면 일치를 검사합니다.
- 최초 목록에 **51개 RDA 조사 작형을 전부 포함**하며, [별도 등록부](../../data/metadata/off_survey_candidate_registry.json)에 공개 정보로 등재된 조사 밖 작목은 UNKNOWN으로 함께 표시합니다. HTML에서 직접 추가한 후보는 브라우저 내에서만 만들며 원본 CSV/통계에 혼합하지 않습니다.
- RDA 2024 전국 `income`, 노동 h/10a/작기, `yield_unit`, 소득·노동 PDF 쪽수는 **참고 정보(R)**입니다. 이를 아래 재무 사례의 노동·판매·운영비에 **자동 복사하지 않습니다**.
- UI에서는 작업별 `operations[]`, 출하 `harvests[]`, 시설/보증금 `facility_events[]`의 숫자를 필수로 입력해야 계산합니다. 빈 값은 0으로 채우지 않으며 입력 사례는 로컬 JSON으로 내보내 `scripts/compare_workflows.py`에 전달할 수 있습니다. JSON 파일에 주소·계좌·거래처 실명을 넣어 Git에 커밋하지 않습니다.
- `harvests[]`는 기존 kg 전용 형식도 유지하고, 신규 범용 형식의 `yield_quantity_per_10a`, `yield_unit`, `price_krw_per_unit`, `buyer_deduction_krw_per_unit`을 추가 지원합니다. **수확수량의 단위와 판매/공제 단위는 반드시 동일**해야 하며 자동 kg 환산은 하지 않습니다. 단위 입력은 시뮬레이터가 단위의 진실성을 인증하는 것은 아닙니다.
- **다년 작기/작기 미확인** 후보는 1년 입력 화면에서 현금흐름 계산을 막고, **과수 신규 식재**는 성목 보고 수익을 신설 첫해 매출로 취급하지 않도록 기본 차단합니다. 기존 성목 포장이라는 사용자의 별도 확인 없이는 과수 단년 계산을 허용하지 않습니다. 다년 작기·신규 과수의 생육/비생산 연도와 시설 수명/감가상각을 추적할 범용 다년 모델은 아직 **미구현**입니다.
- 이 탐색/계산 화면은 현재 브라우저 안에서만 처리하며 서버 전송이 없습니다. RDA 출처의 공식 2024 전국값은 전주 필지 성과나 작목 선정 추천 결과가 아닙니다.
