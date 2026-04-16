#!/usr/bin/env python3
"""
Load CRA T3010 CSV data into DuckDB with multi-year support.

Reads CSV files from a year directory (default: data/raw/2024/) and loads them
into a DuckDB database at data/db/cra_charities.duckdb.  Each raw table has a
`data_year` column.  Loading year X only replaces year X rows, leaving other
years untouched.

Usage:
    python3 scripts/load_csv.py [data_dir] [--rebuild]

Examples:
    python3 scripts/load_csv.py                        # additive load 2024
    python3 scripts/load_csv.py data/raw/2025/         # additive load 2025
    python3 scripts/load_csv.py --rebuild              # clean-slate rebuild 2024
    python3 scripts/load_csv.py data/raw/2023/ --rebuild  # clean rebuild 2023
"""

import argparse
import re
import sys
import os
import time
import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_DATA_DIR = os.path.join("data", "raw", "2024")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")

# 18 raw tables — these get a data_year column
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
}

# 7 lookup tables — NO data_year, overwritten entirely each load
LOOKUP_MAP = {
    "lookups/category_subcategory.csv": "lookup_category",
    "lookups/country.csv": "lookup_country",
    "lookups/designation.csv": "lookup_designation",
    "lookups/form_versioning.csv": "lookup_form_versioning",
    "lookups/programs.csv": "lookup_programs",
    "lookups/province.csv": "lookup_province",
    "lookups/us_state.csv": "lookup_us_state",
}


# ---------------------------------------------------------------------------
# Year detection
# ---------------------------------------------------------------------------

def detect_year(data_dir):
    """Extract the data year from the directory path.

    Looks for four-digit years starting with 20 in the path.
    Takes the last match (e.g. data/raw/2024/ -> 2024).
    """
    matches = re.findall(r'(20\d{2})', data_dir)
    if not matches:
        print(f"ERROR: Cannot detect year from path: {data_dir}")
        print("       Path must contain a four-digit year (e.g. data/raw/2024/)")
        sys.exit(1)
    return int(matches[-1])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def table_exists(con, table_name):
    """Check whether a table already exists in the database."""
    result = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_name = ?",
        [table_name],
    ).fetchone()
    return result[0] > 0


def read_csv_to_temp(con, csv_path):
    """Read a CSV file into a temporary __csv_staging table.

    Tries auto-detect first, then CP1252 encoding, then relaxed parsing.
    Returns the list of column names from the staging table.
    """
    escaped_path = csv_path.replace("'", "''")

    con.execute("DROP TABLE IF EXISTS __csv_staging")

    try:
        con.execute(
            f"""CREATE TEMPORARY TABLE __csv_staging AS
                SELECT * FROM read_csv_auto('{escaped_path}',
                    all_varchar=false
                )"""
        )
    except Exception:
        try:
            con.execute("DROP TABLE IF EXISTS __csv_staging")
            con.execute(
                f"""CREATE TEMPORARY TABLE __csv_staging AS
                    SELECT * FROM read_csv_auto('{escaped_path}',
                        all_varchar=false,
                        encoding='CP1252'
                    )"""
            )
        except Exception:
            con.execute("DROP TABLE IF EXISTS __csv_staging")
            print(f"  [INFO] Retrying with relaxed parsing")
            con.execute(
                f"""CREATE TEMPORARY TABLE __csv_staging AS
                    SELECT * FROM read_csv('{escaped_path}',
                        ignore_errors=true,
                        all_varchar=false,
                        encoding='CP1252',
                        strict_mode=false,
                        auto_detect=true
                    )"""
            )

    cols = [row[0] for row in con.execute("DESCRIBE __csv_staging").fetchall()]
    return cols


def load_csv_with_year(con, csv_path, table_name, data_year):
    """Load a CSV into a year-scoped raw table.

    - If the table doesn't exist: CREATE TABLE with data_year + all CSV columns
    - If the table exists: reconcile columns (ALTER TABLE ADD for new columns),
      DELETE existing rows for this year, INSERT with matching columns
    """
    start = time.time()

    csv_cols = read_csv_to_temp(con, csv_path)

    if not table_exists(con, table_name):
        # Build CREATE TABLE from staging schema + prepend data_year
        col_defs = con.execute("DESCRIBE __csv_staging").fetchall()
        ddl_cols = ["data_year INTEGER"]
        for col_name, col_type, *_ in col_defs:
            ddl_cols.append(f'"{col_name}" {col_type}')
        ddl = f'CREATE TABLE "{table_name}" ({", ".join(ddl_cols)})'
        con.execute(ddl)

        # INSERT all rows with data_year prepended
        quoted_csv_cols = ", ".join(f'"{c}"' for c in csv_cols)
        con.execute(
            f'INSERT INTO "{table_name}" (data_year, {quoted_csv_cols}) '
            f'SELECT {data_year}, {quoted_csv_cols} FROM __csv_staging'
        )
    else:
        # Column reconciliation: add any new columns from CSV to the table
        existing_cols = [
            row[0] for row in con.execute(f'DESCRIBE "{table_name}"').fetchall()
        ]
        existing_set = set(existing_cols)

        staging_defs = con.execute("DESCRIBE __csv_staging").fetchall()
        for col_name, col_type, *_ in staging_defs:
            if col_name not in existing_set:
                print(f"  [ALTER] Adding column \"{col_name}\" ({col_type}) to {table_name}")
                con.execute(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type}'
                )
                existing_set.add(col_name)

        # Delete existing rows for this year
        con.execute(f'DELETE FROM "{table_name}" WHERE data_year = {data_year}')

        # INSERT with only columns that exist in both CSV and table
        matching_cols = [c for c in csv_cols if c in existing_set]
        quoted_matching = ", ".join(f'"{c}"' for c in matching_cols)
        con.execute(
            f'INSERT INTO "{table_name}" (data_year, {quoted_matching}) '
            f'SELECT {data_year}, {quoted_matching} FROM __csv_staging'
        )

    count = con.execute(
        f'SELECT COUNT(*) FROM "{table_name}" WHERE data_year = {data_year}'
    ).fetchone()[0]
    elapsed = time.time() - start

    con.execute("DROP TABLE IF EXISTS __csv_staging")

    print(f"  {table_name:40s} {count:>10,} rows  ({elapsed:.1f}s)")
    return count


def load_lookup(con, csv_path, table_name):
    """Load a lookup CSV — no data_year, overwritten entirely."""
    start = time.time()
    escaped_path = csv_path.replace("'", "''")

    con.execute(f'DROP TABLE IF EXISTS "{table_name}"')

    try:
        con.execute(
            f"""CREATE TABLE "{table_name}" AS
                SELECT * FROM read_csv_auto('{escaped_path}',
                    all_varchar=false
                )"""
        )
    except Exception:
        try:
            con.execute(
                f"""CREATE TABLE "{table_name}" AS
                    SELECT * FROM read_csv_auto('{escaped_path}',
                        all_varchar=false,
                        encoding='CP1252'
                    )"""
            )
        except Exception:
            print(f"  [INFO] Retrying {table_name} with relaxed parsing")
            con.execute(
                f"""CREATE TABLE "{table_name}" AS
                    SELECT * FROM read_csv('{escaped_path}',
                        ignore_errors=true,
                        all_varchar=false,
                        encoding='CP1252',
                        strict_mode=false,
                        auto_detect=true
                    )"""
            )

    count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
    elapsed = time.time() - start
    print(f"  {table_name:40s} {count:>10,} rows  ({elapsed:.1f}s)")
    return count


# ---------------------------------------------------------------------------
# Views — filter to MAX(data_year) by default
# ---------------------------------------------------------------------------

VIEWS_SQL = [
    """
    CREATE OR REPLACE VIEW v_compensation AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "300" AS ft_employees, "370" AS pt_employees, "390" AS total_compensation, *
    FROM schedule_3_compensation
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_3_compensation);
    """,
    """
    CREATE OR REPLACE VIEW v_financial_abc AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Form ID" AS form_id,
           "1510 Subordinate position to a parent organization?" AS is_subsidiary,
           "1510 Parent Business Number" AS parent_bn, "1510 Parent Name" AS parent_name, *
    FROM financial_abc
    WHERE data_year = (SELECT MAX(data_year) FROM financial_abc);
    """,
    """
    CREATE OR REPLACE VIEW v_financial_d AS
    SELECT data_year,
           "BN/Registration Number" AS bn, "Fiscal Period End" AS fiscal_period_end,
           "Form ID" AS form_id, "4700" AS total_revenue, "5100" AS total_expenditures,
           "4200" AS total_assets, *
    FROM financial_d
    WHERE data_year = (SELECT MAX(data_year) FROM financial_d);
    """,
    """
    CREATE OR REPLACE VIEW v_foreign_recipients AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Name of individual/organization" AS recipient_name,
           Country AS country_code, Amount AS amount
    FROM schedule_2_recipients
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_2_recipients);
    """,
    """
    CREATE OR REPLACE VIEW v_grants AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Grant Recipient Name" AS recipient_name,
           "Grant Purpose" AS purpose, "Amount of Cash Disbursed" AS cash_amount,
           "Grant Country" AS country
    FROM grants
    WHERE data_year = (SELECT MAX(data_year) FROM grants);
    """,
    """
    CREATE OR REPLACE VIEW v_operating_countries AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Charity's Program Country Code" AS country_code
    FROM schedule_2_countries
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_2_countries);
    """,
    """
    CREATE OR REPLACE VIEW v_programs AS
    SELECT data_year,
           "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
           "Program type OP=ongoing program, NP=new program, NA=not active" AS program_type,
           "Program Description" AS description
    FROM programs
    WHERE data_year = (SELECT MAX(data_year) FROM programs);
    """,
]


# ---------------------------------------------------------------------------
# Derived tables — rebuilt per year
# ---------------------------------------------------------------------------

def rebuild_derived_tables(con, data_year):
    """Create or update charity_base, latest_filing, charity_counts for a year."""

    # ---- charity_base ----
    if not table_exists(con, "charity_base"):
        con.execute("""
            CREATE TABLE charity_base (
                data_year INTEGER,
                bn VARCHAR,
                legal_name VARCHAR,
                account_name VARCHAR,
                designation_code VARCHAR,
                designation_desc VARCHAR,
                category_code VARCHAR,
                subcategory_code VARCHAR,
                category_desc VARCHAR,
                subcategory_desc VARCHAR,
                charity_type VARCHAR,
                registration_date VARCHAR,
                address VARCHAR,
                city VARCHAR,
                province VARCHAR,
                postal_code VARCHAR,
                country VARCHAR,
                phone VARCHAR,
                email VARCHAR,
                website VARCHAR
            )
        """)
    else:
        con.execute(f"DELETE FROM charity_base WHERE data_year = {data_year}")

    con.execute(f"""
        INSERT INTO charity_base
        SELECT
            {data_year} AS data_year,
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
                                         AND i."Sub-category code" = lc."Sub-Category Code")
        WHERE i.data_year = {data_year}
    """)
    cb_count = con.execute(
        f"SELECT COUNT(*) FROM charity_base WHERE data_year = {data_year}"
    ).fetchone()[0]
    print(f"  charity_base (year {data_year}): {cb_count:,} rows")

    # ---- latest_filing ----
    if not table_exists(con, "latest_filing"):
        con.execute("""
            CREATE TABLE latest_filing (
                data_year INTEGER,
                bn VARCHAR,
                latest_fiscal_end TIMESTAMP
            )
        """)
    else:
        con.execute(f"DELETE FROM latest_filing WHERE data_year = {data_year}")

    con.execute(f"""
        INSERT INTO latest_filing
        SELECT
            {data_year} AS data_year,
            "BN/Registration Number" AS bn,
            MAX("Fiscal Period End") AS latest_fiscal_end
        FROM financial_d
        WHERE data_year = {data_year}
        GROUP BY "BN/Registration Number"
    """)
    lf_count = con.execute(
        f"SELECT COUNT(*) FROM latest_filing WHERE data_year = {data_year}"
    ).fetchone()[0]
    print(f"  latest_filing (year {data_year}): {lf_count:,} rows")

    # ---- charity_counts ----
    if not table_exists(con, "charity_counts"):
        con.execute("""
            CREATE TABLE charity_counts (
                data_year INTEGER,
                bn VARCHAR,
                latest_fiscal_end TIMESTAMP,
                has_filing INTEGER,
                num_programs BIGINT,
                num_grants BIGINT,
                num_operating_countries BIGINT
            )
        """)
    else:
        con.execute(f"DELETE FROM charity_counts WHERE data_year = {data_year}")

    con.execute(f"""
        INSERT INTO charity_counts
        SELECT
            {data_year} AS data_year,
            cb.bn,
            lf.latest_fiscal_end,
            CASE WHEN lf.latest_fiscal_end IS NOT NULL THEN 1 ELSE 0 END AS has_filing,
            COALESCE(p.cnt, 0) AS num_programs,
            COALESCE(g.cnt, 0) AS num_grants,
            COALESCE(c.cnt, 0) AS num_operating_countries
        FROM charity_base cb
        LEFT JOIN latest_filing lf ON cb.bn = lf.bn AND lf.data_year = {data_year}
        LEFT JOIN (
            SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt
            FROM programs WHERE data_year = {data_year} GROUP BY 1
        ) p ON cb.bn = p.bn
        LEFT JOIN (
            SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt
            FROM grants WHERE data_year = {data_year} GROUP BY 1
        ) g ON cb.bn = g.bn
        LEFT JOIN (
            SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt
            FROM schedule_2_countries WHERE data_year = {data_year} GROUP BY 1
        ) c ON cb.bn = c.bn
        WHERE cb.data_year = {data_year}
    """)
    cc_count = con.execute(
        f"SELECT COUNT(*) FROM charity_counts WHERE data_year = {data_year}"
    ).fetchone()[0]
    print(f"  charity_counts (year {data_year}): {cc_count:,} rows")


# ---------------------------------------------------------------------------
# v_subsidiaries — joins on data_year
# ---------------------------------------------------------------------------

V_SUBSIDIARIES_SQL = """
CREATE OR REPLACE VIEW v_subsidiaries AS
SELECT DISTINCT
    fa.data_year,
    fa.bn AS subsidiary_bn,
    cb_sub.legal_name AS subsidiary_name,
    fa.parent_bn,
    cb_parent.legal_name AS parent_name
FROM v_financial_abc fa
INNER JOIN charity_base cb_sub ON fa.bn = cb_sub.bn AND fa.data_year = cb_sub.data_year
LEFT JOIN charity_base cb_parent ON fa.parent_bn = cb_parent.bn AND fa.data_year = cb_parent.data_year
WHERE fa.is_subsidiary = 'Y'
  AND fa.parent_bn IS NOT NULL
  AND trim(fa.parent_bn) != '';
"""


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(con):
    """Print row counts for all tables and views, with per-year breakdown."""
    print("\n" + "=" * 70)
    print("SUMMARY: All tables and views")
    print("=" * 70)

    # Show loaded years
    try:
        years = [r[0] for r in con.execute(
            "SELECT DISTINCT data_year FROM ident ORDER BY data_year"
        ).fetchall()]
        if years:
            print(f"\nLoaded years: {', '.join(str(y) for y in years)}")
    except Exception:
        pass

    # Get all tables
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"\n{'Tables':}")
    print("-" * 65)
    for (tname,) in tables:
        total = con.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]

        # Check if this table has a data_year column
        cols = [row[0] for row in con.execute(f'DESCRIBE "{tname}"').fetchall()]
        if "data_year" in cols:
            year_counts = con.execute(
                f'SELECT data_year, COUNT(*) FROM "{tname}" GROUP BY data_year ORDER BY data_year'
            ).fetchall()
            year_str = ", ".join(f"{yr}: {cnt:,}" for yr, cnt in year_counts)
            print(f"  {tname:40s} {total:>10,} rows  [{year_str}]")
        else:
            print(f"  {tname:40s} {total:>10,} rows")

    # Get all views
    views = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_type = 'VIEW' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"\n{'Views':}")
    print("-" * 65)
    for (vname,) in views:
        count = con.execute(f'SELECT COUNT(*) FROM "{vname}"').fetchone()[0]
        print(f"  {vname:40s} {count:>10,} rows")

    print("=" * 70)
    print(f"Total: {len(tables)} tables, {len(views)} views")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Load CRA T3010 CSV data into DuckDB (multi-year)."
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=None,
        help="Path to year directory (default: data/raw/2024/)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the database and rebuild from scratch",
    )
    args = parser.parse_args()

    # Resolve data directory
    if args.data_dir:
        data_dir = args.data_dir
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(PROJECT_ROOT, data_dir)
    else:
        data_dir = os.path.join(PROJECT_ROOT, DEFAULT_DATA_DIR)

    if not os.path.isdir(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    data_year = detect_year(data_dir)

    print(f"Project root  : {PROJECT_ROOT}")
    print(f"Data directory: {data_dir}")
    print(f"Data year     : {data_year}")
    print(f"Database path : {DB_PATH}")
    print(f"Mode          : {'REBUILD (clean slate)' if args.rebuild else 'ADDITIVE (year-scoped)'}")

    # Ensure db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # --rebuild: delete the database for a clean slate
    if args.rebuild:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"Removed existing database: {DB_PATH}")
        wal_path = DB_PATH + ".wal"
        if os.path.exists(wal_path):
            os.remove(wal_path)

    con = duckdb.connect(DB_PATH)
    total_start = time.time()

    # ----- Phase 1: Load raw CSV files (year-scoped) -----
    print(f"\n--- Phase 1: Loading raw CSV files (year {data_year}) ---")
    loaded = 0
    for csv_rel_path, table_name in TABLE_MAP.items():
        csv_path = os.path.join(data_dir, csv_rel_path)
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] File not found: {csv_rel_path}")
            continue
        load_csv_with_year(con, csv_path, table_name, data_year)
        loaded += 1

    print(f"\nLoaded {loaded}/{len(TABLE_MAP)} raw CSV files.")

    # ----- Phase 2: Load lookup tables (no data_year) -----
    print("\n--- Phase 2: Loading lookup tables ---")
    lookup_loaded = 0
    for csv_rel_path, table_name in LOOKUP_MAP.items():
        csv_path = os.path.join(data_dir, csv_rel_path)
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] File not found: {csv_rel_path}")
            continue
        load_lookup(con, csv_path, table_name)
        lookup_loaded += 1

    print(f"\nLoaded {lookup_loaded}/{len(LOOKUP_MAP)} lookup tables.")

    # ----- Phase 3: Create views -----
    print("\n--- Phase 3: Creating views ---")
    for sql in VIEWS_SQL:
        con.execute(sql)
    print(f"  Created {len(VIEWS_SQL)} views.")

    # ----- Phase 4: Rebuild derived tables for this year -----
    print(f"\n--- Phase 4: Rebuilding derived tables (year {data_year}) ---")
    rebuild_derived_tables(con, data_year)

    # ----- Phase 5: Create v_subsidiaries -----
    print("\n--- Phase 5: Creating v_subsidiaries view ---")
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
