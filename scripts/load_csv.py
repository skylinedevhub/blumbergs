#!/usr/bin/env python3
"""
Load CRA T3010 CSV data into DuckDB.

Reads CSV files from a year directory (default: data/raw/2024/) and creates
a DuckDB database at data/db/cra_charities.duckdb with base tables, views,
and derived tables.

Usage:
    python3 scripts/load_csv.py [year_directory]

Examples:
    python3 scripts/load_csv.py                    # uses data/raw/2024/
    python3 scripts/load_csv.py data/raw/2023/     # uses data/raw/2023/
"""

import sys
import os
import time
import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Project root is one level up from this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_DATA_DIR = os.path.join("data", "raw", "2024")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")

# CSV filename -> table name mapping
TABLE_MAP = {
    "ident.csv": "ident",
    "financial_abc.csv": "financial_abc",
    "financial_d.csv": "financial_d",
    "gift.csv": "gift",
    "grants_nonqd.csv": "grants",
    "programs.csv": "programs",
    "trustee.csv": "trustee",
    "schedule_1_foundations.csv": "schedule_1_foundations",
    "schedule_2_summary.csv": "schedule_2_summary",
    "schedule_2_countries.csv": "schedule_2_countries",
    "schedule_2_destinations.csv": "schedule_2_destinations",
    "schedule_2_recipients.csv": "schedule_2_recipients",
    "schedule_3_compensation.csv": "schedule_3_compensation",
    "schedule_5_noncash.csv": "schedule_5_noncash",
    "schedule_7_description.csv": "schedule_7_description",
    "schedule_7_political_outside.csv": "schedule_7_political_outside",
    "schedule_7_political_resources.csv": "schedule_7_political_resources",
    "schedule_8_disbursement.csv": "schedule_8_disbursement",
    # Lookups (in lookups/ subdirectory)
    "lookups/category_subcategory.csv": "lookup_category",
    "lookups/country.csv": "lookup_country",
    "lookups/designation.csv": "lookup_designation",
    "lookups/form_versioning.csv": "lookup_form_versioning",
    "lookups/programs.csv": "lookup_programs",
    "lookups/province.csv": "lookup_province",
    "lookups/us_state.csv": "lookup_us_state",
}


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

VIEWS_SQL = [
    """
    CREATE OR REPLACE VIEW v_compensation AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "300" AS ft_employees, "370" AS pt_employees, "390" AS total_compensation, *
    FROM schedule_3_compensation;
    """,
    """
    CREATE OR REPLACE VIEW v_financial_abc AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Form ID" AS form_id,
           "1510 Subordinate position to a parent organization?" AS is_subsidiary,
           "1510 Parent Business Number" AS parent_bn, "1510 Parent Name" AS parent_name, *
    FROM financial_abc;
    """,
    """
    CREATE OR REPLACE VIEW v_financial_d AS
    SELECT "BN/Registration Number" AS bn, "Fiscal Period End" AS fiscal_period_end,
           "Form ID" AS form_id, "4200" AS total_revenue, "5000" AS total_expenditures,
           "5030" AS total_assets, *
    FROM financial_d;
    """,
    """
    CREATE OR REPLACE VIEW v_foreign_recipients AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Name of individual/organization" AS recipient_name,
           Country AS country_code, Amount AS amount
    FROM schedule_2_recipients;
    """,
    """
    CREATE OR REPLACE VIEW v_grants AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Grant Recipient Name" AS recipient_name,
           "Grant Purpose" AS purpose, "Amount of Cash Disbursed" AS cash_amount,
           "Grant Country" AS country
    FROM grants;
    """,
    """
    CREATE OR REPLACE VIEW v_operating_countries AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Charity's Program Country Code" AS country_code
    FROM schedule_2_countries;
    """,
    """
    CREATE OR REPLACE VIEW v_programs AS
    SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Program type OP=ongoing program, NP=new program, NA=not active" AS program_type,
           "Program Description" AS description
    FROM programs;
    """,
]


# ---------------------------------------------------------------------------
# Derived tables
# ---------------------------------------------------------------------------

DERIVED_TABLES_SQL = [
    """
    CREATE OR REPLACE TABLE charity_base AS
    SELECT
        i."BN/Registration Number" AS bn,
        i."Legal name" AS legal_name,
        i."Account name" AS account_name,
        i."Designation code" AS designation_code,
        ld."Description_E" AS designation_desc,
        i."Category code" AS category_code,
        i."Sub-category code" AS subcategory_code,
        lc."Category English Desc" AS category_desc,
        lc."Sub-Category English Desc" AS subcategory_desc,
        lc."Charity Type English Desc" AS charity_type,
        i."Registration date" AS registration_date,
        i."Mailing address" AS address,
        i."City" AS city,
        i."Province" AS province,
        i."Postal code" AS postal_code,
        i."Country" AS country,
        i."Contact Phone" AS phone,
        i."Contact Email" AS email,
        i."Contact URL" AS website
    FROM ident i
    LEFT JOIN lookup_designation ld ON i."Designation code" = ld."Designation Code"
    LEFT JOIN lookup_category lc ON (i."Category code" = lc."Category Code"
                                     AND i."Sub-category code" = lc."Sub-Category Code");
    """,
    """
    CREATE OR REPLACE TABLE latest_filing AS
    SELECT "BN/Registration Number" AS bn,
           MAX("Fiscal Period End") AS latest_fiscal_end
    FROM financial_d
    GROUP BY "BN/Registration Number";
    """,
    """
    CREATE OR REPLACE TABLE charity_counts AS
    SELECT
        cb.bn,
        lf.latest_fiscal_end,
        CASE WHEN lf.latest_fiscal_end IS NOT NULL THEN 1 ELSE 0 END AS has_filing,
        COALESCE(p.cnt, 0) AS num_programs,
        COALESCE(g.cnt, 0) AS num_grants,
        COALESCE(c.cnt, 0) AS num_operating_countries
    FROM charity_base cb
    LEFT JOIN latest_filing lf ON cb.bn = lf.bn
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM programs GROUP BY 1) p ON cb.bn = p.bn
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM grants GROUP BY 1) g ON cb.bn = g.bn
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM schedule_2_countries GROUP BY 1) c ON cb.bn = c.bn;
    """,
]

V_SUBSIDIARIES_SQL = """
CREATE OR REPLACE VIEW v_subsidiaries AS
SELECT DISTINCT fa.bn AS subsidiary_bn, cb_sub.legal_name AS subsidiary_name,
       fa.parent_bn, cb_parent.legal_name AS parent_name
FROM v_financial_abc fa
INNER JOIN charity_base cb_sub ON fa.bn = cb_sub.bn
LEFT JOIN charity_base cb_parent ON fa.parent_bn = cb_parent.bn
WHERE fa.is_subsidiary = 'Y' AND fa.parent_bn IS NOT NULL AND trim(fa.parent_bn) != '';
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csv(con, csv_path, table_name):
    """Load a single CSV file into a DuckDB table."""
    start = time.time()
    escaped_path = csv_path.replace("'", "''")

    # Drop existing table first for clean reload
    con.execute(f'DROP TABLE IF EXISTS "{table_name}"')

    try:
        con.execute(
            f"""CREATE OR REPLACE TABLE "{table_name}" AS
                SELECT * FROM read_csv_auto('{escaped_path}',
                    ignore_errors=true,
                    all_varchar=false
                )"""
        )
    except Exception as e:
        # Fallback: try with explicit Windows-1252 encoding
        print(f"  [WARN] Auto-detect failed for {table_name}, retrying with windows-1252: {e}")
        con.execute(
            f"""CREATE OR REPLACE TABLE "{table_name}" AS
                SELECT * FROM read_csv_auto('{escaped_path}',
                    ignore_errors=true,
                    all_varchar=false,
                    encoding='windows-1252'
                )"""
        )

    count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
    elapsed = time.time() - start
    print(f"  {table_name:40s} {count:>10,} rows  ({elapsed:.1f}s)")
    return count


def print_summary(con):
    """Print row counts for all tables and views."""
    print("\n" + "=" * 70)
    print("SUMMARY: All tables and views")
    print("=" * 70)

    # Get all tables
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"\n{'Tables':}")
    print("-" * 55)
    for (tname,) in tables:
        count = con.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        print(f"  {tname:40s} {count:>10,} rows")

    # Get all views
    views = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_type = 'VIEW' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"\n{'Views':}")
    print("-" * 55)
    for (vname,) in views:
        count = con.execute(f'SELECT COUNT(*) FROM "{vname}"').fetchone()[0]
        print(f"  {vname:40s} {count:>10,} rows")

    print("=" * 70)
    print(f"Total: {len(tables)} tables, {len(views)} views")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Determine data directory
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        # Resolve relative to project root
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(PROJECT_ROOT, data_dir)
    else:
        data_dir = os.path.join(PROJECT_ROOT, DEFAULT_DATA_DIR)

    if not os.path.isdir(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Data directory: {data_dir}")
    print(f"Database path : {DB_PATH}")

    # Ensure db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Delete existing database for clean rebuild
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    # Also remove WAL file if it exists
    wal_path = DB_PATH + ".wal"
    if os.path.exists(wal_path):
        os.remove(wal_path)

    # Connect to DuckDB (creates new file)
    con = duckdb.connect(DB_PATH)
    total_start = time.time()

    # ----- Phase 1: Load CSV files -----
    print("\n--- Phase 1: Loading CSV files ---")
    loaded = 0
    for csv_rel_path, table_name in TABLE_MAP.items():
        csv_path = os.path.join(data_dir, csv_rel_path)
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] File not found: {csv_rel_path}")
            continue
        load_csv(con, csv_path, table_name)
        loaded += 1

    print(f"\nLoaded {loaded}/{len(TABLE_MAP)} CSV files.")

    # ----- Phase 2: Create views -----
    print("\n--- Phase 2: Creating views ---")
    for sql in VIEWS_SQL:
        con.execute(sql)
    print(f"  Created {len(VIEWS_SQL)} views.")

    # ----- Phase 3: Create derived tables -----
    print("\n--- Phase 3: Creating derived tables ---")
    for sql in DERIVED_TABLES_SQL:
        con.execute(sql)
    print("  Created charity_base, latest_filing, charity_counts.")

    # ----- Phase 4: Create v_subsidiaries (depends on charity_base) -----
    print("\n--- Phase 4: Creating v_subsidiaries view ---")
    con.execute(V_SUBSIDIARIES_SQL)
    print("  Created v_subsidiaries.")

    total_elapsed = time.time() - total_start

    # ----- Summary -----
    print_summary(con)
    print(f"\nTotal load time: {total_elapsed:.1f}s")

    con.close()
    print(f"\nDatabase written to: {DB_PATH}")


if __name__ == "__main__":
    main()
