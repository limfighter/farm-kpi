# Crop discovery: no crop or cultivation method preselected

**Decision stage:** candidate discovery. The 3,000-pyeong independent land project
near Jeonju does NOT yet have confirmed crop species, acreage by crop, cropping
sequence, greenhouse infrastructure, labor plan or sales channel.

The five existing Monte Carlo strategies using potatoes, scallions and greenhouse
cucumbers remain **illustrative prototypes**, not a selected farming plan.
The family pear orchard and separate forest shiitake project remain excluded
from the independent parcel's revenue and investment accounting.

## Breadth: all crops in the supplied comparable source, not all possible Korean agriculture

The user supplied RDA's **2024 농산물소득자료집**. The crop overview pages
(PDF 17–19; printed 11–13) contain **51** observed/surveyed crop lines across:

| Report category | Crops |
| --- | ---: |
| Food / grain `식량작물` | 7 |
| Field vegetables `노지채소` | 12 |
| Protected vegetables `시설채소` | 17 |
| Field fruit `노지과수` | 9 |
| Protected fruit `시설과수` | 1 |
| Flowers `화훼` | 1 |
| Specialty / medicinal `특용·약용` | 4 |
| **Total** | **51** |

The working dataset is
[`data/reported/rda_2024_all_51_crop_candidates.csv`](../data/reported/rda_2024_all_51_crop_candidates.csv).
It records the complete original crop group and name, published gross receipts,
management costs, income, income ratio and yield per 10a, followed by
owner/hired/total hours in the reported work-stage tables (PDF 127–177;
printed 121–171). Each row cites the specific PDF pages.

Source `R` = national published survey-based reference, **not** a personal
farm transaction `T` or a profit forecast for Jeonju. The uploaded
`2026 농산물 소득조사 분석방법.pdf` and questionnaire ZIP are
methodology/templates, **not** measured 2026 income results. The
`농산물소득정보OpenAPI_제공코드.xlsx` is a codebook, not an API
time series. Only four crops have separately matched API codes so far;
unmatched crops are **pending**, not invalid choices.

**Coverage limit:** 51 surveyed crops are not the set of every possible crop,
variety, agritourism activity, processing, intercropping, dual-season operation,
equipment contracting, leased greenhouse or other farming model. Add new
candidates in a separate registry with `source_available=false` or obtain a
comparable official dataset before numerical screening; never invent yield
or income to fill a missing record.

## Why this cannot determine the winning crop today

- **Source accounting:** reported gross revenue includes incidental byproducts;
  management expense includes paid labor, facility/machinery depreciation,
  rentals and other costs, but **not** all owned-resource opportunity costs.
  Survey income ≠ cash margin ≠ owner-work-adjusted economic NPV.
- **Price basis:** 2024 **nominal KRW** per 10a, one stated cropping cycle.
  It is not the model's 2026-constant KRW 10,000/year and must not overwrite
  `configs/base.json`.
- **Four-year exception:** `인삼(4년근)` shows **four-year
  one-crop-cycle** totals, and is excluded from the default one-cycle scatter
  comparison. Avoid turning this into annual income by silently dividing by
  four without a timing model and establishment costs.
- **Greenhouse/fruit:** facility costs may be reflected as depreciated
  expenses for surveyed existing businesses, NOT the total upfront capital
  required for a NEW build; establishment years and initial fruiting delays
  may be absent from mature orchard survey outcomes.
- **Land scale:** no individual crop area, harvest frequency or facility
  site footprint has been determined. Multiplying any 10a receipt by
  9.917 to obtain a guaranteed 3,000-pyeong annual income is invalid.
- **No independent local verification:** suitability for a specific
  Jeonju parcel, location of actual water/power, irrigation permits,
  market contracts, seasonal labor availability, costs, weather response
  and buyer settlement times are unmeasured.

## Stepwise decision pipeline (no arbitrary point scores)

1. **Discover all:** compare the 51 reported crops in the offline
   [crop discovery interface](../dashboard/crop-discovery/index.html),
   **without a default income ranking**. The exploratory view can filter
   by cultivation category and sort by income, management cost, work hours
   and income rate, with an interactive income-vs-labor scatter.
2. **Include candidates outside the 2024 survey:** add them separately as
   data-deficient opportunities for further research; **missing != zero**.
3. **Site feasibility gate (open):** gather drainage, irrigation, soil
   diagnostics, electricity, land-use restrictions, water/storage access,
   climate thresholds, crop rotation and land occupancy requirements.
4. **Capital/operations gate (open):** facility construction or rent
   quotations, machinery, seed/seedling availability, total/peak labor
   by month, heating and energy, financing service, and capex/maintenance
   timing. Categories `시설*` naturally require a facility feasibility
   review; orchard species require establishment-phase modeling.
5. **Sales/risk gate (open):** documented farmgate buyers, packing and
   transport fees, settlement delays, multi-year prices, quantity/grade
   volatility, uninsured loss and pest susceptibility. Do not infer odds
   of loss solely from a single year's aggregate income.
6. **Pareto/filter comparison:** after genuine data, identify candidates
   that are not dominated simultaneously on modeled net return, startup
   cash requirement, labor burden and downside risk. Ask the user to
   decide priorities only once options and plausible trade-offs are visible.
7. **Then build farm strategy:** choose candidate area mixes and season
   sequences subject to land and monthly labor constraints, account for
   first-year establishment and intercropping limitations, and run
   month-end cash/NPV/stress tests on a separate calibrated config.

This keeps crop, infrastructure and area decisions **open** until evidence
allows comparison. Numeric fields absent from the provided source must
remain UNKNOWN, not zero or subjective rankings.

## Offline browser and automation

```bash
# Open directly: dashboard/crop-discovery/index.html
python scripts/refresh_crop_discovery.py --check
# Only after independent review of changed public statistics:
python scripts/refresh_crop_discovery.py --refresh
pytest -q
```

The page is fully offline (inlined SVG, no external image/chart service).
`--check` fails if the published 51-crop dataset and embedded HTML
desynchronize. `--refresh` deliberately updates **only** the embedded
public-data JSON; it does not edit financial assumptions or old simulation
results. If public source data are corrected, document the exact PDF page
and methodology before accepting a refresh.

**Audit caution:** the dataset was derived from the supplied PDF's
overview and printed labor totals, with monetary reconciliation checks
allowing the book's integer-KRW rounding differences. The PDF itself is
not committed. Historical daily climate and economics are not combined
into a calibrated 51-crop Monte Carlo model yet.
