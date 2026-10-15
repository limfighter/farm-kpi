"""Illustrative month-end liquidity ledger.

Monthly crop receipts, costs, capex and financing dates are ASSUMED profiles;
they are not measured farm cash transactions or a working-capital forecast.
All cash entries returned here are in 2026-constant KRW 10,000.
"""
import math

PROFILE_KEYS = ("potato_sales", "scallion_sales", "cucumber_sales")
MONTH_KEYS = ("field_capex_month", "house_capex_month", "lease_capex_month",
              "loan_draw_month", "loan_payment_month", "repair_month",
              "terminal_month")


def validate_cashflow_config(finance, profiles):
    inflation = float(finance["assumed_annual_inflation_rate"])
    if not math.isfinite(inflation) or inflation <= -1:
        raise ValueError("Invalid annual inflation assumption")
    for key in PROFILE_KEYS:
        weights = profiles[key]
        if len(weights) != 12 or any(
            not math.isfinite(float(w)) or float(w) < 0 for w in weights
        ) or not math.isclose(sum(float(w) for w in weights), 1.0, abs_tol=1e-9):
            raise ValueError(f"Invalid monthly allocation weights: {key}")
    for key in MONTH_KEYS:
        m = profiles[key]
        if isinstance(m, bool) or not isinstance(m, int) or not 1 <= m <= 12:
            raise ValueError(f"Invalid month setting: {key}")


def nominal_to_real(amount, year, finance):
    """Deflate a nominal value in year to constant 2026 KRW."""
    inflation = float(finance["assumed_annual_inflation_rate"])
    if not math.isfinite(inflation) or inflation <= -1:
        raise ValueError("Invalid annual inflation assumption")
    return float(amount) / (1.0 + inflation) ** (year - 2026)


def spread(amount, weights):
    total = sum(weights)
    if total <= 0:
        raise ValueError("Cannot allocate to zero monthly effort")
    return [amount * x / total for x in weights]


def month_ledger(*, year, config, plan, field, house, hired_by_month,
                 wage_factor, potato, scallion, cucumber, annual_cash_cost,
                 field_capex, house_capex, lease_capex, terminal,
                 repair_cost, real_loan_draw, real_loan_payment):
    """Allocate stated costs only; never conceal reconciliation drift as repairs."""
    f = config["finance"]
    m = config["monthly_cashflow"]
    validate_cashflow_config(f, m)
    if len(hired_by_month) != 12:
        raise ValueError("Expected 12 months of hired hours")
    if (isinstance(repair_cost, bool) or not isinstance(repair_cost, (int, float))
            or not math.isfinite(repair_cost) or repair_cost < 0):
        raise ValueError("Repair cost must be a finite nonnegative amount")
    if not house and repair_cost:
        raise ValueError("No facility can incur the facility major-repair event")

    revenues = [
        potato * m["potato_sales"][i]
        + scallion * m["scallion_sales"][i]
        + cucumber * m["cucumber_sales"][i]
        for i in range(12)
    ]
    revenues[11] += config["tax_and_insurance"]["annual_insurance_payout_cash"]

    monthly_costs = [0.0] * 12
    if field:
        potato_costs = spread(f["potato_operating_cost_excluding_hired_labor"],
                              f["hour_requirements_potato"])
        scallion_costs = spread(f["scallion_operating_cost_excluding_hired_labor"],
                               f["hour_requirements_scallion"])
        for i in range(12):
            monthly_costs[i] = (potato_costs[i] + scallion_costs[i]
                                + f["site_overhead"] / 12
                                + hired_by_month[i] * f["hired_hour_rate"] * wage_factor)
        if house:
            cucumber_costs = spread(f["cucumber_operating_cost_excluding_hired_labor"],
                                    f["hour_requirements_cucumber"])
            for i in range(12):
                monthly_costs[i] += cucumber_costs[i]
                monthly_costs[i] += ((f["new_house_maintenance"] if
                                     plan.startswith("new_cucumber") else
                                     f["rent_yearly"] + f["rent_maintenance"]) / 12)
                if plan == "new_cucumber_premium":
                    monthly_costs[i] += 170 * m["cucumber_sales"][i]
    else:
        monthly_costs = [f["land_maintenance_if_idle"] / 12] * 12

    for i in range(12):
        monthly_costs[i] += (
            config["tax_and_insurance"]["annual_tax_cash"]
            + config["tax_and_insurance"]["annual_insurance_premium_cash"]
        ) / 12
    # Post the separately sampled major-repair event, not an unexplained residual.
    monthly_costs[m["repair_month"] - 1] += repair_cost
    if not all(math.isfinite(c) and c >= 0 for c in monthly_costs):
        raise ValueError("Invalid negative/nonfinite monthly operating cash costs")
    if not math.isclose(sum(monthly_costs), annual_cash_cost,
                        rel_tol=1e-10, abs_tol=1e-7):
        raise ValueError("Unexplained annual-to-monthly cost drift; do not hide as repairs")

    capex = [0.0] * 12
    capex[m["field_capex_month"] - 1] += field_capex
    capex[m["house_capex_month"] - 1] += house_capex
    capex[m["lease_capex_month"] - 1] += lease_capex

    rows = []
    for i in range(12):
        draw = real_loan_draw if i + 1 == m["loan_draw_month"] else 0.0
        payment = real_loan_payment if i + 1 == m["loan_payment_month"] else 0.0
        terminal_cash = terminal if i + 1 == m["terminal_month"] else 0.0
        project_cash = revenues[i] - monthly_costs[i] - capex[i] + terminal_cash
        rows.append({
            "year": year, "month": i + 1,
            "revenue": revenues[i], "cash_cost": monthly_costs[i],
            "facility_major_repair_cash_cost": (repair_cost if i + 1 == m["repair_month"] else 0.0),
            "capex": capex[i], "terminal": terminal_cash,
            "project_cash": project_cash, "loan_draw": draw,
            "loan_payment": payment, "equity_cash": project_cash + draw - payment,
        })
    return rows
