"""Cross-check RDA 2024 51-crop table values against a supplied local PDF.

No original PDF is committed; --check verifies an independently recorded
canonical row digest in CI without claiming the uploaded PDF is authenticated.
Needs optional PyMuPDF only when --pdf is passed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data/reported/rda_2024_all_51_crop_candidates.csv"
METADATA = ROOT / "data/metadata/rda_2024_source_verification.json"
CROPS = 51
OVERVIEW_KEYS = (
    "revenue_krw_per_10a", "management_cost_krw_per_10a",
    "income_krw_per_10a",
)
LABOR_KEYS = (
    "labor_owner_hours_per_10a", "labor_hired_hours_per_10a",
    "labor_total_hours_per_10a",
)


def rows_and_digest(path=CSV):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != CROPS or len({r["crop_id"] for r in rows}) != CROPS:
        raise ValueError("Expected 51 distinct crop observations")
    serialized = json.dumps(
        rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return rows, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def overview_matches(text, row):
    """Match the three adjacent published integer KRW amounts in correct order."""
    vals = [f'{int(row[k]):,}' for k in OVERVIEW_KEYS]
    return bool(re.search(r"(?<![0-9])" + r"\s+".join(
        re.escape(v) for v in vals) + r"(?![0-9])", text))


def labor_matches(text, row):
    """Require owner, hired and total hours near the labor page's summary."""
    tail = text[-450:]
    return all(re.search(
        r"(?<![0-9.])" + re.escape(f'{float(row[k]):.1f}') + r"(?![0-9.])",
        tail) for k in LABOR_KEYS)


def verify_pdf(pdf_path, csv_path=CSV):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "Install PyMuPDF locally for --pdf: python -m pip install pymupdf"
        ) from exc
    rows, digest = rows_and_digest(csv_path)
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    if len(doc) != 287:
        raise ValueError("Unexpected RDA 2024 PDF page count")
    checked_summary, checked_labor = 0, 0
    for row in rows:
        overview_page = int(row["source_pdf_page"])
        work_page = int(row["labor_source_pdf_page"])
        if overview_page not in (17, 18, 19) or not 127 <= work_page <= 177:
            raise ValueError("Source page out of book range")
        if not overview_matches(doc[overview_page - 1].get_text(), row):
            raise ValueError("RDA gross/cost/income PDF mismatch: " + row["crop_id"])
        checked_summary += 1
        if not labor_matches(doc[work_page - 1].get_text(), row):
            raise ValueError("RDA owner/hired/total labor PDF mismatch: " + row["crop_id"])
        checked_labor += 1
    return {
        "source": "User-supplied 2024 농산물소득자료집.pdf",
        "source_kind": "R_REPORTED_NATIONAL_NOT_PARCEL",
        "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "pdf_pages": len(doc),
        "csv_canonical_row_sha256": digest,
        "crop_records": len(rows),
        "matching_overview_amount_triplets": checked_summary,
        "matching_labor_page_summary_values": checked_labor,
        "checked_pages": {
            "overview": [17, 18, 19],
            "labor_range": [127, 177],
        },
        "verification_scope": (
            "Text extraction matched three consecutive aggregate values "
            "and three labor totals on referenced PDF pages. This checks "
            "transcription, not crop/parcel comparability, source signing, "
            "regional representativeness, receipt validity or annual NPV."
        ),
        "timing_exception": "인삼(4년근) is 4-year one crop; do not annualize",
        "status": "SUPPLIED_PDF_TRANSCRIPTION_CROSSCHECK_NOT_FARM_CALIBRATION",
    }


def check_metadata(path=METADATA, csv_path=CSV):
    rows, digest = rows_and_digest(csv_path)
    metadata = json.loads(Path(path).read_text(encoding="utf-8"))
    if metadata["csv_canonical_row_sha256"] != digest:
        raise ValueError("Stale RDA PDF crosscheck metadata: crop data changed")
    if metadata["crop_records"] != CROPS or any(
        metadata[k] != CROPS for k in (
            "matching_overview_amount_triplets",
            "matching_labor_page_summary_values",
        )
    ):
        raise ValueError("Incomplete PDF crosscheck")
    if metadata["source_kind"] != "R_REPORTED_NATIONAL_NOT_PARCEL":
        raise ValueError("Invalid source status")
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, help="User-supplied local PDF; NEVER commit")
    parser.add_argument("--csv", type=Path, default=CSV)
    parser.add_argument("--metadata", type=Path, default=METADATA)
    parser.add_argument("--write-metadata", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.pdf:
        report = verify_pdf(args.pdf, args.csv)
        if args.write_metadata:
            args.metadata.parent.mkdir(parents=True, exist_ok=True)
            args.metadata.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
    elif args.check and not args.write_metadata:
        report = check_metadata(args.metadata, args.csv)
    else:
        parser.error("Use --check or --pdf [--write-metadata]")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
