#!/usr/bin/env python3
"""Generate Jewish Charity Sector workbook from T3010 DuckDB data.

Produces an Excel workbook with three sheets:
  1. Judaism Category — charities classified under CRA Judaism category
  2. Name-Identified — charities with Jewish/Hebrew name keywords
  3. Notable Foundations — deep search via programs, grants, family names

Usage:
    python3 scripts/reports/generate_jewish_sector.py
"""

import os
import sys
import time
import duckdb
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")
# Fall back to main repo DB when running from a worktree
if not os.path.exists(DB_PATH):
    _alt = os.path.join(PROJECT_ROOT, "..", "..", "..", "data", "db", "cra_charities.duckdb")
    _alt = os.path.normpath(_alt)
    if os.path.exists(_alt):
        DB_PATH = _alt
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "exports")

COLUMNS = ["BN", "Legal Name", "Designation", "Category", "Subcategory",
           "City", "Province", "Registration Date", "Website"]

SELECT_COLS = """
    cb.bn,
    cb.legal_name,
    cb.designation_desc,
    cb.category_desc,
    cb.subcategory_desc,
    cb.city,
    cb.province,
    cb.registration_date,
    cb.website
"""

# High-confidence: include any charity matching these in legal_name
HIGH_CONFIDENCE_KEYWORDS = [
    "jewish", "hebrew", "synagogue", "chabad", "torah", "yeshiva",
    "talmud", "sephardi", "zionist", "mizrachi", "kosher", "hillel",
    "hadassah", "bnai brith",
]

# Medium-confidence: include only if category is religion-adjacent
MEDIUM_CONFIDENCE_KEYWORDS = ["shalom", "israel", "beth"]

RELIGION_CATEGORIES = [
    "Judaism", "Support of Religion", "Foundations Advancing Religions",
    "Other Religions",
]

# Christian 'beth' names to exclude
BETH_EXCLUSIONS = ["bethel", "bethany", "bethesda", "bethlehem"]


def connect():
    return duckdb.connect(DB_PATH, read_only=True)


def write_sheet(ws, headers, rows):
    """Write headers + rows to a worksheet with standard formatting."""
    ws.append(headers)
    header_font = Font(bold=True)
    for col_idx in range(1, len(headers) + 1):
        ws.cell(row=1, column=col_idx).font = header_font

    for row in rows:
        ws.append(list(row))

    # Auto-width columns
    for col_idx, header in enumerate(headers, 1):
        max_len = len(str(header))
        for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            for cell in row:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 50)

    # Freeze header row
    ws.freeze_panes = "A2"


def build_sheet1_judaism_category(con):
    """Sheet 1: Charities in the CRA Judaism category.

    Returns (rows, set_of_bns) for deduplication by later sheets.
    """
    sql = f"""
        SELECT {SELECT_COLS}
        FROM charity_base cb
        WHERE cb.category_desc LIKE '%Judaism%'
        ORDER BY cb.province, cb.legal_name
    """
    rows = con.execute(sql).fetchall()
    bns = {r[0] for r in rows}
    print(f"  Sheet 1 — Judaism Category: {len(rows)} charities")
    return rows, bns


def build_sheet2_name_identified(con, exclude_bns):
    """Sheet 2: Charities with Jewish/Hebrew name keywords, not on Sheet 1.

    Returns (rows_with_keyword, set_of_bns).
    """
    # Build high-confidence WHERE clause
    high_clauses = [f"LOWER(cb.legal_name) LIKE '%{kw}%'" for kw in HIGH_CONFIDENCE_KEYWORDS]
    high_where = " OR ".join(high_clauses)

    # Build medium-confidence WHERE clause (religion-adjacent categories only)
    med_clauses = [f"LOWER(cb.legal_name) LIKE '%{kw}%'" for kw in MEDIUM_CONFIDENCE_KEYWORDS]
    med_where = " OR ".join(med_clauses)
    cat_clauses = [f"cb.category_desc LIKE '%{cat}%'" for cat in RELIGION_CATEGORIES]
    cat_where = " OR ".join(cat_clauses)

    # Beth exclusion
    beth_excl = " AND ".join([f"LOWER(cb.legal_name) NOT LIKE '%{ex}%'" for ex in BETH_EXCLUSIONS])

    sql = f"""
        SELECT {SELECT_COLS}
        FROM charity_base cb
        WHERE (
            ({high_where})
            OR (
                ({med_where})
                AND ({cat_where})
                AND ({beth_excl})
            )
        )
        ORDER BY cb.province, cb.legal_name
    """
    all_rows = con.execute(sql).fetchall()

    # Exclude Sheet 1 BNs and find matching keyword for each
    results = []
    bns = set()
    for row in all_rows:
        bn = row[0]
        if bn in exclude_bns:
            continue
        name_lower = row[1].lower() if row[1] else ""
        matched = []
        for kw in HIGH_CONFIDENCE_KEYWORDS:
            if kw in name_lower:
                matched.append(kw)
        for kw in MEDIUM_CONFIDENCE_KEYWORDS:
            if kw in name_lower:
                matched.append(kw)
        results.append(row + (", ".join(matched),))
        bns.add(bn)

    print(f"  Sheet 2 — Name-Identified: {len(results)} charities")
    return results, bns


def main():
    start = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "jewish_sector_2024.xlsx")

    con = connect()
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # --- Sheet 1: Judaism Category ---
    print("Building Sheet 1: Judaism Category...")
    sheet1_rows, sheet1_bns = build_sheet1_judaism_category(con)
    ws1 = wb.create_sheet("Judaism Category")
    ws1.sheet_properties.tabColor = "4472C4"  # Blue
    write_sheet(ws1, COLUMNS, sheet1_rows)

    # --- Sheet 2: Name-Identified ---
    print("Building Sheet 2: Name-Identified...")
    sheet2_rows, sheet2_bns = build_sheet2_name_identified(con, sheet1_bns)
    ws2 = wb.create_sheet("Name-Identified")
    ws2.sheet_properties.tabColor = "70AD47"  # Green
    write_sheet(ws2, COLUMNS + ["Match Keyword"], sheet2_rows)

    # Save (Sheet 3 added in later tasks)
    wb.save(filepath)
    con.close()

    elapsed = time.time() - start
    print(f"\nSaved to {filepath} ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
