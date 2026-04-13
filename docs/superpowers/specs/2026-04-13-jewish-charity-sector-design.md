# Jewish Charity Sector Workbook — Design Spec

**Date**: 2026-04-13
**Output**: `data/exports/jewish_sector_2024.xlsx`
**Script**: `scripts/reports/generate_jewish_sector.py`

## Overview

Generate an Excel workbook indexing all identifiable Jewish charities in the CRA T3010 database across three tiers of identification confidence. The workbook serves as a directory/index — financial enrichment will be added later as needed.

## Sheet 1: "Judaism Category"

**Source**: `charity_base WHERE category_desc LIKE '%Judaism%'`

This is the highest-confidence tier — charities the CRA itself classifies under Judaism.

**Expected count**: ~391

**Columns**:
| Column | Source |
|--------|--------|
| BN | `charity_base.bn` |
| Legal Name | `charity_base.legal_name` |
| Designation | `charity_base.designation_desc` |
| Category | `charity_base.category_desc` |
| Subcategory | `charity_base.subcategory_desc` |
| City | `charity_base.city` |
| Province | `charity_base.province` |
| Registration Date | `charity_base.registration_date` |
| Website | `charity_base.website` |

**Sort**: Province ASC, Legal Name ASC

## Sheet 2: "Name-Identified"

**Source**: Charities matching Jewish/Hebrew name keywords that are NOT already on Sheet 1.

### High-confidence keywords (include directly)
`jewish`, `hebrew`, `synagogue`, `chabad`, `torah`, `yeshiva`, `talmud`, `sephardi`, `zionist`, `mizrachi`, `kosher`, `hillel`, `hadassah`, `bnai brith`

Applied against `LOWER(legal_name)`.

### Medium-confidence keywords (category-filtered)
`shalom`, `israel`, `beth` — include ONLY if the charity's `category_desc` falls in a religion-adjacent set:
- `Judaism` (already on Sheet 1, so effectively excluded)
- `Support of Religion`
- `Foundations Advancing Religions`
- `Other Religions`
- Any category where `LOWER(legal_name)` also matches a high-confidence keyword

This filters out Christian churches ("Bethel", "Shalom Christian Assembly") and unrelated orgs ("Friends of Israel Environment Fund").

### Additional filtering
- Exclude charities already on Sheet 1 (Judaism category)
- For `beth`: also exclude names matching common Christian patterns (`bethel`, `bethany`, `bethesda`, `bethlehem`)

**Columns**: Same as Sheet 1, plus:
| Column | Source |
|--------|--------|
| Match Keyword | The keyword(s) that triggered inclusion |

**Sort**: Province ASC, Legal Name ASC

**Expected count**: ~300-400

## Sheet 3: "Notable Foundations & Institutions"

**Source**: Multi-pass automated deep search for Jewish charities not caught by Sheets 1 or 2.

### Detection methods (run in order, deduplicate)

1. **Known Jewish family foundations**: Search `legal_name` for known Jewish philanthropic family names:
   - Azrieli, Bronfman, Reichmann, Asper, Koffler, Schwartz/Reisman, Prosserman, Cummings (Jewish context), Sherman, Reitman, Beutel, Goldberg, Greenberg, Bialkin, Tauben, Donner, Bader, Frum, Rosen, Schottenstein, Cohl, Crestohl, Drimmer, Weston (specific Jewish foundations), Leah, Deitcher
   - Must be manually validated against false positives (e.g., "Asper" matches "Asperger")

2. **Program description search**: Search `programs.description` for Jewish keywords:
   - `jewish`, `hebrew`, `synagogue`, `torah`, `jewish community`, `holocaust`, `antisemitism`, `israel` (in religious/cultural context)
   - Cross-reference with charity_base to get full record

3. **Grant flow analysis**: Search `grants` table for charities whose grants go to organizations on Sheets 1 or 2:
   - Match `grants.recipient_name` against legal names from Sheets 1 & 2
   - The granting charity (if not already on Sheets 1/2) goes on Sheet 3

4. **Gifts to Jewish qualified donees**: Search `v_financial_abc` or schedule tables for charities that gift to known Jewish umbrella organizations (UJA, Jewish Federations, etc.)

### Deduplication
- Exclude all BNs already on Sheets 1 or 2
- Within Sheet 3, deduplicate by BN (a charity found by multiple methods keeps all detection methods listed)

**Columns**: Same as Sheet 1, plus:
| Column | Source |
|--------|--------|
| Detection Method | Which search pass(es) found this charity |

**Sort**: Detection method priority (family foundations first, then program-based, then grant-flow), then Legal Name ASC

**Expected count**: Unknown — depends on search depth. Likely 50-200+.

## Workbook formatting

- Follow existing snapshot workbook patterns (header row with bold, column auto-width, freeze top row)
- Sheet tab colors: Sheet 1 blue, Sheet 2 green, Sheet 3 orange
- Add a summary row at top of each sheet showing total count

## Implementation notes

- Single script `scripts/reports/generate_jewish_sector.py`
- Follows patterns from `generate_snapshot.py` (DuckDB + openpyxl)
- Sheet 1 and 2 BN sets must be computed before Sheet 3 (Sheet 3 deduplicates against them)
- Family name list for Sheet 3 pass 1 needs careful false-positive filtering (substring matches like "asper" in "Asperger", "gasper" etc.)
- The script should print progress/counts to stdout as it runs each pass
