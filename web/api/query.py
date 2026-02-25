"""POST /api/query — Execute a SELECT query against Neon Postgres."""

import json
import os
import re
import time
import decimal
import datetime
from http.server import BaseHTTPRequestHandler
import psycopg2


DATABASE_URL = os.environ.get("NEON_DATABASE_URL", "")


def prep(sql):
    """Strip money() macro definition (DuckDB artifact); leave money() calls for Postgres function."""
    sql = re.sub(
        r"(--[^\n]*\n\s*)?CREATE\s+OR\s+REPLACE\s+MACRO\s+money.*?;\s*", "", sql, flags=re.S | re.I
    )
    return sql.strip()


def only_select(sql):
    s = re.sub(r"--[^\n]*", "", sql).strip().upper()
    if not (s.startswith("SELECT") or s.startswith("WITH")):
        return False
    for kw in (
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "COPY", "ATTACH", "DETACH",
    ):
        if re.search(r"\b" + kw + r"\b", s):
            return False
    return True


def default_ser(o):
    if isinstance(o, decimal.Decimal):
        return float(o)
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            data = json.loads(body)
            sql = prep(data.get("sql", ""))

            if not only_select(sql):
                return self._json({"error": "Only SELECT queries allowed"}, 400)

            t0 = time.perf_counter()
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = [list(r) for r in cur.fetchall()]
            elapsed = time.perf_counter() - t0
            cur.close()
            con.close()

            self._json(
                {"columns": cols, "rows": rows, "count": len(rows), "time": round(elapsed, 4)}
            )
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _json(self, data, status=200):
        raw = json.dumps(data, default=default_ser).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
