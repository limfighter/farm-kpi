# Model-only five-plan screening and real-evidence intake

> Research prototype as of 2026-10-15. No recommendation to build a greenhouse,
> borrow, lease a facility or plant a crop follows from positive model output.

## Reproduce comparison

```bash
python -m pip install -e '.[dev]'
farm-strategy validate
farm-strategy compare --seed 42 --paths 1000 --window recent10 --stress-matrix \
  --output output/strategy-comparison-model-only.json \
  --csv output/strategy-comparison-model-only.csv
pytest -q
```

The CSV has one plan per stress scenario, with model-only downside fractions
and a separate 90th-percentile monthly liquidity buffer column. The JSON additionally
contains the paired path-by-path deltas relative to `field_trial`. A smaller
300-path version is produced as a **CI artifact**, not as audited investment data.

## Only five preliminary plans exist

- `field_trial`: potato and scallion field cultivation.
- `pause_after_trial`: stop after the first year.
- `new_cucumber_house`: construct greenhouse in 2028.
- `leased_cucumber_house`: lease greenhouse in 2028.
- `new_cucumber_premium`: unverified 30% cucumber revenue uplift plus extra costs.

The separately discussed A–J alternatives and forest/mushroom enterprise are
not implemented and must not be compared to these five as if covered.

## What is fairly compared?

Every plan in the same trial receives the same whole historical weather year
(such as heat/wet/frost features), same common and crop-specific *synthetic*
price draws, pest draws and major-repair draw. Unconditional consumption of
the repair random variate ensures paths do not drift after a plan switches
from fields to facilities. Scenarios reuse the same trial seeds.

The paired delta is `alternative value - field_trial value` **for each
matching trial**, summarized by p10/median/p90. This does not mean that
farm yields have empirically established probabilistic distributions.

The overview reports distinct, non-interchangeable dimensions:

| Output | Interpretation |
| --- | --- |
| `project_npv` | 2027–2036 project cash NPV before financing |
| `economic_npv` | project NPV after imputed owner-hours opportunity cost |
| `equity_terminal_liability_adjusted_npv` | equity cash NPV less discounted terminal outstanding principal |
| `monthly_liquidity_buffer_required` | worst **month-end** cumulative cash gap with zero opening cash, not a loan recommendation |
| `cash_2030_after_debt` | 2030 modeled real equity cashflow |
| `negative_fraction_model_only` | fraction of Monte Carlo paths below zero **under assumptions**, not real-world failure probability |

For NPV and 2030 cash, p10 indicates model downside. For the required
month-end buffer, **p90 is the larger-stress funding need**. All monetary
units use 2026-constant KRW 10,000 except the explicitly labeled **nominal**
end-of-horizon debt. The `illustrative_order_by_economic_npv_median` field
is a mechanical sort, NOT a choice, investment ranking or feasible portfolio.

The baseline includes a *hypothetical* 1.5% nominal loan and assumed 2%
inflation deflator. Crop sale timing, facility quotes, prices, damage functions,
tax and insurance are not calibrated. KAMIS data are excluded.

## Actual source documentation before replacing assumptions

The project cannot truthfully replace scenario numbers with actual farm results
until original source evidence is supplied and independently reviewed.

1. Copy `data/templates/private_evidence_TEMPLATE.csv` into a local,
   Git-ignored file such as `data/private/my_evidence.csv`. Do not commit it.
2. Enter candidate rows with:
   `model_key,source_kind,observation_date,period_label,value_2026_constant,unit,reference_id`.
   Each number must have a disclosed scope and unit, including farm area/crop
   grade/year and fee treatment in separate local documentation.
3. `source_kind`: **T** = actual paid/settled farm transaction, **Q** =
   written quote (NOT a transaction), **R** = reported external statistic,
   **O** = measured observation. A quote or unverifiable reference is not
   proof of actual profit, even if the CSV is syntactically valid.
4. `value_2026_constant` is a 2026-real amount in units of KRW 10,000
   (`KRW_10000_2026_constant`); hired-hour rates use
   `KRW_10000_per_hour_2026_constant`. Do not pass nominal receipts of a
   different year without documenting the conversion to 2026 constant KRW.
5. For price/revenue model keys, actual **net sales receipts** should be
   normalized to the same planted area, yields, crop grade, season and
   transport/packing/market-fee accounting as the modeled baseline.
   For facility costs use written construction and rent quotes with a dated
   payment timetable; document taxes, loan fees and optional subsidies
   separately rather than assuming approval.
6. Run `farm-strategy evidence-check --file data/private/my_evidence.csv`.
   This checks metadata and completeness **only**. It does not authenticate
   sources, read invoices, alter `configs/base.json`, or replace any output.
7. Review originals privately, reconcile outliers and multiple transactions,
   and record source-specific methodology and date in a dated decision record
   **before** any separately reviewed configuration change.

Never commit raw hourly ASOS data, exact parcel addresses, bank details,
personal identifiers, scanned invoices or private settlement statements.
Leave the confidential originals local or in separately authorized storage.

## Blocking issues before real investment

- Independently verify KMA ASOS source data and rainfall missing/QC logic.
- Source farmgate net receipts, expected yields and lost-crop evidence.
- Obtain dated builder/landlord quotes, lender's contractual monthly
  schedule and actually available grants/subsidies, if any.
- Check 3,000-pyeong field versus 300-pyeong cucumber-unit scale.
- Model cash needs within each month and buyer settlement delays.
- Re-run stress comparisons only after assumption-to-evidence replacements
  are reviewed and all regression tests pass.
