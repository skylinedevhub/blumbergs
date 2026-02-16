# Directory Setup Design

**Date:** 2026-02-16
**Status:** Approved

## Goal

Restructure the blumbergs CRA T3010 charity data project from a flat file dump into an organized analytics project supporting: Python/DuckDB SQL queries, snapshot-style reports, charity-specific lookups, data exports, and multi-year data loading.

## Directory Structure

```
blumbergs/
├── data/
│   ├── raw/
│   │   └── 2024/
│   │       ├── ident.csv
│   │       ├── financial_abc.csv
│   │       ├── financial_d.csv
│   │       ├── gift.csv
│   │       ├── grants_nonqd.csv
│   │       ├── programs.csv
│   │       ├── trustee.csv
│   │       ├── schedule_1_foundations.csv
│   │       ├── schedule_2_summary.csv
│   │       ├── schedule_2_countries.csv
│   │       ├── schedule_2_destinations.csv
│   │       ├── schedule_2_recipients.csv
│   │       ├── schedule_3_compensation.csv
│   │       ├── schedule_5_noncash.csv
│   │       ├── schedule_7_description.csv
│   │       ├── schedule_7_political_outside.csv
│   │       ├── schedule_7_political_resources.csv
│   │       ├── schedule_8_disbursement.csv
│   │       └── lookups/
│   │           ├── category_subcategory.csv
│   │           ├── country.csv
│   │           ├── designation.csv
│   │           ├── form_versioning.csv
│   │           ├── programs.csv
│   │           ├── province.csv
│   │           └── us_state.csv
│   ├── db/
│   │   └── cra_charities.duckdb
│   └── exports/
├── docs/
│   ├── reference/
│   │   ├── t3010-24e.pdf
│   │   ├── t3010-lp-24e.pdf
│   │   └── blumbergs-snapshot-2022.pdf
│   └── plans/
├── scripts/
│   ├── load_csv.py
│   ├── queries/
│   └── reports/
├── CLAUDE.md
├── CRA_T3010_Reference.md
└── .gitignore
```

## CSV Renaming

All filenames normalized to snake_case. Lookup tables (prefixed with `#`) moved to `lookups/` subfolder.

## Key Components

### load_csv.py
- Takes year directory as input
- Handles cp1252 encoding with UTF-8 fallback
- Strips `$` and `,` from currency columns, casts to DECIMAL
- Creates/replaces all tables in DuckDB
- Recreates views (v_financial_d, v_compensation, etc.)
- Rebuilds derived tables (charity_base, charity_counts, latest_filing)

### .gitignore
Excludes: `*.duckdb`, `data/exports/`, `*.Zone.Identifier`, `data/raw/`, `__pycache__/`

### CLAUDE.md
Updated with new paths, T3010 form insights, Blumbergs Snapshot context, loader usage.

## Decisions

- Raw CSVs excluded from git (200MB+); tracked via year folder naming convention
- DuckDB excluded from git (60MB binary); reproducible via load_csv.py
- Reference PDFs tracked in git (small enough, important for context)
- Snake_case filenames for Python/shell ergonomics
