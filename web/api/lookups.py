"""GET /api/lookups — Return provinces, designations, categories for dropdowns."""

import json
import os
from http.server import BaseHTTPRequestHandler
import psycopg2


DATABASE_URL = os.environ.get("NEON_DATABASE_URL", "") or os.environ.get("DATABASE_URL", "")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            con = psycopg2.connect(DATABASE_URL)
            cur = con.cursor()

            cur.execute("SELECT DISTINCT province FROM charity_base ORDER BY 1")
            provs = [r[0] for r in cur.fetchall()]

            cur.execute(
                "SELECT designation_code, designation_desc FROM charity_base "
                "GROUP BY designation_code, designation_desc ORDER BY 1"
            )
            desigs = [{"code": r[0], "desc": r[1]} for r in cur.fetchall()]

            cur.execute(
                "SELECT DISTINCT category_code, category_desc FROM charity_base "
                "WHERE category_desc IS NOT NULL ORDER BY 2"
            )
            cats = [{"code": r[0], "desc": r[1]} for r in cur.fetchall()]

            cur.close()
            con.close()

            self._json({"provinces": provs, "designations": desigs, "categories": cats})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _json(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
