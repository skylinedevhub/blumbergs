# Snapshot Generator Design

**Date**: 2026-02-23
**Goal**: Generate Excel workbooks with T3010 line totals for Canada, provincial, and designation snapshots using 2024 data.

## Background

The Blumbergs Snapshot is a filled-in T3010 form where every field shows the aggregate total across all charities in scope. The blue text overlaid on the form represents ~150+ computed values spanning Sections A-D, Schedules 1-3, 5, 6, and 8.

## Deliverables

| Report Type | Filter | Workbooks |
|-------------|--------|-----------|
| Canada | All charities | 1 |
| Provincial | By province | 9 (ON, QC, BC, AB, MB, SK, NS, NB, Atlantic=NB+NS+NL+PE) |
| Designation | By designation code | 3 (A=Public Fdn, B=Private Fdn, C=Charitable Org) |

**Total**: 13 workbooks, identical structure, different filter scopes.

## Architecture

Single script: `scripts/reports/generate_snapshot.py`

### Filter Mechanism

```python
def get_scope_filter(filter_type, filter_value):
    """Returns SQL WHERE clause fragment and description string."""
    # filter_type: "all", "province", "designation"
    # filter_value: None, "ON", "Atlantic", "A", etc.
    # Atlantic = ('NB','NS','NL','PE')
```

All queries JOIN against `charity_base` (which has `bn`, `province`, `designation_code`) to apply the scope filter consistently. The BN column varies by table (`"BN/Registration Number"` vs `"BN/Registration number"`) — handle in JOIN logic.

### Workbook Sheet Structure

Each workbook has 8 sheets mirroring T3010 sections:

#### Sheet 1: "Section A - Identification"
Source: `ident` + `charity_base`

| Field | Query |
|-------|-------|
| Total charities | COUNT(*) from ident (in scope) |
| By designation (A/B/C) | COUNT GROUP BY designation_code |
| Provided phone/email/website | COUNT WHERE non-null |
| A1 (1510) subordinate? | Y/N count from financial_abc |
| A2 (1570) wound up? | Y/N count |
| A3 (1600) designated? | Y/N count |

#### Sheet 2: "Section C - Programs & General"
Source: `financial_abc`

| Field | Query |
|-------|-------|
| C1 (1800) active? | Y/N count |
| Ongoing/new programs | COUNT from programs table |
| C3 (2000) gifts to QDs? | Y/N count |
| C4 (2100) outside Canada? | Y/N count |
| C6 (2500-2660) fundraising methods | Count per method code |
| C7 (2700) external fundraisers? | Y/N + lines 5450/5460 sums |
| C7 payment methods (2730-2790) | Count per method |
| C8 (3200) compensate directors? | Y/N count |
| C9 (3400) employment expenses? | Y/N count |
| C10 (3900) $10K+ non-resident? | Y/N count |
| C11 (4000) non-cash gifts? | Y/N count |
| C12-C15 (5800-5830) | Y/N counts |
| C16 (5840/5841) grants to non-QDs | Y/N + lines 5842/5843 |
| C17 (5850) DQ threshold? | Y/N count |
| C18 (5860-5864) DAF fields | Y/N + count/sums |

#### Sheet 3: "Section D - Financial Summary"
Source: `financial_d`

Lines: 4020 (accrual/cash count), 4050 (own land Y/N), 4200, 4350, 4400, 4490, 4500, 5610, 4510, 4530, 4540, 4550, 4560, 4565, 4570 (computed), 4571, 4575, 4580, 4590 (from Sch6=4630), 4600 (from Sch6=4640), 4650, 4700, 4860, 4810, 4920, 4950, 5000, 5010, 5045, 5050, 5100.

All currency fields: `TRY_CAST(REPLACE(REPLACE(col, '$', ''), ',', '') AS DECIMAL)`.

#### Sheet 4: "Schedule 1 - Foundations"
Source: `schedule_1_foundations`

Lines: 100, 110 (Y/N counts), 111, 112 (currency sums), 120, 130 (Y/N counts, private only).

#### Sheet 5: "Schedule 2 - Foreign Activities"
Source: `schedule_2_summary`

Lines: 200 (currency sum), 210, 220, 240, 250, 260 (Y/N counts), 230 (currency sum).

#### Sheet 6: "Schedule 3 - Compensation"
Source: `schedule_3_compensation`

Lines: 300 (BIGINT sum), 305-345 (BIGINT sums per band), 370 (BIGINT sum), 380 (currency sum), 390 (currency sum).

#### Sheet 7: "Schedule 5 - Non-cash Gifts"
Source: `schedule_5_noncash`

Lines: 500-560 (Y/N counts per gift type), 580 (currency sum total).

#### Sheet 8: "Schedule 6 - Detailed Financials"
Source: `financial_d`

All lines from the detailed Schedule 6 form (assets 4100-4200, liabilities 4300-4350, revenue 4500-4700, expenditures 4800-5100, other 5500-5910). This is the most comprehensive sheet with ~70 line items.

#### Sheet 9: "Schedule 8 - Disbursement Quota"
Source: `schedule_8_disbursement`

Lines: 805-890 (all currency sums).

### Data Type Handling

| Table | Column Pattern | Type | Aggregation |
|-------|---------------|------|-------------|
| financial_d | Most columns | VARCHAR ($) | TRY_CAST + SUM |
| financial_abc | Y/N fields | VARCHAR (Y/N) | COUNT WHERE = 'Y' / 'N' |
| financial_abc | 5861 | BIGINT | SUM |
| financial_abc | 5450, 5460, 5843, 5862-5864 | VARCHAR ($) | TRY_CAST + SUM |
| schedule_3 | 300, 305-345, 370 | BIGINT | SUM |
| schedule_3 | 380, 390 | VARCHAR ($) | TRY_CAST + SUM |
| All schedule tables | Y/N fields | VARCHAR | COUNT |
| All schedule tables | $ fields | VARCHAR ($) | TRY_CAST + SUM |

### BN Column Name Mapping

| Table | BN Column |
|-------|-----------|
| ident | `"BN/Registration Number"` |
| charity_base | `bn` |
| financial_d | `"BN/Registration Number"` |
| financial_abc | `"BN/Registration number"` (lowercase n) |
| schedule_1_foundations | `"BN/Registration number"` |
| schedule_2_summary | `"BN/Registration number"` |
| schedule_3_compensation | `"BN/Registration number"` |
| schedule_5_noncash | `"BN/Registration number"` |
| schedule_8_disbursement | `"BN/Registration Number"` |

### CLI Interface

```bash
# All 13 workbooks
python3 scripts/reports/generate_snapshot.py --all

# Canada only
python3 scripts/reports/generate_snapshot.py

# Single province
python3 scripts/reports/generate_snapshot.py --province ON

# All provincial
python3 scripts/reports/generate_snapshot.py --provincial

# All designations
python3 scripts/reports/generate_snapshot.py --designation

# Single designation
python3 scripts/reports/generate_snapshot.py --designation A
```

### Output Files

Directory: `data/exports/snapshots_2024/`

```
snapshot_2024_canada.xlsx
snapshot_2024_ON.xlsx
snapshot_2024_QC.xlsx
snapshot_2024_BC.xlsx
snapshot_2024_AB.xlsx
snapshot_2024_MB.xlsx
snapshot_2024_SK.xlsx
snapshot_2024_NS.xlsx
snapshot_2024_NB.xlsx
snapshot_2024_atlantic.xlsx
snapshot_2024_designation_A.xlsx
snapshot_2024_designation_B.xlsx
snapshot_2024_designation_C.xlsx
```

### Known Gotchas

1. **Line 4570** (total govt): UNRELIABLE — always compute as 4540+4550+4560
2. **Line 4880 vs 390**: Both are total compensation; include both with cross-check
3. **Schedule 3 mixed types**: Lines 300/370 are BIGINT, line 390 is VARCHAR
4. **financial_abc Y/N nulls**: Some charities have NULL (didn't answer). Count Y and N separately; total - Y - N = unanswered.
5. **Province filter**: Uses `ident.Province`, not charity_base (both have it, but ident is authoritative)
6. **Atlantic combined**: NB + NS + NL + PE summed together
