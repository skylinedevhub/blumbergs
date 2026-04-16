# Multi-Year Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the DuckDB database to hold multiple years of CRA T3010 data simultaneously via a `data_year` column on every raw/derived table.

**Architecture:** The loader (`load_csv.py`) switches from wipe-and-rebuild to additive year loading. Each raw/derived table gets `data_year INTEGER` as its first column. Views filter to `MAX(data_year)` by default for backward compatibility. Lookup tables remain shared (no year column).

**Tech Stack:** Python 3, DuckDB 1.4.4, openpyxl (reports)

**Spec:** `docs/plans/2026-04-16-multi-year-database-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/load_csv.py` | Rewrite | Additive year loading, `data_year` injection, `--rebuild` flag, column reconciliation |
| `scripts/validate_db.py` | Rewrite | Per-year validation, `--year` flag, cross-year checks, `data_year` schema checks |
| `scripts/reports/generate_snapshot.py` | Modify | Add `--year` flag, year in scope filter, year in output path/header |
| `scripts/reports/generate_snapshot_articles.py` | Modify | Add `--year` flag, year in scope filter |
| `scripts/reports/generate_jewish_sector.py` | Modify | Add `--year` flag, year in joins |
| `scripts/reports/generate_comparison.py` | Modify | Add `--year` flag, year in scope filter |
| `CLAUDE.md` | Modify | Update schema docs, commands, multi-year notes |

---

### Task 1: Rewrite the Loader — Core Year-Aware Loading

This is the largest task. The loader transforms from "delete DB, create tables from CSVs" to "delete rows for year, insert with data_year prepended."

**Files:**
- Modify: `scripts/load_csv.py` (full rewrite of lines 1-354)

- [ ] **Step 1: Update docstring, imports, and configuration (lines 1-60)**

Replace the entire top section of `scripts/load_csv.py` with:

```python
#!/usr/bin/env python3
"""
Load CRA T3010 CSV data into DuckDB.

Reads CSV files from a year directory (default: data/raw/2024/) and loads
them into a DuckDB database at data/db/cra_charities.duckdb. Each table
gets a data_year column identifying the CRA data release year.

Multiple years can coexist in the same database. Re-loading a year replaces
only that year's data.

Usage:
    python3 scripts/load_csv.py [year_directory]
    python3 scripts/load_csv.py --rebuild             # delete DB first

Examples:
    python3 scripts/load_csv.py                       # loads data/raw/2024/
    python3 scripts/load_csv.py data/raw/2023/        # adds 2023 to DB
    python3 scripts/load_csv.py data/raw/2024/        # replaces 2024 in DB
    python3 scripts/load_csv.py --rebuild              # fresh DB, then 2024
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
}

LOOKUP_MAP = {
    "lookups/category_subcategory.csv": "lookup_category",
    "lookups/country.csv": "lookup_country",
    "lookups/designation.csv": "lookup_designation",
    "lookups/form_versioning.csv": "lookup_form_versioning",
    "lookups/programs.csv": "lookup_programs",
    "lookups/province.csv": "lookup_province",
    "lookups/us_state.csv": "lookup_us_state",
}
```

- [ ] **Step 2: Add the year detection helper**

Append after the config section:

```python
# ---------------------------------------------------------------------------
# Year detection
# ---------------------------------------------------------------------------

def detect_year(data_dir):
    """Extract the 4-digit CRA data release year from a directory path.

    Looks for the last 4-digit number in the path that looks like a year (2000-2099).
    """
    matches = re.findall(r'(20\d{2})', data_dir)
    if not matches:
        print(f"ERROR: Cannot detect year from path: {data_dir}")
        print("Path must contain a 4-digit year (2000-2099), e.g. data/raw/2024/")
        sys.exit(1)
    return int(matches[-1])
```

- [ ] **Step 3: Add the CSV reading helper**

This helper reads a CSV into a temporary table, used by both the raw loader and lookup loader:

```python
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv_to_temp(con, csv_path):
    """Read a CSV file into a DuckDB temp table called __csv_staging.

    Returns the list of column names from the CSV.
    Tries auto-detect first, falls back to CP1252 encoding, then relaxed parsing.
    """
    escaped_path = csv_path.replace("'", "''")
    con.execute("DROP TABLE IF EXISTS __csv_staging")

    try:
        con.execute(
            f"""CREATE TEMP TABLE __csv_staging AS
                SELECT * FROM read_csv_auto('{escaped_path}', all_varchar=false)"""
        )
    except Exception:
        try:
            con.execute(
                f"""CREATE TEMP TABLE __csv_staging AS
                    SELECT * FROM read_csv_auto('{escaped_path}',
                        all_varchar=false, encoding='CP1252')"""
            )
        except Exception:
            print(f"  [INFO] Retrying with relaxed parsing")
            con.execute(
                f"""CREATE TEMP TABLE __csv_staging AS
                    SELECT * FROM read_csv('{escaped_path}',
                        ignore_errors=true, all_varchar=false,
                        encoding='CP1252', strict_mode=false, auto_detect=true)"""
            )

    csv_cols = [r[0] for r in con.execute("DESCRIBE __csv_staging").fetchall()]
    return csv_cols
```

- [ ] **Step 4: Add the year-aware raw table loader**

This is the core function that handles table creation, column reconciliation, and year-scoped insert:

```python
def load_csv_with_year(con, csv_path, table_name, data_year):
    """Load a CSV into a year-aware table.

    - If the table doesn't exist, create it with data_year as the first column.
    - If it exists, reconcile columns (ALTER TABLE ADD COLUMN for new ones).
    - Delete existing rows for this year, then insert new rows.
    """
    start = time.time()

    csv_cols = read_csv_to_temp(con, csv_path)

    # Check if target table exists
    exists = con.execute(
        f"SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_name = '{table_name}' AND table_schema = 'main' AND table_type = 'BASE TABLE'"
    ).fetchone()[0] > 0

    if not exists:
        # Create table with data_year as first column
        col_defs = con.execute("DESCRIBE __csv_staging").fetchall()
        col_ddl = ", ".join(f'"{c[0]}" {c[1]}' for c in col_defs)
        con.execute(f'CREATE TABLE "{table_name}" (data_year INTEGER, {col_ddl})')

        # Insert all rows
        csv_col_list = ", ".join(f'"{c}"' for c in csv_cols)
        con.execute(
            f'INSERT INTO "{table_name}" SELECT {data_year}, {csv_col_list} FROM __csv_staging'
        )
    else:
        # Reconcile columns: add any new CSV columns not in the table
        table_cols = [r[0] for r in con.execute(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name = '{table_name}'"
        ).fetchall()]

        csv_types = {c[0]: c[1] for c in con.execute("DESCRIBE __csv_staging").fetchall()}
        for col in csv_cols:
            if col not in table_cols:
                ctype = csv_types[col]
                con.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {ctype}')
                print(f"  [INFO] Added new column '{col}' ({ctype}) to {table_name}")

        # Delete existing rows for this year
        con.execute(f'DELETE FROM "{table_name}" WHERE data_year = {data_year}')

        # Insert new rows — only matching columns
        matching = [c for c in csv_cols if c in table_cols or c in csv_types]
        col_list = ", ".join(f'"{c}"' for c in matching)
        con.execute(
            f'INSERT INTO "{table_name}" (data_year, {col_list}) '
            f'SELECT {data_year}, {col_list} FROM __csv_staging'
        )

    con.execute("DROP TABLE IF EXISTS __csv_staging")

    count = con.execute(
        f'SELECT COUNT(*) FROM "{table_name}" WHERE data_year = {data_year}'
    ).fetchone()[0]
    elapsed = time.time() - start
    print(f"  {table_name:40s} {count:>10,} rows  ({elapsed:.1f}s)")
    return count
```

- [ ] **Step 5: Add the lookup table loader (unchanged from original, no data_year)**

```python
def load_lookup(con, csv_path, table_name):
    """Load a lookup CSV — overwrites entire table, no data_year column."""
    start = time.time()
    escaped_path = csv_path.replace("'", "''")
    con.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    try:
        con.execute(
            f"""CREATE TABLE "{table_name}" AS
                SELECT * FROM read_csv_auto('{escaped_path}', all_varchar=false)"""
        )
    except Exception:
        con.execute(
            f"""CREATE TABLE "{table_name}" AS
                SELECT * FROM read_csv_auto('{escaped_path}',
                    all_varchar=false, encoding='CP1252')"""
        )
    count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
    elapsed = time.time() - start
    print(f"  {table_name:40s} {count:>10,} rows  ({elapsed:.1f}s)")
    return count
```

- [ ] **Step 6: Update the Views SQL to filter to MAX(data_year)**

Replace the existing `VIEWS_SQL` list with:

```python
# ---------------------------------------------------------------------------
# Views — filter to latest year by default
# ---------------------------------------------------------------------------

VIEWS_SQL = [
    """
    CREATE OR REPLACE VIEW v_compensation AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "300" AS ft_employees, "370" AS pt_employees, "390" AS total_compensation, *
    FROM schedule_3_compensation
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_3_compensation);
    """,
    """
    CREATE OR REPLACE VIEW v_financial_abc AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "Form ID" AS form_id,
           "1510 Subordinate position to a parent organization?" AS is_subsidiary,
           "1510 Parent Business Number" AS parent_bn, "1510 Parent Name" AS parent_name, *
    FROM financial_abc
    WHERE data_year = (SELECT MAX(data_year) FROM financial_abc);
    """,
    """
    CREATE OR REPLACE VIEW v_financial_d AS
    SELECT data_year, "BN/Registration Number" AS bn,
           "Fiscal Period End" AS fiscal_period_end,
           "Form ID" AS form_id, "4700" AS total_revenue, "5100" AS total_expenditures,
           "4200" AS total_assets, *
    FROM financial_d
    WHERE data_year = (SELECT MAX(data_year) FROM financial_d);
    """,
    """
    CREATE OR REPLACE VIEW v_foreign_recipients AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Name of individual/organization" AS recipient_name,
           Country AS country_code, Amount AS amount
    FROM schedule_2_recipients
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_2_recipients);
    """,
    """
    CREATE OR REPLACE VIEW v_grants AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "Sequence number" AS seq, "Grant Recipient Name" AS recipient_name,
           "Grant Purpose" AS purpose, "Amount of Cash Disbursed" AS cash_amount,
           "Grant Country" AS country
    FROM grants
    WHERE data_year = (SELECT MAX(data_year) FROM grants);
    """,
    """
    CREATE OR REPLACE VIEW v_operating_countries AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "Charity's Program Country Code" AS country_code
    FROM schedule_2_countries
    WHERE data_year = (SELECT MAX(data_year) FROM schedule_2_countries);
    """,
    """
    CREATE OR REPLACE VIEW v_programs AS
    SELECT data_year, "BN/Registration number" AS bn,
           "Fiscal period end" AS fiscal_period_end,
           "Program type OP=ongoing program, NP=new program, NA=not active" AS program_type,
           "Program Description" AS description
    FROM programs
    WHERE data_year = (SELECT MAX(data_year) FROM programs);
    """,
]
```

- [ ] **Step 7: Update derived tables to be year-aware**

Replace the existing `DERIVED_TABLES_SQL` and `V_SUBSIDIARIES_SQL` with functions that take a year parameter:

```python
# ---------------------------------------------------------------------------
# Derived tables — rebuilt per year
# ---------------------------------------------------------------------------

def rebuild_derived_tables(con, data_year):
    """Rebuild charity_base, latest_filing, charity_counts for one year."""

    sql_cb = f"""
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
    """

    # latest_filing
    sql_lf = f"""
    INSERT INTO latest_filing
    SELECT {data_year} AS data_year,
           "BN/Registration Number" AS bn,
           MAX("Fiscal Period End") AS latest_fiscal_end
    FROM financial_d
    WHERE data_year = {data_year}
    GROUP BY "BN/Registration Number"
    """

    # charity_counts
    sql_cc = f"""
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
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM programs WHERE data_year = {data_year} GROUP BY 1) p ON cb.bn = p.bn
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM grants WHERE data_year = {data_year} GROUP BY 1) g ON cb.bn = g.bn
    LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM schedule_2_countries WHERE data_year = {data_year} GROUP BY 1) c ON cb.bn = c.bn
    WHERE cb.data_year = {data_year}
    """

    # Create tables if they don't exist, then insert
    if not table_exists(con, "charity_base"):
        con.execute("""
            CREATE TABLE charity_base (
                data_year INTEGER, bn VARCHAR, legal_name VARCHAR, account_name VARCHAR,
                designation_code VARCHAR, designation_desc VARCHAR,
                category_code VARCHAR, subcategory_code VARCHAR,
                category_desc VARCHAR, subcategory_desc VARCHAR, charity_type VARCHAR,
                registration_date VARCHAR, address VARCHAR, city VARCHAR,
                province VARCHAR, postal_code VARCHAR, country VARCHAR,
                phone VARCHAR, email VARCHAR, website VARCHAR
            )
        """)
    else:
        con.execute(f"DELETE FROM charity_base WHERE data_year = {data_year}")
    con.execute(sql_cb)
    cb_count = con.execute(f"SELECT COUNT(*) FROM charity_base WHERE data_year = {data_year}").fetchone()[0]
    print(f"  charity_base ({data_year})            {cb_count:>10,} rows")

    if not table_exists(con, "latest_filing"):
        con.execute("CREATE TABLE latest_filing (data_year INTEGER, bn VARCHAR, latest_fiscal_end TIMESTAMP)")
    else:
        con.execute(f"DELETE FROM latest_filing WHERE data_year = {data_year}")
    con.execute(sql_lf)
    lf_count = con.execute(f"SELECT COUNT(*) FROM latest_filing WHERE data_year = {data_year}").fetchone()[0]
    print(f"  latest_filing ({data_year})           {lf_count:>10,} rows")

    if not table_exists(con, "charity_counts"):
        con.execute("""
            CREATE TABLE charity_counts (
                data_year INTEGER, bn VARCHAR, latest_fiscal_end TIMESTAMP,
                has_filing INTEGER, num_programs BIGINT, num_grants BIGINT,
                num_operating_countries BIGINT
            )
        """)
    else:
        con.execute(f"DELETE FROM charity_counts WHERE data_year = {data_year}")
    con.execute(sql_cc)
    cc_count = con.execute(f"SELECT COUNT(*) FROM charity_counts WHERE data_year = {data_year}").fetchone()[0]
    print(f"  charity_counts ({data_year})          {cc_count:>10,} rows")


def table_exists(con, table_name):
    """Check if a table exists in the database."""
    return con.execute(
        f"SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_name = '{table_name}' AND table_schema = 'main' AND table_type = 'BASE TABLE'"
    ).fetchone()[0] > 0
```

- [ ] **Step 8: Update v_subsidiaries view**

```python
V_SUBSIDIARIES_SQL = """
CREATE OR REPLACE VIEW v_subsidiaries AS
SELECT DISTINCT fa.data_year, fa.bn AS subsidiary_bn, cb_sub.legal_name AS subsidiary_name,
       fa.parent_bn, cb_parent.legal_name AS parent_name
FROM v_financial_abc fa
INNER JOIN charity_base cb_sub ON fa.bn = cb_sub.bn AND fa.data_year = cb_sub.data_year
LEFT JOIN charity_base cb_parent ON fa.parent_bn = cb_parent.bn AND fa.data_year = cb_parent.data_year
WHERE fa.is_subsidiary = 'Y' AND fa.parent_bn IS NOT NULL AND trim(fa.parent_bn) != '';
"""
```

- [ ] **Step 9: Update print_summary to show year breakdown**

Replace the existing `print_summary` function:

```python
def print_summary(con):
    """Print row counts for all tables and views, with year breakdown."""
    print("\n" + "=" * 70)
    print("SUMMARY: All tables and views")
    print("=" * 70)

    # Show loaded years
    years = []
    try:
        years = [r[0] for r in con.execute(
            "SELECT DISTINCT data_year FROM ident ORDER BY data_year"
        ).fetchall()]
    except Exception:
        pass
    if years:
        print(f"\nLoaded years: {', '.join(str(y) for y in years)}")

    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"\n{'Tables':}")
    print("-" * 55)
    for (tname,) in tables:
        count = con.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        # Show per-year breakdown for year-aware tables
        has_year = con.execute(
            f"SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_name = '{tname}' AND column_name = 'data_year'"
        ).fetchone()[0] > 0
        if has_year and len(years) > 1:
            year_counts = con.execute(
                f'SELECT data_year, COUNT(*) FROM "{tname}" GROUP BY data_year ORDER BY data_year'
            ).fetchall()
            breakdown = ", ".join(f"{y}:{c:,}" for y, c in year_counts)
            print(f"  {tname:40s} {count:>10,} rows  ({breakdown})")
        else:
            print(f"  {tname:40s} {count:>10,} rows")

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
```

- [ ] **Step 10: Rewrite main() with argparse and additive loading**

Replace the existing `main()` function:

```python
def main():
    parser = argparse.ArgumentParser(description="Load CRA T3010 CSV data into DuckDB")
    parser.add_argument("data_dir", nargs="?", default=None,
                        help="Year directory (e.g. data/raw/2024/). Default: data/raw/2024/")
    parser.add_argument("--rebuild", action="store_true",
                        help="Delete existing database before loading (fresh start)")
    args = parser.parse_args()

    # Determine data directory
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

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Data directory: {data_dir}")
    print(f"Data year     : {data_year}")
    print(f"Database path : {DB_PATH}")

    # Ensure db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Handle --rebuild
    if args.rebuild:
        for path in [DB_PATH, DB_PATH + ".wal"]:
            if os.path.exists(path):
                os.remove(path)
                print(f"Removed: {path}")

    con = duckdb.connect(DB_PATH)
    total_start = time.time()

    # ----- Phase 1: Load raw CSV files (year-aware) -----
    print(f"\n--- Phase 1: Loading raw CSV files (year={data_year}) ---")
    loaded = 0
    for csv_rel_path, table_name in TABLE_MAP.items():
        csv_path = os.path.join(data_dir, csv_rel_path)
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] File not found: {csv_rel_path}")
            continue
        load_csv_with_year(con, csv_path, table_name, data_year)
        loaded += 1
    print(f"\nLoaded {loaded}/{len(TABLE_MAP)} raw CSV files for year {data_year}.")

    # ----- Phase 2: Load lookup tables (shared, no year) -----
    print("\n--- Phase 2: Loading lookup tables ---")
    for csv_rel_path, table_name in LOOKUP_MAP.items():
        csv_path = os.path.join(data_dir, csv_rel_path)
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] File not found: {csv_rel_path}")
            continue
        load_lookup(con, csv_path, table_name)

    # ----- Phase 3: Create/update views -----
    print("\n--- Phase 3: Creating views ---")
    for sql in VIEWS_SQL:
        con.execute(sql)
    print(f"  Created {len(VIEWS_SQL)} views.")

    # ----- Phase 4: Rebuild derived tables for this year -----
    print(f"\n--- Phase 4: Rebuilding derived tables (year={data_year}) ---")
    rebuild_derived_tables(con, data_year)

    # ----- Phase 5: Create v_subsidiaries (depends on charity_base + views) -----
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
```

- [ ] **Step 11: Test the loader with 2024 data (fresh rebuild)**

Run:
```bash
rm -f data/db/cra_charities.duckdb data/db/cra_charities.duckdb.wal
python3 scripts/load_csv.py
```

Expected: Loads all 2024 data successfully. Summary shows `Loaded years: 2024`. All tables have `data_year` column. Row counts match the original (~83K for ident, financial_d, etc.).

Verify:
```bash
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
# Check data_year column exists
cols = [r[0] for r in con.execute(\"DESCRIBE ident\").fetchall()]
assert 'data_year' in cols, f'data_year not in ident: {cols}'
# Check all rows are year 2024
years = con.execute('SELECT DISTINCT data_year FROM ident').fetchall()
assert years == [(2024,)], f'Unexpected years: {years}'
# Check row count
count = con.execute('SELECT COUNT(*) FROM ident').fetchone()[0]
assert 80000 < count < 90000, f'Unexpected count: {count}'
# Check views filter to latest year
v_count = con.execute('SELECT COUNT(*) FROM v_financial_d').fetchone()[0]
assert v_count > 0, 'v_financial_d is empty'
print(f'All checks passed. ident={count}, v_financial_d={v_count}, years={years}')
con.close()
"
```

- [ ] **Step 12: Test re-loading the same year (idempotent)**

Run:
```bash
python3 scripts/load_csv.py
```

Expected: Database still has exactly one year of data (2024). Row counts unchanged. No duplicate rows.

Verify:
```bash
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
years = con.execute('SELECT DISTINCT data_year FROM ident').fetchall()
assert years == [(2024,)], f'Expected only 2024: {years}'
count = con.execute('SELECT COUNT(*) FROM ident WHERE data_year = 2024').fetchone()[0]
total = con.execute('SELECT COUNT(*) FROM ident').fetchone()[0]
assert count == total, f'Year count {count} != total {total}'
print(f'Idempotent reload passed. {count} rows, all year 2024')
con.close()
"
```

- [ ] **Step 13: Test --rebuild flag**

Run:
```bash
python3 scripts/load_csv.py --rebuild
```

Expected: Database is deleted and recreated. Same result as Step 11.

- [ ] **Step 14: Commit**

```bash
git add scripts/load_csv.py
git commit -m "feat: rewrite loader for multi-year additive loading with data_year column"
```

---

### Task 2: Rewrite the Validator

**Files:**
- Modify: `scripts/validate_db.py` (full rewrite)

- [ ] **Step 1: Rewrite validate_db.py**

Replace the entire file with:

```python
#!/usr/bin/env python3
"""
Validate the CRA charities DuckDB database after loading.

Checks row counts, schema presence, referential integrity,
and cross-table consistency — per year and cross-year.
Exit code 0 = all checks pass.

Usage:
    python3 scripts/validate_db.py              # validate all years
    python3 scripts/validate_db.py --year 2024  # validate one year
"""

import argparse
import sys
import os
import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")

PASS = 0
FAIL = 0
WARN = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def warn(name, detail=""):
    global WARN
    WARN += 1
    print(f"  WARN  {name}  {detail}")


def validate_year(con, year):
    """Run all per-year checks for a single data_year."""
    print(f"\n{'='*50}")
    print(f"Validating year: {year}")
    print(f"{'='*50}")

    # --- Schema checks ---
    print("\n--- Schema Checks ---")
    for table in ["ident", "financial_d", "financial_abc", "charity_base",
                   "schedule_3_compensation", "latest_filing", "charity_counts"]:
        cols = [r[0] for r in con.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
        ).fetchall()]
        check(f"{table} has data_year column", "data_year" in cols,
              f"columns: {cols[:5]}...")

    schema_checks = {
        "financial_d": ["BN/Registration Number", "Fiscal Period End", "4700", "5100", "4200"],
        "financial_abc": ["BN/Registration number", "Fiscal period end", "Form ID"],
        "charity_base": ["bn", "legal_name", "designation_code", "province"],
        "schedule_3_compensation": ["BN/Registration number", "300", "370", "390"],
    }
    for table, columns in schema_checks.items():
        cols = [r[0] for r in con.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
        ).fetchall()]
        for col in columns:
            check(f"{table} has column '{col}'", col in cols,
                  f"available: {cols[:5]}...")

    # --- Row count checks (scoped to year) ---
    print("\n--- Row Count Checks ---")
    tables_expected = {
        "ident": (80000, 90000),
        "financial_d": (80000, 90000),
        "financial_abc": (80000, 90000),
        "charity_base": (80000, 90000),
        "programs": (85000, 110000),
        "schedule_3_compensation": (35000, 50000),
        "grants": (10000, 20000),
    }
    for table, (lo, hi) in tables_expected.items():
        try:
            count = con.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE data_year = {year}'
            ).fetchone()[0]
            check(f"{table} count={count:,} (year={year})", lo <= count <= hi,
                  f"expected {lo:,}-{hi:,}")
        except Exception as e:
            check(f"{table} queryable", False, str(e))

    # Lookups (no year filter)
    for table, expected in [("lookup_designation", 3), ("lookup_province", 13)]:
        try:
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            check(f"{table} count={count}", count == expected,
                  f"expected {expected}")
        except Exception as e:
            check(f"{table} exists", False, str(e))

    # --- View checks ---
    print("\n--- View Checks ---")
    views = ["v_financial_d", "v_financial_abc", "v_compensation",
             "v_programs", "v_grants", "v_subsidiaries"]
    for view in views:
        try:
            count = con.execute(f'SELECT COUNT(*) FROM "{view}"').fetchone()[0]
            check(f"{view} queryable (count={count:,})", count > 0)
        except Exception as e:
            check(f"{view} queryable", False, str(e))

    # --- Referential integrity (scoped to year) ---
    print("\n--- Referential Integrity ---")
    orphan_count = con.execute(f"""
        SELECT COUNT(*) FROM financial_d fd
        LEFT JOIN ident i ON fd."BN/Registration Number" = i."BN/Registration Number"
            AND i.data_year = fd.data_year
        WHERE i."BN/Registration Number" IS NULL AND fd.data_year = {year}
    """).fetchone()[0]
    check(f"financial_d BNs all in ident (orphans={orphan_count}, year={year})",
          orphan_count == 0)

    orphan_s3 = con.execute(f"""
        SELECT COUNT(*) FROM schedule_3_compensation s
        LEFT JOIN ident i ON s."BN/Registration number" = i."BN/Registration Number"
            AND i.data_year = s.data_year
        WHERE i."BN/Registration Number" IS NULL AND s.data_year = {year}
    """).fetchone()[0]
    check(f"schedule_3 BNs all in ident (orphans={orphan_s3}, year={year})",
          orphan_s3 == 0)

    # --- Cross-table consistency (scoped to year) ---
    print("\n--- Cross-Table Consistency ---")
    ident_count = con.execute(
        f"SELECT COUNT(*) FROM ident WHERE data_year = {year}"
    ).fetchone()[0]
    cb_count = con.execute(
        f"SELECT COUNT(*) FROM charity_base WHERE data_year = {year}"
    ).fetchone()[0]
    check(f"charity_base count matches ident ({cb_count:,} vs {ident_count:,}, year={year})",
          cb_count == ident_count)

    # Line 4570 (total govt) vs computed 4540+4550+4560
    govt_check = con.execute(f"""
        SELECT
            SUM(TRY_CAST(REPLACE(REPLACE("4540",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4550",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4560",'$',''),',','') AS DECIMAL)) AS computed,
            SUM(TRY_CAST(REPLACE(REPLACE("4570",'$',''),',','') AS DECIMAL)) AS reported
        FROM financial_d WHERE data_year = {year}
    """).fetchone()
    computed_govt, reported_govt = govt_check
    if computed_govt and reported_govt:
        check(f"Line 4570 unreliable (computed={computed_govt:,.0f} vs reported={reported_govt:,.0f})",
              abs(computed_govt - reported_govt) > 1000000,
              "If these match, 4570 may have been fixed")

    # --- Duplicate check ---
    print("\n--- Duplicate Checks ---")
    for table, bn_col in [("ident", '"BN/Registration Number"'),
                          ("financial_d", '"BN/Registration Number"'),
                          ("charity_base", "bn")]:
        dup_count = con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT data_year, {bn_col}, COUNT(*) AS cnt
                FROM "{table}" WHERE data_year = {year}
                GROUP BY 1, 2 HAVING cnt > 1
            )
        """).fetchone()[0]
        check(f"No duplicate (data_year, BN) in {table} (dupes={dup_count})",
              dup_count == 0)


def validate_cross_year(con, years):
    """Run cross-year consistency checks."""
    if len(years) < 2:
        return

    print(f"\n{'='*50}")
    print(f"Cross-Year Checks ({', '.join(str(y) for y in years)})")
    print(f"{'='*50}")

    # Check table coverage across years
    year_aware_tables = [
        "ident", "financial_d", "financial_abc", "programs",
        "schedule_3_compensation", "grants",
    ]
    for table in year_aware_tables:
        counts = {}
        for y in years:
            try:
                c = con.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE data_year = {y}'
                ).fetchone()[0]
                counts[y] = c
            except Exception:
                counts[y] = 0
        missing = [y for y, c in counts.items() if c == 0]
        if missing:
            warn(f"{table} has no data for years: {missing}",
                 f"counts: {counts}")
        else:
            check(f"{table} has data for all years", True)

    # Check column availability across years
    print("\n--- Column Availability ---")
    for table in ["financial_d", "financial_abc"]:
        cols_by_year = {}
        for y in years:
            rows = con.execute(
                f'SELECT * FROM "{table}" WHERE data_year = {y} LIMIT 1'
            ).description
            cols_by_year[y] = {d[0] for d in rows} if rows else set()

        if len(cols_by_year) >= 2:
            all_cols = set()
            for cols in cols_by_year.values():
                all_cols |= cols
            for y, cols in cols_by_year.items():
                diff = all_cols - cols
                if diff:
                    warn(f"{table} year {y} missing columns: {diff}")


def main():
    parser = argparse.ArgumentParser(description="Validate CRA charities DuckDB database")
    parser.add_argument("--year", type=int, help="Validate a specific year only")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        print("Run: python3 scripts/load_csv.py")
        sys.exit(1)

    con = duckdb.connect(DB_PATH, read_only=True)

    # Discover loaded years
    try:
        all_years = [r[0] for r in con.execute(
            "SELECT DISTINCT data_year FROM ident ORDER BY data_year"
        ).fetchall()]
    except Exception:
        print("ERROR: Cannot query data_year from ident. Is the database in multi-year format?")
        sys.exit(1)

    print(f"Database contains years: {', '.join(str(y) for y in all_years)}")

    if args.year:
        if args.year not in all_years:
            print(f"ERROR: Year {args.year} not found in database. Available: {all_years}")
            sys.exit(1)
        years_to_check = [args.year]
    else:
        years_to_check = all_years

    for year in years_to_check:
        validate_year(con, year)

    validate_cross_year(con, all_years)

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Results: {PASS} passed, {FAIL} failed, {WARN} warnings")
    print(f"{'='*50}")

    con.close()
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the validator against the loaded database**

Run:
```bash
python3 scripts/validate_db.py
```

Expected: All checks pass for year 2024. Summary shows 0 failures. Output shows "Database contains years: 2024".

- [ ] **Step 3: Test --year flag**

Run:
```bash
python3 scripts/validate_db.py --year 2024
```

Expected: Same results as above, scoped to 2024 only.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate_db.py
git commit -m "feat: rewrite validator for multi-year database with per-year and cross-year checks"
```

---

### Task 3: Update generate_snapshot.py

**Files:**
- Modify: `scripts/reports/generate_snapshot.py` (lines 26-29, 76-100, 120-145, 247-252, 951-998)

- [ ] **Step 1: Add --year flag and year-aware scope filtering**

At the top of the file, add imports and update constants (after line 22):

```python
# Add after existing imports
# (no new imports needed)
```

Change line 28 `OUTPUT_DIR` to be a function of year:

Replace:
```python
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "exports", "snapshots_2024")
```
With:
```python
def output_dir(year):
    return os.path.join(PROJECT_ROOT, "data", "exports", f"snapshots_{year}")
```

- [ ] **Step 2: Update get_scope_filter to accept a year parameter**

Replace the `get_scope_filter` function (lines 76-100):

```python
def get_scope_filter(filter_type, filter_value, year=None):
    """Return (WHERE clause for charity_base, description string, filename suffix).

    If year is provided, includes a data_year filter. If None, defaults to MAX(data_year).
    """
    year_clause = (
        f"cb.data_year = {year}" if year
        else "cb.data_year = (SELECT MAX(data_year) FROM charity_base)"
    )

    if filter_type == "all":
        return year_clause, "Canadian Charity Sector", "canada"
    elif filter_type == "province":
        if filter_value == "Atlantic":
            provinces = "','".join(ATLANTIC)
            return (
                f"{year_clause} AND cb.province IN ('{provinces}')",
                "Atlantic Provinces Charity Sector",
                "atlantic",
            )
        return (
            f"{year_clause} AND cb.province = '{filter_value}'",
            f"{filter_value} Charity Sector",
            filter_value,
        )
    elif filter_type == "designation":
        desc = DESIGNATIONS.get(filter_value, filter_value)
        return (
            f"{year_clause} AND cb.designation_code = '{filter_value}'",
            f"{desc}s in the Canadian Charity Sector",
            f"designation_{filter_value}",
        )
    raise ValueError(f"Unknown filter_type: {filter_type}")
```

- [ ] **Step 3: Update scoped_table to pass year filter through**

Replace the `scoped_table` function (lines 103-113). No change needed — it already receives the `where_clause` from `get_scope_filter` which now includes the year filter. The join `INNER JOIN charity_base cb ON t.{bn} = cb.bn` needs a data_year join condition:

```python
def scoped_table(table, where_clause):
    """Return a FROM+JOIN+WHERE clause that filters a table by scope.

    Uses charity_base (cb) as the scope filter, joined on BN and data_year.
    """
    bn = BN_COL[table]
    return f"""
        {table} t
        INNER JOIN charity_base cb ON t.{bn} = cb.bn AND t.data_year = cb.data_year
        WHERE {where_clause}
    """
```

- [ ] **Step 4: Update generate_snapshot to accept year and use dynamic output dir**

Replace lines 120-168 of the `generate_snapshot` function:

```python
def generate_snapshot(filter_type, filter_value, year=None):
    """Generate one snapshot workbook."""
    con = connect()

    # Resolve year
    if year is None:
        year = con.execute("SELECT MAX(data_year) FROM charity_base").fetchone()[0]

    where, description, suffix = get_scope_filter(filter_type, filter_value, year)
    out_dir = output_dir(year)
    filename = f"snapshot_{year}_{suffix}.xlsx"
    filepath = os.path.join(out_dir, filename)

    wb = Workbook()

    # Count charities in scope
    total = con.execute(f"SELECT COUNT(*) FROM charity_base cb WHERE {where}").fetchone()[0]
    print(f"  Generating {filename} — {description} ({total:,} charities)")

    # Combined Summary sheet
    ws_summary = wb.create_sheet("Summary")
    ws_summary.column_dimensions["A"].width = 12
    ws_summary.column_dimensions["B"].width = 55
    ws_summary.column_dimensions["C"].width = 20
    ws_summary.column_dimensions["D"].width = 15
    ws_summary.column_dimensions["E"].width = 20

    # Global header
    ws_summary.append([f"Blumbergs Snapshot {year} — {description}"])
    ws_summary["A1"].font = Font(bold=True, size=14)
    ws_summary.append([f"Based on T3010 filings for {total:,} registered charities."])

    # All 9 section builders write to the same Summary sheet
    build_section_a(ws_summary, con, where, description, total)
    build_section_c(ws_summary, con, where)
    build_section_d(ws_summary, con, where)
    build_schedule_1(ws_summary, con, where)
    build_schedule_2(ws_summary, con, where)
    build_schedule_3(ws_summary, con, where)
    build_schedule_5(ws_summary, con, where)
    build_schedule_6(ws_summary, con, where)
    build_schedule_8(ws_summary, con, where)

    # Add row-level detail sheets for audit verification
    print("  Adding detail sheets...")
    build_detail_sheets(wb, con, where)

    # Remove default empty sheet if present
    if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
        del wb["Sheet"]

    os.makedirs(out_dir, exist_ok=True)
    wb.save(filepath)
    con.close()
    return filepath
```

- [ ] **Step 5: Update the detail sheet builder to join on data_year**

In `build_detail_sheet` (around line 246-252), update the SQL query to join on data_year:

Replace:
```python
    sql = f"""
        SELECT {', '.join(select_parts)}
        FROM {table} t
        INNER JOIN charity_base cb ON t.{bn_col} = cb.bn
        WHERE {where}
        ORDER BY cb.bn
    """
```
With:
```python
    sql = f"""
        SELECT {', '.join(select_parts)}
        FROM {table} t
        INNER JOIN charity_base cb ON t.{bn_col} = cb.bn AND t.data_year = cb.data_year
        WHERE {where}
        ORDER BY cb.bn
    """
```

- [ ] **Step 6: Update main() to accept --year flag**

Replace the `main()` function (lines 951-998):

```python
def main():
    parser = argparse.ArgumentParser(description="Generate Blumbergs Snapshot workbooks")
    parser.add_argument("--all", action="store_true", help="Generate all 13 workbooks")
    parser.add_argument("--province", type=str, help="Single province code (e.g. ON)")
    parser.add_argument("--provincial", action="store_true", help="All 9 provincial workbooks")
    parser.add_argument("--designation", nargs="?", const="ALL", type=str,
                        help="Designation code (A/B/C) or omit for all three")
    parser.add_argument("--designations", action="store_true", help="All 3 designation workbooks")
    parser.add_argument("--year", type=int, default=None,
                        help="Data year (default: latest in database)")
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
        path = generate_snapshot(ftype, fval, year=args.year)
        paths.append(path)

    elapsed = time.time() - start
    print(f"\nDone. {len(paths)} workbook(s) generated in {elapsed:.1f}s")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Test snapshot generation**

Run:
```bash
python3 scripts/reports/generate_snapshot.py
```

Expected: Generates `snapshot_2024_canada.xlsx` in `data/exports/snapshots_2024/`. Values should match the pre-change output (same data, just filtered through `data_year = 2024`).

- [ ] **Step 8: Commit**

```bash
git add scripts/reports/generate_snapshot.py
git commit -m "feat: add --year flag to snapshot generator for multi-year database"
```

---

### Task 4: Update generate_comparison.py

**Files:**
- Modify: `scripts/reports/generate_comparison.py` (lines 23-27, and anywhere `charity_base`/`financial_d` is queried)

- [ ] **Step 1: Add --year flag to the comparison generator**

The comparison script queries the database for 2024 values and uses hardcoded 2023 values. Add a `--year` flag so it can target any year as the "current" year:

At the top of the file, after the existing imports, add argparse:

```python
import argparse
```

Update the constants at lines 23-27 to be year-aware. Replace:

```python
SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, "data", "exports", "snapshots_2024", "snapshot_2024_canada.xlsx")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "exports", "snapshot_comparison_2023_vs_2024.xlsx")
```

With:

```python
def snapshot_path(year):
    return os.path.join(PROJECT_ROOT, "data", "exports", f"snapshots_{year}", f"snapshot_{year}_canada.xlsx")

def output_path(current_year, prior_year):
    return os.path.join(PROJECT_ROOT, "data", "exports", f"snapshot_comparison_{prior_year}_vs_{current_year}.xlsx")
```

- [ ] **Step 2: Update the main function to accept --year and wire it through**

Find the `main()` function at the bottom of the file and add the `--year` flag. The exact edits depend on how `main()` calls the comparison builder, but the pattern is: resolve year, compute paths, pass year to any DB queries.

Add argparse to `main()`:

```python
def main():
    parser = argparse.ArgumentParser(description="Generate Blumbergs Snapshot comparison workbook")
    parser.add_argument("--year", type=int, default=None,
                        help="Current year for comparison (default: latest in database)")
    args = parser.parse_args()

    con = duckdb.connect(DB_PATH, read_only=True)
    if args.year:
        current_year = args.year
    else:
        current_year = con.execute("SELECT MAX(data_year) FROM charity_base").fetchone()[0]
    prior_year = current_year - 1
    con.close()

    sp = snapshot_path(current_year)
    op = output_path(current_year, prior_year)

    # ... rest of main uses sp, op, current_year, prior_year ...
```

Update references to the old `SNAPSHOT_PATH` and `OUTPUT_PATH` constants throughout the function to use the new computed values.

- [ ] **Step 3: Test**

Run:
```bash
python3 scripts/reports/generate_comparison.py
```

Expected: Generates comparison workbook using 2024 as current year. Same output as before.

- [ ] **Step 4: Commit**

```bash
git add scripts/reports/generate_comparison.py
git commit -m "feat: add --year flag to comparison generator for multi-year database"
```

---

### Task 5: Update generate_snapshot_articles.py

**Files:**
- Modify: `scripts/reports/generate_snapshot_articles.py` (lines 39-43, 278-306, and main)

- [ ] **Step 1: Make year constants into parameters**

Replace the hardcoded year constants at lines 39-43:

```python
BYLINE_DATE = "March 3rd, 2026"
PROCESSED_BY = "January 2026"
DATA_YEAR = 2024
PRIOR_YEAR = 2023
APPROX_CHARITIES = "86,000"
```

Keep these as defaults but add a `--year` flag that overrides `DATA_YEAR` and computes `PRIOR_YEAR = year - 1`.

- [ ] **Step 2: Update get_scope_filter to include year**

Update the `get_scope_filter` function (lines 278-306) to accept a `year` parameter and include `cb.data_year = {year}` in the WHERE clause, same pattern as the snapshot generator.

- [ ] **Step 3: Update scoped_from to join on data_year**

Update the `scoped_from` function (line 272-275):

Replace:
```python
def scoped_from(table, where):
    """Return FROM+JOIN+WHERE clause scoped through charity_base."""
    bn = BN_COL[table]
    return f"{table} t INNER JOIN charity_base cb ON t.{bn} = cb.bn WHERE {where}"
```
With:
```python
def scoped_from(table, where):
    """Return FROM+JOIN+WHERE clause scoped through charity_base."""
    bn = BN_COL[table]
    return f"{table} t INNER JOIN charity_base cb ON t.{bn} = cb.bn AND t.data_year = cb.data_year WHERE {where}"
```

- [ ] **Step 4: Update main() to accept --year**

Add `--year` to the argparse and wire it through to `generate_article()` calls.

- [ ] **Step 5: Test**

Run:
```bash
python3 scripts/reports/generate_snapshot_articles.py
```

Expected: Generates Canada article for 2024. Same output as before.

- [ ] **Step 6: Commit**

```bash
git add scripts/reports/generate_snapshot_articles.py
git commit -m "feat: add --year flag to article generator for multi-year database"
```

---

### Task 6: Update generate_jewish_sector.py

**Files:**
- Modify: `scripts/reports/generate_jewish_sector.py` (lines 77-83 FINANCIAL_JOINS, and main)

- [ ] **Step 1: Add year-awareness to joins**

The jewish sector script joins through `charity_base`, `latest_filing`, `financial_d`, and `schedule_3_compensation`. Update `FINANCIAL_JOINS` (lines 77-83) to include `data_year`:

Replace:
```python
FINANCIAL_JOINS = """
    LEFT JOIN latest_filing lf ON lf.bn = cb.bn
    LEFT JOIN financial_d fd ON fd."BN/Registration Number" = cb.bn
        AND fd."Fiscal period end" = lf.latest_fiscal_end
    LEFT JOIN schedule_3_compensation s3 ON s3."BN/Registration number" = cb.bn
        AND s3."Fiscal period end" = lf.latest_fiscal_end
"""
```
With:
```python
FINANCIAL_JOINS = """
    LEFT JOIN latest_filing lf ON lf.bn = cb.bn AND lf.data_year = cb.data_year
    LEFT JOIN financial_d fd ON fd."BN/Registration Number" = cb.bn
        AND fd."Fiscal Period End" = lf.latest_fiscal_end AND fd.data_year = cb.data_year
    LEFT JOIN schedule_3_compensation s3 ON s3."BN/Registration number" = cb.bn
        AND s3."Fiscal period end" = lf.latest_fiscal_end AND s3.data_year = cb.data_year
"""
```

- [ ] **Step 2: Add --year flag and year filter to all queries**

Add `--year` to argparse in `main()`. Add a year filter to all queries that go through `charity_base`:

Wherever the script queries `FROM charity_base cb`, add `AND cb.data_year = {year}` (or `= (SELECT MAX(data_year) FROM charity_base)` when year is None).

- [ ] **Step 3: Test**

Run:
```bash
python3 scripts/reports/generate_jewish_sector.py
```

Expected: Generates the Jewish sector workbook with 2024 data. Same output as before.

- [ ] **Step 4: Commit**

```bash
git add scripts/reports/generate_jewish_sector.py
git commit -m "feat: add --year flag to Jewish sector generator for multi-year database"
```

---

### Task 7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md with multi-year documentation**

Key sections to update:

1. **Common Commands** — Add multi-year loading examples:
   ```
   # Load multiple years
   python3 scripts/load_csv.py data/raw/2023/
   python3 scripts/load_csv.py data/raw/2024/

   # Fresh rebuild
   python3 scripts/load_csv.py --rebuild

   # Validate specific year
   python3 scripts/validate_db.py --year 2024

   # Generate snapshot for specific year
   python3 scripts/reports/generate_snapshot.py --year 2023
   ```

2. **Database Schema** — Add `data_year INTEGER` as the first column in all raw/derived table descriptions. Note that lookup tables don't have it. Update row counts to note they're per-year.

3. **Critical Data Quirks** — Add a new quirk:
   ```
   9. **Multi-year database** — All raw and derived tables have `data_year INTEGER` as
      their first column, identifying the CRA data release year. Views filter to
      `MAX(data_year)` by default. Query raw tables directly for cross-year comparisons.
      Lookup tables are shared across years (no data_year column).
   ```

4. **Views** — Note that views filter to latest year by default and expose `data_year`.

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with multi-year database schema and commands"
```

---

### Task 8: End-to-End Verification

- [ ] **Step 1: Fresh rebuild and load 2024**

```bash
python3 scripts/load_csv.py --rebuild
```

Expected: Clean database with only 2024 data.

- [ ] **Step 2: Run validator**

```bash
python3 scripts/validate_db.py
```

Expected: All checks pass.

- [ ] **Step 3: Generate Canada snapshot**

```bash
python3 scripts/reports/generate_snapshot.py
```

Expected: Snapshot workbook generated successfully with correct values.

- [ ] **Step 4: Verify view backward compatibility**

```bash
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
# Views should work as before
for view in ['v_financial_d', 'v_compensation', 'v_programs', 'v_grants']:
    count = con.execute(f'SELECT COUNT(*) FROM {view}').fetchone()[0]
    print(f'{view}: {count:,} rows')
# charity_base should have data_year
cols = [r[0] for r in con.execute('DESCRIBE charity_base').fetchall()]
assert 'data_year' in cols
print(f'charity_base columns: {cols[:5]}...')
con.close()
print('All backward compatibility checks passed.')
"
```

- [ ] **Step 5: Verify cross-year readiness**

```bash
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
# Verify the structure supports multiple years
count = con.execute('SELECT COUNT(DISTINCT data_year) FROM ident').fetchone()[0]
print(f'Distinct years in ident: {count}')
# Verify year-filtered query works
count = con.execute('SELECT COUNT(*) FROM financial_d WHERE data_year = 2024').fetchone()[0]
print(f'financial_d rows for 2024: {count:,}')
# Verify cross-year query structure works (even with one year)
result = con.execute('''
    SELECT data_year, COUNT(*) as charities,
           SUM(TRY_CAST(REPLACE(REPLACE(\"4700\", '\$', ''), ',', '') AS DECIMAL)) as total_revenue
    FROM financial_d
    GROUP BY data_year
    ORDER BY data_year
''').fetchall()
for year, charities, revenue in result:
    print(f'Year {year}: {charities:,} charities, revenue={revenue:,.0f}')
con.close()
print('Cross-year readiness verified.')
"
```

- [ ] **Step 6: Final commit (if any fixups were needed)**

```bash
git status
# If any fixes were made, commit them
```
