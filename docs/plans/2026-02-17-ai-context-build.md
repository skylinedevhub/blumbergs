# AI Context Build — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Download ~50-60 Blumbergs PDFs, extract their content, and synthesize into structured context documents that give future Claude sessions expert-level T3010 understanding. Also add project infrastructure (requirements.txt, validation script, SQL fixes).

**Architecture:** Three phases — (1) infrastructure fixes, (2) PDF download + text extraction, (3) knowledge synthesis into `docs/context/` markdown files. PDFs are downloaded to `docs/reference/blumbergs/` as working material. Text is extracted with pymupdf. Context docs are the deliverable.

**Tech Stack:** Python 3, DuckDB, pymupdf (fitz), wget, openpyxl

---

## Phase 1: Infrastructure

### Task 1: Create requirements.txt

**Files:**
- Create: `requirements.txt`

**Step 1: Write requirements.txt**

```
duckdb==1.4.4
openpyxl
pymupdf
```

**Step 2: Verify packages match**

Run: `python3 -c "import duckdb; print(duckdb.__version__)" && python3 -c "import openpyxl; print('ok')" && python3 -c "import fitz; print('ok')"`
Expected: `1.4.4`, `ok`, `ok`

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements.txt pinning duckdb, openpyxl, pymupdf"
```

---

### Task 2: Fix SQL queries to use TRY_CAST

**Files:**
- Modify: `scripts/queries/sector_snapshot.sql` (lines 7-19, all CAST calls)
- Modify: `scripts/queries/charity_lookup.sql` (lines 23-31, all CAST calls)

**Why:** `CAST(REPLACE(...) AS DECIMAL)` throws `ConversionException` on rows with non-numeric values (letters, blanks). `TRY_CAST` returns NULL instead.

**Step 1: Fix sector_snapshot.sql**

Replace every `CAST(REPLACE(REPLACE(` with `TRY_CAST(REPLACE(REPLACE(` throughout the file. There are 12 occurrences in the CTE.

**Step 2: Fix charity_lookup.sql**

Replace every `CAST(REPLACE(REPLACE(` with `TRY_CAST(REPLACE(REPLACE(` in the financial summary query. There are 8 occurrences.

**Step 3: Verify both queries still run**

Run: `python3 -c "import duckdb; con=duckdb.connect('data/db/cra_charities.duckdb',read_only=True); print(con.execute(open('scripts/queries/sector_snapshot.sql').read()).fetchdf().to_string()); con.close()"`
Expected: Same results as before but without risk of ConversionException on edge-case rows.

**Step 4: Commit**

```bash
git add scripts/queries/sector_snapshot.sql scripts/queries/charity_lookup.sql
git commit -m "fix: use TRY_CAST in SQL queries to handle non-numeric values"
```

---

### Task 3: Create validate_db.py

**Files:**
- Create: `scripts/validate_db.py`

**Step 1: Write the validation script**

```python
#!/usr/bin/env python3
"""
Validate the CRA charities DuckDB database after loading.

Checks row counts, schema presence, referential integrity,
and cross-table consistency. Exit code 0 = all checks pass.

Usage:
    python3 scripts/validate_db.py
"""

import sys
import os
import duckdb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "db", "cra_charities.duckdb")

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    global PASS, FAIL

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        print("Run: python3 scripts/load_csv.py")
        sys.exit(1)

    con = duckdb.connect(DB_PATH, read_only=True)

    # --- Row count checks ---
    print("\n--- Row Count Checks ---")
    tables_expected = {
        "ident": (80000, 90000),
        "financial_d": (80000, 90000),
        "financial_abc": (80000, 90000),
        "charity_base": (80000, 90000),
        "programs": (85000, 110000),
        "schedule_3_compensation": (35000, 50000),
        "grants": (10000, 20000),
        "lookup_designation": (3, 3),
        "lookup_province": (13, 13),
    }
    for table, (lo, hi) in tables_expected.items():
        try:
            count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            check(f"{table} count={count:,}", lo <= count <= hi,
                  f"expected {lo:,}-{hi:,}")
        except Exception as e:
            check(f"{table} exists", False, str(e))

    # --- Schema checks ---
    print("\n--- Schema Checks ---")
    schema_checks = {
        "financial_d": ["BN/Registration Number", "Fiscal Period End", "4700", "5100", "4200"],
        "financial_abc": ["BN/Registration number", "Fiscal period end", "Form ID"],
        "charity_base": ["bn", "legal_name", "designation_code", "province"],
        "schedule_3_compensation": ["BN/Registration number", "300", "370", "390"],
    }
    for table, columns in schema_checks.items():
        try:
            cols = [r[0] for r in con.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            ).fetchall()]
            for col in columns:
                check(f"{table} has column '{col}'", col in cols,
                      f"available: {cols[:5]}...")
        except Exception as e:
            check(f"{table} schema readable", False, str(e))

    # --- View checks ---
    print("\n--- View Checks ---")
    views = ["v_financial_d", "v_financial_abc", "v_compensation",
             "v_programs", "v_grants", "v_subsidiaries"]
    for view in views:
        try:
            count = con.execute(f'SELECT COUNT(*) FROM "{view}"').fetchone()[0]
            check(f"{view} queryable (count={count:,})", count > 0)
        except Exception as e:
            check(f"{view} queryable", False, str(e))

    # --- Referential integrity ---
    print("\n--- Referential Integrity ---")
    orphan_count = con.execute("""
        SELECT COUNT(*) FROM financial_d fd
        LEFT JOIN ident i ON fd."BN/Registration Number" = i."BN/Registration Number"
        WHERE i."BN/Registration Number" IS NULL
    """).fetchone()[0]
    check(f"financial_d BNs all in ident (orphans={orphan_count})", orphan_count == 0)

    orphan_s3 = con.execute("""
        SELECT COUNT(*) FROM schedule_3_compensation s
        LEFT JOIN ident i ON s."BN/Registration number" = i."BN/Registration Number"
        WHERE i."BN/Registration Number" IS NULL
    """).fetchone()[0]
    check(f"schedule_3 BNs all in ident (orphans={orphan_s3})", orphan_s3 == 0)

    # --- Cross-table consistency ---
    print("\n--- Cross-Table Consistency ---")
    # charity_base should match ident count
    ident_count = con.execute("SELECT COUNT(*) FROM ident").fetchone()[0]
    cb_count = con.execute("SELECT COUNT(*) FROM charity_base").fetchone()[0]
    check(f"charity_base count matches ident ({cb_count:,} vs {ident_count:,})",
          cb_count == ident_count)

    # Line 4570 (total govt) vs computed 4540+4550+4560
    govt_check = con.execute("""
        SELECT
            SUM(TRY_CAST(REPLACE(REPLACE("4540",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4550",'$',''),',','') AS DECIMAL)) +
            SUM(TRY_CAST(REPLACE(REPLACE("4560",'$',''),',','') AS DECIMAL)) AS computed,
            SUM(TRY_CAST(REPLACE(REPLACE("4570",'$',''),',','') AS DECIMAL)) AS reported
        FROM financial_d
    """).fetchone()
    computed_govt, reported_govt = govt_check
    check(f"Line 4570 unreliable (computed={computed_govt:,.0f} vs reported={reported_govt:,.0f})",
          abs(computed_govt - reported_govt) > 1000000,
          "If these match, 4570 may have been fixed")

    # --- Summary ---
    print(f"\n{'='*50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    print(f"{'='*50}")

    con.close()
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
```

**Step 2: Run validation**

Run: `python3 scripts/validate_db.py`
Expected: All checks PASS (exit code 0)

**Step 3: Commit**

```bash
git add scripts/validate_db.py
git commit -m "feat: add database validation script with integrity checks"
```

---

## Phase 2: Download & Extract PDFs

### Task 4: Compile PDF URL list from blog posts

**Files:**
- Create: `docs/reference/blumbergs/pdf_urls.txt`

Visit each blog post URL listed below, extract the PDF download link, and compile into a text file with one URL per line. The PDF URLs follow the pattern `https://www.canadiancharitylaw.ca/wp-content/uploads/YYYY/MM/filename.pdf`.

**Blog posts to visit (sector-wide Snapshots):**

```
https://www.canadiancharitylaw.ca/blog/blumbergs_canadian_charity_sector_snapshot_2010_a_little_more_perspective_o/
https://www.canadiancharitylaw.ca/blog/blumbergs_canadian_charity_sector_snapshot_2011_-understanding_the_charity_/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_canadian_charity_sector_2012/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_canadian_charity_sector_2013/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_canadian_charity_sector_2014/
https://www.canadiancharitylaw.ca/blog/blumbergs_canadian_charity_sector_snapshot_2015/
https://www.canadiancharitylaw.ca/blog/blumbergs_canadian_charity_sector_snapshot_2016/
https://www.canadiancharitylaw.ca/blog/blumbergs_canadian_charity_sector_snapshot_2017/
https://www.canadiancharitylaw.ca/blog/blumbergs-canadian-charity-sector-snapshot-2018/
https://www.canadiancharitylaw.ca/blog/blumbergs-canadian-charity-sector-snapshot-2019-information-on-the-canadian-registered-charity-sector-from-the-t3010-filings-of-canadian-charities/
https://www.canadiancharitylaw.ca/blog/blumbergs-canadian-charity-sector-snapshot-2020/
https://www.canadiancharitylaw.ca/blog/blumbergs-canadian-charity-sector-snapshot-2021/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-canadian-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-canadian-charity-sector-2023/
```

**Blog posts to visit (provincial Snapshots):**

```
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_ontario_charity_sector_2011/
https://www.canadiancharitylaw.ca/blog/blumbergs_ontario_charity_sector_snapshot_2012/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_ontario_charity_sector_2014/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_ontario_charity_sector_2015/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-ontario-charity-sector-2018/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-ontario-charity-sector-2019-information-on-registered-charities-in-ontario-from-the-cra-t3010-annual-filings/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-ontario-charity-sector-2020-a-census-of-the-ontario-charity-sector/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-ontario-charity-sector-2021-a-census-of-the-ontario-charity-sector/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-ontario-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-manitoba-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-manitoba-charity-sector-2023/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_alberta_charity_sector_2012/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-alberta-charity-sector-2018/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-alberta-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs_snapshot_of_the_bc_charity_sector_2012/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-british-columbia-charity-sector-2018/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-british-columbia-charity-sector-2021-a-census-of-the-bc-charity-sector/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-british-columbia-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-quebec-charity-sector-2018/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-quebec-charity-sector-2021-a-census-of-the-quebec-charity-sector/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-quebec-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-atlantic-provinces-charity-sector-2021/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-atlantic-provinces-charity-sector-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshot-of-the-nova-scotia-charity-sector-2018-providing-data-on-the-size-and-scope-of-ns-charity-sector/
```

**Blog posts to visit (designation Snapshots):**

```
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshots-of-designations-charitable-organizations-public-foundations-and-private-foundations-2021/
https://www.canadiancharitylaw.ca/blog/blumbergs-snapshots-of-designations-charitable-organizations-public-foundations-and-private-foundations-2022/
```

**Blog posts to visit (DAF reports):**

```
https://www.canadiancharitylaw.ca/blog/some-preliminary-data-from-the-2023-t3010-on-donor-advised-funds-dafs-in-canada/
https://www.canadiancharitylaw.ca/blog/blumbergs-daf-report-donor-advised-fund-accounts-in-2024/
```

**Blog posts to visit (pre-budget submissions):**

```
https://www.canadiancharitylaw.ca/blog/blumbergs-pre-budget-submission-for-the-federal-budget-2021-relating-to-charities-transparency-and-other-issues/
https://www.canadiancharitylaw.ca/blog/blumbergs-pre-budget-submission-february-25-2022/
https://www.canadiancharitylaw.ca/blog/blumbergs-pre-budget-submission-for-the-2023-canadian-federal-budget/
https://www.canadiancharitylaw.ca/blog/blumbergs-pre-budget-submission-for-the-2024-canadian-federal-budget/
https://www.canadiancharitylaw.ca/blog/blumbergs-pre-budget-submission-for-the-2025-canadian-federal-budget-dated-july-28-2025/
```

**Blog posts to visit (other):**

```
https://www.canadiancharitylaw.ca/blog/snapshot_on_political_activities_in_the_canadian_charity_sector_2013/
https://www.canadiancharitylaw.ca/blog/blumbergs-written-submission-to-the-department-of-finance-with-respect-to-the-disbursement-quota-for-canadian-registered-charities/
https://www.canadiancharitylaw.ca/blog/mark-blumbergs-written-submission-to-the-finance-committee-on-transparency-in-the-non-profit-and-charity-sector/
https://www.canadiancharitylaw.ca/blog/blumbergs_financial_snapshot_of_the_canadian_charity_sector/
https://www.canadiancharitylaw.ca/blog/blumbergs_pre_budget_brief_to_the_finance_committee/
https://www.canadiancharitylaw.ca/blog/blumbergs_budget_submission_to_standing_committee_on_finance/
```

**Step 1:** Use WebFetch on each URL to extract the PDF link. Batch by category. Record each PDF URL into `docs/reference/blumbergs/pdf_urls.txt`.

**Step 2:** Verify the file has ~50-60 PDF URLs, one per line.

---

### Task 5: Download all PDFs

**Files:**
- Create: `docs/reference/blumbergs/snapshots/` (directory)
- Create: `docs/reference/blumbergs/provincial/` (directory)
- Create: `docs/reference/blumbergs/other/` (directory)

**Step 1:** Create directories:

```bash
mkdir -p docs/reference/blumbergs/snapshots
mkdir -p docs/reference/blumbergs/provincial
mkdir -p docs/reference/blumbergs/other
```

**Step 2:** Download sector-wide Snapshot PDFs to `snapshots/`:

```bash
cd docs/reference/blumbergs/snapshots && wget -i ../pdf_urls_snapshots.txt
```

(Or use individual wget commands for each PDF URL extracted in Task 4.)

**Step 3:** Download provincial PDFs to `provincial/`.

**Step 4:** Download DAF, pre-budget, and other PDFs to `other/`.

**Step 5:** Verify downloads by counting files:

```bash
find docs/reference/blumbergs/ -name "*.pdf" | wc -l
```

Expected: ~50-60 PDFs

**Note:** Add `docs/reference/blumbergs/` to `.gitignore` — these are working material, not tracked.

---

### Task 6: Extract text from all PDFs

**Files:**
- Create: `docs/reference/blumbergs/extracted/` (directory with .txt files)

**Step 1:** Write a quick extraction script and run it:

```python
#!/usr/bin/env python3
"""Extract text from all Blumbergs PDFs using pymupdf."""
import os
import fitz  # pymupdf

PDF_DIR = "docs/reference/blumbergs"
OUT_DIR = os.path.join(PDF_DIR, "extracted")
os.makedirs(OUT_DIR, exist_ok=True)

for subdir in ["snapshots", "provincial", "other"]:
    dirpath = os.path.join(PDF_DIR, subdir)
    if not os.path.isdir(dirpath):
        continue
    for fname in sorted(os.listdir(dirpath)):
        if not fname.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(dirpath, fname)
        txt_path = os.path.join(OUT_DIR, fname.replace(".pdf", ".txt"))
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n---PAGE BREAK---\n"
        doc.close()
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  {fname} -> {len(text):,} chars")

print(f"\nExtracted to {OUT_DIR}")
```

Run: `python3 scripts/extract_pdfs.py`
Expected: One .txt file per PDF in `docs/reference/blumbergs/extracted/`

**Step 2:** Spot-check a few extracted files to verify text quality.

---

## Phase 3: Knowledge Synthesis

### Task 7: Create data-interpretation-guide.md

**Files:**
- Create: `docs/context/data-interpretation-guide.md`

**Step 1:** Read extracted text from all sector-wide Snapshots (2010-2023) and synthesize.

**Content to extract and organize:**

1. **Revenue line interpretation** — What counts as "tax-receipted gifts" (line 4500) vs "gifts from other charities" (4510) vs "total revenue from all sources" (4700). How government funding is split (federal 4540, provincial 4550, municipal 4560). Why line 4570 is unreliable.

2. **Expenditure categorization** — What goes in "charitable program expenditures" (5000) vs "management and admin" (5010) vs "fundraising" (5020). How "gifts to qualified donees" (5050) interacts with total expenditures. Why some charities show $0 program expenditures.

3. **Balance sheet gotchas** — Lines 4100 (cash), 4140 (long-term investments), 4200 (total assets), 4250 (assets not used for charitable activities), 4350 (liabilities). What "total assets" means for different designation types.

4. **Compensation data** — Schedule 3 salary bands (305-345), why line 390 is VARCHAR, relationship to financial_d line 4880. Why these sometimes disagree.

5. **Common errors and misreporting** — Documented patterns from Blumbergs methodology notes: volunteers filling forms, subjective categorization, political activity misreporting, double-counting in parent/subsidiary relationships.

6. **Form version changes** — V23 vs V24 differences. Fields 4575, 4580 (revenue from outside Canada) added in V24. Questions that changed meaning between versions.

7. **Designation-specific patterns** — How Public Foundations (A) vs Private Foundations (B) vs Charitable Organizations (C) differ in practice: revenue sources, expenditure patterns, typical size, compensation.

**Step 2:** Commit.

```bash
git add docs/context/data-interpretation-guide.md
git commit -m "docs: add T3010 data interpretation guide from Blumbergs publications"
```

---

### Task 8: Create sector-trends.md

**Files:**
- Create: `docs/context/sector-trends.md`

**Step 1:** Read extracted text from all Snapshots chronologically. Build a historical table and narrative.

**Content to extract:**

1. **Historical metrics table** — For each year 2010-2023:
   - Total registered charities
   - Total revenue (and breakdown: gifts, government, other)
   - Total expenditures (and breakdown: programs, admin, fundraising)
   - Total assets
   - Employee counts
   - Key ratios (government share of revenue, program spending %, etc.)

2. **COVID impact** — 2019 vs 2020 vs 2021 changes. Government funding spike, donation changes, program spending shifts.

3. **DAF growth** — When DAFs first appeared in data, growth trajectory, current scale.

4. **Government funding trends** — Federal vs provincial vs municipal over time.

5. **Sector composition changes** — New registrations vs revocations. Category shifts.

6. **Baseline expectations** — What ranges are "normal" for key metrics, useful for sanity-checking new data.

**Step 2:** Commit.

```bash
git add docs/context/sector-trends.md
git commit -m "docs: add sector trends from 14 years of Blumbergs Snapshots"
```

---

### Task 9: Create methodology-notes.md

**Files:**
- Create: `docs/context/methodology-notes.md`

**Step 1:** Read methodology sections from Snapshots. Synthesize.

**Content to extract:**

1. **Inclusion criteria** — Which charities are included in each Snapshot. How non-filers are handled. When "fiscal period end" means "filed for that year" vs "fiscal year ending in that year."

2. **Aggregation rules** — How currency fields are summed (the TRY_CAST pattern). How missing/blank values are treated. Whether zeroes and blanks mean the same thing.

3. **Provincial breakdowns** — By mailing address province. Known issues (national charities headquartered in Ontario, subsidiary vs parent province attribution).

4. **Data quality caveats** — Self-reported, unverified, volunteer-completed. Subjective categorization. Known areas of systematic error.

5. **Y/N question interpretation** — What blank vs "N" vs "Y" means for Section C questions. Questions where non-response is common.

6. **Subsidiary handling** — How parent/subsidiary relationships are counted. Double-counting risks in financial aggregation.

**Step 2:** Commit.

```bash
git add docs/context/methodology-notes.md
git commit -m "docs: add Snapshot methodology notes for data analysis"
```

---

### Task 10: Create regulatory-context.md

**Files:**
- Create: `docs/context/regulatory-context.md`

**Step 1:** Read pre-budget submissions, disbursement quota submission, political activities snapshot, and finance committee submissions. Synthesize.

**Content to extract:**

1. **Disbursement quota** — Rules as of 2023 (3.5% of assets not used for charitable activities). Pre-2023 rules (historical comparison). How this shows up in schedule_8_disbursement. Why it matters for foundation analysis.

2. **DAF rules** — What a DAF is. Reporting requirements (lines 5860-5864 in financial_abc). When DAF reporting became mandatory. Key DAF metrics.

3. **Foreign activity reporting** — Schedule 2 requirements. When charities must report foreign activities. Country-by-country reporting. Transfer rules.

4. **Political activity** — Historical limits (pre-2018 10% rule), current rules (no limit after Charities can engage in public policy). Why schedule 7 data may be unreliable.

5. **Transparency requirements** — What's public vs confidential in T3010 data. CRA Charities Listing vs open data. What changed when.

6. **Qualified donees** — What a QD is. How gifts to QDs (line 5050) differ from grants to non-QDs. Schedule 2 vs grants table.

**Step 2:** Commit.

```bash
git add docs/context/regulatory-context.md
git commit -m "docs: add regulatory context for T3010 data interpretation"
```

---

## Phase 4: Final Integration

### Task 11: Update MEMORY.md with key single-line patterns

**Files:**
- Modify: `/home/yb97/.claude/projects/-home-yb97-src-blumbergs/memory/MEMORY.md`

**Step 1:** Add concise single-line entries distilled from the context docs:

- Historical baselines (typical revenue range, charity count growth)
- Key regulatory dates (DAF reporting start year, DQ change year)
- Data quality red flags to check for
- Provincial breakdown caveats

Keep total MEMORY.md under 200 lines.

**Step 2:** No git commit needed (memory files are not in repo).

---

### Task 12: Update CLAUDE.md and .gitignore

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.gitignore`

**Step 1:** Add to CLAUDE.md directory structure:

```markdown
│   ├── context/            # AI-optimized context docs (synthesized from publications)
```

Add to CLAUDE.md a new section after "Reference Documentation":

```markdown
## Context Documents (AI-Optimized)

These docs are synthesized from 14 years of Blumbergs publications. Read them when you need deep domain knowledge beyond schema docs.

- `docs/context/data-interpretation-guide.md` — How to interpret each T3010 line correctly
- `docs/context/sector-trends.md` — Historical baselines 2010-2023 for sanity-checking
- `docs/context/methodology-notes.md` — How Snapshots are built, data quality caveats
- `docs/context/regulatory-context.md` — DQ rules, DAF, foreign activity, political activity
```

Add to CLAUDE.md Common Commands:

```bash
# Validate database integrity after loading
python3 scripts/validate_db.py
```

**Step 2:** Add to `.gitignore`:

```
# Working material (PDFs downloaded for text extraction, not tracked)
docs/reference/blumbergs/
```

**Step 3:** Commit everything.

```bash
git add CLAUDE.md .gitignore docs/context/
git commit -m "feat: add AI context docs, validation script, and project infrastructure"
```

---

### Task 13: Stage and commit the 2023 Snapshot PDF and design docs

**Files:**
- Stage: `docs/reference/Blumbergs-Canadian-Charity-Sector-Snapshot-2023.pdf`
- Stage: `docs/plans/2026-02-17-ai-context-build-design.md`
- Stage: `docs/plans/2026-02-17-ai-context-build.md`

**Step 1:** Commit pending changes.

```bash
git add docs/reference/Blumbergs-Canadian-Charity-Sector-Snapshot-2023.pdf
git add docs/plans/2026-02-17-ai-context-build-design.md
git add docs/plans/2026-02-17-ai-context-build.md
git add CLAUDE.md
git commit -m "docs: add 2023 Snapshot PDF, design docs, and CLAUDE.md updates"
```

---

## Execution Notes

- **Task 4 is the most labor-intensive** — visiting ~55 blog posts to extract PDF URLs. Parallelize web fetches where possible (batch by category).
- **Tasks 7-10 are the highest-value** — the knowledge synthesis. Read extracted text carefully and distill practical rules, not just summaries.
- **PDF downloads go to gitignored directory** — they're working material. The context docs are the tracked deliverable.
- **Some older PDFs may not have extractable text** (scanned images). Use pymupdf image rendering + Claude's vision for those.
- **The sector_snapshot.sql and charity_lookup.sql fixes** (Task 2) are independent and can be committed immediately.
