"""Command-line interface: scenario engine; no implicit live API access."""
import argparse
import json
from pathlib import Path
from .model import PLANS, SCENARIOS, read_config, read_weather, simulate
from .cashflow import validate_cashflow_config
from .comparison import compare_plans, save_comparison_csv

ROOT = Path(__file__).resolve().parents[2]

def main(argv=None):
    p = argparse.ArgumentParser(prog="farm-strategy")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="Check input data source and uncertainty status")
    for cmd in ("compare", "forecast"):
        sp = sub.add_parser(cmd)
        sp.add_argument("--scenario", choices=SCENARIOS, default="base")
        sp.add_argument("--window", choices=("recent10", "all20"), default="recent10")
        sp.add_argument("--seed", type=int, default=42)
        sp.add_argument("--paths", type=int, default=1000)
        sp.add_argument("--output", type=Path)
        if cmd == "compare":
            sp.add_argument("--stress-matrix", action="store_true",
                            help="Compare every available stress scenario (assumptions only)")
            sp.add_argument("--csv", type=Path,
                            help="Write a flat scenario-by-plan comparison table")
        if cmd == "forecast":
            sp.add_argument("--plan", choices=PLANS, default="new_cucumber_house")
            sp.add_argument("--monthly-details", action="store_true",
                            help="Include 120 months from a single seeded path, not a median")
    p.add_argument("--config", type=Path, default=ROOT / "configs/base.json")
    p.add_argument("--weather", type=Path, default=ROOT / "data/processed/annual_weather.csv")
    args = p.parse_args(argv)
    config = read_config(args.config)
    observed = read_weather(args.weather)
    validate_cashflow_config(config["finance"], config["monthly_cashflow"])
    if args.cmd == "validate":
        result = {"n_weather_years": len(observed),
                  "years": [int(x["year"]) for x in observed],
                  "weather_source": config["metadata"]["weather_source"],
                  "price_source": config["metadata"]["price_source"],
                  "damage_parameters_status": config["metadata"]["damage_parameters_status"],
                  "tax_insurance_status": config["tax_and_insurance"]["status"],
                  "monthly_cashflow_status": config["monthly_cashflow"]["status"],
                  "assumed_annual_inflation_rate": config["finance"]["assumed_annual_inflation_rate"]}
    elif args.cmd == "compare":
        result = compare_plans(
            observed, config, seed=args.seed, paths=args.paths,
            scenario=args.scenario, window=args.window,
            stress_matrix=args.stress_matrix)
        if args.csv:
            save_comparison_csv(result, args.csv)
    else:
        result = simulate(args.plan, args.scenario, observed, config,
                          seed=args.seed, paths=args.paths, window=args.window,
                          include_monthly_details=args.monthly_details)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if getattr(args, "output", None):
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
