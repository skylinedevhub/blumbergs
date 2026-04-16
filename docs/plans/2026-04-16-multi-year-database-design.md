# Multi-Year Database Design

**Date:** 2026-04-16
**Branch:** `feature/multi-year-database`
**Status:** Approved

## Goal

Enable the DuckDB database to hold multiple years of CRA T3010 data simultaneously, so any query or script can compare across years. The CRA data release year (from the directory name, e.g. `data/raw/2024/`) is the grain — not the per-charity fiscal period end date.

## Constraints

- Backward compatibility: all existing scripts and views must work unchanged against the latest loaded year by default
- CSV files across years share the same filenames and column structure. Columns introduced in newer years are simply absent in older years.
- Fields unavailable in all selected comparison years need no special handling — they're just NULL/absent
- Design must handle 5+ years comfortably

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Multi-year strategy | `data_year` column on every raw/derived table | Simplest cross-year SQL; one database, one connection |
| Year identification | Directory name (e.g. `data/raw/2024/` → 2024) | Unambiguous CRA reporting year, not fiscal year |
| All years coexist | Yes | Enables free cross-year queries |
| Default behavior | Latest year | Views filter to `MAX(data_year)`; scripts default to latest |
| Lookup tables | Shared, no `data_year` | Reference data that only grows; overwritten on each load |

---

## 1. Database Schema Changes

### Raw Tables (18 tables)

Every raw table gets `data_year INTEGER` as the first column:

`ident`, `financial_d`, `financial_abc`, `gift`, `grants`, `programs`, `trustee`, `schedule_1_foundations`, `schedule_2_summary`, `schedule_2_countries`, `schedule_2_destinations`, `schedule_2_recipients`, `schedule_3_compensation`, `schedule_5_noncash`, `schedule_7_description`, `schedule_7_political_outside`, `schedule_7_political_resources`, `schedule_8_disbursement`

Effective primary keys become `(data_year, BN)` for single-row-per-charity tables, `(data_year, BN, sequence)` for multi-row tables.

### Derived Tables (3 tables)

`charity_base`, `latest_filing`, `charity_counts` get `data_year INTEGER` as the first column. They are rebuilt per-year after raw table loading.

- `charity_base`: joined from `ident` + lookups, scoped to one `data_year`
- `latest_filing`: most recent `Fiscal Period End` per `(data_year, BN)` — i.e., within each year's data dump, not across years
- `charity_counts`: aggregated counts per `(data_year, BN)`

### Lookup Tables (7 tables) — No Changes

`lookup_category`, `lookup_country`, `lookup_designation`, `lookup_form_versioning`, `lookup_programs`, `lookup_province`, `lookup_us_state`

These are reference data shared across years. No `data_year` column. The loader overwrites them with the latest loaded year's version (they only grow over time).

---

## 2. Loader Changes (`load_csv.py`)

### Year Detection

Extract the 4-digit year from the data directory path. `data/raw/2024/` → `data_year = 2024`. Validate it's a plausible year (e.g. 2000-2099).

### Load Behavior

1. **Database doesn't exist:** Create it fresh (first load)
2. **Database exists:** Connect read-write — do not delete it
3. **Per raw table:** `DELETE FROM table WHERE data_year = X`, then insert new rows with `data_year` prepended as the first column
4. **Lookup tables:** Overwrite entirely (no year column), same as today
5. **Derived tables:** After raw tables are loaded, `DELETE FROM derived WHERE data_year = X`, then re-derive for that year only
6. **Views:** `CREATE OR REPLACE` — they include the `MAX(data_year)` default filter

### CLI Interface

```bash
# Load 2024 data (default, same as today)
python3 scripts/load_csv.py

# Load 2023 into the same database
python3 scripts/load_csv.py data/raw/2023/

# Re-load 2024 (replaces only 2024 rows)
python3 scripts/load_csv.py data/raw/2024/

# Fresh rebuild from scratch (deletes .duckdb first)
python3 scripts/load_csv.py --rebuild
```

### CSV Import Mechanics

Instead of `CREATE TABLE AS SELECT * FROM read_csv_auto(...)`, the loader:

1. On first load of a table (table doesn't exist): `CREATE TABLE` with `data_year INTEGER` as the first column, then `INSERT INTO ... SELECT {year}, * FROM read_csv_auto(...)`
2. On subsequent loads (table exists): `DELETE FROM table WHERE data_year = {year}`, then `INSERT INTO ... SELECT {year}, * FROM read_csv_auto(...)`

Column compatibility across years: if a newer year has columns that an older year doesn't, the older year's rows will have NULL in those columns. The loader handles this explicitly:

- **Before inserting**, compare the columns in the CSV against the existing table schema
- **New columns in CSV not in table:** `ALTER TABLE ADD COLUMN` for each, then insert
- **Columns in table not in CSV (from a different year):** The `INSERT INTO` statement explicitly lists matching columns; missing ones default to NULL
- This ensures load order doesn't matter — loading 2022 then 2024 produces the same result as 2024 then 2022

---

## 3. Views and Backward Compatibility

### Default-Year Views

Every view filters to the latest loaded year using a subquery:

```sql
CREATE OR REPLACE VIEW v_financial_d AS
SELECT data_year, "BN/Registration Number" AS bn,
       "Fiscal Period End" AS fiscal_period_end,
       "4700" AS total_revenue, "5100" AS total_expenditures,
       "4200" AS total_assets, *
FROM financial_d
WHERE data_year = (SELECT MAX(data_year) FROM financial_d);
```

The `data_year` column is exposed in the view but the filter ensures single-year behavior by default. Cross-year queries use the raw tables directly: `SELECT * FROM financial_d WHERE data_year IN (2023, 2024)`.

### `v_subsidiaries` View

Depends on `charity_base` and `v_financial_abc`. Gets the same `MAX(data_year)` filter applied through its join to `charity_base`.

### Derived Table Strategy

`charity_base` remains a table (not a view) — scripts expect it to be a table. It contains all years. A companion view `v_charity_base` filters to latest year for convenience.

Downstream scripts that join through `charity_base` need a one-line addition: `AND cb.data_year = {year}` in their WHERE clause. This flows through `get_scope_filter()`.

### Year Filter Helper

Add a `year_filter(year=None)` helper to shared scope filtering logic:

- `year_filter(2024)` → `AND cb.data_year = 2024`
- `year_filter(None)` → `AND cb.data_year = (SELECT MAX(data_year) FROM charity_base)`

This is appended to all WHERE clauses via `get_scope_filter()`.

---

## 4. Validation Script (`validate_db.py`)

### Per-Year Validation

All existing checks (row counts, schema, referential integrity) run per loaded year. The script iterates over all `DISTINCT data_year` values in the database.

### New CLI

```bash
# Validate all loaded years (default)
python3 scripts/validate_db.py

# Validate a specific year only
python3 scripts/validate_db.py --year 2024
```

### New Cross-Year Checks

- No duplicate `(data_year, BN)` pairs in single-row-per-charity tables
- Table coverage consistency across years (warning, not failure)
- Year summary header: "Database contains years: 2022, 2023, 2024"
- Column availability differences across years logged as informational

---

## 5. Report Script Impact

### Common Pattern

All report scripts get a `--year` flag (default: latest year in database). The year flows through `get_scope_filter()` which appends the year filter to all WHERE clauses.

### `generate_snapshot.py`

- `--year YYYY` flag added
- Output directory: `data/exports/snapshots_{year}/`
- No structural changes to sheet builders

### `generate_comparison.py`

- `--years YYYY,YYYY` flag (default: two most recent years)
- **Phase 1 (this feature):** hardcoded 2023 dicts stay, `--year` flag controls the "current" year
- **Phase 2 (follow-up):** when both years are loaded, replace hardcoded dicts with live queries

### `generate_snapshot_articles.py`

- `--year YYYY` flag
- Same `get_scope_filter()` year injection
- Prior-year comparison: same fallback strategy (hardcoded dicts until both years loaded)

### `generate_jewish_sector.py`

- `--year YYYY` flag

---

## 6. Out of Scope

| Item | Reason |
|------|--------|
| Data explorer (`data-explorer.html`) | Queries via Neon API, needs separate UI design for year selection |
| Replacing hardcoded 2023 comparison dicts | Follow-up after multi-year database is proven |
| Cross-year derived tables (e.g., charity growth tracking) | Future analytical feature |
| DuckDB version upgrade | 1.4.4 handles all requirements |

---

## 7. Migration Path

1. First run after the change requires `--rebuild` flag (or manual deletion of `.duckdb` file) since the schema changes
2. Load years in any order: `load_csv.py data/raw/2024/`, then `load_csv.py data/raw/2023/`, etc.
3. Existing scripts work immediately — views default to latest year
4. CLAUDE.md updated with multi-year schema docs and commands

No data migration script is needed. The loader rebuilds from source CSVs, which are the authoritative data.

---

## 8. File Changes Summary

| File | Change Type |
|------|-------------|
| `scripts/load_csv.py` | Major rewrite — additive loading, `data_year` injection, `--rebuild` flag |
| `scripts/validate_db.py` | Moderate — per-year validation loop, `--year` flag, cross-year checks |
| `scripts/reports/generate_snapshot.py` | Minor — `--year` flag, year in `get_scope_filter()` |
| `scripts/reports/generate_comparison.py` | Minor — `--years` flag, year in scope filter |
| `scripts/reports/generate_snapshot_articles.py` | Minor — `--year` flag, year in scope filter |
| `scripts/reports/generate_jewish_sector.py` | Minor — `--year` flag, year in scope filter |
| `CLAUDE.md` | Updated schema docs, commands, multi-year notes |
