#!/usr/bin/env python3
"""Extract T3010 line totals from historical Blumbergs Snapshot PDFs (2013-2021).

Parses the extracted text files in docs/reference/blumbergs/extracted/ to pull
out Schedule 6 (detailed financials), Schedule 3 (compensation), and narrative
highlights.  Outputs structured JSON and optionally an Excel comparison workbook.

Usage:
    python3 scripts/reports/extract_historical_snapshots.py              # All 9 years
    python3 scripts/reports/extract_historical_snapshots.py --year 2017  # Single year
    python3 scripts/reports/extract_historical_snapshots.py --verbose    # Show field mappings
    python3 scripts/reports/extract_historical_snapshots.py --excel      # Also generate xlsx
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXTRACTED_DIR = os.path.join(PROJECT_ROOT, "docs", "reference", "blumbergs", "extracted")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "exports")

# ── Source file mapping: year → filename ──────────────────────────────────
SOURCE_FILES = {
    2013: "snapshots_Blumbergs_Canadian_Charity_Sector_Snapshot_2013.txt",
    2014: "snapshots_Blumbergs_Canadian_Charity_Sector_Snapshot_2014.txt",
    2015: "snapshots_Blumbergs_Canadian_Charity_Sector_Snapshot_2015.txt",
    2016: "snapshots_Blumbergs_Canadian_Charity_Sector_Snapshot_2016.txt",
    2017: "snapshots_Blumbergs_Canadian_Charity_Sector_Snapshot_2017.txt",
    2018: "snapshots_Blumbergs-Canadian-Charity-Sector-Snapshot-2018.txt",
    2019: "snapshots_Blumbergs-Canadian-Charity-Sector-Snapshot-2019.txt",
    2020: "snapshots_Blumbergs-Canadian-Charity-Sector-Snapshot-2020.txt",
    2021: "snapshots_Blumbergs-Canadian-Charity-Sector-Snapshot-2021-Final.txt",
}

# ── Form versions ────────────────────────────────────────────────────────
FORM_VERSIONS = {
    2013: "T3010 E (13)",
    2014: "T3010 E (14)",
    2015: "T3010 E (15)",
    2016: "T3010 E (16)",
    2017: "T3010 E (17)",
    2018: "T3010 E (18)",
    2019: "T3010 E (19)",
    2020: "T3010 E (21)",  # 2020 data used the V21 form
    2021: "T3010 E (21)",
}

# ── Schedule 6 field templates ───────────────────────────────────────────
# Ordered list of T3010 line numbers that produce numeric values in Schedule 6.
# Two variants: 2013-2018 includes 5030/5040, 2019-2021 drops 5030.

SCHED6_ASSETS = ["4100", "4110", "4120", "4130", "4140", "4150", "4155", "4160",
                 "4165", "4166", "4170", "4180", "4200"]

SCHED6_LIABILITIES = ["4300", "4310", "4320", "4330", "4350", "4250"]

SCHED6_REVENUE = ["4500", "5610", "4505", "4510", "4530", "4540", "4550", "4560",
                  "4571", "4575", "4580", "4590", "4600", "4610", "4620", "4630",
                  "4640", "4650", "4700"]

# 2013-2018: has 5030 (political) and 5040 (other)
SCHED6_EXPENDITURES_V13_18 = [
    "4800", "4810", "4820", "4830", "4840", "4850", "4860", "4870", "4880",
    "4890", "4891", "4900", "4910", "4920",
    "4950",
    "5000", "5010", "5020", "5030", "5040",
    "5050", "5100",
]

# 2019-2021: no 5030 political, 5040 becomes (d)
SCHED6_EXPENDITURES_V19_21 = [
    "4800", "4810", "4820", "4830", "4840", "4850", "4860", "4870", "4880",
    "4890", "4891", "4900", "4910", "4920",
    "4950",
    "5000", "5010", "5020", "5040",
    "5050", "5100",
]

SCHED6_OTHER = ["5500", "5510", "5750", "5900", "5910"]

# Also extract counts embedded in Schedule 6 (appear right after 4700 totals)
# These are the accrual/cash counts that appear as two numbers after 4700
SCHED6_COUNTS_AFTER_4700 = ["accrual_count", "cash_count"]

# ── Schedule 3 field template ────────────────────────────────────────────
SCHED3_FIELDS = [
    "300",  # FT positions
    "305", "310", "315", "320", "325", "330", "335", "340", "345",  # Salary bands
    "370",  # PT employees
    "380",  # PT compensation (in Section D only)
    "390",  # Total compensation
]

# ── Narrative extraction patterns ────────────────────────────────────────

def extract_narrative(lines):
    """Extract headline metrics from narrative bullet points."""
    text = "\n".join(lines[:150])  # First ~150 lines contain highlights

    narrative = {}

    # Charities filed
    m = re.search(r'([\d,]+)\s+registered charities filed', text)
    if m:
        narrative["charities_filed"] = int(m.group(1).replace(",", ""))

    # Total revenue and expenditures
    m = re.search(r'\$(\d+)\s+billion in total revenue.*?expenditures of.*?\$(\d+)\s+billion', text, re.I)
    if m:
        narrative["total_revenue_approx_B"] = int(m.group(1))
        narrative["total_expenditures_approx_B"] = int(m.group(2))

    # Government revenue total
    m = re.search(r'[Gg]overnment revenue totaled?\s+\$([\d.]+)\s+[Bb]illion', text)
    if m:
        narrative["govt_revenue_approx_B"] = float(m.group(1))

    # Federal government
    m = re.search(r'federal government\s*\(\$([\d.]+)\s*[Bb]illion\)', text)
    if m:
        narrative["federal_govt_approx_B"] = float(m.group(1))

    # Provincial governments
    m = re.search(r'provincial(?:/territorial)?\s+governments?\s*\(\$([\d.]+)\s*[Bb]illion\)', text)
    if m:
        narrative["provincial_govt_approx_B"] = float(m.group(1))

    # Municipal governments
    m = re.search(r'municipal(?:/regional)?\s+governments?\s*\(\$([\d.]+)\s*[Bb]illion\)', text)
    if m:
        narrative["municipal_govt_approx_B"] = float(m.group(1))

    # Compensation
    m = re.search(r'\$([\d.]+)\s+[Bb]illion was spent.*?(?:salaries|compensation)', text)
    if m:
        narrative["compensation_approx_B"] = float(m.group(1))

    # Tax receipts
    m = re.search(r'\$([\d.]+)\s+[Bb]illion in (?:official )?(?:donation|tax)[- ]receipts?\b', text, re.I)
    if not m:
        m = re.search(r'\$([\d.]+)\s+[Bb]illion.*?(?:tax receipts|donation receipts)', text, re.I)
    if m:
        narrative["tax_receipts_approx_B"] = float(m.group(1))

    return narrative


# ── Number parsing ───────────────────────────────────────────────────────

def parse_number(s):
    """Parse a number string from the text.  Returns int or None."""
    s = s.strip()
    if not s or s.upper() == "N/A":
        return None

    # Handle negative numbers in brackets like (123,456)
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    elif s.startswith("-"):
        negative = True
        s = s[1:]

    # Strip currency symbols and formatting
    s = s.replace("$", "").replace(",", "").strip()

    # Remove trailing .00 (some numbers have this)
    if s.endswith(".00"):
        s = s[:-3]
    # Remove lone trailing period
    if s.endswith("."):
        s = s[:-1]

    if not s:
        return None

    try:
        val = int(s)
        return -val if negative else val
    except ValueError:
        try:
            val = int(float(s))
            return -val if negative else val
        except ValueError:
            return None


def is_number_line(line):
    """Check if a line is a standalone number (possibly with $, commas, negatives)."""
    s = line.strip()
    if not s:
        return False
    if s.upper() == "N/A":
        return True
    # Match patterns like: 39,206,437,443  or  -89,875,347,148  or  $1,234.00
    # Also match: "48,430" (counts), "50,518" etc.
    return bool(re.match(r'^-?\$?[\d,]+\.?\d*$', s)) or bool(re.match(r'^\([\d,$]+\.?\d*\)$', s))


# ── Schedule 6 extraction ───────────────────────────────────────────────

def find_schedule6_section(lines):
    """Find the start of Schedule 6 (Detailed Financial Information) section."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Detailed financial information" in stripped or "Detailed Financial Information" in stripped:
            # Verify it's the Schedule 6 header area
            nearby = " ".join(l.strip() for l in lines[max(0,i-3):i+3])
            if "Schedule 6" in nearby or "schedule 6" in nearby.lower():
                return i
            # Sometimes "Schedule 6" is on the line itself or adjacent
            if "Schedule" in stripped:
                return i
            # If "Schedule 6" appears a few lines before
            return i
    return None


def extract_schedule6_numbers(lines, year, verbose=False):
    """Extract Schedule 6 financial data by finding number blocks."""
    sched6_start = find_schedule6_section(lines)
    if sched6_start is None:
        print(f"  WARNING: Could not find Schedule 6 section for {year}")
        return {}

    # Determine field template
    if year <= 2018:
        expenditure_fields = SCHED6_EXPENDITURES_V13_18
    else:
        expenditure_fields = SCHED6_EXPENDITURES_V19_21

    all_fields = SCHED6_ASSETS + SCHED6_LIABILITIES + SCHED6_REVENUE + expenditure_fields + SCHED6_OTHER

    # Strategy: Scan Schedule 6 section for contiguous blocks of numbers.
    # The numbers appear in order matching the field template.
    sched6_lines = lines[sched6_start:]

    # Collect all number values from Schedule 6 to end of file
    numbers = []
    for line in sched6_lines:
        stripped = line.strip()
        if is_number_line(stripped):
            numbers.append(parse_number(stripped))

    if verbose:
        print(f"  Schedule 6 starts at line {sched6_start + 1}")
        print(f"  Found {len(numbers)} numbers, expecting {len(all_fields)} fields")

    # Map positionally
    result = {}
    for i, field in enumerate(all_fields):
        if i < len(numbers):
            result[field] = numbers[i]
        else:
            result[field] = None
            if verbose:
                print(f"  WARNING: Missing value for field {field}")

    if len(numbers) > len(all_fields) and verbose:
        extra = len(numbers) - len(all_fields)
        print(f"  INFO: {extra} extra numbers after Schedule 6 fields (likely counts or other data)")

    return result


# ── Schedule 3 extraction ───────────────────────────────────────────────

def find_schedule3_section(lines):
    """Find the start of Schedule 3 (Compensation) section."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Compensation" in stripped and "Schedule 3" in stripped:
            return i
        if stripped == "Compensation" and i + 1 < len(lines):
            next_line = lines[i+1].strip()
            if "Schedule 3" in next_line or "Schedule" in next_line:
                return i
    # Fallback: look for standalone "Schedule 3" near "Compensation"
    for i, line in enumerate(lines):
        if line.strip() == "Schedule 3" and i > 0:
            nearby = " ".join(l.strip() for l in lines[max(0,i-3):i+3])
            if "Compensation" in nearby or "compensation" in nearby:
                return i
    return None


def find_schedule5_section(lines):
    """Find Schedule 5 (Non-cash gifts) to bound Schedule 3 search."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if ("Non cash gifts" in stripped or "Non-cash gifts" in stripped) and "Schedule 5" in stripped:
            return i
        if ("Non cash gifts" in stripped or "Non-cash gifts" in stripped):
            nearby = " ".join(l.strip() for l in lines[max(0,i-2):i+3])
            if "Schedule 5" in nearby:
                return i
    return None


def extract_schedule3_numbers(lines, year, verbose=False):
    """Extract Schedule 3 compensation data."""
    sched3_start = find_schedule3_section(lines)
    if sched3_start is None:
        print(f"  WARNING: Could not find Schedule 3 section for {year}")
        return {}

    # Find the end boundary (Schedule 4 or Schedule 5)
    sched5_start = find_schedule5_section(lines)
    if sched5_start and sched5_start > sched3_start:
        sched3_lines = lines[sched3_start:sched5_start]
    else:
        # Fallback: take ~120 lines after Schedule 3 start
        sched3_lines = lines[sched3_start:sched3_start + 120]

    # Collect numbers
    numbers = []
    for line in sched3_lines:
        stripped = line.strip()
        if is_number_line(stripped):
            numbers.append(parse_number(stripped))

    if verbose:
        print(f"  Schedule 3 starts at line {sched3_start + 1}")
        print(f"  Found {len(numbers)} numbers, expecting {len(SCHED3_FIELDS)} fields")

    # Map positionally
    result = {}
    for i, field in enumerate(SCHED3_FIELDS):
        if i < len(numbers):
            result[field] = numbers[i]
        else:
            result[field] = None

    return result


# ── Schedule 5 extraction ───────────────────────────────────────────────

def extract_schedule5_total(lines, year, verbose=False):
    """Extract the total non-cash gifts amount (line 580) from Schedule 5."""
    sched5_start = find_schedule5_section(lines)
    if sched5_start is None:
        return None

    sched6_start = find_schedule6_section(lines)
    if sched6_start and sched6_start > sched5_start:
        sched5_lines = lines[sched5_start:sched6_start]
    else:
        sched5_lines = lines[sched5_start:sched5_start + 100]

    # The last number in Schedule 5 section is typically line 580 (total non-cash gifts)
    numbers = []
    for line in sched5_lines:
        stripped = line.strip()
        if is_number_line(stripped):
            numbers.append(parse_number(stripped))

    if numbers:
        return numbers[-1]  # Last number is the total
    return None


# ── Validation ───────────────────────────────────────────────────────────

def validate_year(year, schedule6, schedule3, narrative, verbose=False):
    """Cross-check extracted totals against narrative highlights."""
    validations = {}

    # 4700 vs narrative revenue
    if "4700" in schedule6 and schedule6["4700"] and "total_revenue_approx_B" in narrative:
        actual_B = schedule6["4700"] / 1e9
        expected_B = narrative["total_revenue_approx_B"]
        pct = abs(actual_B - expected_B) / expected_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["4700_vs_narrative"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs ~{expected_B}B"

    # 5100 vs narrative expenditures
    if "5100" in schedule6 and schedule6["5100"] and "total_expenditures_approx_B" in narrative:
        actual_B = schedule6["5100"] / 1e9
        expected_B = narrative["total_expenditures_approx_B"]
        pct = abs(actual_B - expected_B) / expected_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["5100_vs_narrative"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs ~{expected_B}B"

    # Government total (4540+4550+4560) vs narrative
    if all(schedule6.get(f) is not None for f in ["4540", "4550", "4560"]) and "govt_revenue_approx_B" in narrative:
        actual = schedule6["4540"] + schedule6["4550"] + schedule6["4560"]
        actual_B = actual / 1e9
        expected_B = narrative["govt_revenue_approx_B"]
        pct = abs(actual_B - expected_B) / expected_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["govt_vs_narrative"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs ~{expected_B}B"

    # 4500 vs narrative tax receipts
    if "4500" in schedule6 and schedule6["4500"] and "tax_receipts_approx_B" in narrative:
        actual_B = schedule6["4500"] / 1e9
        expected_B = narrative["tax_receipts_approx_B"]
        pct = abs(actual_B - expected_B) / expected_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["4500_vs_narrative"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs ~{expected_B}B"

    # 390 / 4880 vs narrative compensation
    comp_value = schedule3.get("390") or schedule6.get("4880")
    if comp_value and "compensation_approx_B" in narrative:
        actual_B = comp_value / 1e9
        expected_B = narrative["compensation_approx_B"]
        pct = abs(actual_B - expected_B) / expected_B * 100
        status = "match" if pct < 5 else ("close" if pct < 10 else "MISMATCH")
        validations["compensation_vs_narrative"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs ~{expected_B}B"

    return validations


# ── Sector trends cross-check ────────────────────────────────────────────

SECTOR_TRENDS = {
    # From docs/context/sector-trends.md
    # year: (charities, revenue_B, expenditures_B, govt_B, compensation_B, tax_receipts_B)
    2013: (83466, 237, 225, 160.0, 129, 14.6),
    2014: (84521, 246, 228, 165.9, 134, 15.7),
    2015: (84442, 251, 240, 168.5, 135.8, 16.4),
    2016: (84457, 261, 252, 177.0, 142, 16.6),
    2017: (84181, 279, 261, 184.0, 147, 18.0),
    2018: (84323, 284, 271, 189.7, 155, 18.0),
    2019: (83892, 321, 283, 199.2, 162, 19.6),
    2020: (83991, 304, 281, 204.8, 166, 18.7),
    2021: (83771, 334, 308, 228.4, 177, 20.7),
}


def cross_check_sector_trends(year, schedule6, narrative, validations):
    """Additional cross-check against sector-trends.md benchmarks."""
    if year not in SECTOR_TRENDS:
        return

    _, rev_B, exp_B, govt_B, comp_B, tax_B = SECTOR_TRENDS[year]

    if "4700" in schedule6 and schedule6["4700"]:
        actual_B = schedule6["4700"] / 1e9
        pct = abs(actual_B - rev_B) / rev_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["4700_vs_sector_trends"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs {rev_B}B"

    if "5100" in schedule6 and schedule6["5100"]:
        actual_B = schedule6["5100"] / 1e9
        pct = abs(actual_B - exp_B) / exp_B * 100
        status = "match" if pct < 2 else ("close" if pct < 5 else "MISMATCH")
        validations["5100_vs_sector_trends"] = f"{status} ({pct:.1f}%) — {actual_B:.1f}B vs {exp_B}B"


# ── Main processing ─────────────────────────────────────────────────────

def process_year(year, verbose=False):
    """Process a single year's extracted text file."""
    filename = SOURCE_FILES.get(year)
    if not filename:
        print(f"  ERROR: No source file defined for {year}")
        return None

    filepath = os.path.join(EXTRACTED_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ERROR: File not found: {filepath}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Strip the line content (remove trailing newlines but keep structure)
    lines = [line.rstrip("\n") for line in lines]

    print(f"\n{'='*60}")
    print(f"  Processing {year} — {filename}")
    print(f"  {len(lines)} lines in source file")

    # Extract narrative
    narrative = extract_narrative(lines)
    if verbose:
        print(f"  Narrative: {json.dumps(narrative, indent=2)}")

    # Extract Schedule 3
    schedule3 = extract_schedule3_numbers(lines, year, verbose)
    if verbose and schedule3:
        print(f"  Schedule 3: {len(schedule3)} fields extracted")
        for k, v in schedule3.items():
            print(f"    {k}: {v:,}" if v is not None else f"    {k}: None")

    # Extract Schedule 5 total
    sched5_total = extract_schedule5_total(lines, year, verbose)

    # Extract Schedule 6
    schedule6 = extract_schedule6_numbers(lines, year, verbose)
    if verbose and schedule6:
        print(f"  Schedule 6: {len(schedule6)} fields extracted")
        for k, v in schedule6.items():
            print(f"    {k}: {v:,}" if v is not None else f"    {k}: None")

    # Validate
    validations = validate_year(year, schedule6, schedule3, narrative, verbose)
    cross_check_sector_trends(year, schedule6, narrative, validations)

    # Print validation summary
    all_ok = True
    for check, result in validations.items():
        if "MISMATCH" in result:
            print(f"  FAIL: {check} — {result}")
            all_ok = False
        elif "close" in result:
            print(f"  WARN: {check} — {result}")
        else:
            print(f"  OK:   {check} — {result}")

    if all_ok and validations:
        print(f"  All {len(validations)} validation checks passed.")

    # Build result
    result = {
        "source_file": filename,
        "form_version": FORM_VERSIONS.get(year, "unknown"),
        "charities_filed": narrative.get("charities_filed"),
        "narrative": narrative,
        "schedule_3": schedule3,
        "schedule_5_total": sched5_total,
        "schedule_6": schedule6,
        "validation": validations,
    }

    return result


# ── Excel output ─────────────────────────────────────────────────────────

def generate_excel(data, output_path):
    """Generate comparison Excel workbook with years as columns."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, numbers

    wb = Workbook()
    ws = wb.active
    ws.title = "Schedule 6 Comparison"

    years = sorted(data["years"].keys())
    bold = Font(bold=True)
    num_fmt = '#,##0'

    # Header row
    ws.cell(row=1, column=1, value="T3010 Line").font = bold
    ws.cell(row=1, column=2, value="Description").font = bold
    for col_idx, year in enumerate(years, start=3):
        ws.cell(row=1, column=col_idx, value=int(year)).font = bold

    # Field descriptions
    DESCRIPTIONS = {
        "4100": "Cash, bank accounts, short-term investments",
        "4110": "Amounts receivable from non-arm's length",
        "4120": "Amounts receivable from all others",
        "4130": "Investments in non-arm's length persons",
        "4140": "Long-term investments",
        "4150": "Inventories",
        "4155": "Land and buildings in Canada",
        "4160": "Other capital assets in Canada",
        "4165": "Capital assets outside Canada",
        "4166": "Accumulated amortization of capital assets",
        "4170": "Other assets",
        "4180": "10 year gifts",
        "4200": "TOTAL ASSETS",
        "4300": "Accounts payable and accrued liabilities",
        "4310": "Deferred revenue",
        "4320": "Amounts owing to non-arm's length",
        "4330": "Other liabilities",
        "4350": "TOTAL LIABILITIES",
        "4250": "Property not used in charitable activities",
        "4500": "Tax-receipted gifts",
        "5610": "Tax-receipted tuition fees",
        "4505": "10 year gifts received",
        "4510": "From other registered charities",
        "4530": "Other gifts (no receipt)",
        "4540": "Federal government revenue",
        "4550": "Provincial/territorial government revenue",
        "4560": "Municipal/regional government revenue",
        "4571": "Tax-receipted revenue from outside Canada",
        "4575": "Non tax-receipted revenue from outside Canada",
        "4580": "Interest and investment income",
        "4590": "Gross proceeds from disposition of assets",
        "4600": "Net proceeds from disposition of assets",
        "4610": "Rental income (land/buildings)",
        "4620": "Memberships, dues, association fees",
        "4630": "Non tax-receipted fundraising revenue",
        "4640": "Revenue from sale of goods/services",
        "4650": "Other revenue",
        "4700": "TOTAL REVENUE",
        "4800": "Advertising and promotion",
        "4810": "Travel and vehicle expenses",
        "4820": "Interest and bank charges",
        "4830": "Licences, memberships, dues",
        "4840": "Office supplies and expenses",
        "4850": "Occupancy costs",
        "4860": "Professional and consulting fees",
        "4870": "Education and training",
        "4880": "Total compensation (from Sched 3)",
        "4890": "FMV of donated goods used",
        "4891": "Purchased supplies and assets",
        "4900": "Amortization of capital assets",
        "4910": "Research grants and scholarships",
        "4920": "All other expenditures",
        "4950": "TOTAL EXPENDITURES (before gifts to QDs)",
        "5000": "Charitable program expenditures",
        "5010": "Management and administration",
        "5020": "Fundraising expenditures",
        "5030": "Political activities expenditures",
        "5040": "Other expenditures (in line 4950)",
        "5050": "Gifts to qualified donees",
        "5100": "TOTAL EXPENDITURES",
        "5500": "Accumulated property amount",
        "5510": "Disbursed for specified purpose",
        "5750": "Reduction to disbursement quota",
        "5900": "Property not used (24mo before start)",
        "5910": "Property not used (24mo before end)",
    }

    # Collect all fields across all years
    all_fields = []
    seen = set()
    for year in years:
        year_data = data["years"][year]
        for field in year_data.get("schedule_6", {}):
            if field not in seen:
                all_fields.append(field)
                seen.add(field)

    # Sort by canonical order
    canonical_order = (SCHED6_ASSETS + SCHED6_LIABILITIES + SCHED6_REVENUE +
                       SCHED6_EXPENDITURES_V13_18 + SCHED6_OTHER)
    ordered_fields = [f for f in canonical_order if f in seen]
    for f in all_fields:
        if f not in ordered_fields:
            ordered_fields.append(f)

    # Write rows
    row = 2

    # Section headers
    sections = [
        ("ASSETS", SCHED6_ASSETS),
        ("LIABILITIES", SCHED6_LIABILITIES),
        ("REVENUE", SCHED6_REVENUE),
        ("EXPENDITURES", SCHED6_EXPENDITURES_V13_18),
        ("OTHER", SCHED6_OTHER),
    ]

    for section_name, section_fields in sections:
        ws.cell(row=row, column=1, value=section_name).font = bold
        row += 1

        for field in section_fields:
            if field not in seen:
                continue
            ws.cell(row=row, column=1, value=field)
            ws.cell(row=row, column=2, value=DESCRIPTIONS.get(field, ""))
            for col_idx, year in enumerate(years, start=3):
                val = data["years"][year].get("schedule_6", {}).get(field)
                if val is not None:
                    cell = ws.cell(row=row, column=col_idx, value=val)
                    cell.number_format = num_fmt
                    # Bold for totals
                    if field in ("4200", "4350", "4700", "4950", "5100"):
                        cell.font = bold
            row += 1
        row += 1  # Blank row between sections

    # Schedule 3 section
    ws.cell(row=row, column=1, value="SCHEDULE 3 — COMPENSATION").font = bold
    row += 1

    sched3_desc = {
        "300": "FT compensated positions",
        "305": "$1-$39,999",
        "310": "$40,000-$79,999",
        "315": "$80,000-$119,999",
        "320": "$120,000-$159,999",
        "325": "$160,000-$199,999",
        "330": "$200,000-$249,999",
        "335": "$250,000-$299,999",
        "340": "$300,000-$349,999",
        "345": "$350,000+",
        "370": "PT/seasonal employees",
        "380": "PT compensation",
        "390": "TOTAL COMPENSATION",
    }

    for field in SCHED3_FIELDS:
        ws.cell(row=row, column=1, value=field)
        ws.cell(row=row, column=2, value=sched3_desc.get(field, ""))
        for col_idx, year in enumerate(years, start=3):
            val = data["years"][year].get("schedule_3", {}).get(field)
            if val is not None:
                cell = ws.cell(row=row, column=col_idx, value=val)
                cell.number_format = num_fmt
                if field in ("300", "370", "390"):
                    cell.font = bold
        row += 1

    # Column widths
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 45
    for col_idx in range(3, 3 + len(years)):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 20

    # Narrative sheet
    ws2 = wb.create_sheet("Narrative Highlights")
    ws2.cell(row=1, column=1, value="Metric").font = bold
    for col_idx, year in enumerate(years, start=2):
        ws2.cell(row=1, column=col_idx, value=int(year)).font = bold

    metrics = [
        ("charities_filed", "Charities Filed"),
        ("total_revenue_approx_B", "Total Revenue (~$B)"),
        ("total_expenditures_approx_B", "Total Expenditures (~$B)"),
        ("govt_revenue_approx_B", "Govt Revenue (~$B)"),
        ("federal_govt_approx_B", "Federal Govt (~$B)"),
        ("provincial_govt_approx_B", "Provincial Govt (~$B)"),
        ("municipal_govt_approx_B", "Municipal Govt (~$B)"),
        ("compensation_approx_B", "Compensation (~$B)"),
        ("tax_receipts_approx_B", "Tax Receipts (~$B)"),
    ]

    for row_idx, (key, label) in enumerate(metrics, start=2):
        ws2.cell(row=row_idx, column=1, value=label)
        for col_idx, year in enumerate(years, start=2):
            val = data["years"][year].get("narrative", {}).get(key)
            if val is not None:
                ws2.cell(row=row_idx, column=col_idx, value=val)

    ws2.column_dimensions["A"].width = 30

    wb.save(output_path)
    print(f"\nExcel workbook saved: {output_path}")


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract T3010 totals from historical Blumbergs Snapshot text files"
    )
    parser.add_argument("--year", type=int, help="Process a single year (2013-2021)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show field mappings")
    parser.add_argument("--excel", action="store_true", help="Also generate xlsx comparison")
    args = parser.parse_args()

    if args.year:
        if args.year not in SOURCE_FILES:
            print(f"ERROR: Year {args.year} not supported. Valid: {sorted(SOURCE_FILES.keys())}")
            sys.exit(1)
        years = [args.year]
    else:
        years = sorted(SOURCE_FILES.keys())

    print(f"Extracting historical snapshot data for {len(years)} year(s): {years}")

    results = {}
    for year in years:
        result = process_year(year, verbose=args.verbose)
        if result:
            results[str(year)] = result

    # Build output structure
    output = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "generator": "extract_historical_snapshots.py",
            "years": years,
            "source_dir": "docs/reference/blumbergs/extracted/",
        },
        "years": results,
    }

    # Save JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, "historical_snapshot_totals.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nJSON saved: {json_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Year':<6} {'Revenue ($B)':>14} {'Expenditures ($B)':>19} {'Govt ($B)':>12} {'Comp ($B)':>12}")
    print("-" * 65)
    for year in years:
        yr = str(year)
        if yr not in results:
            continue
        s6 = results[yr].get("schedule_6", {})
        rev = s6.get("4700")
        exp = s6.get("5100")
        govt = None
        if all(s6.get(f) is not None for f in ["4540", "4550", "4560"]):
            govt = s6["4540"] + s6["4550"] + s6["4560"]
        comp = s6.get("4880")

        rev_s = f"{rev/1e9:.1f}" if rev else "—"
        exp_s = f"{exp/1e9:.1f}" if exp else "—"
        govt_s = f"{govt/1e9:.1f}" if govt else "—"
        comp_s = f"{comp/1e9:.1f}" if comp else "—"
        print(f"{year:<6} {rev_s:>14} {exp_s:>19} {govt_s:>12} {comp_s:>12}")

    # Optional Excel
    if args.excel:
        xlsx_path = os.path.join(OUTPUT_DIR, "historical_snapshot_comparison.xlsx")
        generate_excel(output, xlsx_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
