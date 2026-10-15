# Farm KPI | Jeonju Farm Strategy

**Private decision-support system** for an independent 3,000-pyeong agricultural land project near Jeonju. The established family pear orchard and separate forest mushroom pilot are **not included** in land-profit calculations.

> Research prototype, **NOT** an investment forecast or loan eligibility confirmation.
> Weather variables use derived KMA ASOS Jeonju (station 146) 2006–2025 records. Actual farmgate prices, pest/yield loss functions, contractor quotes, tax, insurance and policy loan eligibility are NOT calibrated.
> **KAMIS is excluded.**

## CLI

```bash
python -m pip install -e '.[dev]'
farm-strategy validate
farm-strategy compare --seed 42 --paths 1000 --stress-matrix --output output/compare-model-only.json --csv output/compare-model-only.csv
farm-strategy evidence-check --file data/templates/private_evidence_TEMPLATE.csv
farm-strategy forecast --plan new_cucumber_house --seed 42 --paths 2000
farm-strategy forecast --plan new_cucumber_house --seed 42 --paths 2000 --monthly-details --output output/monthly-example.json
pytest -q
```

If you have original user-supplied ASOS files, keep them **locally** in `data/raw` (gitignored); do **not** upload them to GitHub. Derived yearly weather records are included for reproducibility.

## Evidence-first execution roadmap

No crop, planting area, greenhouse construction or lease is selected.
The [**8-week indicative decision workplan**](docs/FARM_DECISION_EXECUTION_PLAN.md)
lists CI/data-quality fixes, parcel verification, buyer/net revenue and capital
requirements, generic crop-cycle simulation, and an evidence-gated pilot/decision.
The timetable is contingent on external sources and responses; **unknown is not zero**.

## Source verification and private site intake (Weeks 1–2)

The user-supplied RDA 2024 book was compared with all **51 aggregate
income triplets and 51 labor-page totals**. The reviewed PDF's SHA256
and a canonical 51-row digest are stored as source metadata; the PDF
itself remains **untracked**. Repeat the digest check:

```bash
python scripts/verify_rda_pdf_source.py --check
```

Open the [**offline brown/sage parcel intake form**](dashboard/site-intake/index.html)
locally to enter all 12 site facts and optionally import/export a private JSON.
The form requires no server and does not transmit data.

The [parcel and operations intake guide](docs/RDA_AUDIT_AND_SITE_INTAKE.md)
describes how to record **unknown** usable area, soil/water/power/permit
statuses, 12 months of owner availability and capital limits safely.
There is no crop selection or verified parcel suitability yet.

```bash
cp data/templates/private_site_intake_TEMPLATE.json data/private/site-facts.json
farm-strategy site-check --file data/private/site-facts.json --output output/site-status-redacted.json
```

The report contains only missingness and gate status counts. Private facts
cannot be imported into the tracked crop dashboard or hypothetical
five-plan model through this command.

## Crop discovery: 51 open options, no crop selected

**No crop type, planting area split, facility decision, or harvesting schedule is
currently selected.** The five existing potato/scallion/cucumber strategies are
illustrative model examples only, not a recommended shortlist.

Open [the 51-crop offline explorer](dashboard/crop-discovery/index.html):
browse all seven RDA survey categories, filter/search, compare published
2024 per-10a gross receipts, operating/management costs, income and
owner/hired work hours. The page uses the existing brown-and-sage design,
with a source-referenced clickable plot; it **does not** rank the crops
as real 3,000-pyeong investment alternatives or auto-apply reported prices.

The tracked 51-crop dataset is
[`data/reported/rda_2024_all_51_crop_candidates.csv`](data/reported/rda_2024_all_51_crop_candidates.csv).
The workflow is explained in
[`docs/CROP_DISCOVERY_PROTOCOL.md`](docs/CROP_DISCOVERY_PROTOCOL.md).
2024 nominal incomes are third-party reported reference values (R),
not 2026-real or new-facility NPV. The 4-year ginseng entry is not
annualized. These 51 are **all crops in the provided 2024 report**,
not every possible crop/planting system in Korea.

```bash
python scripts/refresh_crop_discovery.py --check
# Refresh only when the source registry has been reviewed and changed:
python scripts/refresh_crop_discovery.py --refresh
```

## Before choosing a crop: evidence-readiness board

Open [the 51-crop parcel-feasibility checklist](dashboard/feasibility/index.html)
after viewing the statistical crop explorer. All **51** alternatives remain open:
2024 national income/management-cost/labor observations are R reported values,
**not** plot-specific suitability or 2026-real investment NPV.

The new browser-only board tracks **eight always-unknown parcel evidence gates**:
soil/drainage, irrigation, plot crop climate, land-use restrictions,
initial investment quotes, peak monthly work, buyer/net settlement,
and cultivable area/rotation. Facility labels, orchard labels and the
four-year ginseng crop require additional, **not automatically satisfied**,
reviews. Interested crops, self-attested status changes and non-sensitive
notes can be exported to a **local private JSON**; no user data is uploaded.

Source-derived, fully **unknown-first** checklist CSV:
[`data/derived/crop_readiness_51.csv`](data/derived/crop_readiness_51.csv).
Verification command: `python scripts/build_feasibility.py --check`.
The editable HTML template and builder are included for reproducibility;
CI fails if the source and offline page drift. See
[`docs/CROP_SITE_READINESS.md`](docs/CROP_SITE_READINESS.md) for
official portal links to soil mapping, land-use rules and observed climate.
**No crop, site suitability or financing decision has been approved.**

## Offline treemap dashboard

Open [dashboard/index.html](dashboard/index.html) locally in a browser.
The **brown + sage** dashboard uses two embedded SVG treemaps; it does not need a CDN,
Plotly or a running web server. Click any group or leaf to inspect descriptions,
switch between the six model-only scenarios, and change the KPI comparison view.

The tracked dataset is [dashboard/data/screening-model-only.csv](dashboard/data/screening-model-only.csv):
**seed 42, 300 paired paths, recent10, 6 scenarios x 5 plans**. It is an
illustrative model output, **not an observed farm result**.

Regenerate and verify the static offline page after changing the model:

```bash
farm-strategy compare --seed 42 --paths 300 --window recent10 --stress-matrix \
  --output output/screening-model-only.json \
  --csv output/screening-model-only.csv
python scripts/build_dashboard.py --csv output/screening-model-only.csv \
  --html dashboard/index.html --check
# When the check says stale, review the changes before accepting new assumptions:
python scripts/build_dashboard.py --csv output/screening-model-only.csv \
  --html dashboard/index.html --output output/farm-kpi-dashboard.html
```

The GitHub Actions workflow runs the same check and publishes
`farm-kpi-dashboard.html` as a downloadable **CI artifact**.
If accepting a deliberate model change, update the tracked CSV snapshot
and HTML together, then review the diff. Do not publish raw/private
farm receipts, land addresses, or source hourly observations.

## Uploaded RDA benchmark (R: reported statistic, not actual receipts)

Public 2024 crop-income benchmarks for spring/autumn potatoes, field scallion,
and greenhouse cucumber are recorded in read-only
[`data/reported/rda_2024_crop_income_10a.csv`](data/reported/rda_2024_crop_income_10a.csv);
the model-to-OpenAPI identifiers (codes only, **not** live API data) are in
[`data/reported/rda_income_api_crop_crosswalk.csv`](data/reported/rda_income_api_crop_crosswalk.csv).
All 2024 numbers are **nominal KRW per 10a / one crop**, not 2026-real
KRW 10,000 for your farm; existing finance assumptions remain unchanged.

See [`docs/RDA_2024_SOURCE_REVIEW.md`](docs/RDA_2024_SOURCE_REVIEW.md)
for original PDF pages, key accounting mismatches, 2026 method/form status,
and the notable arithmetic match between 300-pyeong cucumber receipts and
the existing hypothetical configuration.

## Private evidence calibration preview (review-gated)

To compare candidate crop receipts, actual field costs, labor quotes or
greenhouse construction quotes with the *hypothetical* baseline, use
[`docs/PRIVATE_CALIBRATION_PREVIEW.md`](docs/PRIVATE_CALIBRATION_PREVIEW.md).

An independent human review and SHA256-locked local manifest are **required**
before running `farm-strategy calibration-preview`. It creates only ignored
`output/calibration/what-if-config.json` and `what-if-impact.json`;
`configs/base.json` and the published brown-and-sage dashboard remain unchanged.
This is a self-attested **what-if** calculation, not authentication of farm
transactions or a validated investment forecast. All committed tests use
**synthetic-only** receipts/quotes.

## Model scope

- **Land:** 3,000 pyeong independent from the pear orchard; no crop yet chosen. Potato/scallion and cucumber greenhouse models are illustrative trials only.
- **Observed:** ASOS year-level weather patterns sampled as whole years; retain hot/wet/cold correlation.
- **Hypothetical:** pest occurrence/damage, prices, greenhouse quote, hired labor rate, taxes and insurance.
- **Accounting:** distinguish pre-financing project NPV, equity cashflow and owner-hours opportunity cost. Own work is **not** a cash labor expense. Loan principal is **not** business revenue.
- **Investment policy:** no large greenhouse build or new borrowing until actual project quotes, working capital, labor cover and buyers are validated.

## Monthly financing and liquidity (scenario assumptions)

Scenario summaries report both annual year-end and month-end **minimum starting cash buffers** (2026-constant KRW 10,000). Optional `--monthly-details` exports 120 months from **one seeded sample path**, not a median or verified cash budget. Month-of-sale, costs, build payments and loan-draw schedules are assumptions defined in `configs/base.json`.

The hypothetical 1.5% **nominal** loan uses an assumed 2% annual inflation deflator when combined with 2026-constant project cashflows. Nominal draw, repayment and outstanding debt remain separately visible. A monthly cash buffer is not evidence of eligibility for financing, nor is it a validated working-capital requirement.

## Governance

1. Data quality levels: Observed (O), external reported statistics (R), real transactions (T), assumption (A).
2. Each investment decision gets a dated decision record and sensitivity analysis.
3. CI tests run on pushes and pull requests. There is **no monthly scheduled workflow** and no automatic live-observation retrieval or investment execution.
4. Never commit exact private land addresses, IDs, bank records, personally uploaded hourly ASOS originals, or API credentials.

See `docs/ASOS_AUDIT_AND_ROADMAP.md` for the data audit, unresolved assumptions, and next steps.

**Units**: monetary cash figures are 2026-constant KRW 10,000; time range 2027–2036. End-year nominal debt is labeled separately. Nominal loan cash is deflated using an unverified 2% annual inflation assumption and discounted on the existing real-rate basis; the bank's actual payment schedule and real input calibration remain unresolved.

See [strategy comparison and private evidence intake](docs/STRATEGY_COMPARISON_AND_EVIDENCE.md) for model-only risk comparisons, CSV outputs, and how to prepare private source evidence without overwriting scenario assumptions.
