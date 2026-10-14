"""Auditable 2027–2036 farm scenarios; all values in 2026-constant 10k KRW.

Weather annual features: observed KMA ASOS. Crop losses, pest events, crop
revenue and prices: explicit ASSUMPTIONS. This is not a calibrated forecast.
"""
import csv
import json
import math
import random
from pathlib import Path
from statistics import median

PLANS = ("field_trial", "pause_after_trial", "new_cucumber_house",
         "leased_cucumber_house", "new_cucumber_premium")
SCENARIOS = ("base", "weak_damage", "severe_damage", "price_down_15",
             "wage_up_30", "capex_up_20")


def read_config(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_weather(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    years = [int(row["year"]) for row in rows]
    if years != list(range(2006, 2026)):
        raise ValueError("Expected complete chronological ASOS years 2006–2025")
    return rows


def month_labor(f, has_greenhouse):
    keys = ("hour_requirements_site", "hour_requirements_potato",
            "hour_requirements_scallion")
    monthly = [sum(f[k][i] for k in keys)
               + (f["hour_requirements_cucumber"][i] if has_greenhouse else 0)
               for i in range(12)]
    owner = [min(need, available) for need, available
             in zip(monthly, f["owner_available_hours_by_month"])]
    hired = [max(0.0, need - available) for need, available
             in zip(monthly, f["owner_available_hours_by_month"])]
    return sum(owner), sum(hired), hired


def loan_cash(year, loan):
    """Draw amount, payment and year-end outstanding: five full grace years."""
    year0 = int(loan["draw_year"])
    if year < year0:
        return 0.0, 0.0, 0.0
    principal = float(loan["principal"])
    grace = int(loan["grace_years"])
    installments = int(loan["amortization_years"])
    already_paid = min(max(year - year0 - grace, 0), installments)
    start_debt = principal * (1.0 - already_paid / installments)
    annual_principal = principal / installments if year >= year0 + grace else 0.0
    interest = start_debt * float(loan["annual_nominal_rate"])
    return (principal if year == year0 else 0.0,
            interest + annual_principal,
            max(0.0, start_debt - annual_principal))


def lognormal_shock(sigma, rng):
    return math.exp(rng.gauss(-sigma ** 2 / 2, sigma))


def weather_loss(w, scale):
    """Synthetic crop response, NOT calibrated against observed harvest damage."""
    heat = max(0, w["hot33_maysep"] - 15)
    frost = w["frost0_apr"]
    severe_rain = w["rain80_maysep"]
    wet_spring = max(0, w["rain40_aprjun"] - 1)
    hot_spring = max(0, w["heat30_aprjun"] - 8)
    wet_autumn = max(0, w["rain40_juloct"] - 4)
    hot_autumn = max(0, w["hot33_juloct"] - 15)
    return (
        min(0.60, scale * (0.03 * frost + 0.025 * wet_spring + 0.006 * hot_spring)),
        min(0.60, scale * (0.025 * wet_autumn + 0.009 * hot_autumn)),
        min(0.60, scale * (0.004 * heat + 0.035 * severe_rain + 0.01 * frost)),
    )


def quantile(v, q):
    a = sorted(v)
    p = (len(a) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return a[lo] if lo == hi else a[lo] * (hi - p) + a[hi] * (p - lo)


def one_path(plan, scenario, pool, config, rng):
    if plan not in PLANS or scenario not in SCENARIOS:
        raise ValueError("Unknown plan/scenario")
    f, r, loan = config["finance"], config["risk"], config["loan"]
    unresolved = config["tax_and_insurance"]
    damage_scale = {"weak_damage": 0.55, "severe_damage": 1.80}.get(scenario, 1.0)
    price_bias = 0.85 if scenario == "price_down_15" else 1.0
    wage_factor = 1.30 if scenario == "wage_up_30" else 1.0
    capex_factor = 1.20 if scenario == "capex_up_20" else 1.0
    built = plan.startswith("new_cucumber")
    leased = plan == "leased_cucumber_house"
    paused = plan == "pause_after_trial"
    results = []
    project_npv = equity_npv = economic_npv = 0.0
    debt = 0.0

    for t, year in enumerate(range(f["years"][0], f["years"][1] + 1)):
        w = rng.choice(pool)  # whole historical year retains climate correlations
        potato_loss, scallion_loss, cucumber_loss = weather_loss(w, damage_scale)
        wet = min(1.0, w["rain40_maysep"] / 8.0)
        price_common = lognormal_shock(r["price_common_sigma"], rng) * price_bias
        prices = [
            price_common * lognormal_shock(r["price_potato_sigma"], rng),
            price_common * lognormal_shock(r["price_scallion_sigma"], rng),
            price_common * lognormal_shock(r["price_cucumber_sigma"], rng),
        ]
        pest_chances = [min(1, r["pest_potato_base"] + 0.06 * wet),
                        min(1, r["pest_scallion_base"] + 0.07 * wet),
                        min(1, r["pest_cucumber_base"] + 0.10 * wet)]
        pest_hit = [rng.random() < chance for chance in pest_chances]
        pests = [r["pest_loss_potato"], r["pest_loss_scallion"],
                 r["pest_loss_cucumber"]]
        field = not (paused and t > 0)
        house = (built or leased) and year >= 2028
        ramp = r["cucumber_ramp_from_2028"][year - 2028] if house else 0.0
        first_field = r["first_year_field_productivity"] if year == 2027 else 1.0
        potato = f["potato_revenue"] * first_field * (1 - potato_loss) * prices[0]
        scallion = f["scallion_revenue"] * first_field * (1 - scallion_loss) * prices[1]
        if pest_hit[0]: potato *= 1 - pests[0]
        if pest_hit[1]: scallion *= 1 - pests[1]
        revenue = potato + scallion if field else 0.0
        if house:
            cucumber = f["cucumber_revenue_300p"] * ramp * (1 - cucumber_loss) * prices[2]
            if pest_hit[2]: cucumber *= 1 - pests[2]
            if plan == "new_cucumber_premium": cucumber *= 1.30
            revenue += cucumber

        own_hours = hired_hours = 0.0
        if field:
            own_hours, hired_hours, _ = month_labor(f, house)
            cost = (f["potato_operating_cost_excluding_hired_labor"]
                    + f["scallion_operating_cost_excluding_hired_labor"]
                    + f["site_overhead"]
                    + hired_hours * f["hired_hour_rate"] * wage_factor)
            if house:
                cost += f["cucumber_operating_cost_excluding_hired_labor"]
                cost += f["new_house_maintenance"] if built else (
                    f["rent_yearly"] + f["rent_maintenance"])
                if plan == "new_cucumber_premium": cost += 170
                chance = min(1, r["major_repair_base_prob"]
                             + r["major_repair_wet_sensitivity"] * wet)
                if rng.random() < chance: cost += f["facility_major_repair_cost"]
        else:
            cost = f["land_maintenance_if_idle"]
        cost += unresolved["annual_tax_cash"] + unresolved["annual_insurance_premium_cash"]
        revenue += unresolved["annual_insurance_payout_cash"]

        investment = f["field_initial_capex"] if year == 2027 else 0.0
        if year == 2028:
            if built: investment += f["new_house_capex"] * capex_factor
            if leased: investment += f["rent_deposit"] + f["rent_fitout"]
        terminal = 0.0
        if year == 2036:
            if built: terminal = f["new_house_capex"] * capex_factor * f["house_salvage_fraction"]
            if leased: terminal = f["rent_deposit"]  # refundable asset, not rent expense

        project_cash = revenue - cost - investment + terminal
        draw = repayment = 0.0
        if built and loan["enabled_for_new_house"]:
            draw, repayment, debt = loan_cash(year, loan)
        equity_cash = project_cash + draw - repayment
        if year == 2036 and built and loan["enabled_for_new_house"]:
            equity_cash -= debt   # end-of-horizon outstanding liability (not cash repayment)
        factor = (1.0 + f["real_discount_rate"]) ** t
        project_npv += project_cash / factor
        equity_npv += equity_cash / factor
        economic_npv += (project_cash - own_hours * f["owner_hour_economic_value"]) / factor
        results.append({"year": year, "sampled_weather_year": int(w["year"]),
                        "revenue": revenue, "cash_cost": cost, "capex": investment,
                        "owner_hours": own_hours, "hired_hours": hired_hours,
                        "project_cash": project_cash, "loan_draw": draw,
                        "loan_payment": repayment, "debt_end": debt,
                        "equity_cash": equity_cash})
    return {"project_npv": project_npv, "equity_npv": equity_npv,
            "economic_npv": economic_npv,
            "cash_2030_after_debt": next(y["project_cash"] + y["loan_draw"] - y["loan_payment"]
                                         for y in results if y["year"] == 2030),
            "hired_hours_2030": next(y["hired_hours"] for y in results if y["year"] == 2030),
            "debt_end": debt, "years": results}


def simulate(plan, scenario, weather, config, seed=42, paths=1000, window="recent10"):
    if not (1 <= paths <= 100000): raise ValueError("paths must be 1–100,000")
    if window not in ("all20", "recent10"): raise ValueError("Invalid window")
    pool = [row for row in weather if window == "all20" or row["year"] >= 2016]
    if len(pool) < 5: raise ValueError("Need >=5 annual observations")
    rng = random.Random(seed)
    runs = [one_path(plan, scenario, pool, config, rng) for _ in range(paths)]
    keys = ("project_npv", "equity_npv", "economic_npv",
            "cash_2030_after_debt", "hired_hours_2030", "debt_end")
    summary = {}
    for key in keys:
        a = [run[key] for run in runs]
        summary[key] = {"p10": round(quantile(a, .1), 2),
                        "median": round(median(a), 2),
                        "p90": round(quantile(a, .9), 2)}
        if key in ("project_npv", "cash_2030_after_debt"):
            summary[key]["negative_fraction_model_only"] = round(
                sum(v < 0 for v in a) / len(a), 4)
    return {"plan": plan, "scenario": scenario, "seed": seed,
            "paths": paths, "window": window,
            "units": "2026-constant KRW 10000",
            "metrics": summary, "data_quality": {
                "observed": "KMA ASOS station 146 annual weather feature vectors",
                "rain": "hourly numerical rain lower bound; daily archive cross-check pending",
                "pest": "UNVALIDATED occurrence and loss assumptions",
                "price": "UNVALIDATED synthetic shocks; KAMIS excluded",
                "construction": "UNVALIDATED construction and rent quotes",
                "tax_insurance": "ZERO PLACEHOLDERS; NOT a tax-exemption assertion",
                "loan": "illustrative terms; not approved"}}
