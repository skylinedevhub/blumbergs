# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canadian Registered Charities data analysis project using CRA T3010 annual filing data (~82,000 charities). Contains source CSVs and a pre-built DuckDB database (`cra_charities_3.duckdb`, 60 MB).

## Querying the Database

```bash
python3 -c "
import duckdb
con = duckdb.connect('cra_charities_3.duckdb', read_only=True)
print(con.execute('SELECT ... FROM ...').fetchdf())
con.close()
"
```

DuckDB Python module is installed (`duckdb` 1.4.4). Always open with `read_only=True` unless intentionally modifying.

## Database Schema

### Core Tables
- **ident** (82,299 rows) — Master charity list. PK: `BN/Registration Number`
- **charity_base** (82,299) — Cleaned ident with joined lookup descriptions (designation, category, subcategory)
- **latest_filing** (82,299) — Most recent fiscal period end per charity
- **charity_counts** (82,299) — Aggregated counts (programs, grants, operating countries)

### Financial Tables
- **financial_d** (82,113) — Balance sheet + income statement (line numbers as column names: 4100, 4200, 4700, 5000, 5100, etc.)
- **financial_abc** (82,444) — Program codes, Y/N questions, DAF data, subsidiary relationships

### Schedule Tables
- **schedule_1_foundations** (82,444) — Foundation-specific fields
- **schedule_2_summary** (4,931) — Foreign activities summary
- **schedule_2_countries** (9,256) — Countries where charity operates (1:many)
- **schedule_2_recipients** (13,913) — Foreign aid recipients (1:many)
- **schedule_2_destinations** (693) — Export destinations (1:many)
- **schedule_3_compensation** (42,512) — Employee compensation bands
- **schedule_5_noncash** (11,076) — Non-cash gifts
- **schedule_8_disbursement** (14,474) — Disbursement quota calculations

### Supplementary Tables
- **programs** (93,900) — Program descriptions (1:many)
- **grants** (13,967) — Grants to non-qualified donees (1:many)

### Lookup Tables
- **lookup_category**, **lookup_country**, **lookup_designation**, **lookup_programs**, **lookup_province**

### Views (use these for friendlier column names)
- **v_financial_d** — Aliases: `bn`, `fiscal_period_end`, `total_revenue` (4200), `total_expenditures` (5000), `total_assets` (5030)
- **v_financial_abc** — Aliases: `bn`, `fiscal_period_end`, `is_subsidiary`, `parent_bn`, `parent_name`
- **v_compensation** — Aliases: `bn`, `fiscal_period_end`, `ft_employees`, `pt_employees`, `total_compensation`
- **v_programs** — Aliases: `bn`, `fiscal_period_end`, `program_type`, `description`
- **v_grants** — Aliases: `bn`, `fiscal_period_end`, `recipient_name`, `purpose`, `cash_amount`, `country`
- **v_foreign_recipients** — Aliases: `bn`, `fiscal_period_end`, `recipient_name`, `country_code`, `amount`
- **v_operating_countries** — Aliases: `bn`, `fiscal_period_end`, `country_code`
- **v_subsidiaries** — `subsidiary_bn`, `subsidiary_name`, `parent_bn`, `parent_name`

## Critical Data Quirks

1. **Currency fields are text** — Format `"$1,234,567"`. Convert with:
   ```sql
   CAST(REPLACE(REPLACE(column, '$', ''), ',', '') AS DECIMAL)
   ```
2. **Always LEFT JOIN from ident/charity_base** — Not all charities appear in every table
3. **Column names in raw tables use T3010 line numbers** (e.g., `"4700"` = total revenue). Use the views for readable names.
4. **BN column name varies by table** — `"BN/Registration Number"` in some, `"BN/Registration number"` in others. Views normalize to `bn`.
5. **Designation codes**: A = Charitable Org, B = Public Foundation, C = Private Foundation
6. **CSV encoding is mixed** — UTF-8 and Windows-1252 (cp1252). Use `encoding='cp1252'` when loading CSVs.

## Key T3010 Line Number Reference

| Line | Meaning |
|------|---------|
| 4100 | Cash and short-term investments |
| 4200 | Total assets |
| 4350 | Total liabilities |
| 4500 | Tax-receipted gifts |
| 4510 | Gifts from other charities |
| 4540/4550/4560 | Government funding (fed/prov/muni) |
| 4700 | Total revenue |
| 5000 | Charitable program expenditures |
| 5010 | Management and admin |
| 5020 | Fundraising |
| 5050 | Gifts to qualified donees |
| 5100 | Total expenditures |
| 300/370 | FT/PT employee count |
| 390 | Total compensation |
| 5860-5864 | DAF fields |

## CSV Source Files

Located at `CRA csvs/2024 csv as of 2026-01-31/`. Lookup tables are prefixed with `#`. Data is from the 2024 tax year, exported 2026-01-31.

## Reference Documentation

See `CRA_T3010_Reference.md` for full field mappings and relationship diagrams.
