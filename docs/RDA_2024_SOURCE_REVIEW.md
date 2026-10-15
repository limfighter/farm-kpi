# RDA 2024 crop income benchmark: uploaded source review

**Category: R (reported third-party statistic), not T (farm transaction).**
Created from the user-supplied 2024 RDA `농산물소득자료집` by reading
the crop summary tables and per-crop cost/labor pages. The original
PDFs, 2026 blank questionnaire ZIP and XLSX codebook are **not committed**.

## Read-only source registry

`data/reported/rda_2024_crop_income_10a.csv` captures four 2024
reported crop outcomes, each from **one crop season / 10a = 1,000 m²**.
These are **2024 nominal KRW**, not model-year 2026-constant KRW 10,000.

| Crop | Total receipts (KRW / 10a) | Management costs (KRW / 10a) | Income (KRW / 10a) | PDF page |
| --- | ---: | ---: | ---: | ---: |
| Spring potato (`봄감자`) | 2,693,175 | 1,443,511 | 1,249,665 | 25; printed 19 |
| Autumn potato (`가을감자`) | 2,631,152 | 1,685,251 | 945,902 | 26; printed 20 |
| Field scallion (`노지쪽파`) | 5,873,196 | 2,791,661 | 3,081,534 | 37; printed 31 |
| Greenhouse cucumber (`시설오이`) | 25,183,583 | 12,299,942 | 12,883,641 | 43; printed 37 |

The accompanying **labor hours and hired-labor costs** come from the
same PDF's per-crop detail pages **78, 79, 90, 96** respectively.
The PDF warns that independently rounded data may differ by one KRW
from receipts minus costs. 2024 national RDA crop-income survey data
represent participating sampled farms and do not establish Jeonju-specific
field profitability or a full 3,000-pyeong farm result.

`data/reported/rda_income_api_crop_crosswalk.csv` extracts **labels
and identifiers only** from the supplied
`농산물소득정보OpenAPI_제공코드.xlsx`:
`KIN01` general crops, `KIN11` field vegetables,
`KIN12` protected vegetables, `CM0145` Jeonbuk province; spring
and autumn potatoes, field scallion and greenhouse cucumber use their
respective full crop IDs. The workbook does **not** contain API keys,
service endpoint access, or time-series observations. Do not treat it
as an authenticated API response.

## 2026 methodology and blank forms are **not 2026 results**

`2026 농산물 소득조사 분석방법.pdf` specifies the later survey
definitions and methods, and the ZIP consists of **eight questionnaire
templates**, including (1) general crops and (2) vegetables. The two
documents contain no completed 2026 farm responses or calibrated
Jeonju costs. The published 2024 results remain the only validated
numeric crop-income observations in the supplied materials.

The 2024 book defines:

- `총수입`: main harvest at farm-gate realized/assessed price **plus
  incidental byproduct value**, not simply wholesale price times yield;
- `경영비`: reported operating/management expense **including**
  hired labor, depreciation of machinery/facilities, rent and other
  eligible components. This is **not** the model's
  `operating_cost_excluding_hired_labor`;
- `소득`: total receipts less management costs, but **not**
  net present value and **not** an owner-labor-inclusive economic NPV;
- `생산비`: management expense **plus** own labor, capital and land
  opportunity costs, a different concept from cash flow.

The 2026 analysis-method guide likewise distinguishes
`경영비` (externally purchased inputs and labor) from
`생산비` (also includes own capital and labor opportunity costs).
Do not double-count hired labor, depreciation or capital investment
when translating RDA accounting into the current monthly ledger.

## Important baseline coincidence

`configs/base.json` currently sets
`finance.cucumber_revenue_300p = 2497.55` in units of
**2026-constant KRW 10,000**. The 2024 book reports greenhouse
cucumber receipts `25,183,583 KRW / 10a`. A **purely arithmetic**
conversion using **300 pyeong = 991.736 m²** yields approximately
`2497.55 × 10,000 KRW / 300 pyeong`.

The numerical match is notable, but is **not independent validation**:
the baseline may already have used a similar published number.
The figures also have different **price-year units** and the exact
source lineage of `configs/base.json` is not documented. Do not
conclude the model has been calibrated from that coincidence.
Crop area, growing practice, crop turnover, grade, postharvest fees,
and inflation/price escalation need separate evidence.

There is currently **no sufficient information** to convert published
field crop receipts to annual income from the independent 3,000-pyeong
land parcel: how many pyeong are planted in each crop and whether there
are successive crops remain unknown. The crop-specific model revenues
lack explicit area denominators, so direct replacement would be false
precision. Likewise, 2024 management costs cannot be directly copied
into the model's operating-cost-excluding-hired-labor variables.

## Current data governance

- Keep `configs/base.json`, Monte Carlo damage distributions and
  `dashboard/index.html` unchanged; these CSV files are reference
  **R** observations, not staged human-reviewed **T** inputs.
- For eventual local what-if calibration, obtain actual paid farm
  settlements (`T`), written building/rent quotes (`Q`), crop area
  and labor logs, then use the SHA-locked private review procedure in
  `docs/PRIVATE_CALIBRATION_PREVIEW.md`.
- The public RDA income tables are suitable for **benchmarking** and
  plausibility checks, not for automatically changing model defaults,
  estimating real farm-loss probabilities, or asserting eligibility
  for a loan.
