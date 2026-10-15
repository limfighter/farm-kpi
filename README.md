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

- **Land:** 3,000 pyeong independent from the pear orchard; spring potato and scallion trials, candidate cucumber greenhouse (build vs lease).
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
