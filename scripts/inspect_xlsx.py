from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    value = 0
    for letter in letters:
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return value - 1


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings = []
    for node in root.findall("a:si", NS):
        strings.append("".join(text.text or "" for text in node.findall(".//a:t", NS)))
    return strings


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    value_node = cell.find("a:v", NS)
    if value_node is None or value_node.text is None:
        inline = cell.find("a:is", NS)
        if inline is not None:
            return "".join(text.text or "" for text in inline.findall(".//a:t", NS))
        return ""
    value = value_node.text
    if cell.attrib.get("t") == "s":
        return strings[int(value)] if value.isdigit() and int(value) < len(strings) else value
    return value


def workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels
    }
    sheets = []
    for sheet in workbook.findall(".//a:sheet", NS):
        name = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get(f"{{{NS['r']}}}id")
        target = rel_map.get(rel_id or "", "")
        if target:
            if not target.startswith("xl/"):
                target = f"xl/{target.lstrip('/')}"
            sheets.append((name, target))
    return sheets


def rows_from_sheet(path: Path, sheet_index: int = 0) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheets = workbook_sheets(zf)
        sheet_name = sheets[sheet_index][1] if sheets else "xl/worksheets/sheet1.xml"
        root = ET.fromstring(zf.read(sheet_name))
        rows = []
        for row in root.findall(".//a:row", NS):
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                idx = column_index(cell.attrib.get("r", "A1"))
                while len(values) <= idx:
                    values.append("")
                values[idx] = cell_value(cell, strings)
            rows.append(values)
        return rows


def rows_from_first_sheet(path: Path) -> list[list[str]]:
    return rows_from_sheet(path, 0)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Inspect the first worksheet of an XLSX file using only the standard library.")
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--sheet", type=int, default=1, help="1-based sheet number to inspect.")
    parser.add_argument("--list-sheets", action="store_true")
    args = parser.parse_args()
    if args.list_sheets:
        with zipfile.ZipFile(args.xlsx) as zf:
            for idx, (name, target) in enumerate(workbook_sheets(zf), start=1):
                row_count = len(rows_from_sheet(args.xlsx, idx - 1))
                print(f"{idx}\t{name}\t{row_count}\t{target}")
        return
    rows = rows_from_sheet(args.xlsx, args.sheet - 1)
    print(f"file={args.xlsx}")
    print(f"rows={len(rows)}")
    for row in rows[: args.rows]:
        print("\t".join(row))


if __name__ == "__main__":
    main()
