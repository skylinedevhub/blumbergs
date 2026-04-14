#!/usr/bin/env python3
"""
build_schema_index.py — Introspect the CRA charities DuckDB and emit web/lib/schema-index.json.

Run from the project root (where data/db/cra_charities.duckdb lives):
    python3 scripts/build_schema_index.py
"""

import json
import os
import sys
import duckdb

DB_PATH = "data/db/cra_charities.duckdb"
OUT_PATH = "web/lib/schema-index.json"

# ---------------------------------------------------------------------------
# T3010 line-number → human description
# ---------------------------------------------------------------------------
LINE_DESCRIPTIONS = {
    # ---- financial_d: Balance-sheet assets ----
    "4020": "Opening balance — net assets / fund balances",
    "4050": "Closing balance — net assets / fund balances",
    "4100": "Cash and short-term investments",
    "4101": "Cash (V24) / Accounts receivable — pledges (V23)",
    "4102": "Short-term investments (V24) / Accounts receivable — other (V23)",
    "4110": "Accounts receivable",
    "4120": "Inventory",
    "4130": "Prepaid expenses",
    "4140": "Long-term investments",
    "4150": "Capital assets — cost",
    "4155": "Capital assets — accumulated amortization",
    "4157": "Right-of-use assets",
    "4158": "Accumulated amortization — right-of-use assets",
    "4160": "Land and buildings",
    "4165": "Leasehold improvements",
    "4166": "Equipment and furniture",
    "4170": "Other capital assets",
    "4180": "Other assets",
    "4190": "Endowment fund assets",
    "4200": "Total assets",
    "4250": "Assets not used for charitable activities",
    "4300": "Accounts payable and accrued liabilities",
    "4310": "Deferred revenue",
    "4320": "Long-term debt",
    "4330": "Other liabilities",
    "4350": "Total liabilities",
    "4400": "Net assets / fund balances",
    # ---- financial_d: Revenue ----
    "4490": "Gross revenue before adjustments",
    "4500": "Tax-receipted gifts",
    "4505": "Non-tax-receipted gifts from individuals",
    "4510": "Gifts from other registered charities",
    "4530": "Gifts from non-registered charities",
    "4540": "Federal government funding",
    "4550": "Provincial/territorial government funding",
    "4560": "Municipal government funding",
    "4565": "Other Canadian government funding",
    "4570": "Total government funding (UNRELIABLE — compute as 4540+4550+4560)",
    "4571": "Foreign government funding",
    "4575": "V24: Non-tax-receipted revenue from outside Canada; V23: Tax-receipted from outside Canada",
    "4576": "Foreign grants received",
    "4577": "Other foreign revenue",
    "4580": "V24: Interest and investment income; V23: Non-tax-receipted from outside Canada",
    "4590": "Rental income",
    "4600": "Revenue from sale of goods and services",
    "4610": "Membership fees",
    "4620": "Investment income",
    "4630": "Proceeds from disposition of assets",
    "4640": "Other revenue",
    "4650": "Gross proceeds — fundraising activities",
    "4655": "Direct costs — fundraising activities",
    "4700": "Total revenue",
    # ---- financial_d: Expenditures ----
    "4800": "Professional and consulting fees",
    "4810": "Salaries, wages, and benefits",
    "4820": "Occupancy costs",
    "4830": "Travel and vehicle costs",
    "4840": "Interest and bank charges",
    "4850": "Insurance",
    "4860": "Licences and permits",
    "4870": "Advertising and promotion",
    "4880": "Total compensation paid to employees",
    "4890": "Amortization of capital assets",
    "4891": "Amortization of right-of-use assets",
    "4900": "Purchases of supplies",
    "4910": "Costs of goods sold",
    "4920": "Research",
    "4930": "Other expenditures",
    "4950": "Capital asset acquisitions",
    "5000": "Charitable program expenditures",
    "5010": "Management and administration",
    "5020": "Fundraising",
    "5030": "Political activities",
    "5031": "Political activities (policy dialogue)",
    "5032": "Political activities (other)",
    "5040": "Other expenditures",
    "5045": "Grants to non-qualified donees",
    "5050": "Gifts to qualified donees",
    "5100": "Total expenditures",
    # ---- financial_d: Other ----
    "5500": "Total receipted donations for tax purposes",
    "5510": "Donations eligible for 100% deduction",
    "5610": "Line 5610 — supplementary (form version dependent)",
    "5750": "Total qualifying disbursements",
    "5900": "Number of donors who received a tax receipt",
    "5910": "Tax-receipted amount — median donation",
    # ---- financial_abc: Program area codes ----
    "1200 Program Area Code": "Primary program area code (see lookup_programs)",
    "1200 Percent": "Percentage of activities in primary program area",
    "1210 Program Area Code": "Secondary program area code (see lookup_programs)",
    "1210 Percent": "Percentage of activities in secondary program area",
    "1220 Program Area Code": "Tertiary program area code (see lookup_programs)",
    "1220 Percent": "Percentage of activities in tertiary program area",
    # ---- financial_abc: Subsidiary / parent ----
    "1510 Subordinate position to a parent organization?": "Is this charity a subordinate of a parent? (Y/N)",
    "1510 Parent Business Number": "Parent organization BN",
    "1510 Parent Name": "Parent organization legal name",
    # ---- financial_abc: Y/N questions ----
    "1570": "Operates outside Canada? (Y/N)",
    "1600": "Has directors/trustees at arm's length? (Y/N)",
    "1800": "Carries on any political activities? (Y/N)",
    "2000": "Received gifts from outside Canada? (Y/N)",
    "2100": "Made gifts to non-qualified donees? (Y/N)",
    "2400": "Has programs or activities that benefit non-Canadian citizens? (Y/N)",
    "2500": "Accumulated property/funds over past 2 years in excess of charitable needs? (Y/N)",
    "2510": "Applied to CRA to reduce disbursement quota? (Y/N)",
    "2530": "Carries on an unrelated business? (Y/N)",
    "2540": "Incurred debt? (Y/N)",
    "2550": "Issued shares or granted interests? (Y/N)",
    "2560": "Made investments not in compliance with prudent investment provisions? (Y/N)",
    "2570": "Acquired non-qualifying securities? (Y/N)",
    "2575": "Holds any non-qualifying securities? (Y/N)",
    "2580": "Transferred property to another charity at less than fair market value? (Y/N)",
    "2590": "Received property that is subject to a direction to transfer? (Y/N)",
    "2600": "Used any of its income or property to unduly benefit any person? (Y/N)",
    "2610": "Entered into any transaction with a non-arm's-length person? (Y/N)",
    "2620": "Subject to any taxes or penalties under the Income Tax Act? (Y/N)",
    "2630": "Had any legal counsel, litigation, or claims filed? (Y/N)",
    "2640": "Changed its legal structure? (Y/N)",
    "2650": "Changed its by-laws or other governing documents? (Y/N)",
    "2660": "Changed its purposes? (Y/N)",
    "2700": "Is there a change of address or officer since last filing? (Y/N)",
    "2730": "Maintained any books or records outside Canada? (Y/N)",
    "2740": "Retained a fundraiser to solicit donations? (Y/N)",
    "2750": "Issued tax receipts for gifts of property? (Y/N)",
    "2760": "Issued tax receipts for donations received for advantage? (Y/N)",
    "2770": "Issued tax receipts that contain split-receipt amounts? (Y/N)",
    "2780": "Issued receipts for enduring property? (Y/N)",
    "2790": "Issued receipts for a gift of cultural property? (Y/N)",
    "2800": "Issued receipts for a gift of ecologically sensitive land? (Y/N)",
    "3200": "Filed a T3 trust return? (Y/N)",
    "3400": "Has the charity completed Schedule 8 — Disbursement Quota? (Y/N)",
    "3900": "Did the charity file a Section D financial return? (Y/N)",
    "4000": "Did the charity file a financial return with another government body? (Y/N)",
    "5030": "Carries on political activities — Section C indicator (C or 6)",
    "5031": "Amount of political activities expenditures — policy dialogue",
    "5032": "Amount of political activities expenditures — other",
    "5450": "Name of the fundraiser (if retained)",
    "5460": "Address/contact of the fundraiser",
    # ---- financial_abc: DAF fields ----
    "5800": "Is the charity a Donor Advised Fund (DAF) sponsoring organization? (Y/N)",
    "5810": "Does the charity hold any DAF accounts? (Y/N)",
    "5820": "Number of DAF accounts held",
    "5830": "Total value of DAF assets",
    "5840": "Total donations received into DAF accounts",
    "5841": "Total donations from DAF accounts to qualified donees",
    "5842": "Number of DAF accounts that made distributions",
    "5843": "Total DAF distributions",
    "5850": "Does charity have a policy prohibiting advisor-directed accounts? (Y/N)",
    "5860": "Has DAF — primary field (Y/N)",
    "5861": "Number of donor-advised fund accounts",
    "5862": "Total value of DAF fund (assets)",
    "5863": "Total donations received to DAF accounts in the year",
    "5864": "Total gifts from DAF accounts to qualified donees in the year",
    # ---- schedule_1_foundations ----
    "100": "Date last audited financial statements were prepared",
    "110": "Did the foundation receive an unqualified audit opinion? (Y/N)",
    "111": "Did the foundation receive a qualified opinion? (Y/N)",
    "112": "Notes explaining qualified opinion",
    "120": "Total gifts received from a specified non-arm's-length person",
    "130": "Total gifts received from a non-arm's-length corporation",
    # ---- schedule_2_summary ----
    "200": "Total expenditures — charitable activities outside Canada",
    "210": "Total expenditures — gifts to non-qualified donees outside Canada",
    "220": "Total expenditures — gifts to qualified donees outside Canada",
    "230": "Total foreign expenditures",
    "240": "Number of countries where activities carried on",
    "250": "Number of foreign recipients",
    "260": "Total value of goods exported",
    # ---- schedule_3_compensation ----
    "300": "Number of full-time employees (FT positions)",
    "305": "FT employees earning less than $40,000",
    "310": "FT employees earning $40,000–$79,999",
    "315": "FT employees earning $80,000–$119,999",
    "320": "FT employees earning $120,000–$159,999",
    "325": "FT employees earning $160,000–$199,999",
    "330": "FT employees earning $200,000–$249,999",
    "335": "FT employees earning $250,000–$299,999",
    "340": "FT employees earning $300,000–$349,999",
    "345": "FT employees earning $350,000 or more",
    "370": "Number of part-time/casual employees (PT positions)",
    "380": "Compensation paid to top 10 employees — total hours",
    "390": "Total compensation paid to all employees (VARCHAR — has $ formatting)",
    # ---- schedule_5_noncash ----
    "500": "Description of non-cash gift #1",
    "505": "Fair market value of non-cash gift #1",
    "510": "Description of non-cash gift #2",
    "515": "Fair market value of non-cash gift #2",
    "520": "Description of non-cash gift #3",
    "525": "Fair market value of non-cash gift #3",
    "530": "Description of non-cash gift #4",
    "535": "Fair market value of non-cash gift #4",
    "540": "Description of non-cash gift #5",
    "545": "Fair market value of non-cash gift #5",
    "550": "Description of non-cash gift #6",
    "555": "Fair market value of non-cash gift #6",
    "560": "Description of non-cash gift #7",
    "565": "Fair market value of non-cash gift #7",
    "580": "Total fair market value of all non-cash gifts",
    # ---- schedule_8_disbursement ----
    "805": "Charitable activities using own staff and volunteers",
    "810": "Gifts to qualified donees",
    "815": "Administrative expenditures attributable to charitable activities",
    "820": "Total qualifying disbursements (=805+810+815)",
    "825": "Prior year excess disbursements applied",
    "830": "Net qualifying disbursements",
    "835": "Value of charitable gifts — 3.5% base",
    "840": "Value of other property — 3.5% base",
    "845": "Total disbursement quota base",
    "850": "Disbursement quota (3.5% of 845)",
    "855": "Shortfall (850 minus 830)",
    "860": "Accumulated disbursement shortfall",
    "865": "Reduction approved by Minister",
    "870": "Excess disbursements carried forward",
    "875": "10-year gifts received",
    "880": "10-year gifts disbursed",
    "885": "Enduring property held",
    "890": "Net enduring property",
}

# ---------------------------------------------------------------------------
# BN column name per table
# ---------------------------------------------------------------------------
BN_COL = {
    "ident": '"BN/Registration Number"',
    "financial_d": '"BN/Registration Number"',
    "schedule_8_disbursement": '"BN/Registration Number"',
    "charity_base": "bn",
    "latest_filing": "bn",
    "charity_counts": "bn",
    # Views all use bn
    "v_financial_d": "bn",
    "v_financial_abc": "bn",
    "v_compensation": "bn",
    "v_programs": "bn",
    "v_grants": "bn",
    "v_foreign_recipients": "bn",
    "v_operating_countries": "bn",
    "v_subsidiaries": "subsidiary_bn",
}
# Default for all other tables
DEFAULT_BN_COL = '"BN/Registration number"'

# ---------------------------------------------------------------------------
# Human-readable table descriptions
# ---------------------------------------------------------------------------
TABLE_DESCRIPTIONS = {
    "ident": (
        "Master charity list from CRA (T3010 Section A). Primary key: BN/Registration Number. "
        "Contains legal name, designation, category, address, contact info for all ~83,275 charities."
    ),
    "charity_base": (
        "Cleaned and enriched master list — ident joined with lookup descriptions (designation, "
        "category, subcategory, charity_type). Use this as the primary join hub. BN column is 'bn'."
    ),
    "latest_filing": (
        "Most recent fiscal period end per charity. One row per BN. Use to restrict queries to "
        "the latest filing year."
    ),
    "charity_counts": (
        "Aggregated counts per charity: num_programs, num_grants, num_operating_countries, has_filing."
    ),
    "financial_d": (
        "Balance sheet and income statement (T3010 Section D). Column names are T3010 line numbers "
        "(e.g. '4700' = total revenue). All financial values are VARCHAR with '$' and ',' formatting. "
        "Convert with: TRY_CAST(REPLACE(REPLACE(col,'$',''),',','') AS DECIMAL)."
    ),
    "financial_abc": (
        "Program area codes, Y/N questions (lines 1570–3900), DAF data (5800–5864), and subsidiary "
        "relationships (1510). VARCHAR columns except program percentages (BIGINT) and a few DAF "
        "count fields (BIGINT)."
    ),
    "schedule_1_foundations": (
        "Foundation-specific audit and gift disclosure fields (Schedule 1). "
        "Applies to Public Foundations (A) and Private Foundations (B) only."
    ),
    "schedule_2_summary": (
        "Summary of foreign activities (Schedule 2). Totals for expenditures, gifts, and recipients "
        "outside Canada."
    ),
    "schedule_2_countries": (
        "Countries where charity operates (Schedule 2, 1:many). One row per country per filing."
    ),
    "schedule_2_recipients": (
        "Foreign aid recipients (Schedule 2, 1:many). Name, country, and amount for each recipient."
    ),
    "schedule_2_destinations": (
        "Export destinations for goods sent outside Canada (Schedule 2, 1:many)."
    ),
    "schedule_3_compensation": (
        "Employee compensation by salary band (Schedule 3). Lines 300/370 are BIGINT (employee counts). "
        "Line 390 is VARCHAR (total compensation, has '$' formatting). Lines 305–345 are BIGINT salary-band counts."
    ),
    "schedule_5_noncash": (
        "Non-cash gift details (Schedule 5). Up to 7 non-cash gifts per filing with description and "
        "fair market value."
    ),
    "schedule_7_description": (
        "Political activities descriptions (Schedule 7 — typically empty in CRA open dataset)."
    ),
    "schedule_7_political_outside": (
        "Political activities funded outside Canada (Schedule 7 — typically empty in CRA open dataset)."
    ),
    "schedule_7_political_resources": (
        "Political activities resource usage (Schedule 7 — typically empty in CRA open dataset)."
    ),
    "schedule_8_disbursement": (
        "Disbursement quota (DQ) calculations (Schedule 8). Applies to foundations and charities "
        "subject to the 3.5% DQ rule."
    ),
    "programs": (
        "Program descriptions submitted by charities (1:many, up to ~5 programs per filing). "
        "Includes program type (OP=ongoing, NP=new, NA=not active) and free-text description."
    ),
    "grants": (
        "Grants to non-qualified donees (1:many). Recipient name, purpose, cash amount, country."
    ),
    "gift": (
        "Gifts to qualified donees (1:many). Linked charity BN, donee name, city, province, "
        "total amount, and whether a political activities gift."
    ),
    "trustee": (
        "Directors and trustees (T1235 worksheet, 1:many). Last name, first name, position, "
        "arm's-length status, appointed/ceased dates."
    ),
    # Lookup tables
    "lookup_designation": "Designation code lookup: A=Public Foundation, B=Private Foundation, C=Charitable Organization.",
    "lookup_province": "Province/territory code lookup: two-letter codes (ON, QC, BC, AB, etc.) to full English/French names.",
    "lookup_category": "Category and sub-category code lookup with charity type descriptions (252 rows).",
    "lookup_country": "Country code lookup (ISO 2-letter codes) to English/French country names (250 rows).",
    "lookup_programs": "Program area code lookup for lines 1200/1210/1220 (71 codes, e.g. A1=Housing for seniors).",
    "lookup_form_versioning": "Maps form version IDs to fiscal year ranges — used to detect V23 vs V24 field changes.",
    "lookup_us_state": "US state code lookup (51 rows).",
}

VIEW_DESCRIPTIONS = {
    "v_financial_d": (
        "Friendly aliases for financial_d: adds bn, fiscal_period_end, total_revenue (4700), "
        "total_expenditures (5100), total_assets (4200) as named columns alongside all raw line columns."
    ),
    "v_financial_abc": (
        "Friendly aliases for financial_abc: adds bn, fiscal_period_end, is_subsidiary, "
        "parent_bn, parent_name alongside all raw columns."
    ),
    "v_compensation": (
        "Friendly aliases for schedule_3_compensation: adds bn, fiscal_period_end, "
        "ft_employees (=300), pt_employees (=370), total_compensation (=390)."
    ),
    "v_programs": (
        "Simplified view of programs table: bn, fiscal_period_end, program_type "
        "(OP/NP/NA), description."
    ),
    "v_grants": (
        "Simplified view of grants table: bn, fiscal_period_end, seq, recipient_name, "
        "purpose, cash_amount, country."
    ),
    "v_foreign_recipients": (
        "Simplified view of schedule_2_recipients: bn, fiscal_period_end, seq, "
        "recipient_name, country_code, amount."
    ),
    "v_operating_countries": (
        "Simplified view of schedule_2_countries: bn, fiscal_period_end, country_code."
    ),
    "v_subsidiaries": (
        "Flattened subsidiary relationships: subsidiary_bn, subsidiary_name, parent_bn, parent_name. "
        "No BN column named 'bn' — use subsidiary_bn."
    ),
}

# ---- Currency column detection heuristics --------------------------------
# Tables whose numeric-looking columns carry '$' formatting
CURRENCY_TABLES = {
    "financial_d", "financial_abc", "schedule_1_foundations",
    "schedule_2_summary", "schedule_2_recipients", "schedule_2_destinations",
    "schedule_3_compensation", "schedule_5_noncash", "schedule_8_disbursement",
    "grants", "gift", "v_financial_d", "v_compensation",
    "v_grants", "v_foreign_recipients",
}

# Columns that look numeric but are NOT currency (Y/N, codes, counts, etc.)
NON_CURRENCY_COLUMNS = {
    # Y/N question lines in financial_abc
    "1570","1600","1800","2000","2100","2400","2500","2510","2530","2540",
    "2550","2560","2570","2575","2580","2590","2600","2610","2620","2630",
    "2640","2650","2660","2700","2730","2740","2750","2760","2770","2780",
    "2790","2800","3200","3400","3900","4000","5800","5810","5820","5850",
    "5860",
    # Program area codes
    "1200 Program Area Code","1210 Program Area Code","1220 Program Area Code",
    # Schedule 3 BIGINT count lines
    "300","305","310","315","320","325","330","335","340","345","370",
    # DAF count fields (BIGINT)
    "5842","5861",
    # Various flags
    "5030",  # C or 6 indicator
}


def get_bn_col(table_name: str) -> str:
    return BN_COL.get(table_name, DEFAULT_BN_COL)


def get_join_condition(table_name: str, bn_col: str) -> str:
    if table_name == "charity_base":
        return "— this IS charity_base (the join hub)"
    if table_name.startswith("v_") and table_name != "v_subsidiaries":
        return f"charity_base.bn = {table_name}.bn"
    if table_name == "v_subsidiaries":
        return "charity_base.bn = v_subsidiaries.subsidiary_bn  (or parent_bn)"
    if bn_col == "bn":
        return f"charity_base.bn = {table_name}.bn"
    return f"charity_base.bn = {table_name}.{bn_col}"


def is_currency_column(table_name: str, col_name: str, data_type: str) -> bool:
    """Return True if this column holds '$'-formatted monetary values."""
    if data_type != "VARCHAR":
        return False
    if table_name not in CURRENCY_TABLES:
        return False
    if col_name in NON_CURRENCY_COLUMNS:
        return False
    # Only flag columns that are pure line numbers (all digits) or known financial names
    if col_name.isdigit():
        return True
    # Named financial columns in views / descriptive tables
    financial_keywords = {
        "total_revenue", "total_expenditures", "total_assets",
        "total_compensation", "cash_amount", "amount",
        "Total amount gifts", "Amount of gifts in kind",
        "Political Activities Gift Amount",
        "Value (CAN)",
    }
    if col_name in financial_keywords:
        return True
    return False


def build_column_info(table_name: str, col_name: str, data_type: str) -> dict:
    info: dict = {"type": data_type}
    # Look up description by line number or full column name
    desc = LINE_DESCRIPTIONS.get(col_name)
    if desc:
        info["description"] = desc
        # If the column name is a pure line number, store it as "line"
        if col_name.isdigit():
            info["line"] = col_name
    elif " " in col_name and col_name.split()[0].isdigit():
        # e.g. "1200 Program Area Code"
        line = col_name.split()[0]
        desc = LINE_DESCRIPTIONS.get(col_name) or LINE_DESCRIPTIONS.get(line)
        if desc:
            info["description"] = desc
            info["line"] = line
    if is_currency_column(table_name, col_name, data_type):
        info["currency"] = True
    return info


# ---------------------------------------------------------------------------
# Domain value extraction
# ---------------------------------------------------------------------------
LOOKUP_CONFIG = {
    "lookup_designation": ("Designation Code", "Description_E"),
    "lookup_province":    ("Province Code", "English Name"),
    "lookup_country":     ("Country Code", "English Name"),
    "lookup_programs":    ("Line 1200, 1210, 1220", "English Description"),
    "lookup_category":    ("Category Code", "Category English Desc"),
}


def extract_domain_values(con: duckdb.DuckDBPyConnection) -> dict:
    domain: dict = {}
    for table, (code_col, desc_col) in LOOKUP_CONFIG.items():
        try:
            rows = con.execute(
                f'SELECT "{code_col}", "{desc_col}" FROM {table} ORDER BY "{code_col}"'
            ).fetchall()
            domain[table] = {str(r[0]): str(r[1]) for r in rows}
        except Exception as e:
            print(f"  [warn] Could not read {table}: {e}", file=sys.stderr)
    return domain


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: database not found at {DB_PATH}", file=sys.stderr)
        print("Run this script from the project root (where data/ lives).", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    con = duckdb.connect(DB_PATH, read_only=True)

    # 1. Enumerate tables and views
    all_tables = con.execute(
        "SELECT table_name, table_type FROM information_schema.tables ORDER BY table_type, table_name"
    ).fetchall()

    base_tables = [t for t, tt in all_tables if tt == "BASE TABLE"]
    views       = [t for t, tt in all_tables if tt == "VIEW"]

    # 2. Row counts
    row_counts: dict = {}
    for tbl in base_tables:
        try:
            row_counts[tbl] = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except Exception:
            row_counts[tbl] = None

    # 3. Build columns for every table/view
    def build_table_entry(table_name: str, is_view: bool) -> dict:
        cols = con.execute(
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
        ).fetchall()

        bn_col = get_bn_col(table_name)
        columns = {}
        for col_name, data_type in cols:
            columns[col_name] = build_column_info(table_name, col_name, data_type)

        entry: dict = {
            "description": (VIEW_DESCRIPTIONS if is_view else TABLE_DESCRIPTIONS).get(
                table_name, f"{'View' if is_view else 'Table'}: {table_name}"
            ),
            "bn_column": bn_col,
            "join_to_charity_base": get_join_condition(table_name, bn_col),
            "columns": columns,
        }
        if not is_view and table_name in row_counts:
            entry["rows"] = row_counts[table_name]
        return entry

    tables_out: dict = {}
    for tbl in base_tables:
        tables_out[tbl] = build_table_entry(tbl, is_view=False)

    views_out: dict = {}
    for v in views:
        views_out[v] = build_table_entry(v, is_view=True)

    # 4. Join conditions (flat index for quick lookup)
    joins: dict = {}
    for tbl in base_tables + views:
        bn_col = get_bn_col(tbl)
        joins[tbl] = get_join_condition(tbl, bn_col)

    # 5. Domain values
    domain_values = extract_domain_values(con)

    con.close()

    # 6. Quirks
    quirks = [
        (
            "Currency fields are VARCHAR with '$' and ',' formatting. "
            "In PostgreSQL convert with: "
            "CAST(REPLACE(REPLACE(col, '$', ''), ',', '') AS NUMERIC). "
            "Use TRY_CAST (DuckDB) or NULLIF pattern (PostgreSQL) to handle "
            "blank/non-numeric values gracefully."
        ),
        (
            "BN column name varies by table: 'BN/Registration Number' (capital N) in ident, "
            "financial_d, schedule_8_disbursement; "
            "'BN/Registration number' (lowercase n) in most other raw tables; "
            "'bn' in charity_base and all views. "
            "Always quote column names in SQL (double-quotes for PostgreSQL/DuckDB)."
        ),
        (
            "Always LEFT JOIN from charity_base (or ident) as the primary table. "
            "Not every charity appears in every schedule table. "
            "JOIN charity_base ON charity_base.bn = other_table.\"BN/Registration number\"."
        ),
        (
            "Designation codes: A = Public Foundation, B = Private Foundation, "
            "C = Charitable Organization (~85% of charities). "
            "Filter with: WHERE cb.designation_code = 'A'."
        ),
        (
            "schedule_3_compensation has mixed types: lines 300–345 and 370 are BIGINT "
            "(employee count integers, no $ sign). Line 390 (total compensation) is "
            "VARCHAR with $ formatting. Do NOT apply REPLACE() to BIGINT columns."
        ),
        (
            "Line 4570 (total government funding) is UNRELIABLE — charities often leave it blank "
            "or duplicate other lines. Compute government funding as: "
            "4540 (federal) + 4550 (provincial) + 4560 (municipal) instead."
        ),
        (
            "T3010 form version V23→V24 breaking changes (affects year-over-year comparisons): "
            "Line 4575: V23='Tax-receipted from outside Canada', V24='Non-tax-receipted revenue from outside Canada'. "
            "Line 4580: V23='Non-tax-receipted from outside Canada', V24='Interest/investment income'. "
            "Lines 4101/4102: V23='Receivables breakdown', V24='Cash vs short-term investments'. "
            "Do NOT compare these lines directly across filing years spanning the V23/V24 boundary."
        ),
        (
            "SQL dialect: The production database is PostgreSQL (Neon serverless). "
            "Use standard PostgreSQL syntax. DuckDB syntax is similar but may differ on: "
            "string functions, date handling, and CAST semantics. "
            "Avoid DuckDB-specific functions like TRY_CAST in final queries."
        ),
    ]

    # 7. Assemble output
    schema_index = {
        "tables": tables_out,
        "views": views_out,
        "joins": joins,
        "domain_values": domain_values,
        "quirks": quirks,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(schema_index, f, indent=2, ensure_ascii=False)

    # 8. Print summary
    total_table_cols = sum(len(t["columns"]) for t in tables_out.values())
    total_view_cols  = sum(len(v["columns"]) for v in views_out.values())
    currency_cols    = sum(
        sum(1 for c in t["columns"].values() if c.get("currency"))
        for t in {**tables_out, **views_out}.values()
    )
    described_cols   = sum(
        sum(1 for c in t["columns"].values() if c.get("description"))
        for t in {**tables_out, **views_out}.values()
    )

    print(f"Schema index written to: {OUT_PATH}")
    print(f"  Tables:           {len(tables_out)}")
    print(f"  Views:            {len(views_out)}")
    print(f"  Table columns:    {total_table_cols}")
    print(f"  View columns:     {total_view_cols}")
    print(f"  Currency-marked:  {currency_cols}")
    print(f"  Described cols:   {described_cols}")
    print(f"  Domain lookups:   {len(domain_values)}")
    print(f"  Quirks:           {len(quirks)}")
    file_size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"  Output size:      {file_size_kb:.1f} KB")


if __name__ == "__main__":
    main()
