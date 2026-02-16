# Directory Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the blumbergs project from a flat file dump into an organized analytics workspace with multi-year CSV loading, reusable SQL queries, and reproducible DuckDB builds.

**Architecture:** Files reorganized into `data/` (raw CSVs by year, DuckDB, exports), `docs/` (reference PDFs, plans), `scripts/` (loader, queries, reports). A Python loader script replaces the manual DuckDB import process.

**Tech Stack:** Python 3, DuckDB, bash

---

### Task 1: Initialize git repository

**Step 1: Init repo**

Run: `cd /home/yb97/src/blumbergs && git init`

**Step 2: Commit**

```bash
git add CLAUDE.md CRA_T3010_Reference.md docs/plans/
git commit -m "chore: initial commit with reference docs and plans"
```

---

### Task 2: Create directory structure and move files

**Files:**
- Create dirs: `data/raw/2024/lookups/`, `data/db/`, `data/exports/`, `docs/reference/`, `scripts/queries/`, `scripts/reports/`

**Step 1: Create directories**

```bash
mkdir -p data/raw/2024/lookups data/db data/exports docs/reference scripts/queries scripts/reports
```

**Step 2: Move and rename CSVs to `data/raw/2024/`**

```bash
cd /home/yb97/src/blumbergs

# Main data tables
cp "CRA csvs/2024 csv as of 2026-01-31/Ident.csv" data/raw/2024/ident.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Financial Section A_ B and C.csv" data/raw/2024/financial_abc.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Financial Section D & Schedule 6.csv" data/raw/2024/financial_d.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Gift.csv" data/raw/2024/gift.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Grants to Non-Qualified Donees.csv" data/raw/2024/grants_nonqd.csv
cp "CRA csvs/2024 csv as of 2026-01-31/New and Ongoing Programs.csv" data/raw/2024/programs.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Trustee.csv" data/raw/2024/trustee.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 1_ Foundations.csv" data/raw/2024/schedule_1_foundations.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 2_ Activities Outside Canada.csv" data/raw/2024/schedule_2_summary.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 2_ Activities Outside Canada - Country.csv" data/raw/2024/schedule_2_countries.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 2_ Activities Outside Canada - Destination.csv" data/raw/2024/schedule_2_destinations.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 2_ Activities Outside Canada - Recipient.csv" data/raw/2024/schedule_2_recipients.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 3_ Compensation.csv" data/raw/2024/schedule_3_compensation.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 5_ Non-Cash gifts.csv" data/raw/2024/schedule_5_noncash.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 7_ Description.csv" data/raw/2024/schedule_7_description.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 7_ Political Activities - Outside Canada.csv" data/raw/2024/schedule_7_political_outside.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 7_ Political Activities - Resources.csv" data/raw/2024/schedule_7_political_resources.csv
cp "CRA csvs/2024 csv as of 2026-01-31/Schedule 8_ Disbursement Quota.csv" data/raw/2024/schedule_8_disbursement.csv

# Lookup tables
cp "CRA csvs/2024 csv as of 2026-01-31/# Category_Sub-Category.csv" data/raw/2024/lookups/category_subcategory.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# Country.csv" data/raw/2024/lookups/country.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# Designation.csv" data/raw/2024/lookups/designation.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# Form Versioning Details.csv" data/raw/2024/lookups/form_versioning.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# Programs.csv" data/raw/2024/lookups/programs.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# Province.csv" data/raw/2024/lookups/province.csv
cp "CRA csvs/2024 csv as of 2026-01-31/# US State.csv" data/raw/2024/lookups/us_state.csv
```

**Step 3: Move DuckDB file**

```bash
cp cra_charities_3.duckdb data/db/cra_charities.duckdb
```

**Step 4: Move reference PDFs**

```bash
mv t3010-24e.pdf docs/reference/
mv t3010-lp-24e.pdf docs/reference/
mv "Blumbergs-Snapshot-of-Charitable-Organizations-in-the-Canadian-Charity-Sector-2022.pdf" docs/reference/blumbergs-snapshot-2022.pdf
```

**Step 5: Remove Zone.Identifier files and old source dir**

```bash
rm -f *.Zone.Identifier "CRA_T3010_Reference.md:Zone.Identifier"
# Keep "CRA csvs/" as archive until verified — delete manually later
```

**Step 6: Verify structure**

```bash
find data/ docs/ scripts/ -type f | sort
```

Expected: All CSVs in `data/raw/2024/`, lookups in `data/raw/2024/lookups/`, DuckDB in `data/db/`, PDFs in `docs/reference/`.

---

### Task 3: Create .gitignore

**Files:**
- Create: `.gitignore`

**Step 1: Write .gitignore**

```gitignore
# Data files (too large for git, reproducible via load_csv.py)
data/raw/
data/db/*.duckdb
data/exports/

# Windows download metadata
*.Zone.Identifier

# Python
__pycache__/
*.pyc
*.pyo
.venv/

# Original CSV dump (kept as archive until verified)
CRA csvs/
```

**Step 2: Commit structure**

```bash
git add .gitignore docs/reference/ scripts/
git commit -m "chore: organize directory structure with data/docs/scripts layout"
```

---

### Task 4: Write the CSV loader script

**Files:**
- Create: `scripts/load_csv.py`

**Purpose:** Load CSVs from a `data/raw/{year}/` directory into DuckDB at `data/db/cra_charities.duckdb`. Handles encoding, creates all base tables, views, and derived tables.

**Step 1: Write `scripts/load_csv.py`**

The script must:
1. Accept a year directory path as CLI argument (default: `data/raw/2024/`)
2. Open/create `data/db/cra_charities.duckdb`
3. For each CSV, use `read_csv_auto()` with `encoding='cp1252'` and `ignore_errors=true`
4. Load all 18 data CSVs as tables, all 7 lookup CSVs as lookup_ tables
5. Create 8 views matching the existing view definitions:

```sql
-- v_compensation
CREATE OR REPLACE VIEW v_compensation AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "300" AS ft_employees, "370" AS pt_employees, "390" AS total_compensation, *
FROM schedule_3_compensation;

-- v_financial_abc
CREATE OR REPLACE VIEW v_financial_abc AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "Form ID" AS form_id,
       "1510 Subordinate position to a parent organization?" AS is_subsidiary,
       "1510 Parent Business Number" AS parent_bn, "1510 Parent Name" AS parent_name, *
FROM financial_abc;

-- v_financial_d
CREATE OR REPLACE VIEW v_financial_d AS
SELECT "BN/Registration Number" AS bn, "Fiscal Period End" AS fiscal_period_end,
       "Form ID" AS form_id, "4200" AS total_revenue, "5000" AS total_expenditures,
       "5030" AS total_assets, *
FROM financial_d;

-- v_foreign_recipients
CREATE OR REPLACE VIEW v_foreign_recipients AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "Sequence number" AS seq, "Name of individual/organization" AS recipient_name,
       Country AS country_code, Amount AS amount
FROM schedule_2_recipients;

-- v_grants
CREATE OR REPLACE VIEW v_grants AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "Sequence number" AS seq, "Grant Recipient Name" AS recipient_name,
       "Grant Purpose" AS purpose, "Amount of Cash Disbursed" AS cash_amount,
       "Grant Country" AS country
FROM grants;

-- v_operating_countries
CREATE OR REPLACE VIEW v_operating_countries AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "Charity's Program Country Code" AS country_code
FROM schedule_2_countries;

-- v_programs
CREATE OR REPLACE VIEW v_programs AS
SELECT "BN/Registration number" AS bn, "Fiscal period end" AS fiscal_period_end,
       "Program type OP=ongoing program, NP=new program, NA=not active" AS program_type,
       "Program Description" AS description
FROM programs;

-- v_subsidiaries (depends on v_financial_abc and charity_base)
CREATE OR REPLACE VIEW v_subsidiaries AS
SELECT DISTINCT fa.bn AS subsidiary_bn, cb_sub.legal_name AS subsidiary_name,
       fa.parent_bn, cb_parent.legal_name AS parent_name
FROM v_financial_abc fa
INNER JOIN charity_base cb_sub ON fa.bn = cb_sub.bn
LEFT JOIN charity_base cb_parent ON fa.parent_bn = cb_parent.bn
WHERE fa.is_subsidiary = 'Y' AND fa.parent_bn IS NOT NULL AND trim(fa.parent_bn) != '';
```

6. Build 3 derived tables:

```sql
-- charity_base: ident joined with lookup_designation and lookup_category
CREATE OR REPLACE TABLE charity_base AS
SELECT
    i."BN/Registration Number" AS bn,
    i."Legal name" AS legal_name,
    i."Account name" AS account_name,
    i."Designation code" AS designation_code,
    ld."Description_E" AS designation_desc,
    i."Category code" AS category_code,
    i."Sub-category code" AS subcategory_code,
    lc."Category English Desc" AS category_desc,
    lc."Sub-Category English Desc" AS subcategory_desc,
    lc."Charity Type English Desc" AS charity_type,
    i."Registration date" AS registration_date,
    i."Mailing address" AS address,
    i."City" AS city,
    i."Province" AS province,
    i."Postal code" AS postal_code,
    i."Country" AS country,
    i."Contact Phone" AS phone,
    i."Contact Email" AS email,
    i."Contact URL" AS website
FROM ident i
LEFT JOIN lookup_designation ld ON i."Designation code" = ld."Designation Code"
LEFT JOIN lookup_category lc ON (i."Category code" = lc."Category Code"
                                 AND i."Sub-category code" = lc."Sub-Category Code");

-- latest_filing: most recent fiscal period per charity
CREATE OR REPLACE TABLE latest_filing AS
SELECT "BN/Registration Number" AS bn,
       MAX("Fiscal Period End") AS latest_fiscal_end
FROM financial_d
GROUP BY "BN/Registration Number";

-- charity_counts: aggregated counts per charity
CREATE OR REPLACE TABLE charity_counts AS
SELECT
    cb.bn,
    lf.latest_fiscal_end,
    CASE WHEN lf.latest_fiscal_end IS NOT NULL THEN 1 ELSE 0 END AS has_filing,
    COALESCE(p.cnt, 0) AS num_programs,
    COALESCE(g.cnt, 0) AS num_grants,
    COALESCE(c.cnt, 0) AS num_operating_countries
FROM charity_base cb
LEFT JOIN latest_filing lf ON cb.bn = lf.bn
LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM programs GROUP BY 1) p ON cb.bn = p.bn
LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM grants GROUP BY 1) g ON cb.bn = g.bn
LEFT JOIN (SELECT "BN/Registration number" AS bn, COUNT(*) AS cnt FROM schedule_2_countries GROUP BY 1) c ON cb.bn = c.bn;
```

7. Print summary of table row counts when done.

**Step 2: Run the loader to verify it produces equivalent output**

```bash
python3 scripts/load_csv.py data/raw/2024/
```

Expected: All tables created with row counts matching the original DB (within ~1% due to encoding edge cases).

**Step 3: Verify by comparing counts**

```bash
python3 -c "
import duckdb
con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
for t in con.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type IN ('BASE TABLE','VIEW') ORDER BY table_name\").fetchall():
    name = t[0]
    count = con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
    print(f'{name:35s} {count:>10,}')
con.close()
"
```

**Step 4: Commit**

```bash
git add scripts/load_csv.py
git commit -m "feat: add multi-year CSV loader script with views and derived tables"
```

---

### Task 5: Add example query files

**Files:**
- Create: `scripts/queries/sector_snapshot.sql`
- Create: `scripts/queries/charity_lookup.sql`

**Step 1: Write `scripts/queries/sector_snapshot.sql`**

A query that reproduces Blumbergs Snapshot-style aggregate stats (total revenue, total expenditures, government funding breakdown, count of active charities, etc.).

**Step 2: Write `scripts/queries/charity_lookup.sql`**

A parameterized query template for looking up a single charity by BN, returning identity, financials, programs, and compensation.

**Step 3: Commit**

```bash
git add scripts/queries/
git commit -m "feat: add example SQL query files for sector snapshot and charity lookup"
```

---

### Task 6: Update CLAUDE.md with new structure and PDF insights

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md**

Key updates:
- Change all file paths to reflect new directory structure (`data/db/cra_charities.duckdb` not root-level)
- Add loader usage: `python3 scripts/load_csv.py data/raw/2024/`
- Add multi-year instructions: drop CSVs in `data/raw/{year}/`, re-run loader
- Add context from T3010 form: Section A (identification), B (trustees), C (programs/general), D (financial), E (certification), plus Schedules 1-8
- Add context from Blumbergs Snapshot: data quality caveats (unverified by CRA, volunteer-completed, prone to errors in subjective fields), typical analysis patterns
- Update designation codes (the existing CLAUDE.md had A/B swapped): A=Public Foundation, B=Private Foundation, C=Charitable Organization — **WAIT, let me verify this from the lookup_designation query above**

Actually from the DB: A=Public Foundation, B=Private Foundation, C=Charitable Organization. The current CLAUDE.md says "A = Charitable Org, B = Public Foundation, C = Private Foundation" which is WRONG. Must fix.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new directory structure and T3010 form context"
```

---

### Task 7: Clean up old files

**Step 1: Remove original flat files that have been copied**

```bash
rm -f cra_charities_3.duckdb
rm -f t3010-24e.pdf t3010-lp-24e.pdf
rm -f "Blumbergs-Snapshot-of-Charitable-Organizations-in-the-Canadian-Charity-Sector-2022.pdf"
rm -f *.Zone.Identifier "CRA_T3010_Reference.md:Zone.Identifier"
```

Keep `CRA csvs/` as archive until user confirms deletion.

**Step 2: Final commit**

```bash
git add -A
git commit -m "chore: clean up flat files after restructuring"
```
