# ASOS v10 intake and farm-kpi next steps (2026-10-15)

## Data inventory / line of evidence
- Repository: existing Python package farm_strategy; active simulation plans field_trial, pause_after_trial, new_cucumber_house, leased_cucumber_house, new_cucumber_premium. The ten requested alternatives A-J and forestry/mushroom model are **not** complete.
- Supplied v10 ZIP: daily, annual, ASOS-vs-ERA5, price/damage simulation tables, spreadsheet, run_v10.py, build_v10.py, archived test, archived audit JSON, plus nested v9 reference model and ERA5 features. Earlier v1-v8 artifacts **not supplied**.
- Supplied 20-year annual CSV byte-identical to ZIP annual CSV. 20 annual records, 7,305 calendar days. The older repository annual_weather.csv is the 11-feature subset of that annual data.
- Hourly observations **not supplied** in this handoff; original 43 CP949 CSV files and their real QC are not independently rechecked. Archived v10 audit **reports**, not proves anew, 175,319 of 175,320 hours and missing 2015-06-27 05:00.
- The derived daily CSV (7,305 rows) is available in the supplied v10 ZIP, deliberately not copied to the repository; it is optional input to the audit command. No original hourly records or private addresses are committed.

## Verified from submitted derived annual + daily data
| Year window | May-Sep days >=33 C | Mar-Apr days <=0 C | May-Sep days with recorded rain >=40 mm |
| --- | ---: | ---: | ---: |
| 2006-2015 | 14.9 | 12.7 | 7.7 |
| 2016-2025 | 19.7 | 4.7 | 7.4 |

Rain measures are **observed reported-value lower bounds**. Blank hourly rain and QC8/QC9 must not be replaced with 0. KMA ASOS daily totals need reconciliation before interpreting the rainfall thresholds as complete counts. KMA hourly Tmax/Tmin from >=20 valid hours is not the same as official daily extrema. Neither historical weather correlations nor Monte Carlo repetitions validate crop yield loss coefficients.

## Accounting / validation notes
- **Fixed in model**: 2036 outstanding loan principal is not silently deducted from the 2036 *cash* column. Financial diagnostics now distinguish realized equity cash-flow NPV from equity NPV adjusted for unpaid terminal principal.
- **New monthly liquidity calculation:** 120 month-end equity cashflow entries are allocated from the same annual scenario amounts. The reported monthly liquidity buffer is the largest negative cumulative **month-end** balance starting at zero, alongside the existing annual year-end buffer. The ledger exactly reconciles to annual revenues, costs, capex, loan draws and repayments. This is **not** a validated working-capital forecast: within-month cash gaps, credit lines, seasonal planting invoices, and actual buyer payment delays remain unknown.
- Owner hours constrain actual hired labor and are excluded from cash expenses; their opportunity value affects economic NPV only.
- **Nominal/real conversion fixed as an accounting convention:** loan_cash still computes nominal contractual payments and nominal year-end debt. New annual loan draw and payment fields are deflated into 2026-constant KRW using `finance.assumed_annual_inflation_rate = 0.02` (an illustrative inflation assumption, not observed or a forecast). Original nominal amounts are exposed as `loan_draw_nominal`, `loan_payment_nominal` and `debt_end`; the real end-of-horizon liability is discounted at the existing real 5% rate. Debt is not booked as an invented 2036 cash outflow.
- Owner hours are excluded from cash expenses and included as an opportunity cost only in economic NPV. Taxes, insurance, asset life, subsidies, sale prices, legal status and actual loan terms remain unvalidated assumptions. The inflation/loan conversion is internally consistent but still depends on hypothetical inflation and nominal loan terms. A positive illustrative NPV is **not** approval to invest.
- The baseline simulation remains **five preliminary plans**, not a validated ranking among the requested A-J candidates.

## Reproducible work
1. Run baseline: pip install -e ".[dev]" ; pytest -q ; farm-strategy validate.
2. Audit checked-in v10 annual: python -m farm_strategy.audit --annual data/processed/annual_asos_jeonju_2006_2025.csv --metadata data/metadata/asos_v10_archive_audit.json
3. Optionally extract daily_asos_jeonju_2006_2025.csv from v10 ZIP to local data/processed/ and add --daily data/processed/daily_asos_jeonju_2006_2025.csv.
4. On *private local* original 43 files, run python -m farm_strategy.hourly data/raw/OBS_ASOS_TIM_*.csv --output output/hourly-audit.json; inspect any conflicts and compare with archived v10 audit. This command audits raw hours/QC but does not yet regenerate daily and annual aggregates.
5. Compare existing options: `farm-strategy compare --seed 42 --paths 1000 --output output/compare.json`. Scenario summaries now include `monthly_liquidity_buffer_required` (p10, median, p90; the buffer is a model-defined amount, not validated credit need).
6. Inspect all 120 months in **one illustrative stochastic path**, not a Monte Carlo median: `farm-strategy forecast --plan new_cucumber_house --seed 42 --paths 1000 --monthly-details --output output/house-months.json`. The `illustrative_monthly_path.months` rows are in 2026-constant KRW 10,000. A single random path should not be interpreted as the likely month-by-month budget.

## Priorities
1. Obtain official KMA ASOS daily precipitation and original hourly CP949 source to reconcile missing/zero/QC semantics and reconstruct features independently.
2. Obtain actual crop grade-level farm-gate receipts (net of market fee, transport, packaging), sales channel terms, yield and NCPMS occurrence data. No KAMIS.
3. Obtain greenhouse build and lease bids, 3,000-pyeong land status, monthly orchard labor schedule, financing cash terms, taxes/insurance, grants approvals. Never assume subsidy or loan approved.
4. Replace **assumed** monthly sales/expense allocation weights and March capex/loan draws, December debt service, August repairs and December salvage/deposit return with actual buyer/contractor/bank transaction schedules. Add within-month cash timing, payroll due dates, delayed settlements, historical farm accounting calibration, risk stress tests and area optimization. Separate forest/shiitake legal and financial model.
5. Maintain scenario input metadata and unit/invariance regression tests; publish none of the personal hourly/land/financing originals.

## Monthly model timing assumptions (not empirical)
- Revenue weights in `configs/base.json > monthly_cashflow`: potato 75% June / 25% July; scallion 10% April, 15% May, 15% June, 20% September, 25% October, 15% November; cucumber 10% May, 20% June, 20% July, 20% August, 20% September, 10% October. Crop operational costs are allocated in proportion to each crop's pre-existing monthly labor requirements; fixed costs and unresolved tax/insurance placeholders are spread evenly. Hired labor follows modeled monthly shortages.
- Initial land/greenhouse/lease expenditure and hypothetical nominal loan draw are placed in March; nominal annual debt service is represented as a **December** payment; major repairs in August; terminal salvage and returned lease deposit in December 2036. These dates are accounting conventions, not verified contracts.
- All seasonal revenues, operating outlays, project capex and salvage are treated as constant 2026 KRW. Nominal debt draws, repayments and outstanding balance are converted using a hypothetical 2% per-year deflator starting in 2026. The 5% real discount factor remains anchored to the first modeled year, 2027, matching earlier NPV conventions.
- `monthly_liquidity_buffer_required >= annual_liquidity_buffer_required` by construction when sampled on the same path. Both assume no starting cash, no overdraft facility and no within-month timing; neither is a credit recommendation.
