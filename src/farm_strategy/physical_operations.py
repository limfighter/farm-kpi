"""Explicit dates, growth-stage inputs, peak utilities and loan amortization.

An optional *strict overlay* on the existing multi-crop portfolio. It does not
infer any growth rate, irrigation demand, electrical load or bank conditions.
Daily rows reconcile exactly to the already modeled per-month resource amounts.
All loan flows are in constant start-year KRW using a user-supplied REAL rate;
nominal bank terms cannot be entered without a deliberate conversion.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
import math

from .portfolio import simulate_portfolio, _number, _text
from .lifecycle import SOURCE_KINDS

DETAIL_FIELDS = {"schema_version", "disclaimer", "date_occupancies", "stage_demands",
                 "site_peak_limits", "loan_terms"}
DATE_FIELDS = {"case_id", "plot_id", "start_date", "end_date"}
STAGE_FIELDS = {"case_id", "stage", "start_date", "end_date",
                "water_m3_per_day", "electricity_kwh_per_day",
                "concurrent_peak_kw", "source_kind", "source_ref"}
LIMIT_FIELDS = {"pump_capacity_m3_per_hour", "pumping_hours_available_per_day",
                "simultaneous_electric_capacity_kw", "minimum_turnaround_days"}
LOAN_FIELDS = {"name", "draw_year", "draw_month", "principal_krw",
               "annual_real_interest_rate", "grace_months",
               "equal_principal_repayment_months", "source_kind", "source_ref"}


def _shape(row, fields, what):
    if not isinstance(row, dict) or set(row) != fields:
        raise ValueError(f"{what}: required input fields differ")


def _day(s, name):
    _text(s, name)
    try:
        result = date.fromisoformat(s)
        if result.isoformat() != s:
            raise ValueError("Day must be YYYY-MM-DD")
        return result
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name}: require ISO calendar date") from e


def _days(start, end):
    return (start + timedelta(days=d) for d in range((end-start).days+1))


def _rel_month(d, start_year, months):
    i = (d.year-start_year)*12 + d.month-1
    if not 0 <= i < months:
        raise ValueError("Explicit date outside farm scenario horizon")
    return i


def _month_label(y,m):
    return f"{y:04d}-{m:02d}"


def _close(a,b,name):
    if not math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-6):
        raise ValueError(f"{name}: daily stages must reconcile with monthly resource ledger")


def amortization_events(site, terms):
    """Monthly equal-principal loan, after grace; explicit *real* annual rate.

    No interest is accrued/paid in the draw month, from following month onward
    interest on opening principal. Monthly interest is a declared r/12 rule,
    not an actual bank schedule. Each generated event has A class except the
    source class the user explicitly provided, which is NOT verified.
    """
    _shape(terms, LOAN_FIELDS, "loan_terms")
    _text(terms["name"], "loan name")
    _text(terms["source_ref"], "loan source_ref")
    if terms["source_kind"] not in SOURCE_KINDS:
        raise ValueError("Unknown loan source class")
    principal = _number(terms["principal_krw"], "principal_krw")
    if principal <= 0:
        raise ValueError("Loan amount must be positive")
    real_rate = _number(terms["annual_real_interest_rate"], "annual_real_interest_rate")
    if real_rate > 1:
        raise ValueError("Annual rate exceeds 100%; provide real rate explicitly")
    grace = terms["grace_months"]
    repay = terms["equal_principal_repayment_months"]
    if type(grace) is not int or not 0 <= grace <= 120:
        raise ValueError("grace_months must be 0..120")
    if type(repay) is not int or not 1 <= repay <= 360:
        raise ValueError("repayment months must be 1..360")
    y,m=terms["draw_year"],terms["draw_month"]
    yrs=site["horizon_years"]
    if type(y) is not int or not 1 <= y <= yrs or type(m) is not int or not 1 <= m <= 12:
        raise ValueError("Loan draw month outside horizon")
    draw = (y-1)*12 + m-1
    horizon=yrs*12
    # Derived installments are assumptions, never observed transactions or
    # verbatim written lender quotes even if the INPUT terms cite Q or T.
    common={"source_kind":"A","source_ref":"CALCULATED_FROM_"+terms["source_kind"]+": "+terms["source_ref"]}
    def event(i,kind,amount):
        return {**common, "name":terms["name"]+" "+kind,
                "year":i//12+1,"month":i%12+1,
                "kind":kind,"amount_krw":float(amount)}
    events=[event(draw,"DRAW",principal)]
    outstanding = principal
    outstanding_at_end = None
    total_due=grace+repay
    # Full maturity may extend beyond the farm simulation; do not insert a
    # fictitious bullet payoff at year 10.
    for step in range(1, min(total_due,horizon-draw-1)+1):
        i=draw+step
        events.append(event(i,"INTEREST",outstanding*real_rate/12.))
        if step>grace:
            part=principal/repay if step<total_due else outstanding
            outstanding=max(0.,outstanding-part)
            events.append(event(i,"PRINCIPAL",part))
    outstanding_at_end=outstanding
    return {
        "events":events,
        "remaining_principal_after_horizon_krw":outstanding_at_end,
        "maturity_extends_beyond_horizon":(draw+total_due >= horizon),
        "annual_real_rate_input":real_rate,
        "input_terms_source_kind":terms["source_kind"],
        "generated_event_source_kind":"A",
        "assumption":"Monthly simple real interest r/12 on opening principal. Not nominal bank APR, not bank-approved or actual lender billing."
    }


def assess_daily_farm(portfolio, detail):
    _shape(detail,DETAIL_FIELDS,"daily_detail")
    if type(detail["schema_version"]) is not int or detail["schema_version"]!=1:
        raise ValueError("Unknown daily-detail schema version")
    _text(detail["disclaimer"],"disclaimer")
    if not isinstance(detail["date_occupancies"],list) or not isinstance(detail["stage_demands"],list):
        raise ValueError("Dates and stage_demands must be lists")
    lim=detail["site_peak_limits"]
    _shape(lim,LIMIT_FIELDS,"site_peak_limits")
    pump=lim["pump_capacity_m3_per_hour"]
    hours=lim["pumping_hours_available_per_day"]
    power=lim["simultaneous_electric_capacity_kw"]
    for name,val in [("pump_capacity_m3_per_hour",pump),
                     ("pumping_hours_available_per_day",hours),
                     ("simultaneous_electric_capacity_kw",power)]:
        if val is not None:
            _number(val,name)
    if pump is not None and pump<=0:
        raise ValueError("Pump capacity must be positive or unknown")
    if hours is not None and hours>24:
        raise ValueError("Daily pumping hours cannot exceed 24")
    min_gap=lim["minimum_turnaround_days"]
    if type(min_gap) is not int or not 0<=min_gap<=60:
        raise ValueError("Turnaround days must be 0..60")
    if detail["loan_terms"] is not None and portfolio["financing_events"]:
        raise ValueError("Cannot combine generated amortization with manual loan cash events")
    # Baseline model applies strict month collision checks and validates crop
    # operations, site-supply vectors, debt and business cash independently.
    base=simulate_portfolio(portfolio)
    start=portfolio["site"]["start_year"]
    n=portfolio["site"]["horizon_years"]*12
    cases={v["case"]["id"]:v for v in portfolio["plantings"]}
    if len(cases)!=len(portfolio["plantings"]):
        raise ValueError("Duplicate case IDs")
    occupied = {}
    by_plot = defaultdict(list)
    if len(detail["date_occupancies"])!=sum(len(v["occupancies"]) for v in cases.values()):
        raise ValueError("Require one exact-date window per monthly occupation")
    remaining={(id,i) for id,v in cases.items() for i in range(len(v["occupancies"]))}
    for rec in detail["date_occupancies"]:
        _shape(rec,DATE_FIELDS,"date occupation")
        name=rec["case_id"]
        if name not in cases or rec["plot_id"]!=cases[name]["plot_id"]:
            raise ValueError("Unknown case ID or mismatched plot")
        a,b=_day(rec["start_date"],"start_date"),_day(rec["end_date"],"end_date")
        if a>b:
            raise ValueError("Daily occupation ends before starts")
        first,last=_rel_month(a,start,n),_rel_month(b,start,n)
        matches=[i for i,win in enumerate(cases[name]["occupancies"])
            if (win["start_year"]-1)*12+win["start_month"]-1==first
            and (win["end_year"]-1)*12+win["end_month"]-1==last
            and (name,i) in remaining]
        if not matches:
            raise ValueError("Daily occupation month range not in existing portfolio")
        remaining.remove((name,matches[0]))
        occupied.setdefault(name,[]).append((a,b))
        by_plot[rec["plot_id"]].append((a,b,name,cases[name]["case"]["area_m2"]))
    if remaining:
        raise ValueError("Unspecified daily occupation")
    transitions=[]
    for plot, spans in by_plot.items():
        # The base portfolio already checks month-level overlaps. These checks
        # enforce calendar-day turnaround and report the actual idle days.
        spans.sort()
        for i,(a,b,name,area) in enumerate(spans):
            for other_a,other_b,other_name,other_area in spans[:i]:
                if other_b>=a and area+other_area>next(
                    p["area_m2"] for p in portfolio["plots"] if p["id"]==plot):
                    raise ValueError("Daily land occupancy overlaps plot capacity")
            for other_a,other_b,other_name,other_area in spans[:i]:
                if other_b<a:
                    gap=(a-other_b).days-1
                    transitions.append({"plot_id":plot,"previous":other_name,"next":name,
                        "free_days_between":gap,
                        "minimum_required_days":min_gap,
                        "shortage_days":max(0,min_gap-gap)})
                    if gap<min_gap:
                        raise ValueError("Insufficient days between crop turns")
    monthly_water=defaultdict(float)
    monthly_power=defaultdict(float)
    stage_by_case=defaultdict(list)
    water_by_day=defaultdict(float)
    kwh_by_day=defaultdict(float)
    peak_kw_by_day=defaultdict(float)
    stage_names=defaultdict(set)
    for stage in detail["stage_demands"]:
        _shape(stage,STAGE_FIELDS,"growth stage")
        case_id=stage["case_id"]
        if case_id not in cases:
            raise ValueError("Unknown case_id in growth stage")
        _text(stage["stage"],"stage name")
        _text(stage["source_ref"],"stage source")
        if stage["source_kind"] not in SOURCE_KINDS:
            raise ValueError("Unknown stage source")
        a,b=_day(stage["start_date"],"stage start"),_day(stage["end_date"],"stage end")
        if a>b:
            raise ValueError("Growth stage ends before starts")
        w=_number(stage["water_m3_per_day"],"water_m3_per_day")
        e=_number(stage["electricity_kwh_per_day"],"electricity_kwh_per_day")
        kw=_number(stage["concurrent_peak_kw"],"concurrent_peak_kw")
        stage_by_case[case_id].append(stage)
        for day in _days(a,b):
            if not any(s<=day<=t for s,t in occupied[case_id]):
                raise ValueError("Stage demand outside actual planted date occupation")
            if day in stage_names[case_id]:
                raise ValueError("Overlapping stages for same crop-day")
            stage_names[case_id].add(day)
            monthly_water[(case_id,day.year,day.month)]+=w
            monthly_power[(case_id,day.year,day.month)]+=e
            water_by_day[day]+=w
            kwh_by_day[day]+=e
            peak_kw_by_day[day]+=kw
    for case_id,plant in cases.items():
        required_days={d for a,b in occupied[case_id] for d in _days(a,b)}
        if stage_names[case_id]!=required_days:
            raise ValueError("Every planted day must have one explicit growth-stage demand, even zero")
        for rec in plant["resources"]:
            y=start+rec["year"]-1
            m=rec["month"]
            _close(monthly_water[(case_id,y,m)],rec["water_m3"],"Water "+case_id+" "+str(m))
            _close(monthly_power[(case_id,y,m)],rec["electricity_kwh"],"Energy "+case_id+" "+str(m))
    daily=[]
    for day in sorted(water_by_day):
        w=water_by_day[day]; e=kwh_by_day[day]; kw=peak_kw_by_day[day]
        needed=None if pump is None else w/pump
        supply=None if hours is None else hours
        shortage=None if needed is None or supply is None else max(0.,needed-supply)
        kwshort=None if power is None else max(0.,kw-power)
        daily.append({"date":day.isoformat(),"water_m3":w,"electricity_kwh":e,
                      "pump_hours_needed":needed,"pump_hours_available":supply,
                      "pump_hours_shortage":shortage,"sum_simultaneous_peak_kw":kw,
                      "electric_peak_kw_available":power,"peak_kw_shortage":kwshort})
    terms=detail["loan_terms"]
    loan=None
    funded=base
    if terms is not None:
        if portfolio["financing_events"]:
            raise ValueError("Cannot combine generated amortization with manual loan cash events")
        loan=amortization_events(portfolio["site"],terms)
        clone=deepcopy(portfolio)
        clone["financing_events"]=loan["events"]
        funded=simulate_portfolio(clone)
        if not math.isclose(base["unlevered_npv_if_rate_supplied_krw"] or 0,
                            funded["unlevered_npv_if_rate_supplied_krw"] or 0,
                            abs_tol=1e-8):
            raise ValueError("Credit cannot alter underlying farm project NPV")
    return {
        "status":"DAILY_ASSUMPTION_LEDGER_NOT_FIELD_OR_BANK_VALIDATION",
        "crop_count":len(cases),"date_turnarounds":transitions,
        "daily_capacity":daily,
        "growth_stage_count":len(detail["stage_demands"]),
        "days_with_unknown_pump_capacity":sum(x["pump_hours_shortage"] is None for x in daily),
        "days_with_unknown_electric_peak_capacity":sum(x["peak_kw_shortage"] is None for x in daily),
        "days_exceeding_pump_window":[x["date"] for x in daily if x["pump_hours_shortage"] is not None and x["pump_hours_shortage"]>0],
        "days_exceeding_peak_kw":[x["date"] for x in daily if x["peak_kw_shortage"] is not None and x["peak_kw_shortage"]>0],
        "base_ending_cash_krw":base["ending_cash_krw"],
        "financed_ending_cash_krw":funded["ending_cash_krw"],
        "financed_peak_month_end_shortfall_krw":funded["maximum_month_end_cash_shortfall_krw"],
        "unlevered_npv_krw_if_discount_set":funded["unlevered_npv_if_rate_supplied_krw"],
        "loan_schedule":loan,
        "financing_summary":funded["financing"],
        "disclaimer":detail["disclaimer"],
        "caveats":[
            "Strict prior monthly land collision guard still applies. Same-month turnover cannot be certified even when dates do not overlap.",
            "Peak kW loads sum conservatively assuming every listed stage load can coincide. Duty cycle/actual measured demand profiles absent.",
            "No soil sensor, water pressure or water quality validation. Per-day stages must reconcile with monthly m3/kWh.",
            "Real annual rate on constant-year KRW is a hypothetical financing input. Do not substitute nominal quoted APR or interpret as a loan offer."
        ],
    }
