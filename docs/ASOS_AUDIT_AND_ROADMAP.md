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
- The annual liquidity buffer is calculated using **year-end** cumulative modeled cash flows with initial balance 0; it misses within-year/monthly shortages. This is *not* a reliable working-capital forecast.
- Owner hours constrain actual hired labor and are excluded from cash expenses; their opportunity value affects economic NPV only.
- Loan nominal interest and real discount-rate consistency, taxes, insurance, asset life, approved subsidies, crop-specific market prices, producer net sales prices, land tax/legal status, and real pest damage remain unresolved assumptions. A positive illustrative NPV is **not** approval to invest.
- The baseline simulation remains **five preliminary plans**, not a validated ranking among the requested A-J candidates.

## Reproducible work
1. Run baseline: pip install -e ".[dev]" ; pytest -q ; farm-strategy validate.
2. Audit checked-in v10 annual: python -m farm_strategy.audit --annual data/processed/annual_asos_jeonju_2006_2025.csv --metadata data/metadata/asos_v10_archive_audit.json
3. Optionally extract daily_asos_jeonju_2006_2025.csv from v10 ZIP to local data/processed/ and add --daily data/processed/daily_asos_jeonju_2006_2025.csv.
4. On *private local* original 43 files, run python -m farm_strategy.hourly data/raw/OBS_ASOS_TIM_*.csv --output output/hourly-audit.json; inspect any conflicts and compare with archived v10 audit. This command audits raw hours/QC but does not yet regenerate daily and annual aggregates.
5. Compare existing options: farm-strategy compare --seed 42 --paths 1000 --output output/compare.json.

## Priorities
1. Obtain official KMA ASOS daily precipitation and original hourly CP949 source to reconcile missing/zero/QC semantics and reconstruct features independently.
2. Obtain actual crop grade-level farm-gate receipts (net of market fee, transport, packaging), sales channel terms, yield and NCPMS occurrence data. No KAMIS.
3. Obtain greenhouse build and lease bids, 3,000-pyeong land status, monthly orchard labor schedule, financing cash terms, taxes/insurance, grants approvals. Never assume subsidy or loan approved.
4. Add monthly working-capital calendar, labor allocation by crop, historical farm accounting calibration, risk stress tests and area optimization. Separate forest/shiitake legal and financial model.
5. Maintain scenario input metadata and unit/invariance regression tests; publish none of the personal hourly/land/financing originals.
