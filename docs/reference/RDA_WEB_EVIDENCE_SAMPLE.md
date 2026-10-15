# 2022–2023 농사로 웹 실측(보고) 수치 시범 확인

**목적:** 원문 HTML에 표시된 소득 상세표를 **정밀 수치(원/10a)** 수준으로 안전하게 수집하고, 공표 여부·빈 표·PDF 독립 대조 여부를 구별합니다. **대상:** 공공통계 조사·데이터 검증 담당. **상태:** 2026-10-15 기준 **전국 5행 웹 화면에서 확인 / 1개 코드·연도 조합 상세 행 미표시**. 이 자료는 아직 PDF 기반 51작목 장기형 통계가 아닙니다.

## 실제로 읽은 웹 표

| 작목(2024 기준 ID) | 2022 전국 | 2023 전국 | 자료 범위 |
| --- | --- | --- | --- |
| [사과](../../data/reported/rda_web_2022_2023_sample.csv) · RDA2024-37 | 수치 표 확인 | 수치 표 확인 | **성목과수 보고 결과**, 신규 식재 후 수익 추정 금지 |
| 노지쪽파 · RDA2024-18 | 수치 표 확인 | 수치 표 확인 | 농사로 표시명은 '쪽파'; 작형 동일성 추가 검증 필요 |
| 시설오이 · RDA2024-24 | 해당 조회 코드에서 상세 행 미표시 | 수치 표 확인 | **2023년 작형 통폐합 및 수경/토경 분리** 전후 같은 조사대상인지 확인 필요 |

숫자·연도별 URL·원/10a 금액·수량·가격 단위는 [시범 CSV](../../data/reported/rda_web_2022_2023_sample.csv)에 있습니다. [브라운·세이지 오프라인 표본 화면](../../dashboard/source-coverage/index.html)에서 연도/작목과 원문을 확인할 수 있습니다. 이 표의 작목 3개는 기술 검증용 표본이지 투자·추천 대상 목록이 아닙니다.

### 근거 페이지

- [농사로 시각화 — 2022 사과 전국](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696054&menuId=PS65441&upperCode=696004&year=2022)
- [농사로 시각화 — 2023 사과 전국](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696054&menuId=PS65441&upperCode=696004&year=2023)
- [농사로 시각화 — 2022 쪽파 전국](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696031&menuId=PS65441&upperCode=696002&year=2022)
- [농사로 시각화 — 2023 쪽파 전국](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696031&menuId=PS65441&upperCode=696002&year=2023)
- [농사로 시각화 — 2022 시설오이 전국, 상세 행 미표시](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696078&menuId=PS65441&upperCode=696003&year=2022)
- [농사로 시각화 — 2023 시설오이 전국](https://nongsaro.go.kr/portal/ps/psb/psbf/agricultIncomeInfoLst.ps?areaCode=697001&lowerCode=696078&menuId=PS65441&upperCode=696003&year=2023)

전부 **R: 농촌진흥청 보고 통계**입니다. 현재 `pdf_crosscheck_status=NOT_PDF_CROSSCHECKED`, `labor_status=NOT_CAPTURED`입니다. 공식 시각화 표에 없는 시간·PDF 페이지를 지어내지 않으며, 수치가 보이지 않는 행은 `NO_DETAIL_ROW_SHOWN`으로 별도 기록합니다. 이는 해당 해 농산물소득이 0이라는 뜻도, PDF 어디에도 같은 작물이 없다는 뜻도 아닙니다.

농사로 [조사 개요](https://nongsaro.go.kr/portal/ps/psz/psza/contentMain.ps?menuId=PS65442)는 2023년 **6개도 광역조사와 작형 통폐합·수경/토경 분리**를 설명합니다. 2023년 지역 자료집을 전국·전북 동일 표본/동일 조사로 단정하지 않습니다.

**비교 주의:** 2022·2023년 통계는 서로 다른 해의 **명목 원/10a/작기**입니다. 물가 보정·표본 동일성 검증·노동시간 검증 없이 2026 실제 농지 사업 NPV, 수익률, 위험도나 최적 작물을 계산하지 않습니다. 시설오이는 2022 동일 코드에서 수치를 보지 못해 2023만 존재합니다. 2024 전국 51개 기존 잠금 데이터는 수정되지 않았습니다.

## 검사·승격 문턱

```bash
python scripts/check_rda_web_sample.py --check
python scripts/build_rda_web_sample_board.py --check
python -m pytest -q tests/test_rda_web_sample.py tests/test_rda_web_board.py
```

- URL의 `year`·`areaCode=697001`·작목 코드 및 작기 상태, 수입−경영비≈소득, 수입·경영비·소득·수량·가격 **다섯 수치의 기존 캡처 잠금**, 미표시 행의 **빈 숫자**, PDF 대조 미실시 상태를 검사합니다. 잠금 확대는 기록 변조 탐지이며 새로운 원문/PDF 검증이 아닙니다.
- 지역별 2022/2023 전북 구체 수치를 합성하지 않습니다. 지역 단위는 원문 HTML 또는 **지역별 PDF 쪽수/조사 시스템**을 별도로 대조한 뒤에만 도입합니다.
- 2022/2023 PDF의 일치하는 작목·작형·고용/자가 노동·책 페이지와 조사 대상의 일관성을 검증하고, 출처 레지스트리 `NOT_TRANSCRIBED` 상태 변경을 독립 리뷰해야 [장기형](../../data/reported/rda_income_long.csv)에 승격할 수 있습니다.
- 이 화면은 웹 세부 수치의 **결측·커버리지 표시용**입니다. 51개 작목 탐색기 순위나 기존 모델 설정을 자동 변경하지 않습니다.

공공누리 제2유형의 상업적 이용 제한 및 출처표시 조건을 원문별로 확인해야 합니다. 정확한 지번·실거래·개인정보는 저장하지 않습니다.
