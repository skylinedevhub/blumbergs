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
        try:
            cols = [r[0] for r in con.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            ).fetchall()]
            check(f"{table} has data_year column", "data_year" in cols,
                  f"columns: {cols[:5]}...")
        except Exception as e:
            check(f"{table} schema readable", False, str(e))

    schema_checks = {
        "financial_d": ["BN/Registration Number", "Fiscal Period End", "4700", "5100", "4200"],
        "financial_abc": ["BN/Registration number", "Fiscal period end", "Form ID"],
        "charity_base": ["bn", "legal_name", "designation_code", "province"],
        "schedule_3_compensation": ["BN/Registration number", "300", "370", "390"],
    }
    for table, columns in schema_checks.items():
        try:
            cols = [r[0] for r in con.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            ).fetchall()]
            for col in columns:
                check(f"{table} has column '{col}'", col in cols,
                      f"available: {cols[:5]}...")
        except Exception as e:
            check(f"{table} schema readable", False, str(e))

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
    print("\n--- Table Coverage ---")
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
        print("Try: python3 scripts/load_csv.py --rebuild")
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
