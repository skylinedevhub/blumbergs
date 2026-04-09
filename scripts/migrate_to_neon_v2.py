#!/usr/bin/env python3
"""Migrate DuckDB data to Neon Postgres — resilient version with smaller batches and reconnection."""

import os
import sys
import time
import duckdb
import psycopg2
import psycopg2.extras
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "cra_charities.duckdb"
CONN_STR = os.environ.get("NEON_DATABASE_URL", "")
BATCH_SIZE = 1000

TYPE_MAP = {
    "VARCHAR": "TEXT",
    "BIGINT": "BIGINT",
    "INTEGER": "INTEGER",
    "BOOLEAN": "BOOLEAN",
    "DOUBLE": "DOUBLE PRECISION",
    "FLOAT": "REAL",
    "TIMESTAMP": "TIMESTAMP",
    "DATE": "DATE",
    "DECIMAL": "NUMERIC",
}


def pg_type(duck_type):
    duck_type = duck_type.strip().upper()
    for k, v in TYPE_MAP.items():
        if duck_type.startswith(k):
            return v
    return "TEXT"


def quote_col(name):
    return '"' + name.replace('"', '""') + '"'


def get_pg():
    return psycopg2.connect(CONN_STR)


def table_exists_with_count(table_name, expected_count):
    """Check if table already exists with correct row count."""
    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cur.fetchone()[0]
        cur.close()
        pg.close()
        return count == expected_count
    except Exception:
        return False


def pg_row_count(table_name):
    """Get current row count in Postgres, or -1 if table doesn't exist."""
    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cur.fetchone()[0]
        cur.close()
        pg.close()
        return count
    except Exception:
        return -1


def insert_batch_with_retry(insert_sql, batch, max_retries=3):
    """Insert a single batch with reconnection on failure."""
    for attempt in range(max_retries):
        try:
            pg = get_pg()
            pg.autocommit = False
            cur = pg.cursor()
            psycopg2.extras.execute_batch(cur, insert_sql, batch, page_size=50)
            pg.commit()
            cur.close()
            pg.close()
            return True
        except Exception as e:
            try:
                pg.close()
            except Exception:
                pass
            if attempt < max_retries - 1:
                wait = 3 * (attempt + 1)
                print(f"    Retry {attempt+1}/{max_retries} after {wait}s...")
                time.sleep(wait)
            else:
                print(f"    FAILED after {max_retries} attempts: {e}")
                return False
    return False


def migrate_table(duck, table_name):
    t0 = time.perf_counter()
    cols_info = duck.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    col_names = [c[1] for c in cols_info]
    col_types = [c[2] for c in cols_info]

    duck_count = duck.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]

    # Check if already done
    pg_count = pg_row_count(table_name)
    if pg_count == duck_count:
        print(f"  {table_name}: {duck_count:,} rows (already migrated, skipping)")
        return

    # Create table
    pg = get_pg()
    cur = pg.cursor()
    cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
    col_defs = ", ".join(
        f"{quote_col(name)} {pg_type(dtype)}"
        for name, dtype in zip(col_names, col_types)
    )
    cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    pg.commit()
    cur.close()
    pg.close()

    if duck_count == 0:
        print(f"  {table_name}: 0 rows (empty)")
        return

    # Fetch and insert in chunks
    rows = duck.execute(f'SELECT * FROM "{table_name}"').fetchall()
    placeholders = ", ".join(["%s"] * len(col_names))
    quoted_cols = ", ".join(quote_col(c) for c in col_names)
    insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'

    inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        if insert_batch_with_retry(insert_sql, batch):
            inserted += len(batch)
        else:
            print(f"  {table_name}: FAILED at row {i}")
            return

    elapsed = time.perf_counter() - t0
    print(f"  {table_name}: {inserted:,} rows ({elapsed:.1f}s)")


def migrate():
    if not CONN_STR:
        print("ERROR: Set NEON_DATABASE_URL"); sys.exit(1)
    if not DB.exists():
        print(f"ERROR: DuckDB not found: {DB}"); sys.exit(1)

    duck = duckdb.connect(str(DB), read_only=True)

    tables = duck.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' AND table_type='BASE TABLE' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"Found {len(tables)} tables to migrate\n")

    for (table_name,) in tables:
        migrate_table(duck, table_name)

    # Create views
    print("\nCreating views...")
    views = duck.execute(
        "SELECT view_name, sql FROM duckdb_views() WHERE schema_name='main'"
    ).fetchall()

    pg = get_pg()
    cur = pg.cursor()
    for view_name, view_sql in views:
        pg_sql = view_sql.replace("main.", "").replace('"trim"', "trim")
        try:
            cur.execute(f'DROP VIEW IF EXISTS "{view_name}" CASCADE')
            cur.execute(pg_sql)
            pg.commit()
            print(f"  {view_name}: OK")
        except Exception as e:
            pg.rollback()
            print(f"  {view_name}: FAILED - {e}")

    # Create money() function
    print("\nCreating money() function...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION money(val TEXT)
        RETURNS NUMERIC AS $$
        BEGIN
            RETURN CAST(REPLACE(REPLACE(COALESCE(val, '0'), '$', ''), ',', '') AS NUMERIC);
        EXCEPTION WHEN OTHERS THEN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)
    pg.commit()
    print("  money() function: OK")

    # Verify
    print("\nVerifying row counts...")
    all_ok = True
    for (table_name,) in tables:
        duck_count = duck.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        pg_count = cur.fetchone()[0]
        status = "OK" if duck_count == pg_count else "MISMATCH"
        if status != "OK":
            all_ok = False
        print(f"  {table_name}: DuckDB={duck_count:,} Postgres={pg_count:,} [{status}]")

    if all_ok:
        print("\nMigration complete - all counts match!")
    else:
        print("\nWARNING: Some counts don't match!")

    cur.close()
    pg.close()
    duck.close()


if __name__ == "__main__":
    migrate()
