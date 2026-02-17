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
