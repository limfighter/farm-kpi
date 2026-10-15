# 빠른 시작: 저장소와 문서·데이터 검사

**대상:** 새 개발 세션이나 저장소를 처음 여는 사람  
**목표:** 작물을 선정하지 않고 소스·문서·대시보드의 일관성을 재현합니다.

## 준비

- Python **3.11**(CI와 동일한 버전)과 Git 필요.
- 비공개 저장소 접근 권한 필요. GitHub에 연결된 작업 환경에서 `limfighter/farm-kpi`의 **최신 `main`**을 확인합니다.
- 정확한 농지 주소·영수증·원본 API 키는 이 저장소에 커밋하지 마세요.

## 1. 실행환경

\`\`\`bash
git clone git@github.com:limfighter/farm-kpi.git
cd farm-kpi
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
\`\`\`

> 비공개 저장소 인증 방식은 GitHub 사용자 환경에 맞게 설정하세요. 공개 저장소처럼 접근 가능한 것은 아닙니다.

## 2. 첫 검증

\`\`\`bash
python -m pytest -q
python scripts/check_docs.py --check
python scripts/refresh_crop_discovery.py --check
python scripts/build_feasibility.py --check
python scripts/verify_rda_pdf_source.py --check
farm-strategy validate
\`\`\`

**예상 결과:** 모든 검사 종료코드 0. 2024 RDA 원본 PDF는 저장소에 없으며 `verify_rda_pdf_source.py --check`는 저장된 크롭 51개 행의 대조 기록 해시만 확인합니다. PDF 내용을 처음부터 다시 대조하려면 [현장·원본 감사 지침](../RDA_AUDIT_AND_SITE_INTAKE.md)을 따르세요.

## 3. 보이는 결과 열기

- [51개 작목 탐색기](../../dashboard/crop-discovery/index.html) — 2024 전국 통계 기반.
- [작목별 8개 준비도 질문](../../dashboard/feasibility/index.html) — 필지별 적합성 전부 미확인.
- [농지 공통 12개 질문 입력](../../dashboard/site-intake/index.html) — 로컬 JSON 다운로드; 서버에 보내지 않음.
- [기존 5개 예시 전략 트리맵](../../dashboard/index.html) — 수익성 검증 아닌 가상 결과.

HTML을 로컬 브라우저에서 열 수 있으며, 별도 서버·외부 CDN이 필요하지 않습니다.

## 4. 비식별 개인용 현장 자료 예시

\`\`\`bash
mkdir -p data/private output
cp data/templates/private_site_intake_TEMPLATE.json data/private/site-facts.json
farm-strategy site-check \\
  --file data/private/site-facts.json \\
  --output output/site-status-redacted.json
\`\`\`

**예상 결과:** 12개 검증 항목이 모두 UNKNOWN인 **비식별 현황 요약**. 값이 없다면 `null` 유지, 임의로 0을 입력하지 않습니다. 실제 토지의 적합/부적합 판정은 이루어지지 않습니다.

## 5. 실패하면 확인할 것

| 오류 | 확인 |
| --- | --- |
| `ModuleNotFoundError` | 가상환경 활성화, `pip install -e ".[dev]"` |
| 작목 HTML `STALE` | CSV가 변경되었는지 diff 확인. [RDA 갱신 절차](UPDATE_REPORTED_DATA.md) 없는 자동 덮어쓰기 금지 |
| PDF 행의 SHA 불일치 | 데이터 출처와 실제 PDF 대조를 다시 실시하고 변경 근거 확인 |
| `site-check` 검증 실패 | [현장 조사표 구조](../RDA_AUDIT_AND_SITE_INTAKE.md); 주소·개인정보 필드나 단위 오류 확인 |
| CI 실패 | GitHub Actions에서 **현재 커밋**의 첫 실패 단계를 검토, 테스트 무력화 금지 |

**다음 시작점:** [프로젝트 상태](../STATUS.md)에서 현재 차단사항을 확인하고 [세션별 실행 계획](../sessions/README.md)에서 선행조건에 맞는 작업을 골라 이어가세요.
