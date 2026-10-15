# 3,000-pyeong farm crop-choice decision plan (research-to-decision)

**Version:** 2026-10-15, candidate discovery stage.  
**Decision owner:** farm operator; implementation/research support: project developers.  
**Current decision:** NO crop, crop-area split, greenhouse construction/lease, buyer, or financing choice has been made.

> This is an evidence-acquisition and engineering plan, NOT a crop recommendation,
> proof of financial returns, permit approval, or loan eligibility.
> The family pear orchard and separate forest mushroom activity remain out of
> scope for this **independent** parcel.

## 0. Current facts / limitations

| Layer | Present | Still missing / blocking |
| --- | --- | --- |
| Discovery | 51 crop systems from user-supplied RDA *2024 농산물소득자료집*; 2024 nominal KRW per **10a**, reported source level **R**; owner/hired labor hours | Regional/year-to-year dispersion, exact crop-area basis and farm-specific outcomes; 51 surveyed systems are **not all possible crops** |
| Feasibility | Brown/sage HTML 51-crop checklist, eight baseline site evidence gates, flags for protected facilities, orchards and 4-year ginseng | All 51 parcel-specific checks currently `UNKNOWN_NOT_EVALUATED`; no verified parcel observations |
| Weather | KMA Jeonju ASOS 2006–2025 derived annual features | Original hourly ASOS audit unverified without source file; climate station is **not** parcel or crop-specific damage rate |
| Finance | Preliminary paired Monte Carlo across five **example** potato/scallion/cucumber plans; annual and month-end liquidity | No calibrated cost/yield/price/loan/contract; separate costs and facility build not yet transferable to other 46 crop systems |
| Governance | R/T/Q/O category separation, private self-attested calibration preview, offline dashboards, CI | No actual signed review of transactions; `main` untouched and draft PR unmerged |
| CI health | Earlier model and 51-crop checks passed | The formerly failing feasibility HTML/source hash drift was fixed by reconciling tracked CSV line endings. Push/PR CI green at prior head `fa4c7009`; source regression, parcel intake and PDF audits are now added, with their newest CI status checked separately. |

Critical accounting distinctions: RDA `income = gross_receipts - management_costs` is **neither** project NPV **nor** cash balance. Reported management costs include hired labor and facility depreciation, so blindly copying them into a model that separately prices labor, building capex and maintenance would double count. 2024 nominal KRW are not 2026-constant modeled KRW; **4-year ginseng** values must not be silently annualized; existing mature-orchard returns are not establishment-phase cash flows.

## Development progress recorded 2026-10-15

- **P0-01 DONE:** fixed 51-crop feasible-HTML stale source; preceding PR & push Actions both green.
- **P0-02 IMPLEMENTED:** verified all 51 RDA 2024 PDF overview gross/cost/income
  triplets and 51 per-crop labor summary values against the locally supplied
  287-page book. CSV digest/source PDF SHA256 saved without uploading the PDF.
  CI now checks the canonical 51-row lock and arithmetic/percentage/labor guards.
  This does not authenticate the underlying institution data.
- **P0-03 PREPARED ONLY:** created a private non-identifying parcel facts
  template and `farm-strategy site-check`. All real site gates remain UNKNOWN;
  the user's soil/water/permit facts have **not** been provided.
- **P0-04 PREPARED ONLY:** 12 nullable owner-hour inputs, nullable usable
  area/investable funds/buffer/wait-period constraints. No amount is assumed.
- **P1–P3 OPEN:** multi-year/regional price evidence, buyers, real quotations,
  site-specific risks, comparable new crop-system cashflows and pilot decision.
- Details and CLI usage: `docs/RDA_AUDIT_AND_SITE_INTAKE.md`.
- **Current review state:** selected crop NONE, facility choice NONE,
  financing NONE; no additional farm profitability claims.

## 1. Non-negotiable decision principles

1. **Start with the full universe**: all 51 reported systems plus a separate, source-labeled registry of potentially viable candidates absent from the report. Never assume a high-income crop has a feasible market or land fit; avoid preselecting potato/scallion/cucumber.
2. **Unknown ≠ zero or no**: per-crop/site land, water, soil, infrastructure, buyer, capex, labor and risk fields stay `UNKNOWN` until documented. No subjective suitability scores or invented prices.
3. **Hard feasibility before financial rank**: legal restrictions, water, physical access, investment funding, monthly labor and route to market must be independently checked. A missing gate means `pending`, not `passed`.
4. **Comparable clocks and areas**: distinguish 10a single crop cycles, multiple turnovers, productive versus establishment years, 3,000-pyeong gross parcel vs arable/under-cover area, 2024 nominal vs modeled 2026-real, upfront payments vs depreciation.
5. **Multiple objectives, no arbitrary single-score winner**: compare lower-end financial outcomes, maximum cash gap, first-year/peak-month labor and loss/exposure separately; Pareto analysis only after meaningful comparable evidence. User chooses acceptable tradeoffs.
6. **Protect private sources**: original settlement statements, quotations, coordinates, parcel IDs and loan details remain under ignored `data/private/` or an authorized external store; track only redacted source metadata and content hashes.

## 2. Work packages: priority, prerequisite, and acceptance gate

| ID | Priority | Work / action | Responsible / data source | Deliverable and acceptance |
| --- | --- | --- | --- | --- |
| P0-01 | Critical | Resolve latest CI stale HTML check; compare checked-out/generated bytes across Python 3.11/3.13, remove nondeterminism and re-check reproducibility | Development | **Push + PR CI green**, `--check` passes, source CSV/HTML equal, no silenced tests |
| P0-02 | Critical | Freeze provenance of 51 reported rows: crop basis, year, per-10a, PDF/page, hired/owner labor and category. Independently spot check PDF figures and anomalies | Development + RDA PDF | Read-only registry, reconciliation notes, conversion tests, 4-year-cycle exception; no false 2026 output |
| P0-03 | Critical | Local parcel discovery, without publishing precise location: usable area vs gross 3,000 pyeong; soil sample/soil type, slope, drainage, flooding, irrigation water/rights, road access, power/capacity, zoning, greenhouse/structure permits | Operator + agricultural extension/local authority + site services | Dated private site facts with source and **pass/fail/pending separately** for physical and legal prerequisites |
| P0-04 | Critical | Operating constraints: owner available hours **by month**, hired workforce, mechanization/storage/access, investable own funds, max tolerable cash buffer and acceptable time until first revenue | Operator | Ranges or explicit `UNKNOWN`; operating budget not invented |
| P1-01 | High | Expand independent public references: 3–5+ years of comparable crop income/production where available; Jeonbuk regional figures when identifiable, price and grade variation, farmgate rather than wholesale distinction; API codebook is not the API data | RDA publications / crop income API where accessible and authenticated | Multi-year source-tagged table, missing-year flags, documented national-vs-regional comparability |
| P1-02 | High | Build net-market-price dossier: buyer channels (farmgate, co-op, auction, direct), buyer access, quality standards, commission, packing, transport, cold chain, payment lags, realistic volumes | Local buyers / written settlement examples | Source-tagged quote/term ranges, no claims of contracted buyers |
| P1-03 | High | Compare facility choices without assuming a build: new, leased, contractor-assisted, field-only, seasonal cover; electricity/water connections, heating, repair, depreciation vs cash capex, lease deposit/return, feasibility permits | Vendors/landlords/bank; written Q quotes distinct from T paid invoices | 2–3 **comparable** written packages or documented data gap for each viable system |
| P1-04 | High | Resolve agronomy risk: crop window, heat/frost/flood/disease, soil tolerance, rotation, multi-crop incompatibilities, irrigation/heating needs; verify ASOS hourly source and local exposure separately | ASOS, extension agents, agronomic reports | Crop-specific risk matrix with published references and explicit calibration gaps |
| P2-01 | High | Construct crop-system cashflow engine: crop/species + field/house/lease choice + area + crop-cycle/rotation + start-up ramp + monthly operations, sales settlement and hired vs own labor without double-count | Development once P0/P1 evidence sufficient | Candidate-area and month-by-month P&L/liquidity reconciliations, 2026-real conversion tested |
| P2-02 | High | Feasibility screening first, then robust multiobjective shortlisting. Test source uncertainty and adverse price/yield/repair/financing/labor cases; never report synthetic negative fraction as empirical risk | Development + operator | Pareto frontier of feasible candidate systems; pending systems not ranked as infeasible |
| P2-03 | Medium | UI: join 51-crop discovery and site readiness to validated monthly scenario comparison; show `R/Q/T/O/A` provenance and missingness; support importing private review JSON **locally only** | Development | Brown+sage offline HTML, selectable candidates, evidence trail, export; no private uploads |
| P3-01 | Medium | Small-scale/on-site proof before irreversible build: define pilot area, crop cycle, selling channel, measured hours, receipts, yields, fertilizer/water/energy, delays and crop loss | Operator + extension center | Trial log and actual gross-to-net settlements; go/no-go criteria agreed **before** pilot |
| P3-02 | Critical at decision | Decision memo on whether to continue field production, trial another crop, lease/build or defer; quantify minimum cash buffer, owner-hours and worst realistic stress, explicitly identify unsupported assumptions | Operator owns decision; developer prepares evidence | Dated signed decision with alternatives, stop-loss/capital cap and no-commitment outcome permitted |

**P0 tasks are blocking:** no permanent greenhouse construction, borrowing or whole-farm crop allocation based only on current RDA rankings.

## 3. Suggested eight-week sequence (targets, not promises)

Relative weeks start when work resumes; external site surveys, agencies,
buyer responses, crop timing and quotes can extend the schedule.

| Window | Main work | Exit criteria |
| --- | --- | --- |
| Week 1 | P0-01 failing CI and deterministic generator fix; P0-02 audit and source schema; prepare parcel checklist | Green CI; 51 sources reproducible; blockers visible |
| Week 2 | P0-03 site soil/drainage/water/power/use/permit facts; P0-04 operating and capital constraints | Each field `verified / needs follow-up / unknown` with date/source |
| Weeks 3–4 | P1-01 multi-year/region data, P1-02 buyer economics, P1-03 initial build/rent/field package quotes, P1-04 crop-specific regional risks | No silent imputations; at least **illustrative** capex + net revenue scenarios and identified gaps |
| Weeks 5–6 | P2-01 generic crop-cycle/multi-year model and checks; P2-02 screening of feasible systems | Annual ↔ 12-month reconciliation, crop-establishment and cash-buffer tests, data-coverage report |
| Week 7 | P2-03 unified offline browser and candidate mix/budget sensitivity controls | Click-through from crop to evidence to modeled option; privacy tests |
| Week 8 | P3-02 decision-grade review; design P3-01 pilot if justified | Compare continuing research vs pilot vs lease/build vs defer; do not force a crop winner |

## 4. Readiness/status schema

Suggested evidence-gate records include:

- `crop_id`, `system_id` (field/new house/lease/other), `site_fact_key`, `value`, `unit`;
- `status` = `UNKNOWN` / `DOCUMENT_COLLECTED_UNVERIFIED` / `VERIFIED_FEASIBLE` / `VERIFIED_BLOCKED`;
- `source_kind` = `O` measured, `R` reported, `Q` quote, `T` actual paid record, `A` assumption;
- `scope`, `valid_as_of`, `source_reference`, `reviewer`, `checked_at`;
- `capex_date` and `settlement_lag_days` where relevant; `missing_reason` for unknowns.

Existing browser labels `FOLLOWUP_NEEDED`, `DOCUMENT_COLLECTED_UNVERIFIED`
and `NOT_FEASIBLE_USER_ASSERTED` are **not** verified assessment states;
verified states require evidence and independent review and must not be
derived solely from a clicked button.

## 5. Model and investment gates

**Before an option enters quantitative finance screening:**

- State whether the parcel/crop/installation is physically and legally
  feasible or still pending; validate the **arable** area, not just 3,000 pyeong.
- Match each `R` statistic to season/crop system and independent source;
  report missing multi-year/regional observations.
- Separate own/hired work hours and charges, make settlement timing explicit.
- For houses, distinguish capex, maintenance, insurance, heating, rent,
  depreciation and terminal value; for fruit/ginseng, model pre-production years.
- Preserve one risk assessment per *crop-system-place* combination,
  not a single generic pest percentage applied to 51 unrelated crops.

**Before a real construction/lease/borrow decision:**

- Required zoning/permission and utility checks complete; at least one
  dated written offer for full upfront and recurring costs; documented
  financing terms and realistic availability.
- A real or explicitly contingent marketing channel, projected **net**
  proceeds after grade losses/transport/fees, settlement days and required
  working capital.
- Cash buffer under adverse but clearly **assumption-based** scenarios,
  owner peak monthly hours within available time, and an option to defer.
- Independent review of an identified record of which values are observed,
  reported, quoted or assumed. No automatic finance-model overwrite from `R`.

## 6. Next five actions (in order)

1. **Development now:** fix the real CI failure at the latest branch head,
   then rerun all tests and generated-site sync on Python 3.11.
2. **Data work next:** audit 2024 RDA 51 rows (including differing cropping
   cycles), build comparable historical/region source registry without
   fabricating data, preserve PDF source page citations.
3. **Operator when possible:** obtain a non-sensitive **site summary**:
   actual usable area, field vs existing facilities, water availability,
   energy status, drainage and whether zoning checks were completed.
   Avoid uploading parcel identifiers/precise addresses or contracts into Git.
4. **Parallel:** collect existing time/budget constraints and buyer/installer
   quote availability as ranges or `UNKNOWN`; no need to decide a crop yet.
5. **Then:** implement evidence-gated generic crop-system cashflow and
   shortlist options using independent dimensions, not a forced single rank.

**Stop/go outcome at each phase:** continue collecting evidence, run a
low-capital pilot, defer, or consider a verified capital investment. All are
legitimate outcomes; a high 2024 per-10a income is never sufficient on its own.
