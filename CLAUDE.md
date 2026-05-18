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
│       ├── snapshots_2024/     # 13 Excel snapshot workbooks
│       ├── articles_2024/      # 13 Word article documents
│       ├── snapshot_comparison_2023_vs_2024.xlsx
│       └── jewish_sector_2024.xlsx  # Jewish charity sector workbook (4 sheets)
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
│       └── generate_jewish_sector.py     # Jewish charity sector workbook
├── requirements.txt        # Python dependencies (duckdb, openpyxl, pymupdf)
├── CLAUDE.md
└── CRA_T3010_Reference.md
```

## Common Commands

```bash
# Load default year (2024) into database (~20s, additive — preserves other years)
python3 scripts/load_csv.py

# Load additional years into the same database
python3 scripts/load_csv.py data/raw/2023/
python3 scripts/load_csv.py data/raw/2025/

# Re-load a year (replaces only that year's data)
python3 scripts/load_csv.py data/raw/2024/

# Fresh rebuild (delete database first, then load default year)
python3 scripts/load_csv.py --rebuild

# Validate database after loading
python3 scripts/validate_db.py              # all loaded years
python3 scripts/validate_db.py --year 2024  # specific year only

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
python3 scripts/reports/generate_snapshot.py            # Canada-wide only (latest year)
python3 scripts/reports/generate_snapshot.py --all      # All 13 workbooks
python3 scripts/reports/generate_snapshot.py --year 2023          # Specific year
python3 scripts/reports/generate_snapshot.py --province ON
python3 scripts/reports/generate_snapshot.py --provincial
python3 scripts/reports/generate_snapshot.py --designation A
python3 scripts/reports/generate_snapshot.py --designations

# Generate comparison workbook (requires Canada snapshot built first)
python3 scripts/reports/generate_comparison.py           # latest year vs prior
python3 scripts/reports/generate_comparison.py --year 2024  # specific year vs prior

# Generate snapshot article Word documents
python3 scripts/reports/generate_snapshot_articles.py --all
python3 scripts/reports/generate_snapshot_articles.py --year 2023 --all

# Generate Jewish charity sector workbook
python3 scripts/reports/generate_jewish_sector.py
python3 scripts/reports/generate_jewish_sector.py --year 2023

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

**No test suite exists.** Validation is done via `scripts/validate_db.py` (per-year integrity checks + cross-year consistency).

## Database Schema

### Core Tables
All raw and derived tables have `data_year INTEGER` as their first column, identifying the CRA data release year. Row counts below are per-year.

- **ident** (~83,275/yr) — Master charity list. PK: `(data_year, BN/Registration Number)`
- **charity_base** (~83,275/yr) — Cleaned ident joined with lookup descriptions (designation, category, subcategory, charity_type)
- **latest_filing** (~82,937/yr) — Most recent fiscal period end per charity within each year's data
- **charity_counts** (~83,275/yr) — Aggregated counts (programs, grants, operating countries)

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

### Lookup Tables (shared across years, no `data_year`)
- **lookup_category** (252), **lookup_country** (250), **lookup_designation** (3), **lookup_programs** (71), **lookup_province** (13), **lookup_form_versioning** (5), **lookup_us_state** (51)

### Views (filter to latest year by default, expose `data_year`)
Views filter to `MAX(data_year)` by default. For cross-year queries, use the raw tables directly with `WHERE data_year IN (...)`.

- **v_financial_d** — `data_year`, `bn`, `fiscal_period_end`, `total_revenue` (4700), `total_expenditures` (5100), `total_assets` (4200)
- **v_financial_abc** — `data_year`, `bn`, `fiscal_period_end`, `is_subsidiary`, `parent_bn`, `parent_name`
- **v_compensation** — `data_year`, `bn`, `fiscal_period_end`, `ft_employees`, `pt_employees`, `total_compensation`
- **v_programs** — `data_year`, `bn`, `fiscal_period_end`, `program_type`, `description`
- **v_grants** — `data_year`, `bn`, `fiscal_period_end`, `recipient_name`, `purpose`, `cash_amount`, `country`
- **v_foreign_recipients** — `data_year`, `bn`, `fiscal_period_end`, `recipient_name`, `country_code`, `amount`
- **v_operating_countries** — `data_year`, `bn`, `fiscal_period_end`, `country_code`
- **v_subsidiaries** — `data_year`, `subsidiary_bn`, `subsidiary_name`, `parent_bn`, `parent_name`

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
9. **Multi-year database** — All raw and derived tables have `data_year INTEGER` as their first column, identifying the CRA data release year (from directory name, e.g. `data/raw/2024/` → 2024). Views filter to `MAX(data_year)` by default. Query raw tables directly for cross-year comparisons. Lookup tables are shared across years (no `data_year` column). Loading a year replaces only that year's data; other years are preserved.

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
- **Scope filtering**: `get_scope_filter(filter_type, filter_value, year=None)` returns a WHERE clause against `charity_base cb` with `data_year` filter — all queries INNER JOIN through `charity_base` to restrict scope
- **Currency conversion**: `money(col)` helper wraps the `TRY_CAST(REPLACE(REPLACE(...)))` pattern
- **BN column mapping**: `BN_COL` dict maps table names to their specific BN column name (capital vs lowercase N)
- **Sheet builders**: Each `build_*()` function takes `(wb, con, where)` and appends a worksheet
- Output goes to `data/exports/snapshots_{year}/` (year-specific directory)

### Comparison Workbook (`scripts/reports/generate_comparison.py`)
Produces `data/exports/snapshot_comparison_2023_vs_2024.xlsx` with 5 sheets: Comparison, Canada 2024, All Financial Lines, By Designation, Compensation. 2024 values are Excel formulas referencing the embedded "Canada 2024" Summary sheet for full traceability. 2023 values are hardcoded from published Blumbergs Snapshot PDFs (exact Sch6 values where available, rounded text highlights otherwise). Requires `snapshot_2024_canada.xlsx` to exist first.

### Article Generator (`scripts/reports/generate_snapshot_articles.py`)
Produces 13 Word documents in `data/exports/articles_2024/` from a template. Comparison tables use standardized format: `[Scope 2024 | Scope 2023 | Canada 2024]` for provincial/designation articles, `[Canada 2024 | Canada 2023]` for national. 2023 data hardcoded from published Blumbergs PDFs. Uses `python-docx` with explicit `styled_run()` to maintain Times New Roman 13pt font consistency.

### Jewish Charity Sector Workbook (`scripts/reports/generate_jewish_sector.py`)
Produces `data/exports/jewish_sector_2024.xlsx` with 4 sheets identifying ~1,129 Jewish charities across three tiers:

- **Sheet 1 "Judaism Category"** (~391): Charities classified under CRA's `Judaism` category. Highest confidence.
- **Sheet 2 "Name-Identified"** (~374): Charities with Jewish/Hebrew keywords in `legal_name` (e.g., `jewish`, `chabad`, `torah`, `synagogue`), not already on Sheet 1. Medium-confidence keywords (`shalom`, `israel`, `beth`) are restricted to religion-adjacent categories to exclude Christian organizations.
- **Sheet 3 "Notable Foundations"** (~364): Multi-pass deep search — (1) known Jewish family foundations (Azrieli, Bronfman, etc.), (2) Jewish keywords in program descriptions, (3) grant flow analysis to Jewish organizations. Deduplicated against Sheets 1 & 2.
- **Summary sheet**: Aggregated financial totals (revenue, assets, expenditures, compensation) for the entire Jewish charity sector.

All detail sheets include 14 financial columns (LEFT JOINed through `latest_filing` to avoid fiscal-period duplicates) with a TOTALS row using SUM formulas.

## Published 2023 Snapshot Data

2023 comparison data is hardcoded in scripts (not from database). Sources:
- `docs/reference/blumbergs/provincial/` — ON, QC, BC, AB, Atlantic 2023 PDFs
- `docs/reference/blumbergs/other/` — Public Foundation, Private Foundation, Charitable Org 2023 PDFs
- Canada 2023 and MB 2023 data extracted from the national snapshot PDF
- SK, NS, NB have no published 2023 snapshots — no prior year data available for those provinces

## Adding a New Year

1. Place CSVs in `data/raw/{year}/` with the same snake_case naming convention
2. Move lookup tables to `data/raw/{year}/lookups/`
3. Run `python3 scripts/load_csv.py data/raw/{year}/` — this adds the year to the existing database
4. Run `python3 scripts/validate_db.py` to verify all years
5. Generate reports: `python3 scripts/reports/generate_snapshot.py --year {year} --all`

The first time after upgrading from the single-year database, use `--rebuild` to create the new schema.

## AI Context Documents

Read these before any analysis task — they encode 14 years of Blumbergs domain expertise:
- `docs/context/data-interpretation-guide.md` — How to correctly interpret every T3010 line, designation-specific patterns, data type gotchas
- `docs/context/sector-trends.md` — Historical baselines 2010-2023 (revenue, govt funding, compensation, foreign activities by year)
- `docs/context/methodology-notes.md` — Snapshot methodology, all data quality caveats, known unreliable fields
- `docs/context/regulatory-context.md` — DQ rules, DAF regulation, political activities history, CRA oversight, transparency advocacy
- `docs/context/cra-forms-reference.md` — Per-form summary (T3010, T4033, T1235, T1236, T1441, T2081); V23→V24 line redefinitions
- `docs/context/t3010-field-dictionary.md` — Synthesized authoritative line-by-line dictionary (162 indexed lines + every column across 18 tables, with CRA-defined descriptions)

## Reference Documentation

- `CRA_T3010_Reference.md` — Field mappings and relationship diagrams
- `docs/reference/t3010-24e.pdf` — Official T3010 form (2024 version)
- `docs/reference/t3010-lp-24e.pdf` — T3010 large print version (detailed field descriptions)
- `docs/reference/cra-forms/` — CRA forms received from Mark Blumberg 2026-05-18: T3010-24e, T4033-24e (completion guide), T1235-20e (trustees), T1236-19e (qualified donees), T1441 (grants to non-qualified donees), T2081-10e (excess corporate holdings)
- `docs/reference/cra-internal/` — **Confidential** CRA partner materials (gitignored). T3010 Public Data Dictionary 2023 + 2024, Line Number and Contents Index 2024. Content has been paraphrased into `docs/context/t3010-field-dictionary.md`; the source files do not ship in the public repo.
- `docs/reference/blumbergs/` — 51+ Blumbergs PDFs (snapshots, provincial, designation, DAF, pre-budget) + extracted text in `extracted/`
- `docs/reference/blumbergs/provincial/` — Provincial 2023 snapshot PDFs (ON, QC, BC, AB, Atlantic)
- `docs/reference/blumbergs/other/` — Designation 2023 snapshot PDFs (Public/Private Foundations, Charitable Orgs)
