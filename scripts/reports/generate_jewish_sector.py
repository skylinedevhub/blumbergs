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
from openpyxl.styles import numbers

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

FINANCIAL_COLUMNS = [
    "Total Revenue", "Total Expenditures", "Total Assets", "Total Liabilities",
    "Tax-Receipted Gifts", "Gifts from Charities", "Govt Funding",
    "Charitable Expenditures", "Mgmt & Admin", "Fundraising",
    "Gifts to Qual. Donees", "FT Employees", "PT Employees", "Total Compensation",
]


def money(col):
    """SQL expression to convert '$1,234' VARCHAR to DECIMAL."""
    return f"TRY_CAST(REPLACE(REPLACE({col}, '$', ''), ',', '') AS DECIMAL)"


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

FINANCIAL_SELECT = f"""
    {money('fd."4700"')} AS total_revenue,
    {money('fd."5100"')} AS total_expenditures,
    {money('fd."4200"')} AS total_assets,
    {money('fd."4350"')} AS total_liabilities,
    {money('fd."4500"')} AS tax_receipted_gifts,
    {money('fd."4510"')} AS gifts_from_charities,
    (COALESCE({money('fd."4540"')}, 0) + COALESCE({money('fd."4550"')}, 0) + COALESCE({money('fd."4560"')}, 0)) AS govt_funding,
    {money('fd."5000"')} AS charitable_expenditures,
    {money('fd."5010"')} AS mgmt_admin,
    {money('fd."5020"')} AS fundraising,
    {money('fd."5050"')} AS gifts_to_qual_donees,
    s3."300" AS ft_employees,
    s3."370" AS pt_employees,
    {money('s3."390"')} AS total_compensation
"""

FINANCIAL_JOINS = """
    LEFT JOIN latest_filing lf ON lf.bn = cb.bn
    LEFT JOIN financial_d fd ON fd."BN/Registration Number" = cb.bn
        AND fd."Fiscal period end" = lf.latest_fiscal_end
    LEFT JOIN schedule_3_compensation s3 ON s3."BN/Registration number" = cb.bn
        AND s3."Fiscal period end" = lf.latest_fiscal_end
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
    """Write headers + totals row + data rows to a worksheet with formatting."""
    # Row 1: headers
    ws.append(headers)
    header_font = Font(bold=True)
    for col_idx in range(1, len(headers) + 1):
        ws.cell(row=1, column=col_idx).font = header_font

    # Row 2: placeholder TOTALS row (formulas filled after data)
    totals_placeholder = ["TOTALS"] + [None] * (len(headers) - 1)
    ws.append(totals_placeholder)
    ws.cell(row=2, column=1).font = Font(bold=True)

    # Row 3+: data
    for row in rows:
        ws.append(list(row))

    # Fill TOTALS formulas for financial columns
    data_start = 3
    data_end = ws.max_row
    if data_end >= data_start:
        for col_idx, header in enumerate(headers, 1):
            if header in FINANCIAL_COLUMNS:
                col_letter = get_column_letter(col_idx)
                ws.cell(row=2, column=col_idx).value = \
                    f"=SUM({col_letter}{data_start}:{col_letter}{data_end})"
                ws.cell(row=2, column=col_idx).font = Font(bold=True)
                ws.cell(row=2, column=col_idx).number_format = '#,##0'

    # Apply number formatting to financial data cells
    for col_idx, header in enumerate(headers, 1):
        if header in FINANCIAL_COLUMNS:
            for row_cells in ws.iter_rows(min_row=data_start, min_col=col_idx, max_col=col_idx):
                for cell in row_cells:
                    if cell.value is not None:
                        cell.number_format = '#,##0'

    # Auto-width columns
    for col_idx, header in enumerate(headers, 1):
        max_len = len(str(header))
        for row_cells in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            for cell in row_cells:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 50)

    # Freeze header + totals row
    ws.freeze_panes = "A3"


def build_sheet1_judaism_category(con):
    """Sheet 1: Charities in the CRA Judaism category.

    Returns (rows, set_of_bns) for deduplication by later sheets.
    """
    sql = f"""
        SELECT {SELECT_COLS},
            {FINANCIAL_SELECT}
        FROM charity_base cb
        {FINANCIAL_JOINS}
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
        SELECT {SELECT_COLS},
            {FINANCIAL_SELECT}
        FROM charity_base cb
        {FINANCIAL_JOINS}
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
    # The first 9 cols are identity, next 14 are financial
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
        # Insert match keyword after identity cols (idx 9), before financial cols
        results.append(row[:9] + (", ".join(matched),) + row[9:])
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
            SELECT {SELECT_COLS},
                {FINANCIAL_SELECT}
            FROM charity_base cb
            {FINANCIAL_JOINS}
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
            # Insert detection method after identity cols (idx 9), before financial cols
            results.append(row[:9] + (f"Family: {pattern}",) + row[9:])
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
        SELECT DISTINCT {SELECT_COLS},
            {FINANCIAL_SELECT}
        FROM charity_base cb
        INNER JOIN programs p ON p."BN/Registration number" = cb.bn
        {FINANCIAL_JOINS}
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
        # Insert detection method after identity cols (idx 9), before financial cols
        results.append(row[:9] + ("Program description",) + row[9:])
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
        SELECT {SELECT_COLS},
            {FINANCIAL_SELECT}
        FROM charity_base cb
        {FINANCIAL_JOINS}
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
        # Insert detection method after identity cols (idx 9), before financial cols
        results.append(row[:9] + ("Grant to Jewish org",) + row[9:])
        bns.add(bn)

    print(f"    Pass 3 — Grant flows: {len(results)}")
    return results, bns


def build_summary_sheet(wb, con, all_bns, sheet_counts):
    """Build a Summary sheet with aggregated financial totals for all Jewish charities."""
    ws = wb.create_sheet("Summary")
    ws.sheet_properties.tabColor = "7030A0"  # Purple

    if not all_bns:
        ws.append(["No charities found."])
        return

    bn_list = ", ".join([f"'{bn}'" for bn in all_bns])
    where_bn = f'cb.bn IN ({bn_list})'

    def sum_line(col):
        """Sum a financial_d column across all Jewish sector BNs."""
        result = con.execute(f"""
            SELECT SUM({money(f'fd."{col}"')})
            FROM financial_d fd
            INNER JOIN charity_base cb ON fd."BN/Registration Number" = cb.bn
            WHERE {where_bn}
        """).fetchone()[0]
        return result

    def sum_s3_money(col):
        """Sum a schedule_3 VARCHAR currency column."""
        result = con.execute(f"""
            SELECT SUM({money(f's3."{col}"')})
            FROM schedule_3_compensation s3
            INNER JOIN charity_base cb ON s3."BN/Registration number" = cb.bn
            WHERE {where_bn}
        """).fetchone()[0]
        return result

    def sum_s3_int(col):
        """Sum a schedule_3 BIGINT column."""
        result = con.execute(f"""
            SELECT SUM(s3."{col}")
            FROM schedule_3_compensation s3
            INNER JOIN charity_base cb ON s3."BN/Registration number" = cb.bn
            WHERE {where_bn}
        """).fetchone()[0]
        return result

    # Designation breakdown
    designation_counts = con.execute(f"""
        SELECT cb.designation_desc, COUNT(*)
        FROM charity_base cb
        WHERE {where_bn}
        GROUP BY cb.designation_desc
        ORDER BY cb.designation_desc
    """).fetchall()

    total_charities = len(all_bns)

    # --- Title ---
    bold14 = Font(bold=True, size=14)
    bold12 = Font(bold=True, size=12)
    bold = Font(bold=True)
    currency_fmt = '#,##0'

    ws.append(["Jewish Charity Sector — Financial Summary 2024"])
    ws.cell(row=1, column=1).font = bold14
    ws.append([f"Based on T3010 filings for {total_charities} registered charities."])
    ws.append([])

    # --- OVERVIEW ---
    ws.append(["OVERVIEW"])
    ws.cell(row=ws.max_row, column=1).font = bold12
    ws.append([])
    ws.append(["Total charities:", total_charities])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).number_format = '#,##0'
    for sheet_name, count in sheet_counts:
        ws.append([f"  {sheet_name}:", count])
        ws.cell(row=ws.max_row, column=2).number_format = '#,##0'

    ws.append([])
    ws.append(["By Designation:"])
    ws.cell(row=ws.max_row, column=1).font = bold
    for desc, count in designation_counts:
        ws.append([f"  {desc}:", count])
        ws.cell(row=ws.max_row, column=2).number_format = '#,##0'

    # --- FINANCIAL POSITION (D2) ---
    ws.append([])
    ws.append(["FINANCIAL POSITION (D2)"])
    ws.cell(row=ws.max_row, column=1).font = bold12
    ws.append(["Line", "Description", "Value"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold

    for line, desc in [("4200", "Total assets"), ("4350", "Total liabilities")]:
        val = sum_line(line)
        ws.append([line, desc, val])
        ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    # --- REVENUE (D3) ---
    ws.append([])
    ws.append(["REVENUE (D3)"])
    ws.cell(row=ws.max_row, column=1).font = bold12
    ws.append(["Line", "Description", "Value"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold

    revenue_lines = [
        ("4500", "Tax-receipted gifts"),
        ("4510", "Gifts from other charities"),
        ("4540", "Federal government"),
        ("4550", "Provincial/territorial"),
        ("4560", "Municipal/regional"),
    ]
    for line, desc in revenue_lines:
        val = sum_line(line)
        ws.append([line, desc, val])
        ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    # Computed total government
    govt_total = con.execute(f"""
        SELECT SUM(
            COALESCE({money('fd."4540"')}, 0) +
            COALESCE({money('fd."4550"')}, 0) +
            COALESCE({money('fd."4560"')}, 0)
        )
        FROM financial_d fd
        INNER JOIN charity_base cb ON fd."BN/Registration Number" = cb.bn
        WHERE {where_bn}
    """).fetchone()[0]
    ws.append(["4570*", "Total government (computed)", govt_total])
    ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    total_rev = sum_line("4700")
    ws.append(["4700", "TOTAL REVENUE", total_rev])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold
    ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    # --- EXPENDITURES (D4) ---
    ws.append([])
    ws.append(["EXPENDITURES (D4)"])
    ws.cell(row=ws.max_row, column=1).font = bold12
    ws.append(["Line", "Description", "Value"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold

    expenditure_lines = [
        ("4880", "Total compensation"),
        ("5000", "Charitable activities"),
        ("5010", "Management and administration"),
        ("5020", "Fundraising"),
        ("5050", "Gifts to qualified donees"),
    ]
    for line, desc in expenditure_lines:
        val = sum_line(line)
        ws.append([line, desc, val])
        ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    total_exp = sum_line("5100")
    ws.append(["5100", "TOTAL EXPENDITURES", total_exp])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold
    ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    # --- COMPENSATION (Schedule 3) ---
    ws.append([])
    ws.append(["COMPENSATION (Schedule 3)"])
    ws.cell(row=ws.max_row, column=1).font = bold12
    ws.append(["Line", "Description", "Value"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.cell(row=ws.max_row, column=2).font = bold
    ws.cell(row=ws.max_row, column=3).font = bold

    ft = sum_s3_int("300")
    ws.append(["300", "FT positions", ft])
    ws.cell(row=ws.max_row, column=3).number_format = '#,##0'

    pt = sum_s3_int("370")
    ws.append(["370", "PT positions", pt])
    ws.cell(row=ws.max_row, column=3).number_format = '#,##0'

    comp = sum_s3_money("390")
    ws.append(["390", "Total compensation", comp])
    ws.cell(row=ws.max_row, column=3).number_format = currency_fmt

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 22


def main():
    start = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "jewish_sector_2024.xlsx")

    con = connect()
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # Detail sheet headers: identity columns + financial columns
    sheet1_headers = COLUMNS + FINANCIAL_COLUMNS
    sheet2_headers = COLUMNS + ["Match Keyword"] + FINANCIAL_COLUMNS
    sheet3_headers = COLUMNS + ["Detection Method"] + FINANCIAL_COLUMNS

    # --- Sheet 1: Judaism Category ---
    print("Building Sheet 1: Judaism Category...")
    sheet1_rows, sheet1_bns = build_sheet1_judaism_category(con)
    ws1 = wb.create_sheet("Judaism Category")
    ws1.sheet_properties.tabColor = "4472C4"  # Blue
    write_sheet(ws1, sheet1_headers, sheet1_rows)

    # --- Sheet 2: Name-Identified ---
    print("Building Sheet 2: Name-Identified...")
    sheet2_rows, sheet2_bns = build_sheet2_name_identified(con, sheet1_bns)
    ws2 = wb.create_sheet("Name-Identified")
    ws2.sheet_properties.tabColor = "70AD47"  # Green
    write_sheet(ws2, sheet2_headers, sheet2_rows)

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
    write_sheet(ws3, sheet3_headers, sheet3_rows)

    # --- Summary sheet ---
    print("\nBuilding Summary sheet...")
    all_bns = sheet1_bns | sheet2_bns | sheet3_bns
    sheet_counts = [
        ("Judaism Category", len(sheet1_rows)),
        ("Name-Identified", len(sheet2_rows)),
        ("Notable Foundations", len(sheet3_rows)),
    ]
    build_summary_sheet(wb, con, all_bns, sheet_counts)

    # Move Summary to first position
    wb.move_sheet("Summary", offset=-(len(wb.sheetnames) - 1))

    # --- Console summary ---
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
