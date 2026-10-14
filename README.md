# Farm KPI | Jeonju Farm Strategy

**Private decision-support system** for an independent 3,000-pyeong agricultural land project near Jeonju. The established family pear orchard and separate forest mushroom pilot are **not included** in land-profit calculations.

> Research prototype, **NOT** an investment forecast or loan eligibility confirmation.
> Weather variables use derived KMA ASOS Jeonju (station 146) 2006–2025 records. Actual farmgate prices, pest/yield loss functions, contractor quotes, tax, insurance and policy loan eligibility are NOT calibrated.
> **KAMIS is excluded.**

## CLI

```bash
python -m pip install -e '.[dev]'
farm-strategy validate
farm-strategy compare --seed 42 --paths 1000 --output output/compare.json
farm-strategy forecast --plan new_cucumber_house --seed 42 --paths 2000
pytest -q
```

If you have original user-supplied ASOS files, keep them **locally** in `data/raw` (gitignored); do **not** upload them to GitHub. Derived yearly weather records are included for reproducibility.

## Model scope

- **Land:** 3,000 pyeong independent from the pear orchard; spring potato and scallion trials, candidate cucumber greenhouse (build vs lease).
- **Observed:** ASOS year-level weather patterns sampled as whole years; retain hot/wet/cold correlation.
- **Hypothetical:** pest occurrence/damage, prices, greenhouse quote, hired labor rate, taxes and insurance.
- **Accounting:** distinguish pre-financing project NPV, equity cashflow and owner-hours opportunity cost. Own work is **not** a cash labor expense. Loan principal is **not** business revenue.
- **Investment policy:** no large greenhouse build or new borrowing until actual project quotes, working capital, labor cover and buyers are validated.

## Governance

1. Data quality levels: Observed (O), external reported statistics (R), real transactions (T), assumption (A).
2. Each investment decision gets a dated decision record and sensitivity analysis.
3. CI tests run on changes. A monthly scheduled workflow checks model consistency; **it does not fetch live observations or make autonomous investments**.
4. Never commit exact private land addresses, IDs, bank records, personally uploaded hourly ASOS originals, or API credentials.

See `docs/ROADMAP.md`, `docs/DATA_POLICY.md` and `docs/decisions/`.

**Units**: monetary figures are 2026-constant KRW 10,000; time range 2027–2036. Nominal loan rate vs real discount-rate modeling is a known limitation to be fixed.
