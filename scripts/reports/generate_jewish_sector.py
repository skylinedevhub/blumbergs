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


# Known Jewish philanthropic families — (search_term, false_positive_exclusions)
JEWISH_FAMILY_NAMES = [
    ("azrieli", []),
    ("bronfman", []),
    ("reichmann", []),
    ("asper foundation", []),   # "asper" alone matches "asperger"
    ("gail asper", []),
    ("koffler", []),
    ("schwartz/reisman", []),
    ("schwartz reisman", []),
    ("gerald schwartz", []),
    ("prosserman", []),
    ("sherman foundation", []),  # common name, narrow to foundation
    ("reitman", []),
    ("beutel", []),
    ("cummings jewish", []),     # "cummings" alone matches non-Jewish
    ("tauben", []),
    ("frum", []),
    ("crestohl", []),
    ("drimmer", []),
    ("deitcher", []),
    ("silverstein", []),
    ("rabinovitch", []),
    ("reisman centre", []),
    ("tanenbaum", []),
    ("apotex", []),              # Sherman/Apotex
    ("mirvish", []),
    ("latner", []),
    ("hennick", []),
    ("muzzo", []),
    ("wolfe foundation", []),
    ("goldfarb", []),
    ("schiff", []),
    ("cohl", []),
    ("rosen foundation", []),    # narrow to foundation
    ("larry rosen", []),
    ("weston jewish", []),       # narrow
]


def search_family_foundations(con, exclude_bns):
    """Sheet 3 Pass 1: Known Jewish family foundations."""
    results = []
    bns = set()

    for pattern, exclusions in JEWISH_FAMILY_NAMES:
        sql = f"""
            SELECT {SELECT_COLS}
            FROM charity_base cb
            WHERE LOWER(cb.legal_name) LIKE '%{pattern}%'
            ORDER BY cb.legal_name
        """
        rows = con.execute(sql).fetchall()
        for row in rows:
            bn = row[0]
            if bn in exclude_bns or bn in bns:
                continue
            name_lower = (row[1] or "").lower()
            if any(ex in name_lower for ex in exclusions):
                continue
            results.append(row + (f"Family: {pattern}",))
            bns.add(bn)

    print(f"    Pass 1 — Family foundations: {len(results)}")
    return results, bns


PROGRAM_KEYWORDS = [
    "jewish", "hebrew", "synagogue", "torah", "jewish community",
    "holocaust", "antisemitism", "anti-semitism", "kosher", "talmud",
    "yeshiva", "chabad", "sephardi", "israel bond", "state of israel",
    "kibbutz", "zionist",
]


def search_program_descriptions(con, exclude_bns):
    """Sheet 3 Pass 2: Charities with Jewish keywords in program descriptions."""
    clauses = [f"LOWER(p.\"Program Description\") LIKE '%{kw}%'" for kw in PROGRAM_KEYWORDS]
    where = " OR ".join(clauses)

    sql = f"""
        SELECT DISTINCT {SELECT_COLS}
        FROM charity_base cb
        INNER JOIN programs p ON p."BN/Registration number" = cb.bn
        WHERE ({where})
        ORDER BY cb.legal_name
    """
    all_rows = con.execute(sql).fetchall()

    results = []
    bns = set()
    for row in all_rows:
        bn = row[0]
        if bn in exclude_bns or bn in bns:
            continue
        results.append(row + ("Program description",))
        bns.add(bn)

    print(f"    Pass 2 — Program descriptions: {len(results)}")
    return results, bns


def search_grant_flows(con, known_jewish_names, exclude_bns):
    """Sheet 3 Pass 3: Charities granting to known Jewish organizations."""
    grant_rows = con.execute("""
        SELECT "BN/Registration number", "Grant Recipient Name"
        FROM grants
        WHERE "Grant Recipient Name" IS NOT NULL
    """).fetchall()

    jewish_recipient_kws = [
        "jewish", "hebrew", "synagogue", "chabad", "torah", "yeshiva",
        "israel", "zionist", "hadassah", "bnai",
    ]

    candidate_bns = set()
    for bn, recipient in grant_rows:
        if bn in exclude_bns:
            continue
        recipient_lower = (recipient or "").lower()

        for name in known_jewish_names:
            if name.lower() in recipient_lower or recipient_lower in name.lower():
                candidate_bns.add(bn)
                break
        else:
            for kw in jewish_recipient_kws:
                if kw in recipient_lower:
                    candidate_bns.add(bn)
                    break

    if not candidate_bns:
        print("    Pass 3 — Grant flows: 0")
        return [], set()

    placeholders = ", ".join([f"'{bn}'" for bn in candidate_bns])
    sql = f"""
        SELECT {SELECT_COLS}
        FROM charity_base cb
        WHERE cb.bn IN ({placeholders})
        ORDER BY cb.legal_name
    """
    all_rows = con.execute(sql).fetchall()

    results = []
    bns = set()
    for row in all_rows:
        bn = row[0]
        if bn in exclude_bns or bn in bns:
            continue
        results.append(row + ("Grant to Jewish org",))
        bns.add(bn)

    print(f"    Pass 3 — Grant flows: {len(results)}")
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

    # --- Sheet 3: Notable Foundations & Institutions ---
    print("Building Sheet 3: Notable Foundations & Institutions...")
    exclude_bns = sheet1_bns | sheet2_bns
    sheet3_rows = []
    sheet3_bns = set()

    # Collect known Jewish names for grant flow matching
    known_jewish_names = set()
    for row in sheet1_rows:
        if row[1]:
            known_jewish_names.add(row[1])
    for row in sheet2_rows:
        if row[1]:
            known_jewish_names.add(row[1])

    # Pass 1: Family foundations
    p1_rows, p1_bns = search_family_foundations(con, exclude_bns)
    sheet3_rows.extend(p1_rows)
    sheet3_bns.update(p1_bns)
    exclude_bns.update(p1_bns)
    for row in p1_rows:
        if row[1]:
            known_jewish_names.add(row[1])

    # Pass 2: Program descriptions
    p2_rows, p2_bns = search_program_descriptions(con, exclude_bns)
    sheet3_rows.extend(p2_rows)
    sheet3_bns.update(p2_bns)
    exclude_bns.update(p2_bns)
    for row in p2_rows:
        if row[1]:
            known_jewish_names.add(row[1])

    # Pass 3: Grant flows
    p3_rows, p3_bns = search_grant_flows(con, known_jewish_names, exclude_bns)
    sheet3_rows.extend(p3_rows)
    sheet3_bns.update(p3_bns)

    print(f"  Sheet 3 — Total: {len(sheet3_rows)} charities")

    ws3 = wb.create_sheet("Notable Foundations")
    ws3.sheet_properties.tabColor = "ED7D31"  # Orange
    write_sheet(ws3, COLUMNS + ["Detection Method"], sheet3_rows)

    # --- Summary ---
    total = len(sheet1_rows) + len(sheet2_rows) + len(sheet3_rows)
    print(f"\n  Total Jewish charity sector: {total} charities")
    print(f"    Sheet 1 (Judaism Category): {len(sheet1_rows)}")
    print(f"    Sheet 2 (Name-Identified):  {len(sheet2_rows)}")
    print(f"    Sheet 3 (Notable/Deep):     {len(sheet3_rows)}")

    wb.save(filepath)
    con.close()

    elapsed = time.time() - start
    print(f"\nSaved to {filepath} ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
