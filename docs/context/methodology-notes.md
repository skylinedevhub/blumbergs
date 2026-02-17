# Blumbergs Snapshot Methodology and Data Quality Notes

> Synthesized from the "Limitations and Caveats" sections of Blumbergs Snapshot publications (2010-2023) and T3010 form analysis. Use this guide to understand the limitations of any analysis performed on T3010 data.

## Data Source

The T3010 Registered Charity Information Return is filed annually by all Canadian registered charities with the Canada Revenue Agency (CRA). The CRA publishes the data through the Charities Listing database. Blumbergs also maintains CharityData.ca with up to 20 years of historical data per charity.

### Coverage
- There are approximately 86,000 registered charities in Canada
- In any given year, 82,000-84,000 file their T3010 and are processed into the database
- The gap represents late filers, newly registered charities not yet processed, and charities in the process of revocation for non-filing
- Charities must file within 6 months of their fiscal year-end to maintain registration

### Database Lag
- CRA typically processes T3010 data 12-24 months after the fiscal year-end
- The 2023 Snapshot was published April 2025, covering data filed throughout 2024
- This means the "latest" data always reflects economic conditions from 1-2 years prior

## Reliability Caveats

### 1. Self-Reported and Unverified
The T3010 is completed by the charity and signed by one person. CRA does not independently verify the information when it is posted on the CRA site or placed in the database.

### 2. Completed by Non-Experts
The T3010 is often completed by "volunteers or others who may have little understanding of the nuances of the Income Tax Act (Canada), limited language skills, may not have easy access to the correct information or are in a hurry to file the form to avoid deregistration." (Blumbergs, 2023)

### 3. Larger Institutions: More Accurate but More Complex
For larger institutions, accountants or finance staff typically prepare the T3010. Greater accuracy is expected, but "as they also tend to be more complicated and involve bigger numbers, the likelihood of a significant inaccuracy in their T3010 filings is great." (Blumbergs, 2022)

### 4. CRA Processing Errors
T3010s filed on paper need to be coded by hand at CRA, which can introduce mistakes. Only a small number use 2D barcode technology. Electronic filing (available since June 2019) should reduce processing errors over time, but many charities still file on paper.

### 5. Deliberate Misreporting
"In some cases, those completing the T3010 for a charity are deliberately deceptive when completing the T3010. For example, an organization knows that it has substantial fundraising expenses but chooses to put them under charitable activities. Or, an organization claims pharmaceuticals that it can purchase for $50,000 are really worth $50 million." (Blumbergs, 2022)

### 6. Subjective Classifications
Several T3010 fields require subjective judgment:
- **Program vs. fundraising expenditures**: Charities frequently classify fundraising costs as program spending
- **Political activities**: Was the "most frequently incorrectly answered question on the T3010" — the 2013 raw figure of $171M was revised to ~$26M after manual review
- **Employee counts**: 2013 raw data suggested 1.86M FT employees; revised to 1.38M after scrutiny
- **Gifts in kind valuation**: Particularly problematic for pharmaceutical donations

### 7. Tax Form, Not Management Report
"The T3010 is a tax form which is supposed to be completed according to guidance provided by the CRA in Guide Completing the Registered Charity Information Return (T-4033)." It uses Income Tax Act definitions, which may differ from how charities internally categorize their activities.

## Known Data Quality Issues

### Line 4570 (Total Government Funding)
- The pre-computed total in the database is unreliable
- Always compute manually as: line 4540 + line 4550 + line 4560
- Our validation confirms: computed total ($284.7B) differs dramatically from the reported 4570 value ($350M) in the 2024 data

### Employee Count Data (Schedule 3, Lines 300/370)
- Systematically overstated due to data entry errors
- Blumbergs routinely revises the raw counts downward (e.g., 2013: 1.86M raw → 1.38M revised for FT)
- Use the published Snapshot figures rather than raw database aggregates for employee counts

### Political Activity Spending (Line 5030)
- The most error-prone field on the entire T3010
- Raw aggregates are typically 5-7x the actual figure
- Common error: charities enter total charitable spending instead of just political spending
- Questions removed entirely after 2019 — no political activity data available for 2020+

### DAF Fields (Lines 5860-5864)
- New in V24 (2023). First complete year is 2024
- Transpositional errors common: "a group with $31,000 in total DAF assets probably does not have 30,000 DAFs"
- Some charities report restricted gifts as DAFs when they technically aren't
- Some charities that have DAFs don't report them

### Compensation Line 390 vs Line 4880
- Schedule 3 line 390 and financial_d line 4880 should match but may differ slightly
- Both represent total compensation; use whichever is available

## T3010 Form Versions

### Version History
The T3010 has gone through several revisions, tracked in `lookup_form_versioning`:
- Pre-2013: Older form structure
- 2013+: T3010 (13) — added Schedule 7 (Political Activities), revised foreign activities questions
- 2019+: Electronic filing available
- 2023+: T3010 Version 24 — significant changes

### V23 to V24 Transition (2023 Data)
- Charities with fiscal periods ending Dec 31, 2023+ filed using V24
- Charities with fiscal periods ending before Dec 30, 2023 filed using V23
- ~48,418 charities have Dec 31 year-ends and thus used V24
- V24 added: DAF questions (5860-5864), revenue from outside Canada (4575, 4580), and other new fields
- 2023 data is therefore a mix of V23 and V24 responses
- 2024 data is all V24 — the first fully comparable year for new fields

## Snapshot Methodology

### How Blumbergs Produces Snapshots
1. Obtain the complete T3010 database from CRA (CSV files)
2. Load into a database and compute aggregate statistics
3. Manually review outliers and correct known errors (e.g., political spending, employee counts)
4. Cross-reference with prior years for consistency
5. Publish highlights with explicit caveats

### What Blumbergs Does NOT Do
- Does not independently verify individual T3010 filings
- Does not contact charities to confirm reported figures
- Does not adjust for inflation or population growth in trend comparisons
- Does not reconcile T3010 data with provincial financial statements or audited reports

### Interpretation Guidelines from Blumbergs
- "Don't rely on any of this information without checking with the charity and appropriate due diligence as required"
- Use T3010 data for sector-level trends and patterns, not as definitive figures for individual charities
- Treat exact dollar amounts as approximate, especially for smaller charities
- Focus on relative patterns (ratios, rankings, trends) rather than absolute precision
