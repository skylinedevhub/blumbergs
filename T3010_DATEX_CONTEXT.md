# T3010 DatEx — Full Project Context for Claude

> **Reader**: This single document hands an AI assistant (Claude, GPT, or any
> capable LLM) the full working context for the Canadian Registered Charities
> T3010 data project — also known as **t3010datex.vercel.app** — built by
> Skyline Development Hub for Mark Blumberg's team at Blumbergs Professional
> Corporation.
>
> If you are an LLM ingesting this for the first time: read top to bottom once,
> then treat the embedded **System Prompt** (Section 8) as your operating
> instructions when the user asks you to generate SQL for this data.
>
> **Snapshot taken**: 2026-05-19
> **Source repo**: https://github.com/skylinedevhub/blumbergs
> **Live site**: https://t3010datex.vercel.app
> **Branch**: `feature/multi-year-database`

---

## What This Document Contains

| Section | Source File | Purpose |
|---|---|---|
| 1. Project Orientation | `CLAUDE.md` | Directory layout, common commands, database schema, T3010 form structure, data quirks |
| 2. CRA Forms Reference | `docs/context/cra-forms-reference.md` | Per-form purpose (T3010, T4033, T1235, T1236, T1441, T2081); V23→V24 redefinitions |
| 3. T3010 Field Dictionary | `docs/context/t3010-field-dictionary.md` | Authoritative line-by-line dictionary across all 18 tables (162 indexed lines) |
| 4. Data Interpretation Guide | `docs/context/data-interpretation-guide.md` | How to correctly interpret every T3010 line, designation-specific patterns |
| 5. Methodology & Caveats | `docs/context/methodology-notes.md` | Blumbergs Snapshot methodology, data quality caveats, known unreliable fields |
| 6. Sector Trends | `docs/context/sector-trends.md` | Historical baselines 2010–2023 (revenue, govt funding, foreign activities) |
| 7. Regulatory Context | `docs/context/regulatory-context.md` | DQ rules, DAF regulation, political activities history, CRA oversight |
| 8. Chat AI System Prompt | `web/lib/agents/system-prompt.ts` | The prompt the production chatbot uses; treat as operating instructions for SQL-generation tasks |
| 9. Filter Catalog Summary | `web/public/explorer.js` | List of 205 selectable metrics/filters exposed in the Data Explorer sidebar |

---

## Authoritative Sources

The field meanings in this document are reconciled against **three CRA-published references**, received from Mark Blumberg on 2026-05-18:

- **T3010 Registered Charity Information Return (T3010-24e)** — public, the actual annual return form
- **T4033 Completing the T3010 (T4033-24e)** — public, CRA's official completion guide
- **T1235** — public, Directors/Trustees worksheet
- **T1236** — public, Qualified Donees worksheet
- **T1441** — public, Grants to Non-Qualified Donees (V26+ qualifying disbursements regime)
- **T2081** — public, Excess Corporate Holdings worksheet (private foundations only)
- **T3010 Public Data Dictionary 2024** — CRA partner-distributed, marked confidential
- **T3010 Public Data Dictionary 2023** — CRA partner-distributed, marked confidential
- **T3010 Line Number and Contents Index 2024** — CRA partner-distributed, marked confidential

The confidential XLSX files are **not** distributed in the public repo. The content they contain has been synthesized into Section 3 below; the source files remain private with Skyline Development Hub.

Where any field meaning conflicts between this document and CRA's authoritative dictionary, **CRA's dictionary wins**. A schema audit in May 2026 corrected 207 incorrectly-labeled columns; current field meanings in this document reflect those corrections.

---

# Section 1 — Project Orientation (from CLAUDE.md)

> Original location: `CLAUDE.md` at repo root.

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


---

# Section 2 — CRA Forms Reference (from docs/context/cra-forms-reference.md)

> Original location: `docs/context/cra-forms-reference.md`.

# CRA Forms Reference

Authoritative reference for the CRA forms behind the T3010 Registered Charity Information Return. Source files in `docs/reference/cra-forms/`. Per-form summaries below are derived from CRA's own descriptions (T4033 guide + each form's preamble) and from Mark Blumberg's contextual notes.

When interpreting database fields, treat these definitions as ground truth — they override prior assumptions in scripts and earlier docs.

---

## T3010 — Registered Charity Information Return (T3010-24e)

Annual information return filed by every registered Canadian charity within 6 months of fiscal year-end. The core public reporting document; the source of every record in this database.

Sections:
| Section | Contents | DB Table |
|---|---|---|
| A — Identification | BN, legal name, addresses, designation, category | `ident`, `charity_base` |
| B — Directors/Trustees | Board composition (T1235 worksheet) | `trustee` |
| C — Programs & General Info | Fundraising methods, political activities, Y/N questions, DAF data, gifts to qualified donees | `financial_abc`, `programs`, `gift` |
| D — Financial Information | Balance sheet + income statement | `financial_d` |
| Schedule 1 | Foundations only | `schedule_1_foundations` |
| Schedule 2 | Activities outside Canada | `schedule_2_*` |
| Schedule 3 | Compensation (salary bands, top 10) | `schedule_3_compensation` |
| Schedule 5 | Non-cash gifts received | `schedule_5_noncash` |
| Schedule 6 | Alternative financial section (small charities) | merged into `financial_d` with `Section Used (D or 6) = 6` |
| Schedule 7 | Political activities (V23 only; removed in V24) | `schedule_7_*` |
| Schedule 8 | Disbursement quota | `schedule_8_disbursement` |

**Form versioning**: The T3010 evolves. The `Form ID` column on every transactional table identifies the version a particular return used. The active version for 2024 data is V24. A few line numbers were repurposed between V23→V24 (see "Form version pitfalls" below).

**Confidentiality note**: A small portion of the T3010 (e.g. directors' home addresses, signing officer info) is *not* in the public data. Everything you see in our DuckDB is public; absence of a field does not mean a charity didn't file it.

---

## T4033 — Completing the Registered Charity Information Return (T4033-24e)

CRA's official guide for completing the T3010. The starting point for understanding how CRA *expects* charities to report any given item. Use this when interpreting a field's intended meaning or judging whether a charity is misclassifying revenue/expenditures.

Key interpretive principles (paraphrased from T4033):
- **Cash vs accrual** (line 4020): Charities self-select. Mixed accounting across years is common.
- **Fair market value vs cost** (line 4200): For donated assets, charities report FMV at receipt; for purchased assets, at cost. Lines 4200 and 4350 are *not* expected to balance — the difference rolls into a balancing net-assets account.
- **Total revenue (4700)** = 4500 + 4510 + 4530 + 4570 + 4575 + 4630 + 4640 + 4650 (per T4033). Other sub-lines (4540, 4550, 4560, 4565, 4571, 4580, 4590, 4600, 4610, 4620, 4655) are detail that feeds into the larger buckets, not additive.
- **Government funding (4570)** is meant to be the sum of 4540 + 4550 + 4560. T4033 acknowledges this is self-totalled and not validated by CRA — hence our convention to recompute it from 4540/4550/4560.
- **Charitable activities (5000)** + **Mgmt/admin (5010)** + **Fundraising (5020)** should equal 4950 (Total operating expenditures from D4). Total expenditures (5100) = 4950 + 5045 + 5050.
- **Schedule 6 vs Section D**: Smaller charities may use Schedule 6 in lieu of Section D. The `Section Used (D or 6)` column on `financial_d` flags which they used. Field semantics are identical; CRA merges them into the same dataset.

---

## T1235 — Directors/Trustees and Like Officials Worksheet (T1235-20e)

Detailed disclosure of directors, trustees, and similar officials. Supplements Section B governance disclosures. Feeds the `trustee` DB table.

Per-row fields include:
- Position (Director, Trustee, etc.)
- First/Last Name
- Appointed Date / Ceased Date
- **At arm's length** (Y/N) — STRAIGHT ASCII apostrophe in the column header; not curly.

Use this table to assess:
- Board size and turnover
- Arm's-length ratio (governance independence proxy)
- Founder/family entrenchment in private foundations (cross-reference `cb.legal_name`)

Note: directors' home addresses are confidential and NOT in the public data.

---

## T1236 — Qualified Donees Worksheet (T1236-19e)

Disclosure of amounts the charity gave to *qualified donees* (other registered charities, RNASOs, registered amateur athletic associations, registered universities outside Canada listed on Schedule VIII, the United Nations and its agencies, etc.). Feeds the `gift` DB table.

Per-row fields include:
- Donee name, BN (if a Canadian registered charity), city, province
- Total amount of gifts (cash)
- Amount of gifts in kind (non-cash)
- Political Activities Gift Amount (legacy V23 field; deprecated in V24)
- Number of donees

The financial total on T1236 should reconcile to line 5050 on the T3010 (gifts to qualified donees). When it doesn't, the T1236 detail is generally more reliable than 5050.

---

## T1441 — Qualifying Disbursements: Grants to Non-Qualified Donees

Introduced June 2022 by the *qualifying disbursements* regime (Bill C-19). Lets registered charities grant to organizations that are NOT qualified donees (i.e. non-profits, foreign NGOs, etc.) provided certain accountability conditions are met. Feeds the `grants` DB table.

Per-row fields:
- Grantee name, country
- Purpose of the grant
- Cash amount and non-cash amount
- Active monitoring / accountability description

This is *only* available from V26 onward. Records exist only for fiscal years ending after June 23, 2022. The total flows to line 5045 on the T3010.

Practical implication: grants to non-qualified donees are a **new sector activity**. Year-over-year growth on line 5045 reflects regime adoption, not necessarily increased giving.

---

## T2081 — Excess Corporate Holdings Worksheet for Private Foundations (T2081-10e)

Applies only to private foundations subject to the *excess corporate holdings* regime (s. 149.1 of the Income Tax Act, in effect since 2007), which caps a private foundation's holdings of any single class of corporate shares. Tracks holdings, divestment obligations, and any divestment shortfall taxes payable.

Few charities are affected; relevant when analyzing large family-foundation portfolios. Not currently represented as a separate DB table — relevant flags live on `schedule_1_foundations` (line 130 "Excess corporate holdings?").

---

## Confidential CRA Reference Materials (NOT in repo)

The following files are CRA partner-distributed materials, marked confidential by Mark Blumberg. They are stored locally in `docs/reference/cra-internal/` (gitignored) and used only to enrich documentation:

1. **T3010 Public Data Dictionary 2024** — Authoritative field-by-field schema for every table in the public data download. Provides the `DESCRIPTION` text used throughout `t3010-field-dictionary.md` and the `web/lib/schema-index.json` column descriptions.
2. **T3010 Public Data Dictionary 2023** — Prior-year version. Useful for diffing field definitions when investigating V23 vs V24 discrepancies.
3. **T3010 Line Number and Contents Index 2024** — Canonical line-number → short-label + full-question mapping (162 entries). Source for short labels in the field dictionary.

Their content is paraphrased and integrated into the project docs; the source XLSX files themselves should not be committed to the public repo.

---

## Form Version Pitfalls (V23 → V24)

Per the data dictionary's per-column FORM VERSION metadata, these lines changed definition between versions. Direct year-over-year comparison on these lines is **invalid**:

| Line | V23 meaning | V24 meaning |
|---|---|---|
| 4101 | Receivables breakdown | Cash in bank accounts (subset of 4100) |
| 4102 | Receivables breakdown | Short-term investments (subset of 4100) |
| 4575 | Tax-receipted from outside Canada | Non-tax-receipted revenue from outside Canada |
| 4580 | Non-tax-receipted from outside Canada | Interest and investment income |
| 4576 | (new in V24) | Foreign business/investment activities subset of 4580 |
| 4577 | (new in V24) | Related business activities subset of 4580 |
| 4157/4158 | (new in V24) | Canadian land/buildings used for charitable activity |
| 4190 | (new in V24) | Value of all impact investments |
| Schedule 7 | Political activities (Sch7 Desc, Sch7 Political Activities Fund, Sch7 Political Activities Res) | Schedule 7 removed (political activities reform) |

For cross-version analysis, filter on `Form ID` and treat changed lines as separate series, not a continuous metric.


---

# Section 3 — T3010 Field Dictionary (from docs/context/t3010-field-dictionary.md)

> Original location: `docs/context/t3010-field-dictionary.md`. This is the largest section — ~620 lines of authoritative per-column descriptions for every table.

# T3010 Field Dictionary (Authoritative)

Synthesized from CRA's *T3010 Public Data Dictionary 2024* and *Line Number and Contents Index 2024* (both confidential, partner-distributed) plus the published *T4033 Completing the T3010* guide. This is the canonical reference for what every column in the public data actually means.

Numeric line-number columns appear as bare digits (`4100`, `4700`) in the raw tables — quote them in SQL: `fd."4700"`. The "Short" column is CRA's internal shortform label (useful as UI labels or in chat AI explanations).

---

## `ident` (alias `i`)

Source tab: *Ident* — 16 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the business number (BN) system. |  |
| `Designation code` |  | Short Text(1) | Identifies the designation that a charity receives based on its structure, its source of funding, and its mode of operation. *("# Designation" table contains full list of desgination codes.)* |  |
| `Category code` |  | Short Text(4) | Current main classification of the charity's purpose. *("# Category Sub-category" table contains full list of category/sub-category codes.)* |  |
| `Sub-category code` |  | Short Text(4) | Sub-classification of the charity's purpose. |  |
| `Legal name` |  | Short Text(175) | The legal entity name as shown on the charity’s governing documents. |  |
| `Account name` |  | Short Text(175) | The charity's account name. It can be the same as the legal name. |  |
| `Registration date` |  | Date/Time | Effective date of when the organization became a registered charity. |  |
| `Language` |  | Short Text(2) | Code for the primary language of the charity. *(01 = English, 02 = French New in November 2020 (R4.1))* |  |
| `Mailing address` |  | Short Text(62) | The first and second line of the mailing address. |  |
| `City` |  | Short Text(30) | Mailing address - city |  |
| `Province` |  | Short Text(2) | Mailing address - province |  |
| `Postal code` |  | Short Text(10) | Mailing address - postal code |  |
| `Country` |  | Short Text(2) | Mailing address - country code. |  |
| `Contact Phone` |  | Short Text(36) | Charity's contact phone *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |
| `Contact Email` |  | Short Text(200) | Charity's contact email address *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |
| `Contact URL` |  | Short Text(200) | Charity's website address *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |

## `financial_abc` (alias `fabc`)

Source tab: *Financial Section A, B and C* — 67 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `BN/Registration number` |  | Short Text(16) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `1200 Program Area Code` |  | Short Text(3) | Most important field of operations *(Business information sheet (BIS) - program area rank #1.  Important note:  As of May 2019, the business information sheets are no longer being mailed out to the... |  |
| `1200 Percent` |  | Number(Integer) | Most important field of operations percentage *(Business information sheet (BIS) - program area rank #1.)* |  |
| `1210 Program Area Code` |  | Short Text(3) | Second most important field of operations *(Business information sheet (BIS) - program area rank #2.)* |  |
| `1210 Percent` |  | Number(Integer) | Second most important field of operations percentage *(Business information sheet (BIS) - program area rank #2.)* |  |
| `1220 Program Area Code` |  | Short Text(3) | Third most important field of operations *(Business information sheet (BIS) - program area rank #3.)* |  |
| `1220 Percent` |  | Number(Integer) | Third most important field of operations percentage *(Business information sheet (BIS) - program area rank #3.)* |  |
| `1510 Subordinate position to a parent organization?` |  | Short Text(1) | Is the charity subordinate to a parent organization? *(Value can be "Y", "N" or <empty>)* |  |
| `1510 Parent Business Number` |  | Short Text(15) | BN of the parent organization to which this charity is a subordinate |  |
| `1510 Parent Name` |  | Short Text(175) | Name of the parent organization to which this charity is a subordinate |  |
| `1570` | Wound-Up/Dissolved | Short Text(1) | Has the charity wound-up, dissolved or terminated operations? *(Value can be "Y", "N" or <empty>)* |  |
| `1600` | Foundation Designation | Short Text(1) | Is the charity designated as a public foundation or private foundation? *(Value can be "Y", "N" or <empty>)* |  |
| `1800` | Active | Short Text(1) | Was the charity active during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `2000` | Gifts to Qualified Donees | Short Text(1) | Did the charity make gifts or transfer funds to qualified donees or other organizations (excluding grants to non-qualified donees) *(Value can be "Y", "N" or <empty>)* |  |
| `2100` | Foreign Activities | Short Text(1) | Did the charity’s financial resources were spent on programs outside Canada under an arrangement including a contract, agency agreement or joint venture to an individual or organization (excluding ... |  |
| `2400` |  | Short Text(1) | Did charity carry out any political activities during the fiscal period? *(Value can be "Y", "N" or <empty>   On version 24 of T3010 form, the name "political activities" was changed to "public pol... | 23, 24 |
| `5030` |  | Currency | Total expenditures on political activities spent by the charity *(Field no longer exists in T3010 version 24)* | 23 |
| `5031` |  | Currency | Total amount of 5030 gifts made for qualified donees *(Field no longer exists in T3010 version 24)* | 23 |
| `5032` |  | Currency | Total amount received from outside Canada that was directed to be spent on political activities. *(Field no longer exists in T3010 version 24)* | 23 |
| `2500` | Advertising | Short Text(1) | Fundraising method: Advertisements/prints/radio/TV commercials *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2510` | Auctions | Short Text(1) | Fundraising method: Auctions *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2530` | Collection Boxes | Short Text(1) | Fundraising method: Collection plates/boxes *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2540` | Door-to-Door | Short Text(1) | Fundraising method:  Door-to-door solicitation *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2550` | Lotteries | Short Text(1) | Fundraising method:  Draws/lotteries *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2560` | Fundraising Events | Short Text(1) | Fundraising method:  Fundraising dinners/galas/concerts *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2570` | Sales | Short Text(1) | Fundraising method:  Sales *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2575` | Internet | Short Text(1) | Fundraising method:  Internet *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2580` | Mail Campaigns | Short Text(1) | Fundraising method:  Mail campaigns *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2590` | Planned Giving | Short Text(1) | Fundraising method:  Planned-giving programs *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2600` | Corporate Sponsorships | Short Text(1) | Fundraising method:  Targeted corporate donations/sponsorships *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2610` | Targeted Contacts | Short Text(1) | Fundraising method:  Targeted contacts *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2620` | Phone/TV Solicitations | Short Text(1) | Fundraising method:  Telephone/TV solicitations *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2630` | Sporting Events | Short Text(1) | Fundraising method:  Tournament/sporting events *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2640` | Cause Marketing | Short Text(1) | Fundraising method:  Cause-related marketing *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2650` | Other Fundraising | Short Text(1) | Fundraising method:  Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2660` | Specify Fundraising | Short Text(175) | Other - Specify |  |
| `2700` | External Fundraisers | Short Text(1) | Did the charity pay external fundraisers? *(Value can be "Y", "N" or <empty>)* |  |
| `5450` | Fundraiser Gross Revenue | Currency | Gross revenue collected by fundraisers on behalf of the charity |  |
| `5460` | Fundraiser Payments | Currency | Total amount paid to or retained by the fundraisers |  |
| `2730` |  | Short Text(1) | Method of payment to fundraisers: Commissions *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2740` | Bonuses | Short Text(1) | Method of payment to fundraisers: Bonuses *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2750` | Commissions | Short Text(1) | Method of payment to fundraisers: Finder's fees *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2760` | Service Fee | Short Text(1) | Method of payment to fundraisers: Set fee for services *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2770` | Honoraria | Short Text(1) | Method of payment to fundraisers: Honoraria *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2780` | Other Payment | Short Text(1) | Method of payment to fundraisers: Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2790` | Specify Payment | Short Text(175) | Method of payment to fundraisers: Specify |  |
| `2800` | Fundraiser Tax Receipts | Short Text(1) | Did the fundraiser issue tax receipts on behalf of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `3200` | Director Compensation | Short Text(1) | Did the charity compensate any of its directors/trustees or like officials or persons not at arm's length from the charity for services provided during the fiscal period? *(Value can be "Y", "N" or... |  |
| `3400` | Employee Compensation | Short Text(1) | Did charity incur any expenses for compensation of employees during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `3900` | Foreign Donations ≥$10k | Short Text(1) | Did the charity receive any donations or gifts of any kind at $10,000 or more from donor who was not resident in Canada, not Canadian citzen or not liable to pay any income tax in Canada from emplo... |  |
| `4000` | Non-Cash Gifts | Short Text(1) | Did the charity receive any non-cash gifts (gifts-in-kind) for which it issued tax receipts? *(Value can be "Y", "N" or <empty>)* |  |
| `5800` | Non-Qualifying Security | Short Text(1) | Did the charity acquire a non-qualifying security? *(Value can be "Y", "N" or <empty>)* |  |
| `5810` | Donor Property Use | Short Text(1) | Did the charity allow any of its donors to use any of the charity's property during the fiscal period (except for permissable uses)? *(Value can be "Y", "N" or <empty>)* |  |
| `5820` | Third-Party Receipts | Short Text(1) | Did the charity issue any of its tax receipts for donations on behalf of another organization? *(Value can be "Y", "N" or <empty>)* |  |
| `5830` | Partnership Holdings | Short Text(1) | Did the charity have direct partnership holdings at any time during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `5840` | Grants to Grantees | Short Text(1) | Did the charity make qualifying disbursements by way of grants to non-qualified donees (grantees) in the fiscal period? *(Value can be "Y", "N" or <empty>)* | 26 |
| `5841` | Large Grants (>$5k) | Short Text(1) | Did the charity make grants to any grantees totalling more than $5000 in the fiscal period? *(Value can be "Y", "N" or <empty>)* | 26 |
| `5842` | Small Grantee Count | Number(10) | Enter the number of grantees that received grants totalling $5,000 or less in the fiscal period | 26 |
| `5843` | Small Grant Total | Currency(14) | Enter the total amount paid to grantees that received grants totalling $5,000 or less in the fiscal period | 26 |
| `5850` | DAF Held | Short Text(1) | In the 24 months prior to the beginning of the fiscal year, did the average value of your charity’s property (cash, investments, capital property or other assets) not used directly in its charitabl... | 27 |
| `5860` |  | Short Text(1) | Did the charity hold any donor advised funds (DAF) during the fiscal period? *(Value can be "Y", "N" or <empty>)* | 27 |
| `5861` | DAF Accounts | Number(10) | Total number of accounts held at the end of the fiscal period | 27 |
| `5862` | DAF Value | Currency(17) | Total value of all accounts held at the end of the fiscal period | 27 |
| `5863` | DAF Donations | Currency(17) | Total value of donations to DAF accounts received during the fiscal period | 27 |
| `5864` | DAF Disbursements | Currency(17) | Total value of qualifying disbursements from DAFs during the fiscal period | 27 |

## `financial_d` (alias `fd`)

Source tab: *Financial Section D, Schedule 6* — 86 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `Section Used  (D or 6)` |  | Short Text(1) | Section used to file the financial data Values: D=Section D, 6=Schedule 6 *(Value can be "D"or "6" .)* |  |
| `5030 indicator (C or 6)` |  | Short Text(1) | Indicates whether line 5030 is obtained from section C. *(Value can be "C" or <empty> (Schedule 6 copies the value from section C, if present).)* |  |
| `4020` | Accounting Basis | Short Text(1) | Was the financial information reported on an accrual or cash basis? *(Value can be "A" (Accrual), "C" (Cash) or <empty>.)* |  |
| `4050` | Land/Buildings Owned | Short Text(1) | Did the charity own land and/or buildings? *(Pertains to section D only.  Value can be "Y", "N" or <empty>.)* |  |
| `4100` | Cash & Investments | Currency | Cash, bank accounts and short-term investments |  |
| `4110` | Non-Arm's Receivables | Currency | Amounts receivable from non-arm's length parties |  |
| `4120` | Other Receivables | Currency | Amounts received from all others |  |
| `4130` | Non-Arm's Investments | Currency | Investments in non-arm's length parties |  |
| `4140` | Long-Term Investments | Currency | Long-term investments |  |
| `4150` | Inventory | Currency | Inventories |  |
| `4155` | Land/Buildings CA | Currency | Land and buildings in Canada |  |
| `4160` | Other CA Assets | Currency | Other capital assets in Canada |  |
| `4165` | Foreign Assets | Currency | Capital assets outside Canada |  |
| `4166` | Amortization | Currency | Accumulated amortization of capital assets |  |
| `4170` | Other Assets | Currency | Other assets |  |
| `4180` |  | Currency | 10 year gifts *(Removed from T3010 V27)* | 23,24,25,26 |
| `4200` | Total Assets | Currency | Total assets |  |
| `4250` |  | Currency | Amount included in lines 4150, 4155, 4160, 4165 and 4170 not used in charitable activities |  |
| `4300` |  | Currency | Accounts payable and accrued liabilities |  |
| `4310` |  | Currency | Deferred revenue |  |
| `4320` |  | Currency | Amounts owing to non-arm's length parties |  |
| `4330` |  | Currency | Other liabilities |  |
| `4350` | Total Liabilities | Currency | Total liabilities |  |
| `4400` | Non-Arm's Length | Short Text(1) | Did the charity borrow from, loan to, or invest assets with any non-arm's length parties? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4490` | Tax Receipts Issued | Short Text(1) | Did the charity issue tax receipts for gifts? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4500` | Tax-Receipted Gifts | Currency | Total eligible amount of tax-receipted gifts |  |
| `5610` | Tuition Revenue | Currency | Total eligible amount of tax-receipted tuition fees |  |
| `4505` |  | Currency | Total amount of 10 year gifts received *(Removed from T3010 V27)* | 23,24,25,26 |
| `4510` | Charity Revenue | Currency | Total amount received from other registered charities |  |
| `4530` | Non-Tax-Receipted Gifts | Currency | Total other gifts received for which a tax receipt was not issued by the charity (excluding amounts at lines 4575 and 4630) |  |
| `4540` | Federal Funding | Currency | Total revenue received from federal government |  |
| `4550` | Provincial Funding | Currency | Total revenue received from provincial/territorial governments |  |
| `4560` | Municipal Funding | Currency | Total revenue received from municipal/regional governments |  |
| `4565` | Government Funding | Short Text(1) | Did the charity receive any revenue from any level of Canadian government? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4570` | Gov Funding Total | Currency | Total amount revenue received from any level of Canadian government |  |
| `4571` | Foreign Tax Revenue | Currency | Total tax-receipted revenue from all sources outside of Canada (government and non-government) |  |
| `4575` | Foreign Non-Tax Revenue | Currency | Total non tax-receipted revenue from all sources outside of Canada (government and non-government) *(Field no longer exists in T3010 version 24)* |  |
| `4580` | Total Investment Income | Currency | Total interest and investment income received or earned |  |
| `4590` | Gross Asset Sales | Currency | Gross proceeds from disposition of assets |  |
| `4600` | Net Asset Sales | Currency | Net proceeds from disposition of assets |  |
| `4610` | Rental Income | Currency | Gross income received from rental of land and/or buildings |  |
| `4620` | Membership Revenue | Currency | Total non tax-receipted revenues received for memberships, dues and association fees |  |
| `4630` | Fundraising Revenue | Currency | Total non tax-receipted revenue from fundraising activities |  |
| `4640` | Sales Revenue | Currency | Total revenue from sale of goods and services (except to any level of Canadian government) |  |
| `4650` | Other Revenue | Currency | Other revenue (not already included in the amounts above) |  |
| `4655` | Other Revenue Type | Short Text(175) | Specify type(s) of revenue included in the amount reported at line 4650 |  |
| `4700` | Total Revenue | Currency | Total revenue |  |
| `4800` | Advertising Costs | Currency | Advertising and promotion |  |
| `4810` | Travel Costs | Currency | Travel and vehicle expenses |  |
| `4820` | Interest Expenses | Currency | Interest and bank charges |  |
| `4830` | License Fees | Currency | Licenses, memberships and dues |  |
| `4840` | Office Costs | Currency | Office supplies and expenses |  |
| `4850` | Occupancy Costs | Currency | Occupancy costs |  |
| `4860` | Consulting Fees | Currency | Charity's total expenditure on professional & consulting fees |  |
| `4870` | Training Costs | Currency | Education and training for staff and volunteers |  |
| `4880` | Total Comp Expenditure | Currency | Total expenditure on all compensation |  |
| `4890` | Donated Goods | Currency | Fair market value of all donated goods used in charity’s own activities |  |
| `4891` | Supplies/Assets | Currency | Total cost of all purchased supplies and assets |  |
| `4900` | Amortization Exp | Currency | Amortization of capitalized assets |  |
| `4910` | Research Grants | Currency | Research grants and scholarships as part of charity’s own activities |  |
| `4920` | Other Expenditures | Currency | All other expenditures not included in the amounts above (excluding gifts to qualified donees) |  |
| `4930` | Other Expenditure Types | Short Text(175) | Specify type(s) of expenditures included in amount reported at line 4920 |  |
| `4950` | Total Expenditures | Currency | Total expenditures (excluding qualifying disbursements) |  |
| `5000` | Charitable Activities | Currency | Total expenditures on charitable activities (of the amount at line 4950). |  |
| `5010` | Admin Total | Currency | Total expenditures on management and administration (of the amount at line 4950). |  |
| `5020` | Fundraising Costs | Currency | Total expenditures on fundraising (of the amount at line 4950). |  |
| `5030` |  | Currency | Total expenditures on political activities, inside or outside Canada (of the amount at line 4950). *(Field no longer exists in T3010 version 24)* | 23 |
| `5040` | Other Expenses | Currency | Total other expenditures (included in line 4950) |  |
| `5050` | Gifts to Donees | Currency | Total amount of gifts made to all qualified donees |  |
| `5100` | Total Expenses | Currency | Total expenditures (Add lines 4950 and 5050) |  |
| `5500` | Accumulated Funds | Currency | The amount accumulated for the fiscal period, including income earned on accumulated funds |  |
| `5510` | Disbursed Accumulated | Currency | The amount disbursed for the fiscal period for the specified purpose |  |
| `5750` | Quota Reduction | Currency | Pre-approved special reduction amount used in dispursement quota |  |
| `5900` | Prior Property Avg | Currency | Average value of property not used for charitable activities or administration during 24 months preceding the beginning of fiscal period |  |
| `5910` | Post Property Avg | Currency | Average value of property not used for charitable activities or administration during 24 months preceding the end of fiscal period |  |
| `5045` | Grants to Grantees | Currency | Total amount of grants made to all non-qualified donees (grantees) | 26 |
| `4101` | Cash | Currency(17) | Enter the total amounts in cash and bank accounts included on line 4100 | 27 |
| `4102` | Short-Term Investments | Currency(17) | Enter the value of all short-term investments included on line 4100 with an original term to maturity not greater than one year | 27 |
| `4157` | Program Use Assets | Currency(17) | Enter the cost or fair market value of all land and buildings in Canada used for the charity’s charitable programs or administration | 27 |
| `4158` | Non-Program Assets | Currency(17) | Enter the cost or fair market value of all land and buildings in Canada used for the charity’s charitable programs or administration | 27 |
| `4190` | Impact Investments | Currency(17) | Enter the value of all impact investments including those reported in any other line. For the purposes of this guide, impact investments are investments in companies or projects with the intention ... | 27 |
| `4576` | Impact Income | Currency(17) | Enter the amount from line 4580 that represents the total interest and other income the charity received or earned from impact investments | 27 |
| `4577` | Non-Arm's Income | Currency(17) | Enter the total amount from Line 4580 that represents the total amount of interest and investment income received from persons who do not deal at arm’s length with the charity | 27 |

## `schedule_1_foundations` (alias `s1`)

Source tab: *Sch1 Foundations* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `100` | Corporate Control | Short Text(1) | Did the foundation acquire control of a corporation during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `110` | Non-Operating Debt | Short Text(1) | Did the foundation incur any debts (during the fiscal period) other than for current operating expenses, purchasing or selling investments, or in administering charitable activities? *(Value can be... |  |
| `111` | Restricted Funds | Currency(17) | What was the total value of all restricted funds held at the end of the fiscal period? | 27 |
| `112` | Unspendable Funds | Currency(17) | Of that amount, what amount was the foundation not permitted to spend due to a funder's written trust or direction? | 27 |
| `120` | Non-Qualified Investments | Short Text(1) | During fiscal period, did the foundation hold any shares, rights to acquire shares, or debts owing to it that meet the definition of a non-qualified investment? *(Value can be "Y", "N" or <empty>)* |  |
| `130` | Excess Shareholding | Short Text(1) | Did the foundation own more than 2% of any class of shares of a corporation at any time during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |

## `schedule_2_summary` (alias `s2s`)

Source tab: *Sch2 Activities Outside Canada* — 10 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `200` | Foreign Expenditures | Currency | Total expenditures on activities/programs/projects carried on outside Canada, excluding qualifying disbursements |  |
| `210` | Foreign Transfers | Short Text(1) | Were any of the charity's financial resources spent on programs outside of Canada under any kind of an arrangement including a contract, agency agreement, or joint venture to any other individual o... |  |
| `220` | Foreign Countries | Short Text(1) | Were any projects undertaken outside Canada funded by Global Affairs Canada? *(Value can be "Y", "N" or <empty>)* |  |
| `230` | GAC Funding | Currency | Total amount of funds expended under programs funded by Global Affairs Canada |  |
| `240` | Global Affairs Funding | Short Text(1) | Were any of the charity's activities outside of Canada carried out by employees of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `250` | Employee-Led Abroad | Short Text(1) | Were any of the charity's activities outside of Canada carried out by volunteers of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `260` | Goods Exported | Short Text(1) | Did the charity export goods as part of its charitable activities? *(Value can be "Y", "N" or <empty>)* |  |

## `schedule_2_recipients` (alias `s2r`)

Source tab: *Sch2 Activities Recipient* — 7 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(9) | Sequential number reporting the external fundraiser *(New in November 2020 (R4.1))* |  |
| `Name of individual/organization` |  | Text(175) | Name of individual/org that receives the charity's resources which was included in line 200 *(New in November 2020 (R4.1))* |  |
| `Country` |  | Text(2) | Country code where the program is carried out *(New in November 2020 (R4.1))* |  |
| `Amount` |  | Currency(14) | Amount transferred from charity to individual/org *(New in November 2020 (R4.1))* |  |

## `schedule_2_countries` (alias `s2c`)

Source tab: *Sch2 Activities Country* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Short Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the country *(New in November 2020 (R4.1))* |  |
| `Charity's Program Country Code` |  | Short Text(2) | Country where charity carries on program or provide resources *(New in November 2020 (R4.1))* |  |

## `schedule_2_destinations` (alias `s2d`)

Source tab: *Sch2 Activities Export* — 8 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Short Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the export *(New in November 2020 (R4.1))* |  |
| `Item exported` |  | Short Text(30) | Item being exported *(New in November 2020 (R4.1))* |  |
| `Value (CAN)` |  | Currency | Value of item being exported |  |
| `Destination (city/region)` |  | Short Text(175) | Destination *(New in November 2020 (R4.1))* |  |
| `Country code` |  | Short Text(2) | Country code of exported item *(New in November 2020 (R4.1))* |  |

## `schedule_3_compensation` (alias `sc`)

Source tab: *Sch3 Compensation* — 16 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `300` | Full-Time Positions | Number(Long Integer) | Number of permanent, full-time, compensated positions in fiscal period, not including independent contractors |  |
| `305` |  | Number(Long Integer) | $1-39,999 (of the 10 highest compensated) |  |
| `310` |  | Number(Long Integer) | $40,000-$79,999 (of the 10 highest compensated) |  |
| `315` |  | Number(Long Integer) | $80,000-119,999 (of the 10 highest compensated) |  |
| `320` |  | Number(Long Integer) | $120,000-159,999 (of the 10 highest compensated) |  |
| `325` |  | Number(Long Integer) | $160,000-199,999 (of the 10 highest compensated) |  |
| `330` |  | Number(Long Integer) | $200,000-249,999 (of the 10 highest compensated) |  |
| `335` |  | Number(Long Integer) | $250,000-299,999 (of the 10 highest compensated) |  |
| `340` |  | Number(Long Integer) | $300,000-349,999 (of the 10 highest compensated) |  |
| `345` |  | Number(Long Integer) | $350,000-over (of the 10 highest compensated) |  |
| `370` | Part-Time Staff | Number(Long Integer) | The number of part-time or part-year employees the charity employed during the fiscal period. |  |
| `380` | Part-Time Costs | Currency | Total expenditure on compensation for part-time or part-year employees during the fiscal period. |  |
| `390` | Total Compensation | Currency | Total expenditure on all compensation during the fiscal period. |  |

## `schedule_5_noncash` (alias `s5`)

Source tab: *Sch5 NonCash Gifts* — 18 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `500` |  | Short Text(1) | Charity issued receipts for artwork wine jewellery *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `505` |  | Short Text(1) | Charity issued receipts for building materials *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `510` |  | Short Text(1) | Charity issued receipts for clothing/furniture/food *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `515` |  | Short Text(1) | Charity issued receipts for vehicles *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `520` |  | Short Text(1) | Charity issued receipts for cultural properties *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `525` |  | Short Text(1) | Charity issued receipts for ecological properties *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `530` |  | Short Text(1) | Charity issued receipts for life insurance policies *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `535` |  | Short Text(1) | Charity issued receipts for medical equipment/supplies *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `540` |  | Short Text(1) | Charity issued receipts for privately-held securities *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `545` |  | Short Text(1) | Charity issued receipts for machinery/equipment/computers/software *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `550` |  | Short Text(1) | Charity issued receipts for publicly traded securities/commodities/mutual funds *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `555` |  | Short Text(1) | Charity issued receipts for books *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `560` |  | Short Text(1) | Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `565` |  | Short Text(175) | Specify for others |  |
| `580` |  | Currency | Total amount of tax-receipted gifts in kind |  |

## `schedule_7_desc` (alias `s7d`)

Source tab: *Sch7 Desc* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23, 24 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23, 24 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23, 24 |
| `Political Activities Description` |  | Long Text | Describe the charity's political activities, including gifts to qualified donees intended for political activities, and explain how these relate to its charitable purposes. *(Column only populated ... | 23 |
| `Public Policy Description` |  | Long Text | Describe the charity’s public policy dialogue and development activities, and explain how these relate to its stated charitable purposes. *(Column only populated if Form ID = 24)* | 24 |

## `schedule_7_political_fund` (alias `s7f`)

Source tab: *Sch7 Political Activities Fund* — 7 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23 |
| 🔑 `Sequence Number` |  | Number(Long Integer) | Sequence number for political activities funded from outside of Canada | 23 |
| `Political Activity Description` |  | Short Text(175) | Description of the political activity funded from outside of Canada | 23 |
| `Funding Amount` |  | Currency | The amount received from the country outside Canada (CAN$) | 23 |
| `Country Code` |  | Short Text(2) | Country code from which the funding was received | 23 |

## `schedule_7_political_res` (alias `s7r`)

Source tab: *Sch7 Political Activities Res* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23 |
| 🔑 `Line Number (700 to 708)` |  | Number(Integer) | The way the charity participated in or carried out political activities during the fiscal period. *(This is sequence number field where the values will reflect line numbers 700 to 708.)* | 23 |
| `Staff Used?` |  | Short Text(1) | "X" if staff resource is used *(Value can be "X" or <empty>)* | 23 |
| `Volunteers Used?` |  | Short Text(1) | "X" if volunteers resource is used *(Value can be "X" or <empty>)* | 23 |
| `Financial Resource Used?` |  | Short Text(1) | "X" if financial resource is used *(Value can be "X" or <empty>)* | 23 |
| `Property Resource Used?` |  | Short Text(1) | "X" if property resource is used *(Value can be "X" or <empty>)* | 23 |
| `Other Descriptions` |  | Short Text(175) | Description of other way the charities participated in or carried out political activities (only applicable to line 708). | 23 |

## `gift` (alias `g`)

Source tab: *Gift* — 14 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the gifts. |  |
| `Associated charity (Y/N)` |  | Short Text(1) | Is qualified donee an associated charity? *(Value can be "Y", "N" or <empty>)* |  |
| `Donee Business number` |  | Short Text(15) | Business number of qualified donee, if a charity. |  |
| `Donee Name` |  | Short Text(60) | Name of qualified donee. |  |
| `City` |  | Short Text(30) | Donee's city |  |
| `Province` |  | Short Text(2) | Donee's province |  |
| `Total amount gifts` |  | Currency | Total amount of gifts |  |
| `Amount of gifts in kind` |  | Currency | Amount of non-cash gifts (gifts-in-kind) |  |
| `Number of donees` |  | Number(Long Integer) | Number of reported donees |  |
| `Gift for Political Activities?` |  | Short Text(1) | Was any part of the gift intended for political activities? *(Value can be "Y", "N" or <empty>)* | 23 |
| `Political Activities Gift Amount` |  | Currency | Total amount of gifts intended for political activities *(Is entered if "Y" is answered for above indicator.)* | 23 |

## `programs` (alias `p`)

Source tab: *New and Ongoing Programs* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Program type OP=ongoing program NP=new program NA=not active` |  | Short Text(2) | OP = Active Ongoing program ; NP = New Program; NA = Not Active |  |
| `Program Description` |  | Long Text | Program activity freeform text description. |  |

## `trustee` (alias `t`)

Source tab: *Trustee* — 11 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Officer Number` |  | Number(Long Integer) | Sequence number - maximum of 10 officer names |  |
| `Last Name` |  | Short Text(30) | Officer/director or trustee last name |  |
| `First Name` |  | Short Text(30) | Officer/director or trustee first name |  |
| `Initial` |  | Short Text(3) | Initial of director or trustee |  |
| `Position` |  | Short Text(30) | Officer/director or trustee position |  |
| `At arm's length` |  | Short Text(1) | Is the director at arm’s length? *(Value can be "Y", "N" or <empty>)* |  |
| `Appointed Date` |  | Date/Time | Date the director/officer was appointed to this title/postion |  |
| `Ceased Date` |  | Date/Time | End date of director/officer occupying title/postion |  |

## `grants` (alias `gn`)

Source tab: *Grants to Non-Qualified Donees* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 26 |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal period end date | 26 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 26 |
| 🔑 `Sequence Number` |  | Number(10) | Sequence number to uniquely identify each grant recipient for a BN/FPE | 26 |
| `Grant Recipient Name` |  | Text(175) | Name of non-qualified donee | 26 |
| `Grant Purpose` |  | Text(1250) | Description of the purpose for the qualifying disbursements to non-qualified donee | 26 |
| `Amount of Cash Disbursed` |  | Currency(14) | Cash amount disbursed to non-qualified donee | 26 |
| `Amount of non-cash Disbursed` |  | Currency(14) | Non-cash amount disbursed to non-qualified donee | 26 |
| `Grant Country` |  | Text(125) | List of grant countries | 26 |

## `schedule_8_disbursement` (alias `s8`)

Source tab: *Disbursement Quota* — 21 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 27 |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal period end date | 27 |
| `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 27 |
| `Line 805` |  | Currency(17) | Average value of property not used in charitable activities or administration (line 5900 from your return) | 27 |
| `Line 810` |  | Currency(17) | If permission to accumulate property has been granted, enter the total amount accumulated less all disbursements made for the specified purpose (add all amounts from lines 5500 minus all amounts at... | 27 |
| `Line 815` |  | Currency(17) | Must display the total of The amount at line 805 minus the amount at line 810 - “Line 1 minus line 2 (if negative, enter 0)” | 27 |
| `Line 820` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must display the total of line 815 multiplied by 3.5%;  If the amount at line 3 is more than 1,000,000, Must remain blank | 27 |
| `Line 825` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 815 minus $1,000,000 | 27 |
| `Line 830` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 825 multiplied by 5% | 27 |
| `Line 835` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 825 multiplied by 5% | 27 |
| `Line 840` |  | Currency(17) | Must be pre-populated with the amount from line 820 or 835 from Page 1 of Schedule 8 “Enter the amount from line 820 or line 835. This is your charity's disbursement quota requirement for the curre... | 27 |
| `Line 845` |  | Currency(17) | Must be pre-populated with the amount from line 5000 from Schedule 6 of this return “Total expenditures on charitable activities (line 5000 of your return)” | 27 |
| `Line 850` |  | Currency(17) | Must be pre-populated with the amount from line 5045 from Schedule 6 of this return “Total amount of grants made to non-qualified donees (line 5045 of your return)” | 27 |
| `Line 855` |  | Currency(17) | Must be pre-populated with the amount from line 5050 from Schedule 6 of this return “Total amount of gifts made to qualified donees (line 5050 of your return)” | 27 |
| `Line 860` |  | Currency(17) | Must display the total of adding lines 845, 850 and 855 | 27 |
| `Line 865` |  | Currency(17) | Must display the total of subtracting line 860 from line 840 “Line 860 minus line 840. This is your charity’s disbursement quota excess or shortfall for the current fiscal period.” | 27 |
| `Line 870` |  | Currency(17) | Must be pre-populated with the amount from line 5910 from Schedule 6 of this return “Average value of property not used in charitable activities or administration prior to the next fiscal period (l... | 27 |
| `Line 875` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must display the total of line 870 multiplied by 3.5% If the amount at line 870 is more than 1,000,000, Must remain blank “The amount s... | 27 |
| `Line 880` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 870 minus $1,000,000 | 27 |
| `Line 885` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 880 multiplied by 5% | 27 |
| `Line 890` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 885 plus $35,000 “The amount shown o... | 27 |

---

## Line Number Index (sortable, 162 entries)

From the T3010 Line Number and Contents Index 2024. Use this when a user references a "line 4700" style question — the Short column gives a compact label suitable for explanations.

| Line | Short | Full Question |
|---|---|---|
| `100` | Corporate Control | Foundation acquired corporate control? |
| `110` | Non-Operating Debt | Foundation non-operating debt? |
| `111` | Restricted Funds | Total restricted funds value |
| `112` | Unspendable Funds | Restricted funds unspendable |
| `120` | Non-Qualified Investments | Held non-qualified investments? |
| `130` | Excess Shareholding | Owned >2% of corporate shares? |
| `1510` | Subordinate to Head Body | Was the charity in a subordinate position to a head body? |
| `1570` | Wound-Up/Dissolved | Has the charity wound-up, dissolved, or terminated operations? |
| `1600` | Foundation Designation | Is the charity designated as a public foundation or private foundation? |
| `1800` | Active | Was the charity active during the fiscal period? |
| `200` | Foreign Expenditures | Foreign activity expenditures |
| `2000` | Gifts to Qualified Donees | Did the charity make gifts/transfers to qualified donees? |
| `210` | Foreign Transfers | Transferred funds to foreign entities? |
| `2100` | Foreign Activities | Did the charity conduct activities outside Canada? |
| `220` | Foreign Countries | Countries where programs conducted |
| `230` | GAC Funding | Global Affairs funding total |
| `240` | Global Affairs Funding | Funded by Global Affairs Canada? |
| `250` | Employee-Led Abroad | Foreign activities via employees? |
| `2500` | Advertising | Fundraising method: Advertisements/print/radio/TV |
| `2510` | Auctions | Fundraising method: Auctions |
| `2530` | Collection Boxes | Fundraising method: Collection plates/boxes |
| `2540` | Door-to-Door | Fundraising method: Door-to-door solicitation |
| `2550` | Lotteries | Fundraising method: Draws/lotteries |
| `2560` | Fundraising Events | Fundraising method: Dinners/galas/concerts |
| `2570` | Sales | Fundraising method: Sales |
| `2575` | Internet | Fundraising method: Internet |
| `2580` | Mail Campaigns | Fundraising method: Mail campaigns |
| `2590` | Planned Giving | Fundraising method: Planned-giving programs |
| `260` | Volunteer-Led Abroad | Foreign activities via volunteers? |
| `260` | Goods Exported | Exported goods for charity? |
| `2600` | Corporate Sponsorships | Fundraising method: Corporate sponsorships |
| `2610` | Targeted Contacts | Fundraising method: Targeted contacts |
| `2620` | Phone/TV Solicitations | Fundraising method: Telephone/TV solicitations |
| `2630` | Sporting Events | Fundraising method: Tournaments/sporting events |
| `2640` | Cause Marketing | Fundraising method: Cause-related marketing |
| `2650` | Other Fundraising | Fundraising method: Other |
| `2660` | Specify Fundraising | Specify other fundraising method |
| `2700` | External Fundraisers | Did the charity pay external fundraisers? |
| `2740` | Bonuses | Payment method: Bonuses |
| `2750` | Commissions | Payment method: Commissions |
| `2760` | Service Fee | Payment method: Set fee for services |
| `2770` | Honoraria | Payment method: Honoraria |
| `2780` | Other Payment | Payment method: Other |
| `2790` | Specify Payment | Specify other payment method |
| `2800` | Fundraiser Tax Receipts | Fundraiser issued tax receipts? |
| `300` | Full-Time Positions | Permanent full-time positions count |
| `3200` | Director Compensation | Compensation to directors/trustees? |
| `3400` | Employee Compensation | Employee compensation expenses? |
| `370` | Part-Time Staff | Part-time/seasonal employees count |
| `380` | Part-Time Costs | Part-time compensation total |
| `390` | Total Compensation | Total compensation expenses |
| `3900` | Foreign Donations ≥$10k | Foreign donations ≥$10k? |
| `4000` | Non-Cash Gifts | Non-cash gifts with receipts? |
| `4020` | Accounting Basis | Financial info basis (accrual/cash) |
| `4050` | Land/Buildings Owned | Own land/buildings? |
| `4100` | Cash & Investments | Cash/bank/short-term investments |
| `4101` | Cash | Cash and bank accounts |
| `4102` | Short-Term Investments | Short-term investments |
| `4110` | Non-Arm's Receivables | Receivables from non-arm's length |
| `4120` | Other Receivables | Receivables from others |
| `4130` | Non-Arm's Investments | Investments in non-arm's length |
| `4140` | Long-Term Investments | Long-term investments |
| `4150` | Inventory | Inventories |
| `4155` | Land/Buildings CA | Land/buildings in Canada |
| `4157` | Program Use Assets | Used for programs/admin |
| `4158` | Non-Program Assets | Used for other purposes |
| `4160` | Other CA Assets | Other capital assets in Canada |
| `4165` | Foreign Assets | Capital assets outside Canada |
| `4166` | Amortization | Accumulated amortization |
| `4170` | Other Assets | Other assets |
| `4190` | Impact Investments | Impact investments |
| `4200` | Total Assets | Total assets |
| `4350` | Total Liabilities | Total liabilities |
| `4400` | Non-Arm's Length | Transactions with non-arm's length? |
| `4490` | Tax Receipts Issued | Issued tax receipts for gifts? |
| `4500` | Tax-Receipted Gifts | Tax-receipted gifts total |
| `4510` | Charity Revenue | Revenue from other charities |
| `4530` | Non-Tax-Receipted Gifts | Non-tax-receipted gifts |
| `4540` | Federal Funding | Federal government revenue |
| `4550` | Provincial Funding | Provincial/territorial revenue |
| `4560` | Municipal Funding | Municipal/regional revenue |
| `4565` | Government Funding | Received government revenue? |
| `4570` | Gov Funding Total | Total government funding |
| `4571` | Foreign Tax Revenue | Foreign tax-receipted revenue |
| `4574` | Foreign Tax Rev | Foreign tax-receipted revenue |
| `4575` | Foreign Non-Tax Revenue | Foreign non-tax-receipted revenue |
| `4576` | Impact Income | Impact investment income |
| `4577` | Non-Arm's Income | Non-arm's length investment income |
| `4580` | Total Investment Income | Total interest/investment income |
| `4590` | Gross Asset Sales | Gross proceeds from asset sales |
| `4600` | Net Asset Sales | Net proceeds from asset sales |
| `4610` | Rental Income | Rental income from land/buildings |
| `4620` | Membership Revenue | Membership/dues revenue |
| `4630` | Fundraising Revenue | Fundraising revenue (non-tax) |
| `4640` | Sales Revenue | Goods/services sales revenue |
| `4650` | Other Revenue | Other revenue |
| `4655` | Other Revenue Type | Specify other revenue type |
| `4700` | Total Revenue | Total revenue |
| `4800` | Advertising Costs | Advertising/promotion costs |
| `4810` | Travel Costs | Travel/vehicle expenses |
| `4820` | Interest Expenses | Interest/bank charges |
| `4830` | License Fees | Licenses/memberships/dues |
| `4840` | Office Costs | Office supplies/expenses |
| `4850` | Occupancy Costs | Occupancy costs |
| `4860` | Consulting Fees | Professional/consulting fees |
| `4870` | Training Costs | Staff/volunteer training |
| `4880` | Total Comp Expenditure | Total compensation (from S3) |
| `4890` | Donated Goods | FMV of donated goods used |
| `4891` | Supplies/Assets | Purchased supplies/assets |
| `4900` | Amortization Exp | Amortization expense |
| `4910` | Research Grants | Research grants/scholarships |
| `4920` | Other Expenditures | Other expenditures |
| `4930` | Other Expenditure Types | Specify other expenditures |
| `4950` | Total Expenditures | Total expenditures (excl. disbursements) |
| `5000` | Charitable Spending | Expenditures on charitable activities |
| `5000` | Charitable Activities | Charitable activities total |
| `5010` | Admin Costs | Management/admin costs |
| `5010` | Admin Total | Management/admin total |
| `5020` | Fundraising Costs | Fundraising costs total |
| `5040` | Other Expenses | Other expenditures total |
| `5045` | Grants to Grantees | Grants to non-qualified donees |
| `5050` | Gifts to Donees | Gifts to qualified donees |
| `5100` | Total Expenses | Total expenditures |
| `5450` | Fundraiser Gross Revenue | Gross revenue collected by fundraisers |
| `5460` | Fundraiser Payments | Amounts paid/retained by fundraisers |
| `5500` | Accumulated Funds | Accumulated property amount |
| `5510` | Disbursed Accumulated | Disbursed accumulated funds |
| `5610` | Tuition Revenue | Tax-receipted tuition fees |
| `5750` | Quota Reduction | Disbursement quota reduction |
| `5800` | Non-Qualifying Security | Acquired non-qualifying security? |
| `5810` | Donor Property Use | Donor use of charity property? |
| `5820` | Third-Party Receipts | Issued receipts for another org? |
| `5830` | Partnership Holdings | Direct partnership holdings? |
| `5840` | Grants to Grantees | Grants to non-qualified donees? |
| `5841` | Large Grants (>$5k) | Grants >$5k to grantees? |
| `5842` | Small Grantee Count | Number of grantees ≤$5k |
| `5843` | Small Grant Total | Total grants ≤$5k |
| `5850` | DAF Held | Held donor advised funds (DAF)? |
| `5861` | DAF Accounts | DAF accounts count |
| `5862` | DAF Value | DAF total value |
| `5863` | DAF Donations | DAF donations received |
| `5864` | DAF Disbursements | DAF qualifying disbursements |
| `5900` | Prior Property Avg | Avg property not used (24mo prior) |
| `5910` | Post Property Avg | Avg property not used (24mo after) |
| `805` | Quota Base | Disbursement quota base amount |
| `810` | Net Accumulated | Accumulated funds net |
| `815` | Adjusted Base | Adjusted quota base |
| `820` | Quota 3.5% | Quota (≤$1M): 3.5% |
| `825` | Excess Over $1M | Excess over $1M |
| `830` | Quota 5% | Quota (>$1M): 5% |
| `835` | Total Quota | Total quota (>$1M) |
| `840` | Final Quota | Final disbursement quota |
| `845` | Charitable Total | Charitable spending total |
| `850` | Grants Total | Grants to grantees total |
| `855` | Gifts Total | Gifts to donees total |
| `860` | Total Disbursements | Total qualifying disbursements |
| `865` | Quota Balance | Quota excess/shortfall |
| `870` | Next Quota Base | Next period quota base |
| `875` | Next Quota 3.5% | Next quota (≤$1M): 3.5% |
| `880` | Next Excess | Next excess over $1M |
| `885` | Next Quota 5% | Next quota (>$1M): 5% |
| `890` | Next Total Quota | Next total quota (>$1M) |


---

# Section 4 — Data Interpretation Guide (from docs/context/data-interpretation-guide.md)

> Original location: `docs/context/data-interpretation-guide.md`. Encodes Blumbergs domain expertise on how to read each field type.

# T3010 Data Interpretation Guide

> Synthesized from 14 years of Blumbergs Snapshot publications (2010-2023), designation-specific snapshots, and T3010 form analysis. Use this guide when querying or analyzing the CRA T3010 database.

## Revenue Fields (Section D — financial_d)

### Total Revenue (Line 4700)
- Represents all sources: tax-receipted gifts, government, program fees, investment income, other
- 2023 sector total: $393B. Growth from $212B (2011) driven primarily by provincial government transfers
- Majority of revenue is concentrated in a small number of large charities (hospitals, universities, social service agencies)

### Government Funding (Lines 4540, 4550, 4560)
- **4540** = Federal government revenue
- **4550** = Provincial/territorial government revenue (the largest — typically 85-90% of total government)
- **4560** = Municipal/regional government revenue
- **4570** = Total government (DO NOT USE — unreliable). Always compute as `4540 + 4550 + 4560`
- Government funding is 62-70% of total sector revenue, trending upward over time
- Provincial governments dominate: in 2023, $225.6B of $252B total government funding
- Most government funding goes to healthcare and education charities (designation C)

### Revenue from Outside Canada (Lines 4575, 4580 — V24 only)
- New questions added in T3010 Version 24 (fiscal periods ending Dec 31, 2023+)
- 2023 data is partial: only ~48,418 charities (Dec 31 year-ends) answered these questions
- 2024 data will be the first complete year for these fields
- In 2023: $4.1B received from outside Canada (up from $2.6B in 2019)

### Tax-Receipted Donations (Line 4500)
- Official donation receipts issued by charities
- 2023: $23.4B total. Steady growth from $14.6B (2013)
- Private foundations receive a disproportionate share: $3.4B (2021) for just 6,153 charities
- About 1 in 10 donated dollars now goes to DAFs rather than directly to operating charities

### Gifts from Other Charities (Line 4510)
- Inter-charity transfers. Important for understanding the flow of funds between foundations and operating charities
- About 30,000 charities make gifts to other qualified donees each year

## Expenditure Fields

### Charitable Program Expenditures (Line 5000)
- Spending on the charity's own charitable programs
- The largest expenditure category for most charities

### Management & Admin (Line 5010) and Fundraising (Line 5020)
- Self-reported categories — highly subjective and frequently misreported
- Some charities deliberately classify fundraising costs as charitable programs
- Use ratios with caution: a 0% fundraising ratio often means misclassification, not efficiency

### Gifts to Qualified Donees (Line 5050)
- Transfers to other registered charities, the Crown, and other qualified donees
- Critical for understanding foundation grantmaking patterns
- Private foundations: $2.45B in gifts to QDs (2019) on $74.5B in assets

### Grants to Non-Qualified Donees (Line 5045)
- Payments to organizations that are not qualified donees (e.g., foreign NGOs)
- Requires direction and control or joint venture arrangements
- Tracked in the `grants` table (14,101 records in 2024 data)

### Total Compensation (Line 4880 / Schedule 3 Line 390)
- Line 4880 in financial_d mirrors Schedule 3 line 390 (may differ slightly)
- 2023: $199B total. Represents ~56% of sector expenditures
- Schedule 3 also provides FT/PT employee counts (lines 300/370) — these are BIGINT, not currency-formatted

### Total Expenditures (Line 5100)
- Sum of all expenditure lines

## Balance Sheet Fields

### Total Assets (Line 4200) and Cash (Line 4100)
- 2024 database: total assets across all charities exceed $450B
- Private foundations alone held ~$95B in assets (as of 2021 pre-budget submission data)

### Total Liabilities (Line 4350)
- Important for computing net assets

## Designation-Specific Patterns

### Charitable Organizations (Designation C — ~85%)
- ~71,918 charities. The vast majority of the sector
- Receive most government funding. Deliver most direct services
- Include hospitals, universities, churches, social service agencies
- Revenue dominated by provincial government transfers (healthcare, education)

### Private Foundations (Designation B — ~8%)
- ~6,738 charities. Primarily grantmaking entities
- Very little government funding (1.25% of revenue in 2021)
- Hold ~$95B+ in assets. Many give out only the DQ minimum (3.5%, raised to 5% in 2023)
- Only ~10% have employment expenses; most are run by volunteers/family
- $3.4B in tax-receipted donations issued (2021)
- The largest private foundation gave out only 1% of assets (2019)

### Public Foundations (Designation A — ~6%)
- ~4,619 charities. Includes community foundations, hospital foundations, university foundations
- Moderate government funding (6.7% of revenue in 2021)
- $14.9B total revenue, $8.3B expenditures (2021)
- More likely to employ staff than private foundations (27% have employment expenses)
- Community foundations often operate DAFs

## Foreign Activities (Schedule 2)

- About 5,000 charities conduct activities outside Canada
- Total foreign spending: $5.3B (2023), up from $3B (2013)
- Schedule 2 tracks: countries of operation, recipients, contractual relationships
- Global Affairs Canada (formerly CIDA/DFATD) funded ~139 charities (2023)
- Number of charities receiving government funding for foreign work has declined (from 218 in 2013)

## Compensation (Schedule 3)

- Lines 300/370 = FT/PT employee counts (BIGINT — no currency formatting)
- Line 390 = Total compensation (VARCHAR — has `$` and `,` formatting)
- Raw employee count data is unreliable: 2013 raw data suggested 1.86M FT employees, revised to 1.38M
- About 52% of charities have employment expenses; 48% are entirely volunteer-run
- Compensation concentration: a few large employers (hospitals, universities) account for most of the $199B total

## DAF Fields (Lines 5860-5864 in financial_abc)

- **5860**: Did the charity hold any DAFs? (Y/N)
- **5861**: Number of DAF accounts
- **5862**: Total value of all DAF accounts
- **5863**: Donations received into DAF accounts
- **5864**: Qualifying disbursements from DAFs
- New in V24 (2023+). 2024 is first complete year: 834 charities, $16.6B total value
- More money flows into DAFs than out: $3.2B in vs $1.9B out (2024), 58% gift-to-donation ratio
- Top DAFs by value: Charitable Gift Funds Canada ($2.4B), Jewish Community Foundation of Montreal ($2.1B), Winnipeg Foundation ($1.0B)
- Transpositional errors are common in DAF reporting

## Political Activities (Lines 2400, 5030-5032 — removed after 2019)

- Tracked on Schedule 7 from 2013-2019, then removed
- Peak: 791 charities reported political activities in 2019, spending ~$30M
- The political spending field (line 5030) was the "most frequently incorrectly answered question on the T3010"
- 2013 raw data showed $171M in political spending; actual was ~$26M after corrections
- Most common method: staff using website or social media (line 706)
- Foreign funding for political activities (line 5032): minimal — $229K in 2013
- No transparency on political activities since 2019

## Data Type Gotchas

### Currency Fields are VARCHAR
All financial fields in the raw tables use format `"$1,234,567"`. Convert with:
```sql
TRY_CAST(REPLACE(REPLACE(column, '$', ''), ',', '') AS DECIMAL)
```
Use `TRY_CAST` (not `CAST`) because some rows contain non-numeric values (letters, blanks, special characters).

### Schedule 3 Mixed Types
- Lines 300/370 (employee counts) are BIGINT — do not apply REPLACE()
- Line 390 (total compensation) is VARCHAR with currency formatting — needs REPLACE()

### BN Column Name Inconsistency
- Some tables: `"BN/Registration Number"` (capital N)
- Other tables: `"BN/Registration number"` (lowercase n)
- Use views (`v_financial_d`, etc.) which normalize to `bn`

### NULL vs Zero vs Blank
- Charities that don't answer a question may have NULL, blank string, or "$0"
- A zero in a government funding field usually means "not applicable" rather than "received $0"
- Use LEFT JOINs from ident/charity_base — not all charities appear in every table


---

# Section 5 — Methodology & Caveats (from docs/context/methodology-notes.md)

> Original location: `docs/context/methodology-notes.md`. Snapshot methodology and known data-quality caveats.

# Blumbergs Snapshot Methodology and Data Quality Notes

> Synthesized from the "Limitations and Caveats" sections of Blumbergs Snapshot publications (2010-2023) and T3010 form analysis. Use this guide to understand the limitations of any analysis performed on T3010 data.

## Data Source

The T3010 Registered Charity Information Return is filed annually by all Canadian registered charities with the Canada Revenue Agency (CRA). The CRA publishes the data through the Charities Listing database. Blumbergs also maintains CharityData.ca with up to 20 years of historical data per charity.

### Coverage
- There are approximately 86,000 registered charities in Canada
- In any given year, 82,000-84,000 file their T3010 and are processed into the database
- The gap represents late filers, newly registered charities not yet processed, and charities in the process of revocation for non-filing
- Charities must file within 6 months of their fiscal year-end to maintain registration

### Database Lag
- CRA typically processes T3010 data 12-24 months after the fiscal year-end
- The 2023 Snapshot was published April 2025, covering data filed throughout 2024
- This means the "latest" data always reflects economic conditions from 1-2 years prior

## Reliability Caveats

### 1. Self-Reported and Unverified
The T3010 is completed by the charity and signed by one person. CRA does not independently verify the information when it is posted on the CRA site or placed in the database.

### 2. Completed by Non-Experts
The T3010 is often completed by "volunteers or others who may have little understanding of the nuances of the Income Tax Act (Canada), limited language skills, may not have easy access to the correct information or are in a hurry to file the form to avoid deregistration." (Blumbergs, 2023)

### 3. Larger Institutions: More Accurate but More Complex
For larger institutions, accountants or finance staff typically prepare the T3010. Greater accuracy is expected, but "as they also tend to be more complicated and involve bigger numbers, the likelihood of a significant inaccuracy in their T3010 filings is great." (Blumbergs, 2022)

### 4. CRA Processing Errors
T3010s filed on paper need to be coded by hand at CRA, which can introduce mistakes. Only a small number use 2D barcode technology. Electronic filing (available since June 2019) should reduce processing errors over time, but many charities still file on paper.

### 5. Deliberate Misreporting
"In some cases, those completing the T3010 for a charity are deliberately deceptive when completing the T3010. For example, an organization knows that it has substantial fundraising expenses but chooses to put them under charitable activities. Or, an organization claims pharmaceuticals that it can purchase for $50,000 are really worth $50 million." (Blumbergs, 2022)

### 6. Subjective Classifications
Several T3010 fields require subjective judgment:
- **Program vs. fundraising expenditures**: Charities frequently classify fundraising costs as program spending
- **Political activities**: Was the "most frequently incorrectly answered question on the T3010" — the 2013 raw figure of $171M was revised to ~$26M after manual review
- **Employee counts**: 2013 raw data suggested 1.86M FT employees; revised to 1.38M after scrutiny
- **Gifts in kind valuation**: Particularly problematic for pharmaceutical donations

### 7. Tax Form, Not Management Report
"The T3010 is a tax form which is supposed to be completed according to guidance provided by the CRA in Guide Completing the Registered Charity Information Return (T-4033)." It uses Income Tax Act definitions, which may differ from how charities internally categorize their activities.

## Known Data Quality Issues

### Line 4570 (Total Government Funding)
- The pre-computed total in the database is unreliable
- Always compute manually as: line 4540 + line 4550 + line 4560
- Our validation confirms: computed total ($284.7B) differs dramatically from the reported 4570 value ($350M) in the 2024 data

### Employee Count Data (Schedule 3, Lines 300/370)
- Systematically overstated due to data entry errors
- Blumbergs routinely revises the raw counts downward (e.g., 2013: 1.86M raw → 1.38M revised for FT)
- Use the published Snapshot figures rather than raw database aggregates for employee counts

### Political Activity Spending (Line 5030)
- The most error-prone field on the entire T3010
- Raw aggregates are typically 5-7x the actual figure
- Common error: charities enter total charitable spending instead of just political spending
- Questions removed entirely after 2019 — no political activity data available for 2020+

### DAF Fields (Lines 5860-5864)
- New in V24 (2023). First complete year is 2024
- Transpositional errors common: "a group with $31,000 in total DAF assets probably does not have 30,000 DAFs"
- Some charities report restricted gifts as DAFs when they technically aren't
- Some charities that have DAFs don't report them

### Compensation Line 390 vs Line 4880
- Schedule 3 line 390 and financial_d line 4880 should match but may differ slightly
- Both represent total compensation; use whichever is available

## T3010 Form Versions

### Version History
The T3010 has gone through several revisions, tracked in `lookup_form_versioning`:
- Pre-2013: Older form structure
- 2013+: T3010 (13) — added Schedule 7 (Political Activities), revised foreign activities questions
- 2019+: Electronic filing available
- 2023+: T3010 Version 24 — significant changes

### V23 to V24 Transition (2023 Data)
- Charities with fiscal periods ending Dec 31, 2023+ filed using V24
- Charities with fiscal periods ending before Dec 30, 2023 filed using V23
- ~48,418 charities have Dec 31 year-ends and thus used V24
- V24 added: DAF questions (5860-5864), revenue from outside Canada (4575, 4580), and other new fields
- 2023 data is therefore a mix of V23 and V24 responses
- 2024 data is all V24 — the first fully comparable year for new fields

## Snapshot Methodology

### How Blumbergs Produces Snapshots
1. Obtain the complete T3010 database from CRA (CSV files)
2. Load into a database and compute aggregate statistics
3. Manually review outliers and correct known errors (e.g., political spending, employee counts)
4. Cross-reference with prior years for consistency
5. Publish highlights with explicit caveats

### What Blumbergs Does NOT Do
- Does not independently verify individual T3010 filings
- Does not contact charities to confirm reported figures
- Does not adjust for inflation or population growth in trend comparisons
- Does not reconcile T3010 data with provincial financial statements or audited reports

### Interpretation Guidelines from Blumbergs
- "Don't rely on any of this information without checking with the charity and appropriate due diligence as required"
- Use T3010 data for sector-level trends and patterns, not as definitive figures for individual charities
- Treat exact dollar amounts as approximate, especially for smaller charities
- Focus on relative patterns (ratios, rankings, trends) rather than absolute precision


---

# Section 6 — Sector Trends (from docs/context/sector-trends.md)

> Original location: `docs/context/sector-trends.md`. Multi-year baselines 2010–2023.

# Canadian Charity Sector Trends (2010-2023)

> Historical baselines from 14 years of Blumbergs Snapshot publications. Use these figures to contextualize analysis of any single year's data and to validate computed aggregates against published benchmarks.

## Headline Metrics by Year

| Year | Charities Filed | Revenue ($B) | Expenditures ($B) | Govt Revenue ($B) | Govt % | Compensation ($B) | Tax Receipts ($B) |
|------|----------------|-------------|-------------------|-------------------|--------|-------------------|-------------------|
| 2010 | 84,137 | — | — | — | — | — | — |
| 2011 | ~82,000 | 212 | 205 | — | — | — | — |
| 2012 | ~85,000 | 223 | 218 | — | — | — | — |
| 2013 | 83,466 | 237 | 225 | 160.0 | ~68% | 129 | 14.6 |
| 2014 | 84,521 | 246 | 228 | 165.9 | ~67% | 134 | 15.7 |
| 2015 | 84,442 | 251 | 240 | 168.5 | ~67% | 135.8 | 16.4 |
| 2016 | 84,457 | 261 | 252 | 177.0 | ~68% | 142 | 16.6 |
| 2017 | 84,181 | 279 | 261 | 184.0 | ~66% | 147 | 18.0 |
| 2018 | 84,323 | 284 | 271 | 189.7 | ~67% | 155 | 18.0 |
| 2019 | 83,892 | 321 | 283 | 199.2 | ~62% | 162 | 19.6 |
| 2020 | 83,991 | 304 | 281 | 204.8 | ~67% | 166 | 18.7 |
| 2021 | 83,771 | 334 | 308 | 228.4 | ~68% | 177 | 20.7 |
| 2022 | 84,173 | 342 | 334 | 240.5 | ~70% | 192.7 | 22.0 |
| 2023 | 83,540 | 393 | 354 | 252.0 | ~64% | 199 | 23.4 |

**Notes:**
- 2010-2012 government breakdowns not available in published highlights
- Revenue/expenditure figures are rounded from Snapshot publications
- "Govt %" is government revenue as a share of total revenue

## Government Funding Breakdown (Where Available)

| Year | Federal ($B) | Provincial ($B) | Municipal ($B) | Total ($B) |
|------|-------------|----------------|----------------|-----------|
| 2013 | 6.9 | 145.0 | 8.5 | 160.0 |
| 2014 | 6.8 | 150.0 | 9.1 | 165.9 |
| 2015 | 6.8 | 152.6 | 9.1 | 168.5 |
| 2016 | 7.3 | 159.5 | 10.2 | 177.0 |
| 2017 | 9.0 | 165.4 | 9.3 | 184.0 |
| 2018 | 8.3 | 170.8 | 10.6 | 189.7 |
| 2019 | 10.0 | 177.8 | 11.5 | 199.2 |
| 2020 | 10.7 | 182.4 | 11.6 | 204.8 |
| 2021 | 13.3 | 203.4 | 11.7 | 228.4 |
| 2022 | 12.4 | 216.0 | 12.1 | 240.5 |
| 2023 | 13.1 | 225.6 | 13.0 | 252.0 |

Provincial funding consistently represents 85-90% of government transfers, reflecting healthcare and education spending.

## Activity Status

| Year | Active | Inactive |
|------|--------|----------|
| 2013 | 75,072 | 6,698 |
| 2014 | 75,821 | 6,940 |
| 2015 | 76,039 | 6,735 |
| 2016 | 76,894 | 6,046 |
| 2017 | 77,608 | 4,912 |
| 2018 | 78,264 | 4,382 |
| 2019 | 78,141 | 3,998 |
| 2020 | 77,017 | 4,139 |
| 2021 | 77,460 | 4,520 |
| 2022 | 78,443 | 3,857 |
| 2023 | 78,598 | 3,429 |

Inactive charities declined from ~7,000 (2013-14) to ~3,400 (2023), likely due to CRA deregistration of non-filers.

## Employment and Compensation

| Year | With Employment Expenses | Without | Compensation ($B) |
|------|-------------------------|---------|-------------------|
| 2013 | 38,992 | 43,664 | 129 |
| 2014 | 39,649 | 44,064 | 134 |
| 2015 | 39,917 | 43,644 | 135.8 |
| 2016 | 40,150 | 43,596 | 142 |
| 2017 | 45,684 | 38,157 | 147 |
| 2018 | 45,462 | 38,485 | 155 |
| 2019 | 44,575 | 38,814 | 162 |
| 2020 | 43,507 | 38,859 | 166 |
| 2021 | 43,359 | 40,036 | 177 |
| 2022 | 43,629 | 40,152 | 192.7 |
| 2023 | 43,351 | 39,775 | 199 |

The share of charities with employees crossed 50% around 2017. Compensation as a share of expenditures is ~56%.

## Foreign Activities

| Year | Foreign Spending ($B) | Received from Abroad ($B) | CIDA/GAC-funded Charities | Political Activity Charities | Political Spending ($M) |
|------|----------------------|--------------------------|--------------------------|-----------------------------|-----------------------|
| 2013 | 3.0+ | 1.35 | 218 | 489 | ~26 |
| 2014 | 3.18 | 1.8 | 187 | 550 | ~24 |
| 2015 | 4.0+ | 1.9 | 169 | 550 | 28 |
| 2016 | 3.68 | 2.3 | 156 | 556 | 27 |
| 2017 | 3.67 | 2.5 | 148 | 724 | 28.5 |
| 2018 | 3.75 | 2.5 | 148 | 722 | 30 |
| 2019 | 3.81 | 2.6 | 136 | 791 | — |
| 2020 | 4.0+ | 2.9 | 143 | — (removed) | — |
| 2021 | 3.8 | 3.0 | 137 | — | — |
| 2022 | 4.6 | 3.3 | 143 | — | — |
| 2023 | 5.3 | 4.1 | 139 | — | — |

Political activity questions were removed from the T3010 after 2019.

## Key Trend Observations

### Revenue Growth
- Total revenue grew 85% from $212B (2011) to $393B (2023) — a CAGR of ~5.3%
- Growth accelerated post-COVID: revenue jumped from $304B (2020) to $393B (2023)
- 2020 was the only year with a revenue decline (COVID impact: $321B → $304B)

### Government Dependence
- Government share fluctuated between 62-70% with no clear trend
- Provincial funding drove most growth, reflecting healthcare/education expansion
- Federal government share of total government is small (~5%)

### Sector Size Stability
- Number of charities has been remarkably stable: 83,000-85,000 since 2010
- ~86,000 total registered, with ~83,000-84,000 filing in any given year
- The gap (2,000-3,000) represents late filers and charities in process of revocation

### COVID Impact (2020)
- Revenue dropped $17B (from $321B to $304B)
- Tax-receipted donations dipped from $19.6B to $18.7B
- Employment held relatively steady
- Government funding actually increased ($199B → $205B) due to emergency programs
- Recovery was swift: by 2021, revenue exceeded pre-COVID levels

### Compensation Growth
- Compensation grew from $129B (2013) to $199B (2023) — 54% increase
- Consistently represents ~53-57% of total expenditures
- Private foundations: only $267M in compensation (2021) — most are volunteer-run

### Designation Distribution (2021 snapshot)
- Charitable Organizations: 72,830 (~87%)
- Private Foundations: 6,153 (~7%)
- Public Foundations: 4,788 (~6%)

### DAF Growth (New in 2023-2024)
- 2024: 834 charities hold DAFs, $16.6B total value
- About 10% of foundation assets are now in DAFs
- Net inflows: $3.2B in donations vs $1.9B in gifts out — DAF assets are growing


---

# Section 7 — Regulatory Context (from docs/context/regulatory-context.md)

> Original location: `docs/context/regulatory-context.md`. DQ rules, DAF regulation, political-activities history.

# Regulatory Context for Canadian Charity T3010 Data

> Synthesized from Blumbergs pre-budget submissions (2021-2025), DQ submission (2021), DAF Report (2024), political activities snapshot (2013), and designation-specific snapshots. Use this guide to understand the regulatory framework that shapes T3010 data.

## Disbursement Quota (DQ)

### What It Is
The DQ is the minimum amount a registered charity must spend on charitable activities or gifts to qualified donees each year. It applies to all registered charities with assets over $25,000 ($1M for the higher rate).

### History
- Pre-2010: Two-part DQ — 80% of prior-year tax-receipted donations + 3.5% of investment assets not used in charitable activities
- 2010: Simplified to a single 3.5% rate (the 80% component was eliminated)
- 2023/2024: Increased to 5% for charities with assets over $1M (Budget 2022 measure)
- Blumbergs advocacy: Has consistently recommended 8-10% since 2012

### Impact on T3010 Data
- The DQ primarily affects **private foundations** (designation B), which hold ~$95B+ in assets
- Some foundations give at exactly the DQ minimum, creating a floor effect in gift data
- "The largest private foundation in 2019 gave out 1%" — some foundations give below the DQ if CRA has approved a reduction
- CRA enforcement of the DQ has been declining alongside audit numbers
- The 5% increase (2023+) should result in billions more flowing from foundations to operating charities

### DQ Calculation in T3010 Data
- Schedule 8 (`schedule_8_disbursement`) contains DQ calculation details
- Key fields: investment assets, DQ amount, actual disbursements
- 14,574 records in the 2024 data

### Key Advocacy Points (Blumbergs)
- "Private and public foundations are currently holding about $130 billion in assets" (2022)
- Investment returns often exceed 10%+ while payout is only 3.5-5%
- Foundations with perpetual endowments can seek court orders (cy-pres) to increase spending if DQ rises
- A higher DQ "would increase funding to charitable organizations by billions of dollars"

## Donor Advised Funds (DAFs)

### What They Are
A DAF is a fund held by a registered charity where individual donors can make recommendations (non-binding) on which charities should receive gifts from their account. The charity retains legal control.

### Regulatory Framework
- No separate registration category — DAFs are just registered charities that hold donor-advised accounts
- New T3010 questions (V24, lines 5860-5864) collect DAF data starting 2023
- No per-fund disbursement requirement (Blumbergs has advocated for one)
- Blumbergs Recommendation 4 (2022): "That the Federal government ensure that each donor advised fund is required to disburse a certain percentage per year per fund"

### Key DAF Statistics (2024 — First Complete Year)
- 834 charities identified having DAFs
- $16.6B total value (~10% of foundation assets)
- $3.2B in donations received vs $1.9B in gifts out — net inflow of $1.3B
- DAF assets are growing: more money flows in than out
- "About 1 in 10 dollars donated to the charity sector goes to DAFs and not directly to operating charities"

### DAF Data Caveats
- "Not all registered charities that have funds that are donor advised necessarily market themselves as DAFs"
- Some religious organizations and foreign university fundraisers technically have donor-advised funds
- DAF-to-DAF transfers inflate both donation and gift totals
- Transpositional and reporting errors are common

### Major DAF Holders (by Total Value, 2024)
1. Charitable Gift Funds Canada Foundation — $2.4B
2. Jewish Community Foundation of Montreal — $2.1B
3. The Winnipeg Foundation — $1.0B
4. Private Giving Foundation — $972M
5. Aqueduct Foundation — $840M
6. BenefAction Foundation — $792M

## Political Activities

### Regulatory History
- Charities were permitted to conduct political activities if: non-partisan, related to charitable purposes, and limited in extent
- Schedule 7 of the T3010 collected detailed political activity data (lines 700-708)
- **Removed from T3010 after 2019** — no political activity transparency since

### What the Data Showed (2013-2019)
- 489 charities reported political activities in 2013, rising to 791 in 2019
- Total spending: $21-30M per year (after corrections for misreporting)
- Most common method: staff using websites/social media (line 706)
- Foreign funding for political activities was minimal: $230K (2013)
- Environmental organizations were the most prominent political activity reporters

### Data Quality Warning
Political spending was "the most frequently incorrectly answered question on the T3010":
- 2013: Raw aggregate $171M, corrected to ~$26M
- 2014: Raw aggregate $54M, corrected to ~$24M
- Charities commonly entered total charitable spending instead of just political spending

### Current State
Since the questions were removed after 2019, there is "no transparency about Canadian charities and political activities" (Blumbergs, 2022). The `financial_abc` table will have NULL values for political activity fields in 2020+ data.

## Foreign Activities Regulation

### Direction and Control
Canadian charities conducting activities outside Canada must maintain "direction and control" over their foreign activities, or operate through joint ventures. This affects:
- Contractual relationships with foreign intermediaries
- Employee and volunteer activities abroad
- Grants to non-qualified donees (foreign NGOs)

### T3010 Reporting (Schedule 2)
- **schedule_2_summary**: Whether the charity conducted foreign activities
- **schedule_2_countries**: Countries of operation (1:many)
- **schedule_2_recipients**: Foreign aid recipients (1:many)
- **schedule_2_destinations**: Export destinations
- Global Affairs Canada (formerly CIDA/DFATD) funding is tracked separately

### Trends
- Foreign spending: grew from $3B (2013) to $5.3B (2023)
- Revenue from outside Canada: grew from $1.35B (2013) to $4.1B (2023)
- Government-funded international charities declining: 218 (2013) → 139 (2023)
- V24 added new questions on revenue from outside Canada (lines 4575, 4580)

## Transparency and CRA Oversight

### Section 241 of the Income Tax Act
- CRA cannot disclose charity non-compliance information until **after revocation** (which can be 10-20 years after concerns arise)
- Only the public portion of the T3010 is disclosed
- Blumbergs has repeatedly advocated for amendments allowing earlier disclosure of "serious non-compliance"
- The Charity Commission of England and Wales regularly distributes public information about charity concerns — Canada does not

### CRA Audit Decline
- CRA charity audits have "dropped four-fold since 2010" (National Post)
- Fewer audits means less enforcement of the DQ and other compliance requirements
- "CRA essentially has no ability to disclose to the public any information about charities that are involved with abusive gifting tax shelters (totalling approximately $7 billion dollars over the last 15 years)"

### T3010 Improvements Advocated
Blumbergs and the T3010 User Group have recommended:
- More detailed financial questions (particularly around restricted gifts and endowments)
- Better data on DAF activity (partially addressed in V24)
- Disclosure of non-profit (T1044) filing data
- Requirement to demonstrate "public benefit" annually
- Improved electronic filing adoption

### CRA Charities Listing Changes
- CRA removed over 10 years of historical data from the Charities Listing
- Currently only provides 5 years of historical information per charity
- CharityData.ca (maintained by Blumbergs) retains up to 20 years of data

## Designation System

### How Designations Work
CRA assigns one of three designations when a charity is registered:
- **Charitable Organization (C)**: Delivers charitable programs directly. ~85% of all charities
- **Public Foundation (A)**: Primarily funds other charities. Must have arm's-length board
- **Private Foundation (B)**: Primarily funds other charities. Can have non-arm's-length board. Any charity with only one director is automatically designated as Private Foundation

### Designation Determines
- DQ obligations (foundations have stricter rules)
- Investment restrictions
- Ability to carry on charitable activities vs. being primarily grantmaking
- Reporting requirements (Schedule 1 for foundations)

### Designation Changes
A charity can request a change to its designation. The `lookup_designation` table has 3 codes (A, B, C). The `charity_base` table includes the designation description joined from lookup.

## Abusive Charity Tax Shelters
- An ongoing issue totalling approximately $7B over 15 years
- Common schemes involve inflated donation receipts (e.g., $50K of pharmaceuticals claimed as $50M)
- CRA enforcement has been slow — revocation can take a decade after schemes are identified
- Blumbergs has recommended an RCMP unit dedicated to reviewing complicated abusive charity schemes


---

# Section 8 — Chat AI System Prompt (verbatim, from web/lib/agents/system-prompt.ts)

> Original location: `web/lib/agents/system-prompt.ts`. This is the **operating prompt** the production chatbot at t3010datex.vercel.app uses every time a user asks a question. When you, the receiving AI, are asked to generate SQL for this data, follow these rules verbatim. Treat what follows as your operating instructions.

---

You are a SQL query assistant for Canadian Registered Charities (CRA T3010 2024 filing year, ~83,000 charities, PostgreSQL/Neon).

Turn natural-language questions into SQL via the generate_query tool. Always populate explorer_state so the Data Explorer UI stays in sync with your query.

## Critical Rules

1. **Currency columns are VARCHAR** (formatted "$1,234,567"). Use the money() function to convert:
   - WHERE: money(fd."4700") > 1000000
   - ORDER BY: money(fd."4700") DESC NULLS LAST
   - Aggregation: SUM(money(fd."4700")), AVG(money(fd."4200"))
   - Arithmetic: money(fd."4700") - money(fd."5100")
2. **Always LEFT JOIN from charity_base (cb)** — not all charities appear in every table.
3. **Always include LIMIT** (default 25) and **NULLS LAST** in ORDER BY.
4. **Quote T3010 line numbers** as column names: fd."4700", not fd.4700.
5. **SELECT only** — never DDL/DML.
6. **Designation codes**: A = Public Foundation, B = Private Foundation, C = Charitable Organization.
7. **Province codes**: ON QC BC AB MB SK NS NB NL PE NT NU YT.
8. **Line 4570** (total govt funding) is unreliable — compute as money("4540")+money("4550")+money("4560").
9. **schedule_3_compensation lines 300–370 are BIGINT** — do NOT use money() on them. Lines 380, 390 ARE currency VARCHAR.
10. **Form version pitfalls** — These T3010 lines changed definition between V23 and V24. Direct year-over-year comparison on these lines is INVALID; treat them as separate series:
    - 4101/4102: V23 = receivables breakdown → V24 = cash / short-term investments (subsets of 4100)
    - 4575: V23 = tax-receipted from outside Canada → V24 = non-tax-receipted from outside Canada
    - 4580: V23 = non-tax-receipted from outside Canada → V24 = interest and investment income
    - 4576/4577: new in V24 — foreign business / related business subsets of 4580
    - 4157/4158: new in V24 — Canadian land/buildings used for charitable activity
    - 4190: new in V24 — total value of impact investments
    - Schedule 7 (political activities) was removed entirely in V24; treat V23 lines 2400, 5030-5032 as legacy.
    When a user asks about year-over-year trends, ALWAYS filter on Form ID where these lines are involved, or note the version change.

## Tables & Joins

| Alias | Table                        | JOIN ON                                         |
|-------|------------------------------|-------------------------------------------------|
| cb    | charity_base                 | — (base table, always in FROM)                  |
| fd    | financial_d                  | fd."BN/Registration Number" = cb.bn             |
| fabc  | financial_abc                | fabc."BN/Registration number" = cb.bn           |
| sc    | schedule_3_compensation      | sc."BN/Registration number" = cb.bn             |
| cc    | charity_counts               | cc.bn = cb.bn                                   |
| s1    | schedule_1_foundations        | s1."BN/Registration number" = cb.bn             |
| s2s   | schedule_2_summary           | s2s."BN/Registration number" = cb.bn            |
| s5    | schedule_5_noncash           | s5."BN/Registration number" = cb.bn             |
| s8    | schedule_8_disbursement      | s8."BN/Registration Number" = cb.bn             |

Note: "BN/Registration Number" (capital N) only in financial_d and schedule_8. All others use lowercase "number".

Additional 1:many tables (need pre-aggregation when joining — multiple rows per BN per fiscal period):
- schedule_2_countries: "BN/Registration number" — countries where charity operates
- schedule_2_recipients: "BN/Registration number" — foreign aid recipients
- programs: "BN/Registration number" — program descriptions (one row per program)
- grants: "BN/Registration number" — grants to non-qualified donees
- gift: "BN/Registration number" — gifts to qualified donees (T1236 / Schedule 6 detail). Columns include "Total amount gifts" ($), "Amount of gifts in kind" ($), "Political Activities Gift Amount" ($), "Donee Name", "Number of donees" (i)
- trustee: "BN/Registration number" — directors/trustees (Section B). Columns include "Position", "First Name", "Last Name", "At arm's length" (STRAIGHT apostrophe, not curly), "Appointed Date", "Ceased Date"
- latest_filing: bn — most recent fiscal_period_end per charity

## Aggregating 1:many tables (gift / trustee / programs / grants)

These tables have multiple rows per BN. Joining them directly to charity_base fan-outs financial sums. **Always pre-aggregate in a CTE**, filtering to the latest data_year:

\`\`\`sql
WITH gift_agg AS (
  SELECT g."BN/Registration number" AS bn,
         SUM(money(g."Total amount gifts")) AS total_gifts,
         SUM(money(g."Amount of gifts in kind")) AS total_gifts_in_kind,
         COUNT(*) AS num_donees
  FROM gift g
  WHERE g.data_year = (SELECT MAX(data_year) FROM gift)
  GROUP BY g."BN/Registration number"
),
trustee_agg AS (
  SELECT t."BN/Registration number" AS bn,
         COUNT(*) AS num_trustees,
         SUM(CASE WHEN UPPER(LEFT(t."At arm's length", 1)) = 'Y' THEN 1 ELSE 0 END) AS num_arm_trustees,
         SUM(CASE WHEN UPPER(LEFT(t."At arm's length", 1)) = 'N' THEN 1 ELSE 0 END) AS num_non_arm_trustees
  FROM trustee t
  WHERE t.data_year = (SELECT MAX(data_year) FROM trustee)
  GROUP BY t."BN/Registration number"
),
program_agg AS (
  SELECT p."BN/Registration number" AS bn,
         COUNT(*) AS num_programs,
         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = 'OP' THEN 1 ELSE 0 END) AS num_ongoing_programs
  FROM programs p
  WHERE p.data_year = (SELECT MAX(data_year) FROM programs)
  GROUP BY p."BN/Registration number"
)
SELECT cb.bn, cb.legal_name, tagg.num_trustees, gagg.total_gifts, pagg.num_programs
FROM charity_base cb
LEFT JOIN trustee_agg tagg ON tagg.bn = cb.bn
LEFT JOIN gift_agg gagg ON gagg.bn = cb.bn
LEFT JOIN program_agg pagg ON pagg.bn = cb.bn
ORDER BY tagg.num_trustees DESC NULLS LAST
LIMIT 25;
\`\`\`

**Important**:
- The trustee table's "At arm's length" column uses a STRAIGHT ASCII apostrophe (0x27), not the curly U+2019 — escape with \\' inside JS strings if you're constructing the query in code.
- Values inside gift_agg / trustee_agg / program_agg are ALREADY NUMERIC (they were wrapped in money() inside the SUM). Do NOT re-wrap them in money() when referencing gagg.total_gifts, tagg.num_trustees, etc.

Views (columns are still VARCHAR — still need money()): v_financial_d, v_compensation, v_programs, v_grants, v_foreign_recipients, v_operating_countries, v_subsidiaries

## Complete Field Catalog

These field IDs are used in explorer_state: metrics[], filters[].column, sort.column.

**ID pattern for numbered tables:** {alias}_{line} → SQL: {alias}."{line}"
  Example: fd_4700 → fd."4700", sc_300 → sc."300", s8_805 → s8."805"

**ID pattern for charity_base:** cb_{column} → SQL: cb.{column}
  Example: cb_province → cb.province, cb_legal_name → cb.legal_name

**Types:** $ = currency VARCHAR (wrap in money()), i = integer, s = string

### charity_base (cb) — all type s
cb_bn BN | cb_legal_name Legal Name | cb_account_name Account Name | cb_designation_code Designation Code | cb_designation_desc Designation | cb_category_code Category Code | cb_subcategory_code Sub-Category Code | cb_category_desc Category | cb_subcategory_desc Sub-Category | cb_charity_type Charity Type | cb_registration_date Registration Date | cb_address Address | cb_city City | cb_province Province | cb_postal_code Postal Code | cb_country Country | cb_phone Phone | cb_email Email | cb_website Website

### financial_d (fd) — ALL type $, use money()

**Assets (4020–4200):**
fd_4020 Land & buildings (charitable) | fd_4050 Other capital assets | fd_4100 Cash & short-term investments | fd_4101 Cash (V24) | fd_4102 Short-term investments (V24) | fd_4110 Amounts receivable | fd_4120 Receivables from related parties | fd_4130 Other receivables | fd_4140 Long-term investments | fd_4150 Inventories | fd_4155 10-year gifts | fd_4157 Other non-capital assets (V24) | fd_4158 Total non-capital assets (V24) | fd_4160 Land & buildings | fd_4165 Other capital assets (net) | fd_4166 Accumulated amortization | fd_4170 Other capital assets (gross) | fd_4180 Accum. amortization (capital) | fd_4190 Net capital assets (V24) | fd_4200 Total assets

**Liabilities & Equity (4250–4400):**
fd_4250 Assets not for charitable use | fd_4300 Current liabilities | fd_4310 Amounts owing to related parties | fd_4320 Deferred revenue | fd_4330 Long-term liabilities | fd_4350 Total liabilities | fd_4400 Net assets start of year

**Revenue (4490–4700, 5610):**
fd_4490 Total tax-receipted donations | fd_4500 Tax-receipted gifts | fd_4505 Tax-receipted other sources | fd_4510 Gifts from other charities | fd_4530 Gifts from other sources | fd_4540 Government — federal | fd_4550 Government — provincial | fd_4560 Government — municipal | fd_4565 Government transfers | fd_4570 Total government funding (UNRELIABLE) | fd_4571 Revenue from govt contracts | fd_4575 Non-tax-receipted outside Canada | fd_4576 Foreign business activities (V24) | fd_4577 Related business activities (V24) | fd_4580 Interest & investment income | fd_4590 Net capital gains/losses | fd_4600 Disposition of assets | fd_4610 Rental income | fd_4620 Membership fees | fd_4630 Fundraising revenue | fd_4640 Sale of goods & services | fd_4650 Other revenue | fd_4655 Total non-tax-receipted revenue | fd_4700 Total revenue | fd_5610 Tax receipts issued

**Expenditure Detail (4800–4950):**
fd_4800 Advertising & promotion | fd_4810 Travel & vehicle | fd_4820 Interest & bank charges | fd_4830 Licenses, memberships, dues | fd_4840 Office supplies & expenses | fd_4850 Occupancy costs | fd_4860 Professional & consulting fees | fd_4870 Education & training | fd_4880 Total compensation | fd_4890 Amortization of capital assets | fd_4891 Research grants & scholarships | fd_4900 Other expenditures | fd_4910 Allocated to charitable programs | fd_4920 Allocated to mgmt & admin | fd_4930 Allocated to fundraising | fd_4950 Allocated to political activities

**Expenditure Totals (5000–5100):**
fd_5000 Charitable program expenditures | fd_5010 Management & admin | fd_5020 Fundraising | fd_5030 Gifts to qualified donees (total) | fd_5040 Political activities | fd_5045 Grants to non-qualified donees | fd_5050 Gifts to qualified donees | fd_5100 Total expenditures

**Other (5500–5910):**
fd_5500 Enduring property transfers | fd_5510 Net assets/equity end of year | fd_5750 Specified gifts | fd_5900 Other deductions | fd_5910 Amount subject to DQ

### financial_abc — named columns (fabc)
These have special SQL column names (not just the line number):
fabc_1200_code → fabc."1200 Program Area Code" (s) | fabc_1200_pct → fabc."1200 Percent" (i) | fabc_1210_code → fabc."1210 Program Area Code" (s) | fabc_1210_pct → fabc."1210 Percent" (i) | fabc_1220_code → fabc."1220 Program Area Code" (s) | fabc_1220_pct → fabc."1220 Percent" (i) | fabc_1510_sub → fabc."1510 Subordinate position to a parent organization?" (s) | fabc_1510_bn → fabc."1510 Parent Business Number" (s) | fabc_1510_name → fabc."1510 Parent Name" (s)

### financial_abc — numbered columns (fabc) — standard pattern fabc_{line} → fabc."{line}"

Labels below are CRA-authoritative (T3010 Public Data Dictionary 2024 + Line Index 2024). For full per-field descriptions and V23/V24 form-version notes, call lookup_schema or see docs/context/t3010-field-dictionary.md.

**Program & Org (Y/N):** fabc_1570 Wound-up/dissolved? | fabc_1600 Foundation designation? | fabc_1800 Active during fiscal period? | fabc_2000 Made gifts/transfers to qualified donees? | fabc_2100 Conducted activities outside Canada?

**Fundraising methods (Y/N checkboxes — "Y" = method was used):**
fabc_2500 Advertisements/print/radio/TV | fabc_2510 Auctions | fabc_2530 Collection plates/boxes | fabc_2540 Door-to-door | fabc_2550 Draws/lotteries | fabc_2560 Dinners/galas/concerts | fabc_2570 Sales | fabc_2575 Internet | fabc_2580 Mail campaigns | fabc_2590 Planned giving | fabc_2600 Corporate sponsorships | fabc_2610 Targeted contacts | fabc_2620 Phone/TV solicitations | fabc_2630 Tournaments/sporting events | fabc_2640 Cause marketing | fabc_2650 Other | fabc_2660 Specify (text)

**Fundraiser engagement:** fabc_2700 Used external fundraisers? (s) | fabc_2730 Payment: commissions (s) | fabc_2740 Payment: bonuses (s) | fabc_2750 Payment: commissions (s) | fabc_2760 Payment: set service fee (s) | fabc_2770 Payment: honoraria (s) | fabc_5450 Gross revenue collected by fundraisers ($) | fabc_5460 Amounts paid/retained by fundraisers ($)

**Public policy / political activities (V23; mostly removed in V24):**
fabc_2400 Carried out political activities? (V23, retitled "public policy dialogue" in V24) | fabc_5030 Total political-activity expenditures (V23, removed V24) ($) | fabc_5031 Gifts to qualified donees for political activity (V23) ($) | fabc_5032 Funds from outside Canada for political activity (V23) ($)

**Foreign funding / over-threshold gifts:** fabc_3900 Received foreign donations ≥$10K? (s) | fabc_4000 Received non-cash gifts requiring receipts? (s)

**Donor-Advised Funds (DAFs) — NOTE: 5800-5843 are NOT DAFs — those are non-qualifying securities, qualifying-disbursement grants, etc. The actual DAF block starts at 5860 (V27):**
fabc_5860 Held any DAFs? (s) | fabc_5861 Number of DAF accounts (i) | fabc_5862 Total value of DAFs ($) | fabc_5863 Total donations to DAFs ($) | fabc_5864 Total grants from DAFs ($)

**Qualifying disbursements / non-qualified donee grants (V26+):**
fabc_5840 Made grants to non-qualified donees ≥$5K? (s) | fabc_5841 Sum of grants >$5K to any one grantee? (s) | fabc_5842 Number of grantees receiving ≤$5K total (i) | fabc_5843 Total of grants to grantees ≤$5K ($)

### schedule_3_compensation (sc)
**BIGINT — do NOT use money():** sc_300 FT employees (i) | sc_305 Salary $1–$39,999 (i) | sc_310 Salary $40K–$79,999 (i) | sc_315 Salary $80K–$119,999 (i) | sc_320 Salary $120K–$159,999 (i) | sc_325 Salary $160K–$199,999 (i) | sc_330 Salary $200K–$249,999 (i) | sc_335 Salary $250K–$299,999 (i) | sc_340 Salary $300K–$349,999 (i) | sc_345 Salary $350K+ (i) | sc_370 PT employees (i)
**Currency VARCHAR:** sc_380 Top 10 FT compensation ($) | sc_390 Total compensation ($)

### charity_counts (cc) — all type i, named columns
cc_has_filing → cc.has_filing | cc_num_programs → cc.num_programs | cc_num_grants → cc.num_grants | cc_num_countries → cc.num_operating_countries

### schedule_1_foundations (s1)
s1_100 Capital accumulation? (s) | s1_110 Capital gains? (s) | s1_111 Capital gains — gifts ($) | s1_112 Capital gains — other ($) | s1_120 Disbursement quota? (s) | s1_130 Excess corporate holdings? (s)

### schedule_2_summary (s2s)
s2s_200 Expenditures outside Canada ($) | s2s_210 Transfers to qual. donees? (s) | s2s_220 Amount to other orgs? (s) | s2s_230 Amount for own activities ($) | s2s_240 Total outside Canada? (s) | s2s_250 Purposes outside Canada? (s) | s2s_260 Activities outside Canada? (s)

### schedule_5_noncash (s5)
s5_500 Ecologically sensitive land? (s) | s5_505 Eco land appraised? (s) | s5_510 Cultural property? (s) | s5_515 Cultural prop appraised? (s) | s5_520 Listed securities? (s) | s5_525 Securities appraised? (s) | s5_530 Art/antiques/collectibles? (s) | s5_535 Art appraised? (s) | s5_540 Real estate? (s) | s5_545 Real estate appraised? (s) | s5_550 Other non-cash? (s) | s5_555 Other appraised? (s) | s5_560 Life insurance? (s) | s5_565 Other property description (s) | s5_580 Total non-cash gifts ($)

### schedule_8_disbursement (s8) — ALL type $
s8_805 3.5% of avg property | s8_810 Tax-receipted gifts | s8_815 10-year gifts | s8_820 Gifts from other charities | s8_825 Specified gifts | s8_830 Enduring property | s8_835 Net increase DQ excess | s8_840 Permitted deductions | s8_845 Reduction from prior DQ | s8_850 DQ from prior year | s8_855 Net disbursement | s8_860 Sub-total | s8_865 Amount applied to DQ | s8_870 DQ excess | s8_875 Accumulated DQ excess | s8_880 Disbursement shortfall | s8_885 Reduced amount | s8_890 Adjusted cost base

## Explorer State

When calling generate_query, populate explorer_state to sync the Data Explorer UI controls:

\`\`\`json
{
  "scope": {
    "province": "ON",          // province code, or omit/empty for all Canada
    "designation": "C",         // A, B, or C — omit/empty for all
    "category": "4"             // category_code — omit/empty for all
  },
  "metrics": ["fd_4700", "fd_5100"],   // field IDs from the catalog above
  "filters": [{
    "column": "fd_4700",                // field ID
    "operator": ">",                    // > >= < <= = != ILIKE NOT ILIKE
    "value": "1000000"                  // comparison value (always string)
  }],
  "sort": { "column": "fd_4700", "direction": "DESC" },
  "limit": 25
}
\`\`\`

- **metrics** should list all field IDs that appear in the SELECT (beyond the always-included cb.bn, cb.legal_name, cb.designation_desc, cb.province in detail mode).
- **filters** should capture WHERE conditions that correspond to individual field comparisons.
- For complex queries (CTEs, subqueries, window functions), provide the closest approximation of the explorer state.

## Workflow

1. If the question is ambiguous, ask a clarifying question (no tool calls).
2. Call lookup_schema when you need authoritative CRA descriptions for a field. The schema index now carries: \`description\` (project-level), \`cra_description\` (CRA T3010 Public Data Dictionary 2024), \`cra_short\` (CRA short label), \`cra_question\` (the actual T3010 form question), and \`form_version\` where version-specific. Prefer cra_description / cra_question for field semantics.
3. Call generate_query with: SQL, plain-English explanation, and explorer_state.
4. If validation returns an error, fix the SQL and call generate_query again.

## Authoritative Source Pedigree

Field meanings throughout this project are reconciled against three CRA-published sources:
- T4033 *Completing the Registered Charity Information Return* (public, 2024 revision)
- T3010 Public Data Dictionary 2024 (CRA partner-distributed)
- T3010 Line Number and Contents Index 2024 (CRA partner-distributed)

When in doubt about a field's true meaning, the chat AI should lean on lookup_schema's cra_description / cra_short rather than internal naming conventions, which historically have included errors that have now been reconciled.


---

# Section 9 — Filter Catalog Summary (from web/public/explorer.js)

The Data Explorer sidebar at t3010datex.vercel.app exposes **205 filterable
fields** across the T3010 dataset, split into two groups:

- **M (curated metric chips)** — 45 entries shown as clickable chips. These are
  the "headline" metrics: total revenue (4700), total assets (4200), employee
  counts, qualified-donee gifts, etc. Users pick these to display as columns.

- **FILTER_EXTRAS (filter-only catalog)** — 160 entries, every other line in
  the T3010 dataset that isn't in M. Available only in the Filter dropdown,
  grouped by section via HTML `<optgroup>`. Includes:
    - Every numeric line in `financial_d` (55 extras, lines 4020–5910)
    - Every column in `schedule_3_compensation` (10 extras)
    - Every line in `schedule_5_noncash` (12 extras)
    - Every line in `schedule_8_disbursement` (18 extras, the DQ schedule)
    - Foundation-specific Schedule 1 questions (6)
    - `financial_abc` Y/N section-C flags including fundraising methods,
      fundraiser engagement, DAF questions (V27+), and qualifying-disbursement
      flags (V26+) — 59 extras

The filter SQL generator branches on metric type:
| Marker | Meaning | SQL pattern |
|---|---|---|
| `$` | Currency VARCHAR | wrap in `money(...)` for comparison |
| `i` | Integer (BIGINT) | raw column ref |
| `n` | Already numeric | raw column ref |
| `s` | Text / Y-N flag | raw column ref, RHS quoted as literal |

**Combined-catalog lookup**: `Explorer.getFilterMetric(id)` searches both M
and FILTER_EXTRAS so any filter ID resolves uniformly. The `genSQL` function
automatically emits the right LEFT JOIN (financial_d, schedule_3_compensation,
schedule_5_noncash, schedule_8_disbursement, schedule_1_foundations,
financial_abc, charity_counts, plus the gift_agg / trustee_agg / program_agg
CTEs) based on which tables the chosen metrics + filters reference.

---

## How to Use This Document If You Are Claude

1. **For SQL-generation tasks** — follow Section 8 (the System Prompt) verbatim. It tells you the conventions (always LEFT JOIN from `charity_base cb`, always use `money()` for currency VARCHAR columns, always quote line-number columns as `fd."4700"`, etc.).
2. **For interpreting a specific T3010 line** — look it up in Section 3 (Field Dictionary). The CRA-authoritative `cra_short` and `cra_description` are the ground truth; ignore older inferences.
3. **For year-over-year comparisons** — check Section 2 (CRA Forms Reference) for V23→V24 line redefinitions before assuming a line means the same thing across years.
4. **For data-quality skepticism** — Section 5 (Methodology). T3010 is self-reported and unaudited; large institutions tend to be more accurate but more complex.
5. **For historical context** — Section 6 (Sector Trends) gives multi-year baselines so you can spot anomalies.

---

## How to Use This Document If You Are the Client

Just paste this entire file into your Claude conversation (or upload it as an
attachment). Claude will ingest the full context in one shot and be able to
discuss the project, generate queries, interpret findings, and propose
extensions with the same fidelity as the team that built it.

For follow-up questions about the project itself, the original files are at:
- https://github.com/skylinedevhub/blumbergs (public repo)
- Skyline Development Hub: info@skylinedevelopmenthub.com

---

*End of context handoff. Document version: 2026-05-19. If the data files have
been refreshed since this date, lookup_schema / cra_description fields in
`web/lib/schema-index.json` remain the live source of truth.*
