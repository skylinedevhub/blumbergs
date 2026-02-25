#!/usr/bin/env python3
"""Migrate DuckDB data to Neon Postgres for Vercel deployment.

Usage:
    python3 scripts/migrate_to_neon.py
    python3 scripts/migrate_to_neon.py --connection-string "postgresql://..."

Reads NEON_DATABASE_URL from environment if --connection-string not provided.
"""

import os
import sys
import time
import duckdb
import psycopg2
import psycopg2.extras
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "cra_charities.duckdb"

# DuckDB type -> Postgres type mapping
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


def get_connection_string():
    for arg in sys.argv[1:]:
        if arg.startswith("postgresql://"):
            return arg
    if "--connection-string" in sys.argv:
        idx = sys.argv.index("--connection-string")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return os.environ.get("NEON_DATABASE_URL", "")


def pg_type(duck_type: str) -> str:
    duck_type = duck_type.strip().upper()
    for k, v in TYPE_MAP.items():
        if duck_type.startswith(k):
            return v
    return "TEXT"


def quote_col(name: str) -> str:
    """Quote a column name for Postgres."""
    return '"' + name.replace('"', '""') + '"'


def migrate():
    conn_str = get_connection_string()
    if not conn_str:
        print("ERROR: No connection string provided.")
        print("Set NEON_DATABASE_URL or pass --connection-string")
        sys.exit(1)

    if not DB.exists():
        print(f"ERROR: DuckDB not found: {DB}")
        sys.exit(1)

    duck = duckdb.connect(str(DB), read_only=True)
    pg = psycopg2.connect(conn_str)
    pg.autocommit = False
    cur = pg.cursor()

    # Get all tables (not views)
    tables = duck.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' AND table_type='BASE TABLE' "
        "ORDER BY table_name"
    ).fetchall()

    print(f"Found {len(tables)} tables to migrate\n")

    for (table_name,) in tables:
        t0 = time.perf_counter()
        cols_info = duck.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        col_names = [c[1] for c in cols_info]
        col_types = [c[2] for c in cols_info]

        # Drop and create
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

        col_defs = ", ".join(
            f"{quote_col(name)} {pg_type(dtype)}"
            for name, dtype in zip(col_names, col_types)
        )
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        # Fetch all data from DuckDB
        rows = duck.execute(f'SELECT * FROM "{table_name}"').fetchall()
        if rows:
            placeholders = ", ".join(["%s"] * len(col_names))
            quoted_cols = ", ".join(quote_col(c) for c in col_names)
            insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'

            # Batch insert
            batch_size = 5000
            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                # Convert tuples to lists for psycopg2
                psycopg2.extras.execute_batch(cur, insert_sql, batch, page_size=1000)

        pg.commit()
        elapsed = time.perf_counter() - t0
        print(f"  {table_name}: {len(rows):,} rows ({elapsed:.1f}s)")

    # Create views
    print("\nCreating views...")
    views = duck.execute(
        "SELECT view_name, sql FROM duckdb_views() WHERE schema_name='main'"
    ).fetchall()

    for view_name, view_sql in views:
        # Adapt DuckDB view SQL to Postgres
        pg_sql = adapt_view_sql(view_sql)
        try:
            cur.execute(f'DROP VIEW IF EXISTS "{view_name}" CASCADE')
            cur.execute(pg_sql)
            pg.commit()
            print(f"  {view_name}: OK")
        except Exception as e:
            pg.rollback()
            print(f"  {view_name}: FAILED - {e}")

    # Create money() function for Postgres
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

    # Verify counts
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


def adapt_view_sql(sql: str) -> str:
    """Adapt DuckDB CREATE VIEW SQL to Postgres-compatible SQL."""
    # Remove main. schema prefix
    sql = sql.replace("main.", "")
    # DuckDB uses trim() as main.trim() — just use trim()
    sql = sql.replace('"trim"', "trim")
    return sql


if __name__ == "__main__":
    migrate()
