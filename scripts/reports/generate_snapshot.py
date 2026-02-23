#!/usr/bin/env python3
"""Generate Blumbergs Snapshot Excel workbooks from T3010 DuckDB data.

Produces workbooks with aggregated T3010 line totals, mirroring the
filled-in T3010 form used in Blumbergs Snapshot publications.

Usage:
    python3 scripts/reports/generate_snapshot.py          # Canada only
    python3 scripts/reports/generate_snapshot.py --all     # All 13 workbooks
    python3 scripts/reports/generate_snapshot.py --province ON
    python3 scripts/reports/generate_snapshot.py --provincial
    python3 scripts/reports/generate_snapshot.py --designation A
    python3 scripts/reports/generate_snapshot.py --designations
"""

import argparse
import os
import sys
import time
import duckdb
from openpyxl import Workbook
from openpyxl.styles import Font, numbers

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "exports", "snapshots_2024")

# BN column name varies by table
BN_COL = {
    "ident": '"BN/Registration Number"',
    "financial_d": '"BN/Registration Number"',
    "financial_abc": '"BN/Registration number"',
    "schedule_1_foundations": '"BN/Registration number"',
    "schedule_2_summary": '"BN/Registration number"',
    "schedule_3_compensation": '"BN/Registration number"',
    "schedule_5_noncash": '"BN/Registration number"',
    "schedule_8_disbursement": '"BN/Registration Number"',
}

PROVINCES = ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB"]
ATLANTIC = ["NB", "NS", "NL", "PE"]
DESIGNATIONS = {
    "A": "Public Foundation",
    "B": "Private Foundation",
    "C": "Charitable Organization",
}


def money(col):
    """SQL expression to convert '$1,234' VARCHAR to DECIMAL."""
    return f"TRY_CAST(REPLACE(REPLACE({col}, '$', ''), ',', '') AS DECIMAL)"


def get_scope_filter(filter_type, filter_value):
    """Return (WHERE clause for charity_base, description string, filename suffix)."""
    if filter_type == "all":
        return "1=1", "Canadian Charity Sector", "canada"
    elif filter_type == "province":
        if filter_value == "Atlantic":
            provinces = "','".join(ATLANTIC)
            return (
                f"cb.province IN ('{provinces}')",
                "Atlantic Provinces Charity Sector",
                "atlantic",
            )
        return (
            f"cb.province = '{filter_value}'",
            f"{filter_value} Charity Sector",
            filter_value,
        )
    elif filter_type == "designation":
        desc = DESIGNATIONS.get(filter_value, filter_value)
        return (
            f"cb.designation_code = '{filter_value}'",
            f"{desc}s in the Canadian Charity Sector",
            f"designation_{filter_value}",
        )
    raise ValueError(f"Unknown filter_type: {filter_type}")


def scoped_table(table, where_clause):
    """Return a FROM+JOIN+WHERE clause that filters a table by scope.

    Uses charity_base (cb) as the scope filter, joined on BN.
    """
    bn = BN_COL[table]
    return f"""
        {table} t
        INNER JOIN charity_base cb ON t.{bn} = cb.bn
        WHERE {where_clause}
    """


def connect():
    return duckdb.connect(DB_PATH, read_only=True)


def generate_snapshot(filter_type, filter_value):
    """Generate one snapshot workbook."""
    where, description, suffix = get_scope_filter(filter_type, filter_value)
    filename = f"snapshot_2024_{suffix}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    con = connect()
    wb = Workbook()

    # Count charities in scope
    total = con.execute(f"SELECT COUNT(*) FROM charity_base cb WHERE {where}").fetchone()[0]
    print(f"  Generating {filename} — {description} ({total:,} charities)")

    # Build each sheet
    build_section_a(wb, con, where, description, total)
    build_section_c(wb, con, where)
    build_section_d(wb, con, where)
    build_schedule_1(wb, con, where)
    build_schedule_2(wb, con, where)
    build_schedule_3(wb, con, where)
    build_schedule_5(wb, con, where)
    build_schedule_6(wb, con, where)
    build_schedule_8(wb, con, where)

    # Remove default empty sheet if present
    if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
        del wb["Sheet"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    wb.save(filepath)
    con.close()
    return filepath


# -- Sheet builders (Tasks 2-9) go here --


def build_section_a(wb, con, where, description, total):
    """Section A: Identification — charity counts, contact info, A1-A3."""
    ws = wb.create_sheet("Section A")
    bold = Font(bold=True)
    st = scoped_table

    # Header
    ws.append([f"Blumbergs Snapshot 2024 — {description}"])
    ws["A1"].font = bold
    ws.append([f"Based on T3010 filings for {total:,} registered charities."])
    ws.append([])

    ws.append(["", "Metric", "Value"])
    ws[f"B{ws.max_row}"].font = bold
    ws[f"C{ws.max_row}"].font = bold

    # Total charities (from charity_base, the scope table)
    ws.append(["", "Total registered charities in scope", total])

    # By designation
    rows = con.execute(f"""
        SELECT designation_code, designation_desc, COUNT(*)
        FROM charity_base cb WHERE {where}
        GROUP BY 1, 2 ORDER BY 1
    """).fetchall()
    for code, desc, cnt in rows:
        ws.append(["", f"  {code}: {desc}", cnt])

    # Contact info
    phone = con.execute(f"""
        SELECT COUNT(*) FROM ident t
        INNER JOIN charity_base cb ON t."BN/Registration Number" = cb.bn
        WHERE {where} AND t."Contact Phone" IS NOT NULL AND t."Contact Phone" != ''
    """).fetchone()[0]
    email = con.execute(f"""
        SELECT COUNT(*) FROM ident t
        INNER JOIN charity_base cb ON t."BN/Registration Number" = cb.bn
        WHERE {where} AND t."Contact Email" IS NOT NULL AND t."Contact Email" != ''
    """).fetchone()[0]
    url = con.execute(f"""
        SELECT COUNT(*) FROM ident t
        INNER JOIN charity_base cb ON t."BN/Registration Number" = cb.bn
        WHERE {where} AND t."Contact URL" IS NOT NULL AND t."Contact URL" != ''
    """).fetchone()[0]
    ws.append(["", "Provided phone numbers", phone])
    ws.append(["", "Provided email addresses", email])
    ws.append(["", "Provided websites", url])

    # A1-A3 yes/no counts
    ws.append([])
    ws.append(["Line", "Question", "Yes", "No"])
    ws[f"A{ws.max_row}"].font = bold

    for line, label in [
        ("1510 Subordinate position to a parent organization?", "A1: Subordinate to parent org?"),
        ("1570", "A2: Wound up/dissolved/terminated?"),
        ("1600", "A3: Designated as public/private foundation?"),
    ]:
        col = f'"{line}"'
        y = con.execute(f"SELECT COUNT(*) FROM {st('financial_abc', where)} AND t.{col} = 'Y'").fetchone()[0]
        n = con.execute(f"SELECT COUNT(*) FROM {st('financial_abc', where)} AND t.{col} = 'N'").fetchone()[0]
        ws.append([line.split(" ")[0] if " " in line else line, label, y, n])

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 45
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15


def build_section_c(wb, con, where):
    ws = wb.create_sheet("Section C")
    ws.append(["Section C", "", "placeholder"])


def build_section_d(wb, con, where):
    ws = wb.create_sheet("Section D")
    ws.append(["Section D", "", "placeholder"])


def build_schedule_1(wb, con, where):
    ws = wb.create_sheet("Schedule 1")
    ws.append(["Schedule 1", "", "placeholder"])


def build_schedule_2(wb, con, where):
    ws = wb.create_sheet("Schedule 2")
    ws.append(["Schedule 2", "", "placeholder"])


def build_schedule_3(wb, con, where):
    ws = wb.create_sheet("Schedule 3")
    ws.append(["Schedule 3", "", "placeholder"])


def build_schedule_5(wb, con, where):
    ws = wb.create_sheet("Schedule 5")
    ws.append(["Schedule 5", "", "placeholder"])


def build_schedule_6(wb, con, where):
    ws = wb.create_sheet("Schedule 6")
    ws.append(["Schedule 6", "", "placeholder"])


def build_schedule_8(wb, con, where):
    ws = wb.create_sheet("Schedule 8")
    ws.append(["Schedule 8", "", "placeholder"])


def main():
    parser = argparse.ArgumentParser(description="Generate Blumbergs Snapshot workbooks")
    parser.add_argument("--all", action="store_true", help="Generate all 13 workbooks")
    parser.add_argument("--province", type=str, help="Single province code (e.g. ON)")
    parser.add_argument("--provincial", action="store_true", help="All 9 provincial workbooks")
    parser.add_argument("--designation", nargs="?", const="ALL", type=str,
                        help="Designation code (A/B/C) or omit for all three")
    parser.add_argument("--designations", action="store_true", help="All 3 designation workbooks")
    args = parser.parse_args()

    start = time.time()
    jobs = []

    if args.all:
        jobs.append(("all", None))
        for p in PROVINCES:
            jobs.append(("province", p))
        jobs.append(("province", "Atlantic"))
        for d in DESIGNATIONS:
            jobs.append(("designation", d))
    elif args.province:
        jobs.append(("province", args.province))
    elif args.provincial:
        for p in PROVINCES:
            jobs.append(("province", p))
        jobs.append(("province", "Atlantic"))
    elif args.designations or (args.designation and args.designation == "ALL"):
        for d in DESIGNATIONS:
            jobs.append(("designation", d))
    elif args.designation:
        jobs.append(("designation", args.designation))
    else:
        jobs.append(("all", None))

    print(f"Generating {len(jobs)} snapshot workbook(s)...")
    paths = []
    for ftype, fval in jobs:
        path = generate_snapshot(ftype, fval)
        paths.append(path)

    elapsed = time.time() - start
    print(f"\nDone. {len(paths)} workbook(s) generated in {elapsed:.1f}s")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
