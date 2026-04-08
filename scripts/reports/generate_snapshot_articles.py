#!/usr/bin/env python3
"""Generate Blumbergs Snapshot article Word documents for 2024.

Takes the Manitoba 2023 .docx as a format template, updates all content
with 2024 data from DuckDB, embeds annotated T3010 PDF pages as images,
and produces one Word document per scope (13 total).

Usage:
    python3 scripts/reports/generate_snapshot_articles.py              # Canada only
    python3 scripts/reports/generate_snapshot_articles.py --all        # All 13 articles
    python3 scripts/reports/generate_snapshot_articles.py --province ON
    python3 scripts/reports/generate_snapshot_articles.py --provincial # All 9 provincial
    python3 scripts/reports/generate_snapshot_articles.py --designation A
    python3 scripts/reports/generate_snapshot_articles.py --designations
"""

import argparse
import io
import os
import sys
import copy
from decimal import Decimal

import duckdb
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches, Pt, Emu, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ── paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "Blumbergs Snapshot of the Manitoba Charity Sector 2023.docx")
PDF_DIR = os.path.join(PROJECT_ROOT, "data", "exports", "snapshot_pdfs_2024")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "exports", "articles_2024")

# ── constants ────────────────────────────────────────────────────────────────
BYLINE_DATE = "March 3rd, 2026"
PROCESSED_BY = "January 2026"
DATA_YEAR = 2024
PRIOR_YEAR = 2023
APPROX_CHARITIES = "86,000"

BN_COL = {
    "ident": '"BN/Registration Number"',
    "financial_d": '"BN/Registration Number"',
    "financial_abc": '"BN/Registration number"',
    "schedule_1_foundations": '"BN/Registration number"',
    "schedule_2_summary": '"BN/Registration number"',
    "schedule_3_compensation": '"BN/Registration number"',
    "schedule_5_noncash": '"BN/Registration number"',
    "schedule_8_disbursement": '"BN/Registration Number"',
}

PROVINCES = ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB"]
ATLANTIC = ["NB", "NS", "NL", "PE"]
DESIGNATIONS = {
    "A": "Public Foundation",
    "B": "Private Foundation",
    "C": "Charitable Organization",
}

PROVINCE_NAMES = {
    "ON": "Ontario",
    "QC": "Quebec",
    "BC": "British Columbia",
    "AB": "Alberta",
    "MB": "Manitoba",
    "SK": "Saskatchewan",
    "NS": "Nova Scotia",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "PE": "Prince Edward Island",
    "Atlantic": "Atlantic Provinces",
}

# ── Prior year (2023) comparison data from published Blumbergs snapshot PDFs ──
# Source: canadiancharitylaw.ca/wp-content/uploads/2025/05/

CANADA_2023 = {
    "charity_count": 83540,
    "active": 78598,
    "inactive": 3429,
    "gifts_to_qd": 29814,
    "total_revenue": 393_000_000_000,
    "total_expenditures": 354_000_000_000,
    "foreign_projects": 5089,
    "foreign_amount": 5_300_000_000,
    "global_affairs": 139,
    "has_employment": 43351,
    "no_employment": 39775,
    "compensation": 200_000_000_000,
    "tax_receipted": 23_400_000_000,
}

MB_2023 = {
    "charity_count": 4682,
    "active": 4437,
    "inactive": 155,
    "gifts_to_qd": 1691,
    "total_revenue": 15_000_000_000,
    "total_expenditures": 14_200_000_000,
    "foreign_projects": 255,
    "foreign_amount": 196_000_000,
    "global_affairs": 4,
    "has_employment": 2607,
    "no_employment": 2049,
    "compensation": 8_200_000_000,
    "tax_receipted": 825_000_000,
}

# Ontario 2023 (from published 2023 snapshot comparison table)
ON_2023 = {
    "charity_count": 30426,
    "active": 28644,
    "inactive": 1295,
    "gifts_to_qd": 12408,
    "total_revenue": 162_000_000_000,
    "total_expenditures": 136_000_000_000,
    "foreign_projects": 2285,
    "foreign_amount": 3_700_000_000,
    "global_affairs": 76,
    "has_employment": 15156,
    "no_employment": 15090,
    "compensation": 76_300_000_000,
    "tax_receipted": 12_600_000_000,
}

# Quebec 2023 (from published 2023 snapshot comparison table)
QC_2023 = {
    "charity_count": 15437,
    "active": 14384,
    "inactive": 879,
    "gifts_to_qd": 3663,
    "total_revenue": 83_000_000_000,
    "total_expenditures": 77_400_000_000,
    "foreign_projects": 731,
    "foreign_amount": 750_000_000,
    "global_affairs": 34,
    "has_employment": 8695,
    "no_employment": 6704,
    "compensation": 43_000_000_000,
    "tax_receipted": 2_600_000_000,
}

# British Columbia 2023 (from published 2023 snapshot comparison table)
BC_2023 = {
    "charity_count": 12021,
    "active": 11312,
    "inactive": 448,
    "gifts_to_qd": 4498,
    "total_revenue": 55_800_000_000,
    "total_expenditures": 52_700_000_000,
    "foreign_projects": 930,
    "foreign_amount": 289_800_000,
    "global_affairs": 11,
    "has_employment": 6084,
    "no_employment": 5877,
    "compensation": 28_900_000_000,
    "tax_receipted": 3_500_000_000,
}

# Alberta 2023 (from published 2023 snapshot comparison table)
AB_2023 = {
    "charity_count": 9100,
    "active": 8604,
    "inactive": 281,
    "gifts_to_qd": 3344,
    "total_revenue": 44_300_000_000,
    "total_expenditures": 42_700_000_000,
    "foreign_projects": 616,
    "foreign_amount": 160_900_000,
    "global_affairs": 8,
    "has_employment": 4614,
    "no_employment": 4444,
    "compensation": 23_600_000_000,
    "tax_receipted": 2_500_000_000,
}

# Atlantic Canada 2023 (from published 2023 snapshot comparison table)
ATL_2023 = {
    "charity_count": 7698,
    "active": 7263,
    "inactive": 245,
    "gifts_to_qd": 2730,
    "total_revenue": 19_600_000_000,
    "total_expenditures": 18_700_000_000,
    "foreign_projects": 200,
    "foreign_amount": 210_700_000,
    "global_affairs": 4,
    "has_employment": 4099,
    "no_employment": 3554,
    "compensation": 11_500_000_000,
    "tax_receipted": 987_500_000,
}

# Public Foundations 2023 (from published 2023 snapshot highlights)
PUBLIC_FOUNDATIONS_2023 = {
    "charity_count": 4689,
    "active": 4372,
    "inactive": 294,
    "gifts_to_qd": 3061,
    "total_revenue": 14_000_000_000,
    "total_expenditures": 10_000_000_000,
    "foreign_projects": None,
    "foreign_amount": 195_400_000,
    "global_affairs": 2,
    "has_employment": 1296,
    "no_employment": 3367,
    "compensation": 1_100_000_000,
    "tax_receipted": 5_400_000_000,
}

# Private Foundations 2023 (from published 2023 snapshot highlights)
PRIVATE_FOUNDATIONS_2023 = {
    "charity_count": 6557,
    "active": 4503,
    "inactive": 431,
    "gifts_to_qd": 4164,
    "total_revenue": 28_400_000_000,
    "total_expenditures": 7_000_000_000,
    "foreign_projects": None,
    "foreign_amount": 1_100_000_000,
    "global_affairs": 1,
    "has_employment": 664,
    "no_employment": 5856,
    "compensation": 376_000_000,
    "tax_receipted": 4_400_000_000,
}

# Charitable Organizations 2023 (from published 2023 snapshot highlights)
CHARITABLE_ORGS_2023 = {
    "charity_count": 74132,
    "active": 70084,
    "inactive": 2690,
    "gifts_to_qd": 22589,
    "total_revenue": 351_300_000_000,
    "total_expenditures": 337_000_000_000,
    "foreign_projects": None,
    "foreign_amount": 3_900_000_000,
    "global_affairs": 136,
    "has_employment": 41391,
    "no_employment": 30553,
    "compensation": 198_000_000_000,
    "tax_receipted": 13_500_000_000,
}

# Mapping: scope key → (prior year data dict, prior year number)
PRIOR_YEAR_DATA = {
    "canada": (CANADA_2023, 2023),
    "MB": (MB_2023, 2023),
    "ON": (ON_2023, 2023),
    "QC": (QC_2023, 2023),
    "BC": (BC_2023, 2023),
    "AB": (AB_2023, 2023),
    "atlantic": (ATL_2023, 2023),
    "designation_A": (PUBLIC_FOUNDATIONS_2023, 2023),
    "designation_B": (PRIVATE_FOUNDATIONS_2023, 2023),
    "designation_C": (CHARITABLE_ORGS_2023, 2023),
    # SK, NS, NB have no published 2023 snapshot
}


# ── SQL helpers ──────────────────────────────────────────────────────────────

def money(col):
    """SQL expression to convert '$1,234' VARCHAR to DECIMAL."""
    return f"TRY_CAST(REPLACE(REPLACE({col}, '$', ''), ',', '') AS DECIMAL)"


def scoped_from(table, where):
    """Return FROM+JOIN+WHERE clause scoped through charity_base."""
    bn = BN_COL[table]
    return f"{table} t INNER JOIN charity_base cb ON t.{bn} = cb.bn WHERE {where}"


def get_scope_filter(scope_type, scope_value):
    """Return (WHERE clause, full title, filename suffix, pdf suffix)."""
    if scope_type == "all":
        return "1=1", "Canadian Charity Sector", "canada", "canada"
    elif scope_type == "province":
        if scope_value == "Atlantic":
            provinces = "','".join(ATLANTIC)
            return (
                f"cb.province IN ('{provinces}')",
                "Atlantic Provinces Charity Sector",
                "atlantic",
                "atlantic",
            )
        name = PROVINCE_NAMES.get(scope_value, scope_value)
        return (
            f"cb.province = '{scope_value}'",
            f"{name} Charity Sector",
            scope_value,
            scope_value,
        )
    elif scope_type == "designation":
        desc = DESIGNATIONS[scope_value]
        return (
            f"cb.designation_code = '{scope_value}'",
            f"{desc}s in the Canadian Charity Sector",
            f"designation_{scope_value}",
            f"designation_{scope_value}",
        )
    raise ValueError(f"Unknown scope_type: {scope_type}")


# ── data queries ─────────────────────────────────────────────────────────────

def query_stats(con, where):
    """Query all statistics needed for the article from the 2024 database."""
    s = {}

    # Charity count
    s["charity_count"] = con.execute(
        f"SELECT COUNT(*) FROM charity_base cb WHERE {where}"
    ).fetchone()[0]

    # Active/inactive (C1 line 1800)
    s["active"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"1800\" = 'Y'"
    ).fetchone()[0]
    s["inactive"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"1800\" = 'N'"
    ).fetchone()[0]

    # Gifts to qualified donees (C3 line 2000)
    s["gifts_to_qd"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"2000\" = 'Y'"
    ).fetchone()[0]

    # Financial D sums
    def sum_fd(line):
        val = con.execute(
            f"SELECT SUM({money(f't.\"{line}\"')}) FROM {scoped_from('financial_d', where)}"
        ).fetchone()[0]
        return int(val) if val else 0

    s["total_revenue"] = sum_fd("4700")
    s["total_expenditures"] = sum_fd("5100")
    s["total_assets"] = sum_fd("4200")
    s["fed_govt"] = sum_fd("4540")
    s["prov_govt"] = sum_fd("4550")
    s["muni_govt"] = sum_fd("4560")
    s["total_govt"] = s["fed_govt"] + s["prov_govt"] + s["muni_govt"]
    s["tax_receipted"] = sum_fd("4500")
    s["compensation_fd"] = sum_fd("4880")
    s["revenue_outside_canada"] = sum_fd("4575")

    # Government as % of revenue
    if s["total_revenue"] > 0:
        s["govt_pct"] = round(s["total_govt"] / s["total_revenue"] * 100)
    else:
        s["govt_pct"] = 0

    # Foreign activities (C4 line 2100)
    s["foreign_projects"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"2100\" = 'Y'"
    ).fetchone()[0]

    # Foreign expenditures (Schedule 2 line 200)
    foreign_exp = con.execute(
        f"SELECT SUM({money('t.\"200\"')}) FROM {scoped_from('schedule_2_summary', where)}"
    ).fetchone()[0]
    s["foreign_amount"] = int(foreign_exp) if foreign_exp else 0

    # Global Affairs funded (Schedule 2 line 220)
    s["global_affairs"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('schedule_2_summary', where)} AND t.\"220\" = 'Y'"
    ).fetchone()[0]

    # Foreign intermediaries (line 210), employees (240), volunteers (250)
    s["foreign_intermediaries"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('schedule_2_summary', where)} AND t.\"210\" = 'Y'"
    ).fetchone()[0]
    s["foreign_employees"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('schedule_2_summary', where)} AND t.\"240\" = 'Y'"
    ).fetchone()[0]
    s["foreign_volunteers"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('schedule_2_summary', where)} AND t.\"250\" = 'Y'"
    ).fetchone()[0]

    # Employment (C9 line 3400)
    s["has_employment"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"3400\" = 'Y'"
    ).fetchone()[0]
    s["no_employment"] = con.execute(
        f"SELECT COUNT(*) FROM {scoped_from('financial_abc', where)} AND t.\"3400\" = 'N'"
    ).fetchone()[0]

    # Total compensation (schedule 3 line 390 — VARCHAR with $)
    comp = con.execute(
        f"SELECT SUM({money('t.\"390\"')}) FROM {scoped_from('schedule_3_compensation', where)}"
    ).fetchone()[0]
    s["compensation"] = int(comp) if comp else s["compensation_fd"]

    return s


# ── formatting helpers ───────────────────────────────────────────────────────

def fmt_count(n):
    """Format integer with commas: 83275 → '83,275'"""
    if n is None:
        return "N/A"
    return f"{int(n):,}"


def fmt_dollars_short(n):
    """Format dollar amount in human-readable short form.
    e.g. 393_000_000_000 → '$393 billion', 825_000_000 → '$825 million'
    """
    if n is None:
        return "N/A"
    n = int(n)
    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        val = n / 1_000_000_000
        if val == int(val):
            return f"${int(val)} billion"
        return f"${val:.1f} billion"
    elif abs_n >= 1_000_000:
        val = n / 1_000_000
        if val == int(val):
            return f"${int(val)} million"
        return f"${val:.0f} million"
    elif abs_n >= 1_000:
        return f"${n:,}"
    return f"${n}"


def fmt_dollars_table(n):
    """Format dollar amount for comparison table (shorter).
    e.g. 15_000_000_000 → '$15 billion', 196_000_000 → '$196 million'
    """
    return fmt_dollars_short(n)


# ── PDF to images ────────────────────────────────────────────────────────────

def render_pdf_pages(pdf_path, dpi=200):
    """Render all pages of a PDF to PNG byte buffers."""
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


# ── Word document manipulation ───────────────────────────────────────────────

FONT_NAME = "Times New Roman"
FONT_SIZE_BODY = Pt(13)
FONT_SIZE_BYLINE = Pt(14)


def styled_run(para, text, bold=False, size=None, italic=False):
    """Add a run with Times New Roman at the standard body size."""
    run = para.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = size or FONT_SIZE_BODY
    if bold:
        run.bold = True
    if italic:
        run.italic = True
    return run


def set_paragraph_text(para, text, bold=False, size=None, italic=False):
    """Clear a paragraph and set its text with consistent font."""
    clear_paragraph(para)
    styled_run(para, text, bold=bold, size=Pt(size) if size else None, italic=italic)


def clear_paragraph(para):
    """Remove all content (runs, hyperlinks, etc.) from a paragraph, keeping pPr."""
    p_elem = para._element
    # Remove everything except paragraph properties (pPr)
    for child in list(p_elem):
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag != 'pPr':
            p_elem.remove(child)


def delete_paragraph(para):
    """Delete a paragraph element from the document body."""
    p = para._element
    p.getparent().remove(p)


def rebuild_table(table, headers, rows, scope_type):
    """Clear and rebuild the comparison table with new data.

    headers: list of column header strings
    rows: list of [metric, val1, val2, ...] lists
    """
    # Determine target column count
    target_cols = len(headers)
    existing_cols = len(table.columns)

    # Remove extra columns if needed (from right)
    if existing_cols > target_cols:
        for row in table.rows:
            for _ in range(existing_cols - target_cols):
                cells = row._tr.findall(qn('w:tc'))
                if cells:
                    row._tr.remove(cells[-1])
    # Add columns if needed
    elif existing_cols < target_cols:
        for row in table.rows:
            for _ in range(target_cols - existing_cols):
                new_tc = copy.deepcopy(row.cells[-1]._tc)
                row._tr.append(new_tc)

    # Adjust row count
    existing_rows = len(table.rows)
    target_rows = len(rows) + 1  # +1 for header

    # Remove excess rows (from bottom)
    if existing_rows > target_rows:
        for _ in range(existing_rows - target_rows):
            tr = table.rows[-1]._tr
            table._tbl.remove(tr)
    # Add rows if needed
    elif existing_rows < target_rows:
        for _ in range(target_rows - existing_rows):
            new_tr = copy.deepcopy(table.rows[-1]._tr)
            table._tbl.append(new_tr)

    # Fill header row
    for ci, h in enumerate(headers):
        cell = table.rows[0].cells[ci]
        for p in cell.paragraphs:
            for r in p.runs:
                r.text = ""
            if p.runs:
                p.runs[0].text = h
                p.runs[0].bold = True
                p.runs[0].font.name = FONT_NAME
                p.runs[0].font.size = FONT_SIZE_BODY
            else:
                styled_run(p, h, bold=True)

    # Fill data rows
    for ri, row_data in enumerate(rows):
        row = table.rows[ri + 1]
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            for p in cell.paragraphs:
                for r in p.runs:
                    r.text = ""
                text = str(val) if val is not None else ""
                if p.runs:
                    p.runs[0].text = text
                    p.runs[0].font.name = FONT_NAME
                    p.runs[0].font.size = FONT_SIZE_BODY
                else:
                    styled_run(p, text)


def build_comparison_rows(scope_stats, canada_stats, prior_stats, scope_type, scope_name):
    """Build the data rows for the comparison table.

    Standardized format:
      - Canada: [Scope 2024, Scope 2023]
      - Province/Designation: [Scope 2024, Scope 2023, Canada 2024]
    """

    def row(metric, key, formatter=fmt_count):
        """Build one row of comparison data."""
        vals = [metric]
        vals.append(formatter(scope_stats.get(key)))
        if prior_stats:
            vals.append(formatter(prior_stats.get(key)))
        if scope_type != "all":  # Add Canada column for province/designation
            vals.append(formatter(canada_stats.get(key)))
        return vals

    scope_label = scope_name.replace(" Charity Sector", "")

    rows = [
        row(f"Number of registered charities in {scope_label}", "charity_count"),
        row(f"{scope_label} charities identified themselves as active", "active"),
        row(f"{scope_label} charities identified themselves as inactive", "inactive"),
        row(f"{scope_label} charities that made gifts to other charities or qualified donees", "gifts_to_qd"),
        row(f"Total revenue for {scope_label} charities", "total_revenue", fmt_dollars_table),
        row(f"Total expenditures of {scope_label} charities", "total_expenditures", fmt_dollars_table),
        row(f"{scope_label} charities who funded projects outside of Canada", "foreign_projects"),
        row(f"Amount spent by {scope_label} charities outside of Canada", "foreign_amount", fmt_dollars_table),
        row(f"{scope_label} charities received funds from Global Affairs Canada", "global_affairs"),
        row(f"{scope_label} charities that had employment expenses", "has_employment"),
        row(f"{scope_label} charities that did not have any employment expenses", "no_employment"),
        row(f"Amount spent by {scope_label} charities on salaries and other compensation", "compensation", fmt_dollars_table),
        row(f"Value of official donation receipts issued by {scope_label} charities", "tax_receipted", fmt_dollars_table),
    ]
    return rows


def insert_t3010_images(doc, page_images, insert_after_index):
    """Insert T3010 page images into the document body after a given element index.

    Replaces empty paragraphs between highlights and 'Further information'
    with page-break-separated images.
    """
    body = doc.element.body
    elements = list(body)

    # Find the empty paragraphs between highlights and "Further information"
    # We'll insert images replacing these empty paragraphs
    # First, find the range of empty paragraphs after the last bullet
    # and before "Further information"

    # Find "Further information" paragraph
    further_info_idx = None
    for i, elem in enumerate(elements):
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'p':
            # Concatenate all <w:t> text nodes (text may span multiple runs)
            texts = elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            full_text = ''.join(t.text or '' for t in texts).strip()
            if 'Further information' in full_text:
                further_info_idx = i
                break

    if further_info_idx is None:
        print("    WARNING: Could not find 'Further information' paragraph")
        return

    # Find empty paragraphs before "Further information" to replace
    empty_start = None
    for i in range(further_info_idx - 1, -1, -1):
        elem = elements[i]
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'p':
            text = ''.join(
                t.text or '' for t in
                elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            ).strip()
            if text:
                empty_start = i + 1
                break

    if empty_start is None or empty_start >= further_info_idx:
        empty_start = further_info_idx

    # Remove existing empty paragraphs in the gap
    to_remove = []
    for i in range(empty_start, further_info_idx):
        to_remove.append(elements[i])
    for elem in to_remove:
        body.remove(elem)

    # Now insert image paragraphs before "Further information"
    # Re-find the further_info element (index shifted after removals)
    further_info_elem = None
    for elem in list(body):
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'p':
            texts = elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            full_text = ''.join(t.text or '' for t in texts).strip()
            if 'Further information' in full_text:
                further_info_elem = elem
                break

    if further_info_elem is None:
        return

    # Insert images
    from docx.enum.text import WD_BREAK
    for i, png_bytes in enumerate(page_images):
        # Create a new paragraph with a page break (except first)
        new_para = doc.add_paragraph()
        if i > 0:
            # Add page break before this image
            run = new_para.add_run()
            run.add_break(WD_BREAK.PAGE)

        # Add the image
        run = new_para.add_run()
        run.add_picture(io.BytesIO(png_bytes), width=Inches(6.5))

        # Move this paragraph before "Further information"
        further_info_elem.addprevious(new_para._element)

    # Add a blank paragraph before Further information
    blank = doc.add_paragraph()
    further_info_elem.addprevious(blank._element)


# ── article generation ───────────────────────────────────────────────────────

def generate_article(scope_type, scope_value, con, canada_stats):
    """Generate one snapshot article Word document."""
    where, title, suffix, pdf_suffix = get_scope_filter(scope_type, scope_value)

    # Query 2024 stats for this scope
    stats = query_stats(con, where)

    # Prior year comparison data — look up from PRIOR_YEAR_DATA mapping
    prior_stats = None
    prior_year = PRIOR_YEAR  # default
    if scope_type == "all":
        lookup_key = "canada"
    elif scope_type == "designation":
        lookup_key = f"designation_{scope_value}"
    else:
        lookup_key = suffix
    if lookup_key in PRIOR_YEAR_DATA:
        prior_stats, prior_year = PRIOR_YEAR_DATA[lookup_key]

    # Load fresh template
    doc = Document(TEMPLATE_PATH)
    paras = doc.paragraphs

    # Determine scope label for text
    scope_name = title
    if scope_type == "province":
        scope_label = PROVINCE_NAMES.get(scope_value, scope_value)
    elif scope_type == "designation":
        scope_label = DESIGNATIONS[scope_value] + "s"
    else:
        scope_label = "Canadian"

    # ── P2-P3: Title ──
    set_paragraph_text(paras[2], "Blumbergs\u2019 Snapshot of the")
    set_paragraph_text(paras[3], f"{title} {DATA_YEAR}")

    # ── P5: Byline + intro paragraph ──
    p5 = paras[5]
    clear_paragraph(p5)

    # Byline
    styled_run(p5, f"By Mark Blumberg and Henri Pasha ({BYLINE_DATE})", bold=True, size=FONT_SIZE_BYLINE)

    # Intro text depends on scope type
    if scope_type == "province":
        prov_name = PROVINCE_NAMES.get(scope_value, scope_value)
        intro = (
            f"\n\nBlumbergs Professional Corporation recently reviewed the T3010 "
            f"Registered Charity Information Return database for {DATA_YEAR} as part of "
            f"the Sean Blumberg Transparency Project. The database covers about "
            f"{fmt_count(stats['charity_count'])} {prov_name} Charities of the approximately "
            f"{APPROX_CHARITIES} registered charities in Canada that had filed their T3010 "
            f"and were processed into CRA\u2019s Charity Listing database by {PROCESSED_BY}."
        )
    elif scope_type == "designation":
        desig_name = DESIGNATIONS[scope_value] + "s"
        intro = (
            f"\n\nBlumbergs Professional Corporation recently reviewed the T3010 "
            f"Registered Charity Information Return database for {DATA_YEAR} as part of "
            f"the Sean Blumberg Transparency Project. The database covers about "
            f"{fmt_count(stats['charity_count'])} {desig_name} of the approximately "
            f"{APPROX_CHARITIES} registered charities in Canada that had filed their T3010 "
            f"and were processed into CRA\u2019s Charity Listing database by {PROCESSED_BY}."
        )
    else:  # Canada
        intro = (
            f"\n\nWe recently reviewed the T3010 Registered Charity Information Return "
            f"database for {DATA_YEAR} as part of the Sean Blumberg Transparency Project. "
            f"The database covers about {fmt_count(stats['charity_count'])} of the approximately "
            f"{APPROX_CHARITIES} registered charities in Canada that had filed their T3010 "
            f"and were processed into CRA\u2019s Charity Listing database by {PROCESSED_BY}."
        )
    styled_run(p5, intro)

    # ── P6: Second intro paragraph ──
    if scope_type == "province":
        prov_name = PROVINCE_NAMES.get(scope_value, scope_value)
        p6_text = (
            f"This article provides a snapshot of the registered charity sector in "
            f"{prov_name} taken from a subset of the {DATA_YEAR} T3010 filings. We have "
            f"completed Blumbergs\u2019 Snapshots of the Canadian Charity Sector for "
            f"2010 \u2013 {PRIOR_YEAR} as well. Keep in mind that these statistics only relate "
            f"to registered charities under the Income Tax Act (Canada) and not to the "
            f"80,000 -100,000 non-profits across Canada which are not registered charities "
            f"and for which CRA is not permitted to release information. The Canadian charity "
            f"sector is a vital part of Canadian society and economy with revenue of over "
            f"{fmt_dollars_short(canada_stats['total_revenue'])} and expenditures of about "
            f"{fmt_dollars_short(canada_stats['total_expenditures'])}."
        )
    elif scope_type == "designation":
        desig_name = DESIGNATIONS[scope_value] + "s"
        p6_text = (
            f"This article provides a snapshot of {desig_name} in Canada based on the "
            f"{DATA_YEAR} T3010 filings. We have completed Blumbergs\u2019 Snapshots of the "
            f"Canadian Charity Sector for 2010 \u2013 {PRIOR_YEAR} as well. Keep in mind that "
            f"these statistics only relate to registered charities under the Income Tax Act "
            f"(Canada) and not to the 80,000 -100,000 non-profits across Canada which are "
            f"not registered charities and for which CRA is not permitted to release "
            f"information. The Canadian charity sector is a vital part of Canadian society "
            f"and economy with revenue of over {fmt_dollars_short(canada_stats['total_revenue'])} "
            f"and expenditures of about {fmt_dollars_short(canada_stats['total_expenditures'])}."
        )
    else:  # Canada
        p6_text = (
            f"This article provides a snapshot of the registered charity sector based on "
            f"the {DATA_YEAR} T3010 filings. We have completed Blumbergs\u2019 Snapshots of "
            f"the Canadian Charity Sector for 2010 \u2013 {PRIOR_YEAR} as well. Keep in mind "
            f"that these statistics only relate to registered charities under the Income Tax "
            f"Act (Canada) and not to the 80,000 -100,000 non-profits which are not "
            f"registered charities and for which CRA is not permitted to release information."
        )
    set_paragraph_text(paras[6], p6_text)

    # ── P7: Transparency paragraph — static, keep as-is ──

    # ── Comparison Table ──
    table = doc.tables[0]

    if scope_type == "all":
        if prior_stats:
            headers = ["", f"Canada {DATA_YEAR}", f"Canada {prior_year}"]
        else:
            headers = ["", f"Canada {DATA_YEAR}"]
    elif scope_type == "province":
        prov_name = PROVINCE_NAMES.get(scope_value, scope_value)
        if prior_stats:
            headers = ["", f"{prov_name} {DATA_YEAR}", f"{prov_name} {prior_year}", f"Canada {DATA_YEAR}"]
        else:
            headers = ["", f"{prov_name} {DATA_YEAR}", f"Canada {DATA_YEAR}"]
    elif scope_type == "designation":
        desig_name = DESIGNATIONS[scope_value] + "s"
        if prior_stats:
            headers = ["", f"{desig_name} {DATA_YEAR}", f"{desig_name} {prior_year}", f"Canada {DATA_YEAR}"]
        else:
            headers = ["", f"{desig_name} {DATA_YEAR}", f"Canada {DATA_YEAR}"]

    rows_data = build_comparison_rows(
        stats, canada_stats, prior_stats, scope_type, scope_name
    )
    rebuild_table(table, headers, rows_data, scope_type)

    # ── P11: "The Canadian charity sector is vital..." ──
    clear_paragraph(paras[11])
    styled_run(paras[11],
        f"The Canadian charity sector is a vital part of Canadian society and economy "
        f"with revenue of over {fmt_dollars_short(canada_stats['total_revenue'])} and "
        f"expenditures of about {fmt_dollars_short(canada_stats['total_expenditures'])}. "
        f"Please review the caveats at the end about the reliability and usage of T3010 information."
    )

    # ── P12: Sean Blumberg dedication — keep as-is (static) ──

    # ── P13: T3010 filing count ──
    clear_paragraph(paras[13])
    styled_run(paras[13],
        f"\nIn {DATA_YEAR}, {fmt_count(canada_stats['charity_count'])} of approximately "
        f"{APPROX_CHARITIES} Canadian registered charities completed their T3010 returns. "
        f"All charities filed using T3010 Version 24."
    )

    # ── P14-16: V24/V23 form version notes — simplify for 2024 ──
    clear_paragraph(paras[14])
    styled_run(paras[14],
        f"\nCharities filed their T3010 using T3010 Version 24. "
        f"Fillable PDF (t3010-fill24e.pdf). This is the version in which we have displayed the data."
    )

    # Clear P15 and P16 (V23 note and "when you look at" paragraph — no longer applicable)
    for pi in [15, 16]:
        clear_paragraph(paras[pi])

    # ── P19: Highlights header ──
    set_paragraph_text(paras[19], f"Some of the highlights of the Blumbergs\u2019 Snapshot of the {title} {DATA_YEAR} include:")

    # ── P20-31: Highlight bullets ──
    if scope_type == "province":
        prov_name = PROVINCE_NAMES.get(scope_value, scope_value)
        label = prov_name
    elif scope_type == "designation":
        label = DESIGNATIONS[scope_value] + "s"
    else:
        label = "Canadian"

    bullets = [
        f"\u2022\t{fmt_count(stats['charity_count'])} Registered Charities in the Database "
        f"{label} registered charities filed their T3010 out of approximately {APPROX_CHARITIES} charities in Canada",

        f"\u2022\t{fmt_dollars_short(stats['total_revenue'])} in total revenue for {label} "
        f"charities and total expenditures of {fmt_dollars_short(stats['total_expenditures'])}.",

        f"\u2022\tGovernment revenue totaled {fmt_dollars_short(stats['total_govt'])} including from "
        f"the federal government ({fmt_dollars_short(stats['fed_govt'])}), provincial governments "
        f"({fmt_dollars_short(stats['prov_govt'])}) and municipal/regional governments "
        f"({fmt_dollars_short(stats['muni_govt'])}). In total government is approximately "
        f"{stats['govt_pct']}% of revenue of the whole charity sector"
        + (f" in {PROVINCE_NAMES.get(scope_value, scope_value)}." if scope_type == "province" else "."),

        f"\u2022\t{fmt_count(stats['active'])} identified themselves as active and "
        f"{fmt_count(stats['inactive'])} as inactive",

        f"\u2022\t{fmt_count(stats['gifts_to_qd'])} made gifts to other charities or qualified "
        f"donees during their {DATA_YEAR} fiscal year",

        f"\u2022\t{label} charities spent over {fmt_dollars_short(stats['foreign_amount'])} "
        f"outside of Canada",

        f"\u2022\t{fmt_count(stats['global_affairs'])} {label} charities received funds from "
        f"Global Affairs Canada",

        f"\u2022\t{fmt_count(stats['foreign_intermediaries'])} identified having contractual "
        f"relationships with foreign intermediaries, {fmt_count(stats['foreign_employees'])} "
        f"charities identified that employees conducted activities outside of Canada and "
        f"{fmt_count(stats['foreign_volunteers'])} had volunteers conducting foreign activities.",

        f"\u2022\t{fmt_dollars_short(stats['revenue_outside_canada'])} was received by {label} "
        f"charities from outside of Canada",

        f"\u2022\t{fmt_count(stats['has_employment'])} identified having employment expenses "
        f"while {fmt_count(stats['no_employment'])} did not have any employment expenses",

        f"\u2022\t{fmt_dollars_short(stats['compensation'])} was spent by {label} charities "
        f"on salaries and other compensation expenditures",

        f"\u2022\t{fmt_dollars_short(stats['tax_receipted'])} in official donation receipts "
        f"were issued by {label} registered charities",
    ]

    # Update bullet paragraphs P20-P31
    for i, bullet_text in enumerate(bullets):
        pi = 20 + i
        if pi < len(paras):
            clear_paragraph(paras[pi])
            styled_run(paras[pi], bullet_text)

    # ── Update links section year references ──
    # Update "2023" → "2024" in the link titles that reference snapshot years
    for pi in range(41, min(193, len(paras))):
        p = paras[pi]
        for run in p.runs:
            if run.text and "Snapshot" in run.text and "2023" in run.text:
                run.text = run.text.replace("2023", "2024")

    # ── Embed T3010 PDF pages as images ──
    pdf_path = os.path.join(PDF_DIR, f"Blumbergs-Snapshot-T3010-2024-{pdf_suffix}.pdf")
    if os.path.exists(pdf_path):
        print(f"    Rendering T3010 PDF pages from {os.path.basename(pdf_path)}...")
        page_images = render_pdf_pages(pdf_path, dpi=200)
        print(f"    Embedding {len(page_images)} T3010 pages as images...")
        insert_t3010_images(doc, page_images, 0)
    else:
        print(f"    WARNING: T3010 PDF not found: {pdf_path}")

    # ── Save ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"Blumbergs-Snapshot-{title.replace(' ', '-')}-{DATA_YEAR}.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc.save(filepath)
    print(f"    Saved: {filepath}")
    return filepath


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Blumbergs Snapshot articles as Word documents")
    parser.add_argument("--all", action="store_true", help="Generate all 13 articles")
    parser.add_argument("--province", type=str, help="Generate for one province (e.g. ON, BC, MB)")
    parser.add_argument("--provincial", action="store_true", help="Generate all 9 provincial articles")
    parser.add_argument("--designation", type=str, help="Generate for one designation (A, B, or C)")
    parser.add_argument("--designations", action="store_true", help="Generate all 3 designation articles")
    args = parser.parse_args()

    if not os.path.exists(TEMPLATE_PATH):
        print(f"ERROR: Template not found: {TEMPLATE_PATH}")
        sys.exit(1)
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        sys.exit(1)

    con = duckdb.connect(DB_PATH, read_only=True)

    # Always compute Canada-wide stats (needed for comparison columns)
    print("Computing Canada-wide 2024 statistics...")
    canada_where, _, _, _ = get_scope_filter("all", None)
    canada_stats = query_stats(con, canada_where)
    print(f"  {fmt_count(canada_stats['charity_count'])} charities, "
          f"revenue {fmt_dollars_short(canada_stats['total_revenue'])}, "
          f"expenditures {fmt_dollars_short(canada_stats['total_expenditures'])}")

    scopes_to_generate = []

    if args.all:
        scopes_to_generate.append(("all", None))
        for prov in PROVINCES:
            scopes_to_generate.append(("province", prov))
        scopes_to_generate.append(("province", "Atlantic"))
        for desig in DESIGNATIONS:
            scopes_to_generate.append(("designation", desig))
    elif args.provincial:
        for prov in PROVINCES:
            scopes_to_generate.append(("province", prov))
        scopes_to_generate.append(("province", "Atlantic"))
    elif args.designations:
        for desig in DESIGNATIONS:
            scopes_to_generate.append(("designation", desig))
    elif args.province:
        scopes_to_generate.append(("province", args.province))
    elif args.designation:
        scopes_to_generate.append(("designation", args.designation))
    else:
        # Default: Canada only
        scopes_to_generate.append(("all", None))

    print(f"\nGenerating {len(scopes_to_generate)} article(s)...\n")

    for scope_type, scope_value in scopes_to_generate:
        _, title, _, _ = get_scope_filter(scope_type, scope_value)
        print(f"  [{title}]")
        generate_article(scope_type, scope_value, con, canada_stats)
        print()

    con.close()
    print("Done.")


if __name__ == "__main__":
    main()
