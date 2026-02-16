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
├── docs/
│   ├── reference/          # T3010 form PDFs, Blumbergs Snapshot report
│   └── plans/              # Design and implementation docs
├── scripts/
│   ├── load_csv.py         # CSV → DuckDB loader
│   ├── queries/            # Reusable .sql files
│   └── reports/            # Report-generating Python scripts
├── CLAUDE.md
└── CRA_T3010_Reference.md
```

## Common Commands

```bash
# Rebuild database from CSVs (idempotent, ~20s)
python3 scripts/load_csv.py

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
```

DuckDB Python module is installed (`duckdb` 1.4.4). Always open with `read_only=True` unless intentionally modifying.

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
- **v_financial_d** — `bn`, `fiscal_period_end`, `total_revenue` (4200), `total_expenditures` (5000), `total_assets` (5030)
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
   CAST(REPLACE(REPLACE(column, '$', ''), ',', '') AS DECIMAL)
   ```
2. **Always LEFT JOIN from ident/charity_base** — Not all charities appear in every table
3. **Column names in raw tables use T3010 line numbers** (e.g., `"4700"` = total revenue). Use the views for readable names.
4. **BN column name varies by table** — `"BN/Registration Number"` vs `"BN/Registration number"`. Views normalize to `bn`.
5. **Designation codes**: A = Public Foundation, B = Private Foundation, C = Charitable Organization (~85% of charities)
6. **CSV encoding** — Files are ISO-8859/CP1252. The loader uses DuckDB encoding `CP1252` (NOT `IBM_1252` which is EBCDIC and mangles ASCII to fullwidth Unicode).

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
| 4570 | Total government funding |
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

## Adding a New Year

1. Place CSVs in `data/raw/{year}/` with the same snake_case naming convention
2. Move lookup tables to `data/raw/{year}/lookups/`
3. Run `python3 scripts/load_csv.py data/raw/{year}/`

## Reference Documentation

- `CRA_T3010_Reference.md` — Field mappings and relationship diagrams
- `docs/reference/t3010-24e.pdf` — Official T3010 form (2024 version)
- `docs/reference/t3010-lp-24e.pdf` — T3010 large print version (detailed field descriptions)
- `docs/reference/blumbergs-snapshot-2022.pdf` — Blumbergs' Snapshot analysis methodology and findings
