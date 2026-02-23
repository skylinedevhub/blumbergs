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
    """Section C: Programs, general info, fundraising, DAF."""
    ws = wb.create_sheet("Section C")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Section C: Programs and General Information"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Question / Metric", "Yes / Count", "No", "Notes"])
    for c in ["A", "B", "C", "D", "E"]:
        ws[f"{c}3"].font = bold

    def yn(col_name, label, notes=""):
        """Add a yes/no count row for a financial_abc column."""
        col = f'"{col_name}"'
        y = con.execute(f"SELECT COUNT(*) FROM {st('financial_abc', where)} AND t.{col} = 'Y'").fetchone()[0]
        n = con.execute(f"SELECT COUNT(*) FROM {st('financial_abc', where)} AND t.{col} = 'N'").fetchone()[0]
        ws.append([col_name, label, y, n, notes])

    def count_method(col_name, label):
        """Count non-null checkboxes for fundraising methods."""
        col = f'"{col_name}"'
        cnt = con.execute(f"SELECT COUNT(*) FROM {st('financial_abc', where)} AND t.{col} = 'Y'").fetchone()[0]
        ws.append([col_name, label, cnt])

    # C1 Active?
    yn("1800", "C1: Was charity active during fiscal period?")

    # Programs count
    prog_type_col = '"Program type OP=ongoing program, NP=new program, NA=not active"'
    ongoing = con.execute(f"""
        SELECT COUNT(*) FROM programs t
        INNER JOIN charity_base cb ON t."BN/Registration number" = cb.bn
        WHERE {where} AND t.{prog_type_col} = 'OP'
    """).fetchone()[0]
    new_prog = con.execute(f"""
        SELECT COUNT(*) FROM programs t
        INNER JOIN charity_base cb ON t."BN/Registration number" = cb.bn
        WHERE {where} AND t.{prog_type_col} = 'NP'
    """).fetchone()[0]
    ws.append(["", "Ongoing programs", ongoing])
    ws.append(["", "New programs", new_prog])

    # C3-C4
    yn("2000", "C3: Made gifts to qualified donees?")
    yn("2100", "C4: Activities outside Canada?")

    # C6 Fundraising methods
    ws.append([])
    ws.append(["", "FUNDRAISING METHODS (C6)"])
    ws[f"B{ws.max_row}"].font = bold
    methods = [
        ("2500", "Advertisements/print/radio/TV"),
        ("2510", "Auctions"),
        ("2530", "Collection plates/boxes"),
        ("2540", "Door-to-door"),
        ("2550", "Draws/lotteries"),
        ("2560", "Dinners/galas/concerts"),
        ("2570", "Sales"),
        ("2575", "Internet"),
        ("2580", "Mail campaigns"),
        ("2590", "Planned-giving programs"),
        ("2600", "Targeted corporate donations/sponsorships"),
        ("2610", "Targeted contacts"),
        ("2620", "Telephone/TV solicitations"),
        ("2630", "Tournament/sporting events"),
        ("2640", "Cause-related marketing"),
        ("2650", "Other"),
    ]
    for code, label in methods:
        count_method(code, label)

    # C7 External fundraisers
    ws.append([])
    yn("2700", "C7: Pay external fundraisers?")
    # C7 sub-fields: gross revenue and amounts retained
    for col, label in [("5450", "Gross revenue collected by fundraisers"), ("5460", "Amounts paid to/retained by fundraisers")]:
        val = con.execute(f"SELECT SUM({money(f't.\"{col}\"')}) FROM {st('financial_abc', where)}").fetchone()[0]
        ws.append([col, f"  {label}", val])

    # C7 payment methods
    for code, label in [("2730", "Commissions"), ("2740", "Bonuses"), ("2750", "Finder's fee"),
                        ("2760", "Set fee for services"), ("2770", "Honoraria"), ("2780", "Other")]:
        count_method(code, f"  {label}")

    # C8-C11
    ws.append([])
    yn("3200", "C8: Compensate directors at arm's length?")
    yn("3400", "C9: Employment expenses?")
    yn("3900", "C10: Donations $10K+ from non-residents?")
    yn("4000", "C11: Non-cash gifts for tax receipts?")

    # C12-C15
    yn("5800", "C12: Acquire a non-qualifying security?")
    yn("5810", "C13: Allow donors to use property?")
    yn("5820", "C14: Issue tax receipts for another org?")
    yn("5830", "C15: Direct partnership holdings?")

    # C16 Grants to non-QDs
    ws.append([])
    yn("5840", "C16: Grants to non-qualified donees?")
    yn("5841", "  Grants > $5,000?")
    val_5842 = con.execute(f"""
        SELECT SUM(t."5842") FROM {st('financial_abc', where)} AND t."5842" IS NOT NULL
    """).fetchone()[0]
    val_5843 = con.execute(f"SELECT SUM({money('t.\"5843\"')}) FROM {st('financial_abc', where)}").fetchone()[0]
    ws.append(["5842", "  Number of grantees ($5K or less)", val_5842])
    ws.append(["5843", "  Total paid to grantees ($5K or less)", val_5843])

    # C17 DQ threshold
    yn("5850", "C17: Avg property > threshold?")

    # C18 DAF
    ws.append([])
    ws.append(["", "DONOR ADVISED FUNDS"])
    ws[f"B{ws.max_row}"].font = bold
    yn("5860", "C18: Hold any DAF accounts?")
    val_5861 = con.execute(f'SELECT SUM(t."5861") FROM {st("financial_abc", where)}').fetchone()[0]
    ws.append(["5861", "  Total DAF accounts", val_5861])
    for col, label in [("5862", "Total value of DAF accounts"),
                       ("5863", "Donations to DAFs received"),
                       ("5864", "Qualifying disbursements from DAFs")]:
        val = con.execute(f"SELECT SUM({money(f't.\"{col}\"')}) FROM {st('financial_abc', where)}").fetchone()[0]
        ws.append([col, f"  {label}", val])

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 20


def build_section_d(wb, con, where):
    """Section D: Financial information summary (lines 4020-5100)."""
    ws = wb.create_sheet("Section D")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Section D: Financial Information"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Description", "Value"])
    for c in ["A", "B", "C"]:
        ws[f"{c}3"].font = bold

    def sum_line(col):
        return con.execute(
            f"SELECT SUM({money(f't.\"{col}\"')}) FROM {st('financial_d', where)}"
        ).fetchone()[0]

    def yn_line(col, table="financial_d"):
        """Count yes/no responses."""
        bn = BN_COL[table]
        y = con.execute(f"""
            SELECT COUNT(*) FROM {table} t
            INNER JOIN charity_base cb ON t.{bn} = cb.bn
            WHERE {where} AND t."{col}" = 'Y'
        """).fetchone()[0]
        n = con.execute(f"""
            SELECT COUNT(*) FROM {table} t
            INNER JOIN charity_base cb ON t.{bn} = cb.bn
            WHERE {where} AND t."{col}" = 'N'
        """).fetchone()[0]
        return y, n

    # D1: Accrual vs Cash (coded as 'A' and 'C')
    accrual = con.execute(f"""
        SELECT COUNT(*) FROM {st('financial_d', where)} AND t."4020" = 'A'
    """).fetchone()[0]
    cash = con.execute(f"""
        SELECT COUNT(*) FROM {st('financial_d', where)} AND t."4020" = 'C'
    """).fetchone()[0]
    ws.append(["4020", "D1: Accrual basis", accrual])
    ws.append(["", "    Cash basis", cash])

    # D2: Balance sheet
    ws.append([])
    ws.append(["", "D2: SUMMARY OF FINANCIAL POSITION"])
    ws[f"B{ws.max_row}"].font = bold

    y4050, n4050 = yn_line("4050")
    ws.append(["4050", "Own land and/or buildings?", f"Yes: {y4050:,}  No: {n4050:,}"])
    ws.append(["4200", "Total assets", sum_line("4200")])
    ws.append(["4350", "Total liabilities", sum_line("4350")])

    y4400, n4400 = yn_line("4400")
    ws.append(["4400", "Borrow from non-arm's length?", f"Yes: {y4400:,}  No: {n4400:,}"])

    # D3: Revenue
    ws.append([])
    ws.append(["", "D3: REVENUE"])
    ws[f"B{ws.max_row}"].font = bold

    y4490, n4490 = yn_line("4490")
    ws.append(["4490", "Issue tax receipts for gifts?", f"Yes: {y4490:,}  No: {n4490:,}"])

    revenue_lines = [
        ("4500", "Tax-receipted gifts"),
        ("5610", "Tax-receipted tuition fees"),
        ("4510", "Gifts from other registered charities"),
        ("4530", "Other gifts (no tax receipt)"),
        ("4540", "Revenue from FEDERAL government"),
        ("4550", "Revenue from PROVINCIAL/TERRITORIAL governments"),
        ("4560", "Revenue from MUNICIPAL/REGIONAL governments"),
    ]
    for line, desc in revenue_lines:
        ws.append([line, desc, sum_line(line)])

    # Computed government total (4540+4550+4560)
    govt = con.execute(f"""
        SELECT SUM({money('t."4540"')}) + SUM({money('t."4550"')}) + SUM({money('t."4560"')})
        FROM {st('financial_d', where)}
    """).fetchone()[0]
    ws.append(["4570*", "Total government (computed: 4540+4550+4560)", govt])

    more_revenue = [
        ("4571", "Tax-receipted revenue from outside Canada (govt+non-govt)"),
        ("4575", "Non-tax-receipted revenue from outside Canada"),
        ("4630", "Non-tax-receipted revenue from fundraising"),
        ("4640", "Revenue from sale of goods and services"),
        ("4650", "Other revenue"),
        ("4700", "TOTAL REVENUE"),
    ]
    for line, desc in more_revenue:
        ws.append([line, desc, sum_line(line)])

    # D4: Expenditures
    ws.append([])
    ws.append(["", "D4: EXPENDITURES"])
    ws[f"B{ws.max_row}"].font = bold

    exp_lines = [
        ("4860", "Professional and consulting fees"),
        ("4810", "Travel and vehicle expenses"),
        ("4920", "All other expenditures"),
        ("4950", "Total expenditures excl. qualifying disbursements"),
        ("5000", "  (a) Charitable activities"),
        ("5010", "  (b) Management and administration"),
        ("5045", "Grants to non-qualified donees"),
        ("5050", "Gifts to all qualified donees"),
        ("5100", "TOTAL EXPENDITURES"),
    ]
    for line, desc in exp_lines:
        ws.append([line, desc, sum_line(line)])

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 20


def build_schedule_1(wb, con, where):
    """Schedule 1: Foundations."""
    ws = wb.create_sheet("Schedule 1")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Schedule 1: Foundations"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Question", "Yes / Value", "No"])
    for c in ["A", "B", "C", "D"]:
        ws[f"{c}3"].font = bold

    def yn(col, label):
        y = con.execute(f"SELECT COUNT(*) FROM {st('schedule_1_foundations', where)} AND t.\"{col}\" = 'Y'").fetchone()[0]
        n = con.execute(f"SELECT COUNT(*) FROM {st('schedule_1_foundations', where)} AND t.\"{col}\" = 'N'").fetchone()[0]
        ws.append([col, label, y, n])

    yn("100", "Did foundation acquire control of a corporation?")
    yn("110", "Did foundation incur debts other than operating?")

    val_111 = con.execute(f"SELECT SUM({money('t.\"111\"')}) FROM {st('schedule_1_foundations', where)}").fetchone()[0]
    val_112 = con.execute(f"SELECT SUM({money('t.\"112\"')}) FROM {st('schedule_1_foundations', where)}").fetchone()[0]
    ws.append(["111", "Total value of restricted funds", val_111])
    ws.append(["112", "Amount not permitted to spend (funder direction)", val_112])

    ws.append([])
    ws.append(["", "FOR PRIVATE FOUNDATIONS ONLY"])
    ws[f"B{ws.max_row}"].font = bold
    yn("120", "Hold non-qualified investments?")
    yn("130", "Own >2% of any class of shares?")

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 12


def build_schedule_2(wb, con, where):
    """Schedule 2: Activities outside Canada."""
    ws = wb.create_sheet("Schedule 2")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Schedule 2: Activities Outside Canada"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Question / Metric", "Yes / Value", "No"])
    for c in ["A", "B", "C", "D"]:
        ws[f"{c}3"].font = bold

    # Line 200: total foreign expenditures
    val_200 = con.execute(f"SELECT SUM({money('t.\"200\"')}) FROM {st('schedule_2_summary', where)}").fetchone()[0]
    ws.append(["200", "Total expenditures on activities outside Canada", val_200])

    def yn(col, label):
        y = con.execute(f"SELECT COUNT(*) FROM {st('schedule_2_summary', where)} AND t.\"{col}\" = 'Y'").fetchone()[0]
        n = con.execute(f"SELECT COUNT(*) FROM {st('schedule_2_summary', where)} AND t.\"{col}\" = 'N'").fetchone()[0]
        ws.append([col, label, y, n])

    yn("210", "Financial resources spent via contracts/arrangements?")

    yn("220", "Projects funded by Global Affairs Canada?")
    val_230 = con.execute(f"SELECT SUM({money('t.\"230\"')}) FROM {st('schedule_2_summary', where)}").fetchone()[0]
    ws.append(["230", "  Total amount from Global Affairs Canada", val_230])

    yn("240", "Employees conducted activities outside Canada?")
    yn("250", "Volunteers conducted foreign activities?")
    yn("260", "Export goods as charitable activities?")

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 12


def build_schedule_3(wb, con, where):
    """Schedule 3: Compensation by salary band."""
    ws = wb.create_sheet("Schedule 3")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Schedule 3: Compensation"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Description", "Value"])
    for c in ["A", "B", "C"]:
        ws[f"{c}3"].font = bold

    def sum_bigint(col):
        """Sum a BIGINT column (no currency formatting)."""
        return con.execute(
            f'SELECT SUM(t."{col}") FROM {st("schedule_3_compensation", where)}'
        ).fetchone()[0]

    def sum_currency(col):
        return con.execute(
            f"SELECT SUM({money(f't.\"{col}\"')}) FROM {st('schedule_3_compensation', where)}"
        ).fetchone()[0]

    # Full-time positions
    ws.append(["", "FULL-TIME POSITIONS"])
    ws[f"B{ws.max_row}"].font = bold

    ws.append(["300", "Total FT compensated positions", sum_bigint("300")])

    bands = [
        ("305", "$1 - $39,999"),
        ("310", "$40,000 - $79,999"),
        ("315", "$80,000 - $119,999"),
        ("320", "$120,000 - $159,999"),
        ("325", "$160,000 - $199,999"),
        ("330", "$200,000 - $249,999"),
        ("335", "$250,000 - $299,999"),
        ("340", "$300,000 - $349,999"),
        ("345", "$350,000 and over"),
    ]
    for line, desc in bands:
        ws.append([line, f"  {desc}", sum_bigint(line)])

    # Part-time
    ws.append([])
    ws.append(["", "PART-TIME AND TOTAL"])
    ws[f"B{ws.max_row}"].font = bold

    ws.append(["370", "PT/seasonal positions", sum_bigint("370")])
    ws.append(["380", "PT/seasonal compensation", sum_currency("380")])
    ws.append(["390", "TOTAL COMPENSATION (all)", sum_currency("390")])

    # Cross-check with financial_d line 4880
    ws.append([])
    val_4880 = con.execute(
        f"SELECT SUM({money('t.\"4880\"')}) FROM {scoped_table('financial_d', where)}"
    ).fetchone()[0]
    ws.append(["", "Cross-check: financial_d line 4880", val_4880])

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 20


def build_schedule_5(wb, con, where):
    """Schedule 5: Non-cash gifts by type."""
    ws = wb.create_sheet("Schedule 5")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Schedule 5: Non-cash Gifts"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Gift Type", "Count"])
    for c in ["A", "B", "C"]:
        ws[f"{c}3"].font = bold

    gift_types = [
        ("500", "Artwork/wine/jewellery"),
        ("505", "Building materials"),
        ("510", "Clothing/furniture/food"),
        ("515", "Vehicles"),
        ("520", "Cultural properties"),
        ("525", "Ecological properties"),
        ("530", "Life insurance policies"),
        ("535", "Medical equipment/supplies"),
        ("540", "Privately-held securities"),
        ("545", "Machinery/equipment/computers/software"),
        ("550", "Publicly traded securities/mutual funds"),
        ("555", "Books"),
        ("560", "Other"),
    ]

    for code, label in gift_types:
        cnt = con.execute(f"""
            SELECT COUNT(*) FROM {st('schedule_5_noncash', where)}
            AND t."{code}" = 'Y'
        """).fetchone()[0]
        ws.append([code, label, cnt])

    ws.append([])
    val_580 = con.execute(
        f"SELECT SUM({money('t.\"580\"')}) FROM {st('schedule_5_noncash', where)}"
    ).fetchone()[0]
    ws.append(["580", "Total amount of tax-receipted non-cash gifts", val_580])

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 20


def build_schedule_6(wb, con, where):
    """Schedule 6: Detailed financial information (all line items)."""
    ws = wb.create_sheet("Schedule 6")
    bold = Font(bold=True)
    st = scoped_table

    ws.append(["Blumbergs Snapshot 2024 — Schedule 6: Detailed Financial Information"])
    ws["A1"].font = bold
    ws.append([])
    ws.append(["Line", "Description", "Value"])
    for c in ["A", "B", "C"]:
        ws[f"{c}3"].font = bold

    def s(col):
        """Sum a currency column from financial_d."""
        return con.execute(
            f"SELECT SUM({money(f't.\"{col}\"')}) FROM {st('financial_d', where)}"
        ).fetchone()[0]

    def section(title):
        ws.append([])
        ws.append([title])
        ws[f"A{ws.max_row}"].font = bold

    # --- ASSETS ---
    section("ASSETS")
    assets = [
        ("4100", "Cash, bank accounts, short-term investments"),
        ("4101", "  Cash and bank accounts"),
        ("4102", "  Short-term investments"),
        ("4110", "Amounts receivable from non-arm's length persons"),
        ("4120", "Amounts receivable from all others"),
        ("4130", "Investments in non-arm's length persons"),
        ("4140", "Long-term investments"),
        ("4150", "Inventories"),
        ("4155", "Land and buildings in Canada"),
        ("4157", "  Used for charitable programs or admin"),
        ("4158", "  Used for other purposes"),
        ("4160", "Other capital assets in Canada"),
        ("4165", "Capital assets outside Canada"),
        ("4166", "Accumulated amortization of capital assets"),
        ("4170", "Other assets"),
        ("4190", "Impact investments"),
        ("4200", "TOTAL ASSETS"),
    ]
    for line, desc in assets:
        ws.append([line, desc, s(line)])

    # --- LIABILITIES ---
    section("LIABILITIES")
    liabilities = [
        ("4300", "Accounts payable and accrued liabilities"),
        ("4310", "Deferred revenue"),
        ("4320", "Amounts owing to non-arm's length persons"),
        ("4330", "Other liabilities"),
        ("4350", "TOTAL LIABILITIES"),
    ]
    for line, desc in liabilities:
        ws.append([line, desc, s(line)])

    # Property not used in charitable activities
    ws.append([])
    ws.append(["4250", "Property not used in charitable activities", s("4250")])

    # --- REVENUE ---
    section("REVENUE")
    revenue = [
        ("4500", "Tax-receipted gifts (donation receipts issued)"),
        ("5610", "Tax-receipted tuition fees"),
        ("4510", "Gifts from other registered charities"),
        ("4530", "Other gifts (no tax receipt)"),
        ("4540", "Revenue from FEDERAL government"),
        ("4550", "Revenue from PROVINCIAL/TERRITORIAL governments"),
        ("4560", "Revenue from MUNICIPAL/REGIONAL governments"),
        ("4571", "Tax-receipted revenue from outside Canada (govt+non-govt)"),
        ("4575", "Non-tax-receipted revenue from outside Canada"),
        ("4576", "Interest/investment income from impact investments"),
        ("4577", "Interest/investment income from non-arm's length persons"),
        ("4580", "Interest/investment income received or earned"),
        ("4590", "Gross proceeds from disposition of assets"),
        ("4600", "Net proceeds from disposition of assets"),
        ("4610", "Gross income from rental of land/buildings"),
        ("4620", "Membership fees, dues, association fees"),
        ("4630", "Non-tax-receipted revenue from fundraising"),
        ("4640", "Revenue from sale of goods and services"),
        ("4650", "Other revenue"),
        ("4700", "TOTAL REVENUE"),
    ]
    for line, desc in revenue:
        ws.append([line, desc, s(line)])

    # --- EXPENDITURES ---
    section("EXPENDITURES")
    expenditures = [
        ("4800", "Advertising and promotion"),
        ("4810", "Travel and vehicle expenses"),
        ("4820", "Interest and bank charges"),
        ("4830", "Licences, memberships, and dues"),
        ("4840", "Office supplies and expenses"),
        ("4850", "Occupancy costs"),
        ("4860", "Professional and consulting fees"),
        ("4870", "Education and training for staff and volunteers"),
        ("4880", "Total expenditure on all compensation"),
        ("4890", "Fair market value of donated goods used"),
        ("4891", "Purchased supplies and assets"),
        ("4900", "Amortization of capitalized assets"),
        ("4910", "Research grants and scholarships"),
        ("4920", "All other expenditures"),
        ("4950", "Total expenditures before qualifying disbursements"),
        ("5000", "  (a) Charitable activities"),
        ("5010", "  (b) Management and administration"),
        ("5020", "  (c) Fundraising"),
        ("5040", "  (d) Other expenditures included in 4950"),
        ("5045", "Grants to non-qualified donees"),
        ("5050", "Gifts to all qualified donees"),
        ("5100", "TOTAL EXPENDITURES"),
    ]
    for line, desc in expenditures:
        ws.append([line, desc, s(line)])

    # --- OTHER FINANCIAL INFO ---
    section("OTHER FINANCIAL INFORMATION")
    other = [
        ("5500", "Amount accumulated (permission to accumulate)"),
        ("5510", "Amount disbursed for specified purpose"),
        ("5750", "Permission to reduce disbursement quota"),
        ("5900", "Property not used — beginning of period (24 months)"),
        ("5910", "Property not used — end of period (24 months)"),
    ]
    for line, desc in other:
        ws.append([line, desc, s(line)])

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 20


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
