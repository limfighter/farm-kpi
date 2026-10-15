# 농촌진흥청 보고자료 갱신 절차

**목적:** 공식 새 연도/지역 데이터가 들어왔을 때 **출처·단위·조사작기를 유지**하며 탐색기를 갱신합니다.  
**전제:** 공개 PDF, 사용 가능한 API 원문 또는 동일한 신뢰 수준의 기관 공표 자료가 실제로 확보되어 있어야 합니다.

## 실무 절차

1. [현재 상태](../STATUS.md)에서 필요한 기간/지역과 자료 공백 확인. 기존 \`data/reported/rda_2024_all_51_crop_candidates.csv\`는 **2024년 스냅샷**이며, 2025 숫자로 덮어쓰지 않습니다.
2. 먼저 [공식 전국·지역 출처 등록부](../reference/RDA_MULTYEAR_SOURCE_REGISTRY.md)에서 출처 URL과 전사 상태를 확인합니다. **출처 확인만으로 수치 행을 추가하지 않습니다.** 공식 문서의 **기관명, 발행일, 관측·조사연도, 공간 범위(전국/전북 등), 원본 링크/쪽수, 원/10a/작기 기준**을 기록합니다. API 코드표만 있으면 \`CODEBOOK_ONLY\`이며 실적 관측치가 아닙니다.
3. **새 연도·지역 자료**는 우선 별도 long-format 파일/스키마로 작성합니다. 농가의 실제 판매명세서 \`T\`, 서면 견적 \`Q\`와 공공통계 \`R\`를 섞지 않습니다. 없는 작물/연도는 **결측**, 0 아님.
4. 원자료 표의 총수입−경영비≈소득을 확인하고 자가/고용/합계 노동시간, 소득률, 작기 예외, 시설/노지 분류를 기록합니다. **인삼(4년근)**은 4년 1기작.
5. **2024 기준표 자체의 오기 정정**만 필요한 경우, 근거 PDF와 페이지를 독립적으로 검토한 다음 기존 CSV를 수정합니다. 내용이 달라졌으면 SHA 잠금 문서를 새 원본 대조로 갱신해야 합니다.

\`\`\`bash
# 2024 고정 기준표에서 오류를 공식 근거로 수정한 경우에만:
python scripts/refresh_crop_discovery.py --check
# HTML이 STALE라면 수치 diff와 페이지 근거를 검토한 뒤에만:
python scripts/refresh_crop_discovery.py --refresh
python scripts/build_feasibility.py --refresh
# 원본 PDF가 있으면 재검증 및 감사 기록 갱신:
python scripts/verify_rda_pdf_source.py \\
  --pdf data/raw/2024_농산물소득자료집.pdf --write-metadata
# 마지막 검증:
python scripts/verify_rda_pdf_source.py --check
python scripts/check_crop_income_history.py --check
python scripts/check_docs.py --check
python -m pytest -q
\`\`\`

6. 새 연도/지역 데이터 파일은 **개별 출처 확인 후** 카탈로그/스키마, 단위 테스트, 사용자 탐색기와 한 PR에서 연결합니다. 기존 \`configs/base.json\`의 가정값과 모형 현금흐름을 자동 변경하지 않습니다.
7. [현재 상태](../STATUS.md)의 충족·미충족 표, [전체 로드맵](../FARM_DECISION_EXECUTION_PLAN.md)의 미완료 항목을 업데이트하고 PR CI 성공을 확인합니다.

## 완료 기준

- 서로 다른 연도·지역·재배방식·작기의 숫자가 **일단 따로 기록**되고 비교 가능 여부가 명시됨.
- 숫자마다 \`R/O/Q/T/A\` 출처 범주와 단위, 원자료가 연결됨.
- 비슷한 작물 이름이나 가격/수확량 단위로 잘못 결합되지 않음.
- 현장 적합성, 시설 투자비, 재무 NPV 등 **증거가 없는 필드에는 UNKNOWN** 유지.

**주의:** 2024 RDA 통계의 소득은 기존 시설 감가상각과 고용노동을 포함한 *조사 회계*입니다. 신규 신축 CAPEX와 자가노동 기회비용을 별도로 계산하는 모델에 단순 복사하면 이중 계상 위험이 있습니다. [모델 경계](../explanation/MODEL_BOUNDARIES.md) 참고.
