from __future__ import annotations

import argparse
import csv
from pathlib import Path

from inspect_xlsx import rows_from_first_sheet


def convert(xlsx_path: Path, csv_path: Path, start_row: int, sheet: int) -> int:
    from inspect_xlsx import rows_from_sheet

    rows = rows_from_sheet(xlsx_path, sheet - 1)
    rows = rows[start_row - 1 :]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the first worksheet of an XLSX file to CSV using only the standard library.")
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--start-row", type=int, default=1, help="1-based first row to write. Use this to skip title/comment rows.")
    parser.add_argument("--sheet", type=int, default=1, help="1-based sheet number to convert.")
    args = parser.parse_args()
    count = convert(args.xlsx, args.csv, args.start_row, args.sheet)
    print(f"Wrote {count} rows to {args.csv}")


if __name__ == "__main__":
    main()
