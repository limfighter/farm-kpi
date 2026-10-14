"""KMA CP949 hourly ASOS integrity/QC audit. Does not interpret blank rain as 0.

Audit only: v10-derived daily/annual features are preserved as immutable reference
until original hourly inputs can be reprocessed and independently reconciled.
"""
import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path

COLUMNS = {
    "temperature": ("기온(°C)", "기온 QC플래그"),
    "humidity": ("습도(%)", "습도 QC플래그"),
    "wind": ("풍속(m/s)", "풍속 QC플래그"),
    "rain": ("강수량(mm)", "강수량 QC플래그"),
}
BAD_QC = {"8", "9"}


def audit_hourly(paths, station="146", start="2006-01-01 00:00", end="2025-12-31 23:00"):
    lo = datetime.strptime(start, "%Y-%m-%d %H:%M")
    hi = datetime.strptime(end, "%Y-%m-%d %H:%M")
    if hi < lo:
        raise ValueError("end must be >= start")
    files = [Path(p) for p in paths]
    if not files:
        raise ValueError("No hourly files specified")
    seen = {}
    duplicate_count = 0
    conflicts = {field: 0 for field in COLUMNS}
    qc_rejections = {field: 0 for field in COLUMNS}
    for path in files:
        with path.open(encoding="cp949", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"지점", "일시"} | {column for pair in COLUMNS.values() for column in pair}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(f"Missing ASOS column(s) in {path.name}")
            for row in reader:
                if row["지점"].strip() != str(station):
                    continue
                at = datetime.strptime(row["일시"].strip(), "%Y-%m-%d %H:%M")
                if at < lo or at > hi:
                    continue
                obs = {}
                for field, (value_col, qc_col) in COLUMNS.items():
                    raw = (row.get(value_col) or "").strip()
                    qc = (row.get(qc_col) or "").strip()
                    if qc in BAD_QC:
                        qc_rejections[field] += 1
                    if not raw or qc in BAD_QC:
                        obs[field] = None
                    else:
                        val = float(raw)
                        if field == "rain" and val < 0:
                            raise ValueError(f"Negative ASOS rainfall at {at}")
                        obs[field] = val
                if at in seen:
                    duplicate_count += 1
                    old = seen[at]
                    for key in COLUMNS:
                        if old[key] is not None and obs[key] is not None and old[key] != obs[key]:
                            conflicts[key] += 1
                    if sum(v is not None for v in obs.values()) > sum(v is not None for v in old.values()):
                        seen[at] = obs
                else:
                    seen[at] = obs
    expected = int((hi - lo) / timedelta(hours=1)) + 1
    missing = []
    cursor = lo
    while cursor <= hi:
        if cursor not in seen:
            missing.append(cursor.isoformat())
        cursor += timedelta(hours=1)
    return {
        "station": str(station),
        "period": [lo.isoformat(), hi.isoformat()],
        "files_scanned": len(files),
        "expected_hours": expected,
        "unique_hours": len(seen),
        "missing_hours": missing,
        "duplicate_records": duplicate_count,
        "conflicting_duplicate_fields": {k: n for k, n in conflicts.items() if n},
        "valid_value_hours": {k: sum(r[k] is not None for r in seen.values()) for k in COLUMNS},
        "qc_rejections_in_source_rows": qc_rejections,
        "rain_policy": "Missing/blank/QC8/QC9 rainfall stays unknown, not zero",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit KMA 146 CP949 hourly observations without rewriting source files")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--station", default="146")
    parser.add_argument("--start", default="2006-01-01 00:00")
    parser.add_argument("--end", default="2025-12-31 23:00")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit_hourly(args.files, station=args.station, start=args.start, end=args.end)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(exist_ok=True, parents=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
