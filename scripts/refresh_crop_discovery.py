"""Validate/refresh the 2024 RDA public statistics embedded in the offline crop explorer.

Does not calculate farm profitability or modify the five-plan simulation.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
# Keep direct ``python scripts/refresh_crop_discovery.py`` usable from checkout.
sys.path.insert(0, str(ROOT / "src"))
from farm_strategy.reported import (  # noqa: E402
    CATEGORIES, NUMERIC_INT, NUMERIC_FLOAT, load_source,
)

CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
HTML = ROOT / "dashboard/crop-discovery/index.html"
BINDING = re.compile(r"(const DATA=)(\[.*?\])(;\s*\nconst cats=)", re.DOTALL)


def process(csv_path=CSV, html_path=HTML, *, check=False):
    data = load_source(csv_path)
    path = Path(html_path)
    content = path.read_text(encoding="utf-8")
    found = BINDING.search(content)
    if found is None:
        raise ValueError("Embedded crop data slot was not found in HTML")
    old = json.loads(found.group(2))
    if check:
        if old != data:
            raise ValueError("Crop discovery HTML is STALE relative to the RDA CSV")
        return False
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    content = content[:found.start(2)] + encoded + content[found.end(2):]
    path.write_text(content, encoding="utf-8")
    return old != data


def main():
    p = argparse.ArgumentParser(description="Reconcile public RDA 2024 crop index")
    p.add_argument("--csv", type=Path, default=CSV)
    p.add_argument("--html", type=Path, default=HTML)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--refresh", action="store_true")
    args = p.parse_args()
    process(args.csv, args.html, check=args.check)
    print("RDA 2024 51-crop data valid; offline HTML " +
          ("current" if args.check else "refreshed"))


if __name__ == "__main__":
    main()
