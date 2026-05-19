# CRA T3010 Registered Charity Dataset - Reference Guide

## Overview

The CRA T3010 is the annual information return that all ~82,000 Canadian registered charities must file. The data is provided as multiple CSV files that can be loaded into a DuckDB database.

## Directory Structure

```
cra_2024/
├── csv/          # Place all CSV files here
└── db/           # Output for DuckDB file
```

## CSV Files

### Master Table
- **Ident.csv** - Master charity list (~82,000 rows). Primary key: `BN/Registration Number`

### Financial Tables
- **Financial Section D Schedule 6.csv** - Assets, liabilities, revenue, expenditures
- **Financial Section A B and C.csv** - Program codes, Y/N questions, DAF data

### Schedule Tables
- **Schedule 1 Foundations.csv** - Foundation-specific data
- **Schedule 2 Activities Outside Canada.csv** - Foreign activities summary
- **Schedule 2 Activities Outside Canada Country.csv** - Operating countries (1:many)
- **Schedule 2 Activities Outside Canada Recipient.csv** - Foreign recipients (1:many)
- **Schedule 2 Activities Outside Canada Destination.csv** - Export destinations (1:many)
- **Schedule 3 Compensation.csv** - Employee compensation
- **Schedule 5 NonCash gifts.csv** - Non-cash gift details
- **Schedule 7** files - Political activities (likely empty)
- **Schedule 8 Disbursement Quota.csv** - DQ calculations

### Supplementary Tables
- **Grants to NonQualified Donees.csv** - Grants to non-QDs (1:many)
- **New and Ongoing Programs.csv** - Program descriptions (1:many)

### Lookup Tables
- **_Category_SubCategory.csv**, **_Province.csv**, **_Country.csv**, **_Programs.csv**, **_Designation.csv**, **_US State.csv**, **_Form Versioning Details.csv**

## Key T3010 Line Numbers

Columns are named by T3010 line numbers. Key mappings:

| Line | Description |
|------|-------------|
| 4100 | Cash and short-term investments |
| 4140 | Long-term investments |
| 4200 | Total Assets |
| 4250 | Assets not used for charitable activities |
| 4350 | Total Liabilities |
| 4500 | Tax-receipted gifts |
| 4510 | Gifts from other charities |
| 4540/4550/4560 | Government funding (fed/prov/muni) |
| 4700 | Total Revenue |
| 5000 | Charitable program expenditures |
| 5010 | Management and admin |
| 5020 | Fundraising |
| 5050 | Gifts to qualified donees |
| 5100 | Total Expenditures |
| 300 | Full-time employee positions |
| 305-345 | Salary bands ($40k increments) |
| 390 | Total compensation |
| 5860-5864 | DAF fields (has DAF, accounts, value, donations, gifts) |

## Data Relationships

```
ident (master)
  ├── 1:1 ── financial_d, financial_abc, schedule_1, schedule_2_foreign, 
  │          schedule_3_compensation, schedule_5_noncash, schedule_8_dq
  │
  └── 1:many ── schedule_2_countries, schedule_2_recipients, 
               schedule_2_destinations, grants_nonqd, programs
```

## Important Notes

1. **Always LEFT JOIN from ident** - Not all charities have data in every table
2. **BN column name varies** - Check exact spelling in each CSV
3. **Currency fields are text** - Format: "$1,234,567". Convert with:
   ```sql
   CAST(REPLACE(REPLACE(column, '$', ''), ',', '') AS DECIMAL)
   ```
4. **Encoding** - Some CSVs are UTF-8, others Windows-1252 (cp1252)
5. **Designation codes** (authoritative — from CRA `# Designation` lookup):
   - `A` = Public Foundation
   - `B` = Private Foundation
   - `C` = Charitable Organization (~85% of all registered charities)

## Authoritative Field Reference

For the full line-by-line dictionary (162 indexed lines × 18 tables, with CRA-defined descriptions from the 2024 Public Data Dictionary and Line Index), see:

- `docs/context/t3010-field-dictionary.md` — Every column, every table, with CRA's authoritative description text
- `docs/context/cra-forms-reference.md` — Per-form purpose (T3010, T4033, T1235, T1236, T1441, T2081) and V23→V24 line-redefinition pitfalls
- `docs/reference/cra-forms/` — Source PDFs of the public CRA forms
- `docs/reference/cra-internal/` — Source XLSX dictionaries (confidential, gitignored)
