# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canadian Registered Charities data analysis project using CRA T3010 annual filing data (~83,000 charities). Source CSVs are loaded into a DuckDB database via a Python loader script. The project supports sector-wide statistical reports (Blumbergs Snapshot style), charity-specific lookups, data exports, and multi-year analysis.

## Directory Structure

```
blumbergs/
├── data/
│   ├── raw/2024/           # Source CSVs (snake_case), with lookups/ subfolder
│   ├── db/                 # cra_charities.duckdb (built by loader)
│   └── exports/            # Generated output files
│       ├── snapshots_2024/        # 13 Excel snapshot workbooks
│       ├── articles_2024/         # 13 Word article documents (with embedded T3010 PDF pages)
│       ├── snapshot_pdfs_2024/    # 13 annotated T3010 PDF snapshots (source for article images)
│       ├── t3010_data/            # 13 JSON data files (structured snapshot data)
│       └── snapshot_comparison_2023_vs_2024.xlsx
├── docs/
│   ├── context/            # AI-optimized context docs (read these for domain expertise)
│   ├── reference/          # T3010 form PDFs, Blumbergs publications
│   │   └── blumbergs/      # 51+ Blumbergs PDFs + extracted text
│   │       ├── provincial/     # Provincial 2023 snapshot PDFs (ON, QC, BC, AB, Atlantic)
│   │       └── other/          # Designation 2023 snapshot PDFs (Public/Private/Charitable)
│   └── plans/              # Design and implementation docs
├── scripts/
│   ├── load_csv.py         # CSV → DuckDB loader
│   ├── validate_db.py      # Post-load database integrity checks (35 checks)
│   ├── queries/            # Reusable .sql files
│   └── reports/            # Report-generating Python scripts
│       ├── generate_snapshot.py          # 13 Excel snapshot workbooks
│       ├── generate_snapshot_articles.py # 13 Word article documents
│       ├── generate_comparison.py        # 2023 vs 2024 comparison workbook
│       └── update_article_pdfs.py        # Replace embedded T3010 PDF images in articles
├── requirements.txt        # Python dependencies (duckdb, openpyxl, pymupdf)
├── CLAUDE.md
└── CRA_T3010_Reference.md
```

## Common Commands

```bash
# Rebuild database from CSVs (idempotent, ~20s)
python3 scripts/load_csv.py

# Validate database after loading (35 integrity checks)
python3 scripts/validate_db.py

# Load a different year
python3 scripts/load_csv.py data/raw/2025/

# Query the database
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
print(con.execute('SELECT ...').fetchdf())
con.close()
"

# Run a query file
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
print(con.execute(open('scripts/queries/sector_snapshot.sql').read()).fetchdf().to_string())
"

# Generate snapshot Excel workbooks (requires database built first)
python3 scripts/reports/generate_snapshot.py            # Canada-wide only
python3 scripts/reports/generate_snapshot.py --all      # All 13 workbooks (Canada + 9 provincial + 3 designation)
python3 scripts/reports/generate_snapshot.py --province ON
python3 scripts/reports/generate_snapshot.py --provincial  # All 9 provincial workbooks
python3 scripts/reports/generate_snapshot.py --designation A  # Public Foundations only
python3 scripts/reports/generate_snapshot.py --designations   # All 3 designation workbooks

# Generate comparison workbook (2023 vs 2024, requires Canada snapshot built first)
python3 scripts/reports/generate_comparison.py

# Generate snapshot article Word documents
python3 scripts/reports/generate_snapshot_articles.py --all

# Replace T3010 PDF images in existing articles (after regenerating PDFs)
python3 scripts/reports/update_article_pdfs.py          # All 13 articles
python3 scripts/reports/update_article_pdfs.py --dry-run # Preview mapping only

# Charity lookup (replace BN)
python3 -c "
import duckdb, sys
bn = sys.argv[1]
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
sql = open('scripts/queries/charity_lookup.sql').read().replace('\$BN', bn)
for stmt in sql.split(';\n'):
    stmt = stmt.strip()
    if stmt and not stmt.startswith('--'):
        print(con.execute(stmt).fetchdf().to_string()); print()
con.close()
" 119080464RR0001
```

DuckDB Python module is installed (`duckdb` 1.4.4). Always open with `read_only=True` unless intentionally modifying. `openpyxl` is installed for Excel workbook generation. `pymupdf` (fitz) is available for PDF rendering/extraction. `python-docx` is available for Word document manipulation.

**No test suite exists.** Validation is done via `scripts/validate_db.py` (35 integrity checks on the database).

## Database Schema

### Core Tables
- **ident** (83,275) — Master charity list. PK: `BN/Registration Number`
- **charity_base** (83,275) — Cleaned ident joined with lookup descriptions (designation, category, subcategory, charity_type)
- **latest_filing** (82,937) — Most recent fiscal period end per charity
- **charity_counts** (83,275) — Aggregated counts (programs, grants, operating countries)

### Financial Tables
- **financial_d** (83,093) — Balance sheet + income statement. Column names are T3010 line numbers (4100, 4200, 4700, 5000, etc.)
- **financial_abc** (83,433) — Program area codes, Y/N questions, DAF data, subsidiary relationships

### Schedule Tables
- **schedule_1_foundations** (83,433) — Foundation-specific fields
- **schedule_2_summary** (5,001) — Foreign activities summary
- **schedule_2_countries** (9,332) — Countries where charity operates (1:many)
- **schedule_2_recipients** (13,953) — Foreign aid recipients (1:many)
- **schedule_2_destinations** (699) — Export destinations (1:many)
- **schedule_3_compensation** (42,878) — Employee compensation by salary band
- **schedule_5_noncash** (11,151) — Non-cash gifts
- **schedule_8_disbursement** (14,574) — Disbursement quota calculations

### Supplementary Tables
- **programs** (94,973) — Program descriptions (1:many)
- **grants** (14,101) — Grants to non-qualified donees (1:many)

### Lookup Tables
- **lookup_category** (252), **lookup_country** (250), **lookup_designation** (3), **lookup_programs** (71), **lookup_province** (13), **lookup_form_versioning** (5), **lookup_us_state** (51)

### Views (use these for friendlier column names)
- **v_financial_d** — `bn`, `fiscal_period_end`, `total_revenue` (4700), `total_expenditures` (5100), `total_assets` (4200)
- **v_financial_abc** — `bn`, `fiscal_period_end`, `is_subsidiary`, `parent_bn`, `parent_name`
- **v_compensation** — `bn`, `fiscal_period_end`, `ft_employees`, `pt_employees`, `total_compensation`
- **v_programs** — `bn`, `fiscal_period_end`, `program_type`, `description`
- **v_grants** — `bn`, `fiscal_period_end`, `recipient_name`, `purpose`, `cash_amount`, `country`
- **v_foreign_recipients** — `bn`, `fiscal_period_end`, `recipient_name`, `country_code`, `amount`
- **v_operating_countries** — `bn`, `fiscal_period_end`, `country_code`
- **v_subsidiaries** — `subsidiary_bn`, `subsidiary_name`, `parent_bn`, `parent_name`

## Critical Data Quirks

1. **Currency fields are text** — Format `"$1,234,567"`. Convert with:
   ```sql
   TRY_CAST(REPLACE(REPLACE(column, '$', ''), ',', '') AS DECIMAL)
   ```
   Use `TRY_CAST` not `CAST` — some rows have non-numeric values (letters, blanks) that cause `CAST` to fail.
2. **Always LEFT JOIN from ident/charity_base** — Not all charities appear in every table
3. **Column names in raw tables use T3010 line numbers** (e.g., `"4700"` = total revenue). Use the views for readable names.
4. **BN column name varies by table** — `"BN/Registration Number"` (capital N) in `ident`, `financial_d`, `schedule_8_disbursement`; `"BN/Registration number"` (lowercase n) everywhere else. Views normalize to `bn`.
5. **Designation codes**: A = Public Foundation, B = Private Foundation, C = Charitable Organization (~85% of charities)
6. **CSV encoding** — Files are ISO-8859/CP1252. The loader uses DuckDB encoding `CP1252` (NOT `IBM_1252` which is EBCDIC and mangles ASCII to fullwidth Unicode).
7. **schedule_3_compensation mixed types** — Lines 300/370 are BIGINT (no currency formatting), but line 390 is VARCHAR (has `$` and `,`). Don't apply REPLACE() to BIGINT columns.
8. **T3010 form version changes (V23→V24)**: Lines 4575, 4580, 4101, 4102 changed definition. V23 4575="Tax-receipted from outside Canada" → V24 4575="Non-tax-receipted revenue from outside Canada". V23 4580="Non-tax-receipted from outside Canada" → V24 4580="Interest/investment income". V23 4101/4102="Receivables breakdown" → V24 4101/4102="Cash vs short-term investments". Direct year-over-year comparisons on these lines are invalid.

## T3010 Form Structure

The T3010 has 5 sections mapped to the database:

| T3010 Section | Database Tables |
|---------------|-----------------|
| A: Identification | ident, charity_base |
| B: Directors/Trustees | trustee (via T1235 worksheet) |
| C: Programs & General Info | financial_abc, programs, grants |
| D: Financial Information | financial_d |
| Schedules 1-8 | schedule_* tables |

### Key T3010 Line Numbers (financial_d columns)

| Line | Meaning |
|------|---------|
| 4100 | Cash and short-term investments |
| 4200 | Total assets |
| 4350 | Total liabilities |
| 4500 | Tax-receipted gifts |
| 4510 | Gifts from other charities |
| 4540/4550/4560 | Government funding (fed/prov/muni) |
| 4570 | Total government funding (**UNRELIABLE** — compute as 4540+4550+4560 instead) |
| 4880 | Total compensation (mirrors schedule_3 line 390) |
| 4700 | Total revenue |
| 5000 | Charitable program expenditures |
| 5010 | Management and admin |
| 5020 | Fundraising |
| 5045 | Grants to non-qualified donees |
| 5050 | Gifts to qualified donees |
| 5100 | Total expenditures |
| 300/370 | FT/PT employee count (schedule_3) |
| 390 | Total compensation (schedule_3) |
| 5860-5864 | DAF fields (financial_abc) |

## Data Quality Caveats

Per the Blumbergs Snapshot methodology:
- T3010 data is **self-reported and not independently verified** by CRA
- Often completed by volunteers with limited understanding of the Income Tax Act
- Subjective fields (like political expenditures, program allocations) are prone to errors
- Larger institutions tend to be more accurate but also more complex
- Some questions changed between form versions (see `lookup_form_versioning`)

## Snapshot Generator Architecture

`scripts/reports/generate_snapshot.py` produces 13 Excel workbooks (1 Canada-wide, 9 provincial, 3 by designation). Each workbook has 9 sheets mirroring T3010 sections (A, C, D, Schedules 1-3, 5-6, 8).

Key patterns:
- **Scope filtering**: `get_scope_filter()` returns a WHERE clause against `charity_base cb` — all queries INNER JOIN through `charity_base` to restrict scope
- **Currency conversion**: `money(col)` helper wraps the `TRY_CAST(REPLACE(REPLACE(...)))` pattern
- **BN column mapping**: `BN_COL` dict maps table names to their specific BN column name (capital vs lowercase N)
- **Sheet builders**: Each `build_*()` function takes `(wb, con, where)` and appends a worksheet
- Output goes to `data/exports/snapshots_2024/`

### Comparison Workbook (`scripts/reports/generate_comparison.py`)
Produces `data/exports/snapshot_comparison_2023_vs_2024.xlsx` with 5 sheets: Comparison, Canada 2024, All Financial Lines, By Designation, Compensation. 2024 values are Excel formulas referencing the embedded "Canada 2024" Summary sheet for full traceability. 2023 values are hardcoded from published Blumbergs Snapshot PDFs (exact Sch6 values where available, rounded text highlights otherwise). Requires `snapshot_2024_canada.xlsx` to exist first.

### Article Generator (`scripts/reports/generate_snapshot_articles.py`)
Produces 13 Word documents in `data/exports/articles_2024/` from a template. Comparison tables use standardized format: `[Scope 2024 | Scope 2023 | Canada 2024]` for provincial/designation articles, `[Canada 2024 | Canada 2023]` for national. 2023 data hardcoded from published Blumbergs PDFs. Uses `python-docx` with explicit `styled_run()` to maintain Times New Roman 13pt font consistency. Title is 20pt Times New Roman centered; body is 13pt.

### PDF Image Updater (`scripts/reports/update_article_pdfs.py`)
Replaces embedded T3010 PDF page images in existing article Word documents without regenerating the full article content. Renders PDFs from `snapshot_pdfs_2024/` at 250 DPI and inserts them at full-page size (7.5" x 9.71" within 0.5" margins). Uses paragraph-level `pageBreakBefore` and zero before/after spacing for tight layout. Saves as `-v2.docx` alongside originals. Cleans orphaned media from docx zips to keep file sizes uniform (~4.2M each).

## Published 2023 Snapshot Data

2023 comparison data is hardcoded in scripts (not from database). Sources:
- `docs/reference/blumbergs/provincial/` — ON, QC, BC, AB, Atlantic 2023 PDFs
- `docs/reference/blumbergs/other/` — Public Foundation, Private Foundation, Charitable Org 2023 PDFs
- Canada 2023 and MB 2023 data extracted from the national snapshot PDF
- SK, NS, NB have no published 2023 snapshots — no prior year data available for those provinces

## Adding a New Year

1. Place CSVs in `data/raw/{year}/` with the same snake_case naming convention
2. Move lookup tables to `data/raw/{year}/lookups/`
3. Run `python3 scripts/load_csv.py data/raw/{year}/`

## AI Context Documents

Read these before any analysis task — they encode 14 years of Blumbergs domain expertise:
- `docs/context/data-interpretation-guide.md` — How to correctly interpret every T3010 line, designation-specific patterns, data type gotchas
- `docs/context/sector-trends.md` — Historical baselines 2010-2023 (revenue, govt funding, compensation, foreign activities by year)
- `docs/context/methodology-notes.md` — Snapshot methodology, all data quality caveats, known unreliable fields
- `docs/context/regulatory-context.md` — DQ rules, DAF regulation, political activities history, CRA oversight, transparency advocacy

## Reference Documentation

- `CRA_T3010_Reference.md` — Field mappings and relationship diagrams
- `docs/reference/t3010-24e.pdf` — Official T3010 form (2024 version)
- `docs/reference/t3010-lp-24e.pdf` — T3010 large print version (detailed field descriptions)
- `docs/reference/blumbergs/` — 51+ Blumbergs PDFs (snapshots, provincial, designation, DAF, pre-budget) + extracted text in `extracted/`
- `docs/reference/blumbergs/provincial/` — Provincial 2023 snapshot PDFs (ON, QC, BC, AB, Atlantic)
- `docs/reference/blumbergs/other/` — Designation 2023 snapshot PDFs (Public/Private Foundations, Charitable Orgs)
