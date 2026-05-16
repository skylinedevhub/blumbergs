"""Execute each generated SQL against the local DuckDB; surface any error.

Postgres exposes money(text) as a function; locally we substitute the
equivalent TRY_CAST expression (matches scripts/explorer_server.py)."""
import json, re, sys, duckdb


def to_duckdb(sql):
    # money() arguments in generated SQL are always a single column ref
    # (e.g. fd."4500"), so a non-greedy regex suffices.
    return re.sub(
        r"\bmoney\(([^()]+)\)",
        r"TRY_CAST(REPLACE(REPLACE(\1, '$', ''), ',', '') AS DECIMAL)",
        sql,
    )


with open("/tmp/explorer_queries.json") as f:
    cases = json.load(f)

con = duckdb.connect("data/db/cra_charities.duckdb", read_only=True)

failed = 0
for c in cases:
    sql = to_duckdb(c["sql"])
    try:
        cur = con.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print(f"OK   {c['name']:10s}  -> {len(rows):3d} rows, {len(cols)} cols")
    except Exception as e:
        failed += 1
        print(f"FAIL {c['name']:10s}  -> {e}", file=sys.stderr)
        print(sql, file=sys.stderr)

sys.exit(1 if failed else 0)
