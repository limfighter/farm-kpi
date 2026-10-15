# Private evidence calibration — review-gated preview (2026-10-15)

**No original farm sale receipts, crop records, construction quotes or loan contracts
have been received or authenticated.** The code below only lets an authorized
human compare candidate numbers with existing *hypothetical* inputs offline.
The repo baseline `configs/base.json` and public/dashboard snapshots stay unchanged.

## 1. Use private ignored paths

From the project root:

```bash
mkdir -p data/private output/calibration
cp data/templates/reviewed_calibration_TEMPLATE.csv data/private/reviewed-candidates.csv
cp data/templates/review_manifest_TEMPLATE.json data/private/review-manifest.json
```

Both working files must stay in Git-ignored `data/private/`. Do not include
original receipts, identifiers, bank details, business addresses or raw hourly
ASOS records in Git commits or Actions artifacts.

## 2. Normalize the evidence before any preview

One reviewed **model-equivalent** candidate per finance key, not a collection of
individual transaction lines. Capture and independently reconcile the original
records in private working papers *before* writing the single candidate number.
CSV columns:

| Column | Required meaning |
| --- | --- |
| `model_key` | One of the supported scalar `finance.*` keys in `evidence.py` |
| `source_kind` | `T` actual settled transaction; `Q` written quote; `O` observation; `R` reported statistic |
| `observation_date` | ISO date from the underlying source |
| `period_label` | Which harvest season or priced work period |
| `value_2026_constant` | Numerically converted 2026-constant KRW 10,000 |
| `unit` | `KRW_10000_2026_constant`; hourly wage has `KRW_10000_per_hour_2026_constant` |
| `reference_id` | Opaque local reference, not the receipt number or personal identifiers |
| `scope_note` | Crop grade, planted area, years/season and exact model scale alignment |
| `normalization_note` | Inflation conversion, net transport/packing/fees, yields and duplicate handling |
| `review_status` | Must be `reviewed` for approved candidate rows |

Revenue and farm operating expense overrides require source kind `T`
(actual transactions). Wage rates, construction and rent amounts permit
`Q` (written quote) or `T`; **Q remains a quote, never a booked cost**.
`O` and `R` metadata can be checked by `evidence-check` but cannot override
finance scalars in this preview. The schema validator checks plausibility,
types and units only: it does **not** verify scope notes or primary documents.

**Area caveat:** the land plot is 3,000 pyeong but the cucumber revenue line
is a **300-pyeong** unit model. The potato and scallion revenue base does not
supply individual planted areas. Verify reference crop areas and the
crop-specific model scaling before attesting normalization. Do not apply an
entire 3,000-pyeong receipt as the revenue for an unverified subarea.

## 3. Review a SHA-locked snapshot

Hash the exact **private** candidate CSV (locally):

```bash
python -c "import hashlib; p='data/private/reviewed-candidates.csv'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"
```

Set `evidence_sha256` in your private JSON manifest to that hash. Fill
`reviewer_id`, `reviewed_on` (ISO date), and exactly the
`approved_reference_ids` you have examined. Set each of the four
`review_checklist` booleans true **only if you actually verified** the
relevant materials:

- `original_documents_checked`
- `area_grade_season_reconciled`
- `net_fees_reconciled`
- `constant_2026_currency_checked`

The distributed manifest deliberately has no approvals and all checklist
booleans false, so it cannot stage data accidentally. Any modification of
the candidate CSV after review invalidates the SHA256 lock. This is **human
self-attestation**, not a secure e-signature or a substitute for auditing.

## 4. Generate a local before/after scenario (no Git writes)

```bash
farm-strategy calibration-preview \
  --file data/private/reviewed-candidates.csv \
  --review data/private/review-manifest.json \
  --output-dir output/calibration \
  --seed 42 --paths 300 --scenario base --window recent10
```

Outputs are intentionally written **only** to an ignored local directory,
or to a directory *outside* the repository:

- `what-if-config.json`: a deep copy of the base model with only approved
  reviewed candidates replaced. The baseline is untouched.
- `what-if-impact.json`: paired seeded simulation, the before/after
  medians and p90s for all **five** preliminary plans, source category
  `T`/`Q`, and a SHA256 evidence-file fingerprint (not a source-document ID). Values in this **private**
  report are business-sensitive; never commit or publish it.
  
Both runs sample matching synthetic weather, pest, crop price and repair
events, making their **modeled** differences reproducible. This still says
nothing about verified probability distributions or farm profitability.
For a separate local inspection of **all six modeled stress scenarios**,
run the comparison with the global `--config` flag **before** the command:

```bash
farm-strategy --config output/calibration/what-if-config.json compare \
  --seed 42 --paths 300 --stress-matrix \
  --output output/calibration/compare-what-if.json \
  --csv output/calibration/compare-what-if.csv
```

The existing dashboard is **not** automatically replaced by any private
calibration preview, because it is a tracked model-only snapshot. Generate
a separate untracked HTML locally only after carefully reviewing the
scenario result and privacy exposure.

## Review limitations and next blockers

- File hashes detect post-review CSV changes, **not** document forgery.
- Reviewer assertions and free-text normalization are not source audited.
- One annual scalar cannot capture grade-specific prices, cash receipt lags,
  weekly seasonality, taxes, variable planted area, or labor-specific timing.
- Price and damage coefficients remain synthetic even after some financial
  inputs have been replaced.
- Never present a self-attested what-if as verified financial performance,
  credit approval, or a recommendation to expand greenhouse investment.
