#!/usr/bin/env python3
"""
Validate the CRA charities DuckDB database after loading.

Checks row counts, schema presence, referential integrity,
and cross-table consistency. Exit code 0 = all checks pass.

Usage:
    python3 scripts/validate_db.py
"""

import sys
import os
import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    global PASS, FAIL

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        print("Run: python3 scripts/load_csv.py")
        sys.exit(1)

    con = duckdb.connect(DB_PATH, read_only=True)

    # --- Row count checks ---
    print("\n--- Row Count Checks ---")
    tables_expected = {
        "ident": (80000, 90000),
        "financial_d": (80000, 90000),
        "financial_abc": (80000, 90000),
        "charity_base": (80000, 90000),
        "programs": (85000, 110000),
        "schedule_3_compensation": (35000, 50000),
        "grants": (10000, 20000),
        "lookup_designation": (3, 3),
        "lookup_province": (13, 13),
    }
    for table, (lo, hi) in tables_expected.items():
        try:
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            check(f"{table} count={count:,}", lo <= count <= hi,
                  f"expected {lo:,}-{hi:,}")
        except Exception as e:
            check(f"{table} exists", False, str(e))

    # --- Schema checks ---
    print("\n--- Schema Checks ---")
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

    # --- Referential integrity ---
    print("\n--- Referential Integrity ---")
    orphan_count = con.execute("""
        SELECT COUNT(*) FROM financial_d fd
        LEFT JOIN ident i ON fd."BN/Registration Number" = i."BN/Registration Number"
        WHERE i."BN/Registration Number" IS NULL
    """).fetchone()[0]
    check(f"financial_d BNs all in ident (orphans={orphan_count})", orphan_count == 0)

    orphan_s3 = con.execute("""
        SELECT COUNT(*) FROM schedule_3_compensation s
        LEFT JOIN ident i ON s."BN/Registration number" = i."BN/Registration Number"
        WHERE i."BN/Registration Number" IS NULL
    """).fetchone()[0]
    check(f"schedule_3 BNs all in ident (orphans={orphan_s3})", orphan_s3 == 0)

    # --- Cross-table consistency ---
    print("\n--- Cross-Table Consistency ---")
    ident_count = con.execute("SELECT COUNT(*) FROM ident").fetchone()[0]
    cb_count = con.execute("SELECT COUNT(*) FROM charity_base").fetchone()[0]
    check(f"charity_base count matches ident ({cb_count:,} vs {ident_count:,})",
          cb_count == ident_count)

    # Line 4570 (total govt) vs computed 4540+4550+4560
    govt_check = con.execute("""
        SELECT
            SUM(TRY_CAST(REPLACE(REPLACE("4540",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4550",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4560",'$',''),',','') AS DECIMAL)) AS computed,
            SUM(TRY_CAST(REPLACE(REPLACE("4570",'$',''),',','') AS DECIMAL)) AS reported
        FROM financial_d
    """).fetchone()
    computed_govt, reported_govt = govt_check
    check(f"Line 4570 unreliable (computed={computed_govt:,.0f} vs reported={reported_govt:,.0f})",
          abs(computed_govt - reported_govt) > 1000000,
          "If these match, 4570 may have been fixed")

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    print(f"{'='*50}")

    con.close()
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
