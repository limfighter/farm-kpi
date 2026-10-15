# Crop-option site screening: explicit unknowns, not simulated suitability

**Decision status (2026-10-15): no crop, crop area, construction/rent approach or production schedule has been selected.** The crop universe from the uploaded 2024 RDA income report contains **51 surveyed lines**. A nationally reported crop-income observation is not evidence that a particular plot near Jeonju can cultivate or profit from that crop.

## What the new screen actually does

- Browse [the 51-crop readiness board](../dashboard/feasibility/index.html) offline, alongside the preexisting [2024 statistical explorer](../dashboard/crop-discovery/index.html).
- The **eight common evidence gates** are: soil and drainage; water and irrigation; parcel-specific crop weather; land-use restrictions and permits; real startup capex; peak monthly labor; buyers/net settlement; and plot area/rotation/season sequence.
- For **19 protected-cropping labels** (17 facility vegetables, 1 facility fruit, and 1 facility rose), the category label triggers a **facility infrastructure investigation**, NOT a conclusion that a greenhouse can be built.
- For **10 orchard labels** (9 field and 1 facility fruit), request **establishment-year funding and immature-tree revenue timing** before using mature-orchard averages.
- For **four-year ginseng**, request a **multi-year crop-cycle cashflow**; never divide the published entire-cycle income by four and call it actual annual cash.
- All source-derived crop labels and income/labor statistics remain `R` reported reference data, **2024 nominal KRW per 10a**, not 2026-real farm revenue or lender-verified collateral.
- All eight *parcel-specific* checks start with `UNKNOWN_NOT_EVALUATED`, for every one of the 51 crops. The board does not invent costs, weather damage percentages, construction budgets or suitability scores. A category flag `CATEGORY_NOT_FLAGGED` is **not** a statement that a facility or establishment is unnecessary.

## Candidate notes and privacy

The browser lets a reviewer mark any crop as **interested**, change gate labels to `FOLLOWUP_NEEDED`, `DOCUMENT_COLLECTED_UNVERIFIED`, or `NOT_FEASIBLE_USER_ASSERTED`, and type local, **non-sensitive** notes. These are *reviewer assertions* (not authenticated project facts), kept in volatile browser state until the page is closed/refreshed. **Nothing is sent to GitHub or a server**. The “개인 검토기록 JSON 저장” control downloads an optional private JSON file containing these notes. Store it locally; do not commit this exported JSON or enter addresses, contact details, account numbers or private land identifiers.

A source document, survey area and year, crop and plot correspondence, actual water and power access, and verified written quotes are still required to move from ‘notes recorded’ to an investment decision. **No crop automatically passes** because a report has high income per 10a or because a reviewer marks a checklist item “자료 확보.”

## Independent official sources for the next information request

| Area | Official information resource | Use, and its limits |
| --- | --- | --- |
| Soil type, drainage and crop-specific suitability | [농촌진흥청 흙토람 – 작물별 토양적성도](https://soil.rda.go.kr/soilmap/crop.do) | The GIS shows suitability **classes based on soil/environment variables**, not investment feasibility or actual plot yield. Requires parcel-specific lookup and soil testing where appropriate. |
| Land-use designations, restrictions and administrative checks | [토지이음 – 주요 서비스](https://www.eum.go.kr/web/am/visit.jsp) | Identify zoning and listed use restrictions. Any greenhouse or building permission must be confirmed with the appropriate authority, not inferred solely from a generic category. |
| KMA station weather histories | [기상청 – 종관기상관측(ASOS) 안내](https://www.kma.go.kr/kma/public/adm/open_01.jsp?s=4) | Station observations are not a crop-specific weather damage function or parcel microclimate. Verify climate thresholds and water/thermal requirements separately. |
| Crop income, management costs, labor | User-provided *2024 농산물소득자료집* (summary PDF pp. 17–19; labor PDF pp. 127–177) | 51 sampled national cropping systems at 10a reference scale, not local net farm profits, actual buyer contracts or startup capex. |

The official portals establish **where to check**. The user has not provided a plot identifier, soil analysis, water-rights documents, energy hookup, crop calendar, builder quotes or sale agreements. No parcel-level suitability grade is asserted here.

## Repeatable build and checks

```bash
python scripts/build_feasibility.py --check
# Only after reviewing changes to source crop reports:
python scripts/build_feasibility.py --refresh
pytest -q
```

- Source: `data/reported/rda_2024_all_51_crop_candidates.csv` (51 R observations).
- Generated, non-sensitive checklist registry: `data/derived/crop_readiness_51.csv` (no invented numeric suitability).
- Static source template: `dashboard/feasibility/template.html`.
- Offline generated dashboard: `dashboard/feasibility/index.html`.
- Both CSV and HTML are audited in CI for source synchronization.

**Not in scope yet:** claims of a winning crop, whole-3,000-pyeong profit projections, line-item electricity/heating quotes, buyer selection, greenhouse permit approval, regional crop-response curves, proof of actual site suitability or revised five-plan Monte Carlo assumptions.