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
