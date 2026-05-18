# T3010 Field Dictionary (Authoritative)

Synthesized from CRA's *T3010 Public Data Dictionary 2024* and *Line Number and Contents Index 2024* (both confidential, partner-distributed) plus the published *T4033 Completing the T3010* guide. This is the canonical reference for what every column in the public data actually means.

Numeric line-number columns appear as bare digits (`4100`, `4700`) in the raw tables — quote them in SQL: `fd."4700"`. The "Short" column is CRA's internal shortform label (useful as UI labels or in chat AI explanations).

---

## `ident` (alias `i`)

Source tab: *Ident* — 16 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the business number (BN) system. |  |
| `Designation code` |  | Short Text(1) | Identifies the designation that a charity receives based on its structure, its source of funding, and its mode of operation. *("# Designation" table contains full list of desgination codes.)* |  |
| `Category code` |  | Short Text(4) | Current main classification of the charity's purpose. *("# Category Sub-category" table contains full list of category/sub-category codes.)* |  |
| `Sub-category code` |  | Short Text(4) | Sub-classification of the charity's purpose. |  |
| `Legal name` |  | Short Text(175) | The legal entity name as shown on the charity’s governing documents. |  |
| `Account name` |  | Short Text(175) | The charity's account name. It can be the same as the legal name. |  |
| `Registration date` |  | Date/Time | Effective date of when the organization became a registered charity. |  |
| `Language` |  | Short Text(2) | Code for the primary language of the charity. *(01 = English, 02 = French New in November 2020 (R4.1))* |  |
| `Mailing address` |  | Short Text(62) | The first and second line of the mailing address. |  |
| `City` |  | Short Text(30) | Mailing address - city |  |
| `Province` |  | Short Text(2) | Mailing address - province |  |
| `Postal code` |  | Short Text(10) | Mailing address - postal code |  |
| `Country` |  | Short Text(2) | Mailing address - country code. |  |
| `Contact Phone` |  | Short Text(36) | Charity's contact phone *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |
| `Contact Email` |  | Short Text(200) | Charity's contact email address *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |
| `Contact URL` |  | Short Text(200) | Charity's website address *(This not directly related to the T3010 filing (the business information sheet is no longer being collected as of May 2019).)* |  |

## `financial_abc` (alias `fabc`)

Source tab: *Financial Section A, B and C* — 67 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `BN/Registration number` |  | Short Text(16) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `1200 Program Area Code` |  | Short Text(3) | Most important field of operations *(Business information sheet (BIS) - program area rank #1.  Important note:  As of May 2019, the business information sheets are no longer being mailed out to the... |  |
| `1200 Percent` |  | Number(Integer) | Most important field of operations percentage *(Business information sheet (BIS) - program area rank #1.)* |  |
| `1210 Program Area Code` |  | Short Text(3) | Second most important field of operations *(Business information sheet (BIS) - program area rank #2.)* |  |
| `1210 Percent` |  | Number(Integer) | Second most important field of operations percentage *(Business information sheet (BIS) - program area rank #2.)* |  |
| `1220 Program Area Code` |  | Short Text(3) | Third most important field of operations *(Business information sheet (BIS) - program area rank #3.)* |  |
| `1220 Percent` |  | Number(Integer) | Third most important field of operations percentage *(Business information sheet (BIS) - program area rank #3.)* |  |
| `1510 Subordinate position to a parent organization?` |  | Short Text(1) | Is the charity subordinate to a parent organization? *(Value can be "Y", "N" or <empty>)* |  |
| `1510 Parent Business Number` |  | Short Text(15) | BN of the parent organization to which this charity is a subordinate |  |
| `1510 Parent Name` |  | Short Text(175) | Name of the parent organization to which this charity is a subordinate |  |
| `1570` | Wound-Up/Dissolved | Short Text(1) | Has the charity wound-up, dissolved or terminated operations? *(Value can be "Y", "N" or <empty>)* |  |
| `1600` | Foundation Designation | Short Text(1) | Is the charity designated as a public foundation or private foundation? *(Value can be "Y", "N" or <empty>)* |  |
| `1800` | Active | Short Text(1) | Was the charity active during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `2000` | Gifts to Qualified Donees | Short Text(1) | Did the charity make gifts or transfer funds to qualified donees or other organizations (excluding grants to non-qualified donees) *(Value can be "Y", "N" or <empty>)* |  |
| `2100` | Foreign Activities | Short Text(1) | Did the charity’s financial resources were spent on programs outside Canada under an arrangement including a contract, agency agreement or joint venture to an individual or organization (excluding ... |  |
| `2400` |  | Short Text(1) | Did charity carry out any political activities during the fiscal period? *(Value can be "Y", "N" or <empty>   On version 24 of T3010 form, the name "political activities" was changed to "public pol... | 23, 24 |
| `5030` |  | Currency | Total expenditures on political activities spent by the charity *(Field no longer exists in T3010 version 24)* | 23 |
| `5031` |  | Currency | Total amount of 5030 gifts made for qualified donees *(Field no longer exists in T3010 version 24)* | 23 |
| `5032` |  | Currency | Total amount received from outside Canada that was directed to be spent on political activities. *(Field no longer exists in T3010 version 24)* | 23 |
| `2500` | Advertising | Short Text(1) | Fundraising method: Advertisements/prints/radio/TV commercials *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2510` | Auctions | Short Text(1) | Fundraising method: Auctions *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2530` | Collection Boxes | Short Text(1) | Fundraising method: Collection plates/boxes *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2540` | Door-to-Door | Short Text(1) | Fundraising method:  Door-to-door solicitation *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2550` | Lotteries | Short Text(1) | Fundraising method:  Draws/lotteries *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2560` | Fundraising Events | Short Text(1) | Fundraising method:  Fundraising dinners/galas/concerts *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2570` | Sales | Short Text(1) | Fundraising method:  Sales *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2575` | Internet | Short Text(1) | Fundraising method:  Internet *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2580` | Mail Campaigns | Short Text(1) | Fundraising method:  Mail campaigns *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2590` | Planned Giving | Short Text(1) | Fundraising method:  Planned-giving programs *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2600` | Corporate Sponsorships | Short Text(1) | Fundraising method:  Targeted corporate donations/sponsorships *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2610` | Targeted Contacts | Short Text(1) | Fundraising method:  Targeted contacts *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2620` | Phone/TV Solicitations | Short Text(1) | Fundraising method:  Telephone/TV solicitations *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2630` | Sporting Events | Short Text(1) | Fundraising method:  Tournament/sporting events *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2640` | Cause Marketing | Short Text(1) | Fundraising method:  Cause-related marketing *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2650` | Other Fundraising | Short Text(1) | Fundraising method:  Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2660` | Specify Fundraising | Short Text(175) | Other - Specify |  |
| `2700` | External Fundraisers | Short Text(1) | Did the charity pay external fundraisers? *(Value can be "Y", "N" or <empty>)* |  |
| `5450` | Fundraiser Gross Revenue | Currency | Gross revenue collected by fundraisers on behalf of the charity |  |
| `5460` | Fundraiser Payments | Currency | Total amount paid to or retained by the fundraisers |  |
| `2730` |  | Short Text(1) | Method of payment to fundraisers: Commissions *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2740` | Bonuses | Short Text(1) | Method of payment to fundraisers: Bonuses *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2750` | Commissions | Short Text(1) | Method of payment to fundraisers: Finder's fees *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2760` | Service Fee | Short Text(1) | Method of payment to fundraisers: Set fee for services *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2770` | Honoraria | Short Text(1) | Method of payment to fundraisers: Honoraria *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2780` | Other Payment | Short Text(1) | Method of payment to fundraisers: Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `2790` | Specify Payment | Short Text(175) | Method of payment to fundraisers: Specify |  |
| `2800` | Fundraiser Tax Receipts | Short Text(1) | Did the fundraiser issue tax receipts on behalf of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `3200` | Director Compensation | Short Text(1) | Did the charity compensate any of its directors/trustees or like officials or persons not at arm's length from the charity for services provided during the fiscal period? *(Value can be "Y", "N" or... |  |
| `3400` | Employee Compensation | Short Text(1) | Did charity incur any expenses for compensation of employees during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `3900` | Foreign Donations ≥$10k | Short Text(1) | Did the charity receive any donations or gifts of any kind at $10,000 or more from donor who was not resident in Canada, not Canadian citzen or not liable to pay any income tax in Canada from emplo... |  |
| `4000` | Non-Cash Gifts | Short Text(1) | Did the charity receive any non-cash gifts (gifts-in-kind) for which it issued tax receipts? *(Value can be "Y", "N" or <empty>)* |  |
| `5800` | Non-Qualifying Security | Short Text(1) | Did the charity acquire a non-qualifying security? *(Value can be "Y", "N" or <empty>)* |  |
| `5810` | Donor Property Use | Short Text(1) | Did the charity allow any of its donors to use any of the charity's property during the fiscal period (except for permissable uses)? *(Value can be "Y", "N" or <empty>)* |  |
| `5820` | Third-Party Receipts | Short Text(1) | Did the charity issue any of its tax receipts for donations on behalf of another organization? *(Value can be "Y", "N" or <empty>)* |  |
| `5830` | Partnership Holdings | Short Text(1) | Did the charity have direct partnership holdings at any time during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `5840` | Grants to Grantees | Short Text(1) | Did the charity make qualifying disbursements by way of grants to non-qualified donees (grantees) in the fiscal period? *(Value can be "Y", "N" or <empty>)* | 26 |
| `5841` | Large Grants (>$5k) | Short Text(1) | Did the charity make grants to any grantees totalling more than $5000 in the fiscal period? *(Value can be "Y", "N" or <empty>)* | 26 |
| `5842` | Small Grantee Count | Number(10) | Enter the number of grantees that received grants totalling $5,000 or less in the fiscal period | 26 |
| `5843` | Small Grant Total | Currency(14) | Enter the total amount paid to grantees that received grants totalling $5,000 or less in the fiscal period | 26 |
| `5850` | DAF Held | Short Text(1) | In the 24 months prior to the beginning of the fiscal year, did the average value of your charity’s property (cash, investments, capital property or other assets) not used directly in its charitabl... | 27 |
| `5860` |  | Short Text(1) | Did the charity hold any donor advised funds (DAF) during the fiscal period? *(Value can be "Y", "N" or <empty>)* | 27 |
| `5861` | DAF Accounts | Number(10) | Total number of accounts held at the end of the fiscal period | 27 |
| `5862` | DAF Value | Currency(17) | Total value of all accounts held at the end of the fiscal period | 27 |
| `5863` | DAF Donations | Currency(17) | Total value of donations to DAF accounts received during the fiscal period | 27 |
| `5864` | DAF Disbursements | Currency(17) | Total value of qualifying disbursements from DAFs during the fiscal period | 27 |

## `financial_d` (alias `fd`)

Source tab: *Financial Section D, Schedule 6* — 86 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `Section Used  (D or 6)` |  | Short Text(1) | Section used to file the financial data Values: D=Section D, 6=Schedule 6 *(Value can be "D"or "6" .)* |  |
| `5030 indicator (C or 6)` |  | Short Text(1) | Indicates whether line 5030 is obtained from section C. *(Value can be "C" or <empty> (Schedule 6 copies the value from section C, if present).)* |  |
| `4020` | Accounting Basis | Short Text(1) | Was the financial information reported on an accrual or cash basis? *(Value can be "A" (Accrual), "C" (Cash) or <empty>.)* |  |
| `4050` | Land/Buildings Owned | Short Text(1) | Did the charity own land and/or buildings? *(Pertains to section D only.  Value can be "Y", "N" or <empty>.)* |  |
| `4100` | Cash & Investments | Currency | Cash, bank accounts and short-term investments |  |
| `4110` | Non-Arm's Receivables | Currency | Amounts receivable from non-arm's length parties |  |
| `4120` | Other Receivables | Currency | Amounts received from all others |  |
| `4130` | Non-Arm's Investments | Currency | Investments in non-arm's length parties |  |
| `4140` | Long-Term Investments | Currency | Long-term investments |  |
| `4150` | Inventory | Currency | Inventories |  |
| `4155` | Land/Buildings CA | Currency | Land and buildings in Canada |  |
| `4160` | Other CA Assets | Currency | Other capital assets in Canada |  |
| `4165` | Foreign Assets | Currency | Capital assets outside Canada |  |
| `4166` | Amortization | Currency | Accumulated amortization of capital assets |  |
| `4170` | Other Assets | Currency | Other assets |  |
| `4180` |  | Currency | 10 year gifts *(Removed from T3010 V27)* | 23,24,25,26 |
| `4200` | Total Assets | Currency | Total assets |  |
| `4250` |  | Currency | Amount included in lines 4150, 4155, 4160, 4165 and 4170 not used in charitable activities |  |
| `4300` |  | Currency | Accounts payable and accrued liabilities |  |
| `4310` |  | Currency | Deferred revenue |  |
| `4320` |  | Currency | Amounts owing to non-arm's length parties |  |
| `4330` |  | Currency | Other liabilities |  |
| `4350` | Total Liabilities | Currency | Total liabilities |  |
| `4400` | Non-Arm's Length | Short Text(1) | Did the charity borrow from, loan to, or invest assets with any non-arm's length parties? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4490` | Tax Receipts Issued | Short Text(1) | Did the charity issue tax receipts for gifts? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4500` | Tax-Receipted Gifts | Currency | Total eligible amount of tax-receipted gifts |  |
| `5610` | Tuition Revenue | Currency | Total eligible amount of tax-receipted tuition fees |  |
| `4505` |  | Currency | Total amount of 10 year gifts received *(Removed from T3010 V27)* | 23,24,25,26 |
| `4510` | Charity Revenue | Currency | Total amount received from other registered charities |  |
| `4530` | Non-Tax-Receipted Gifts | Currency | Total other gifts received for which a tax receipt was not issued by the charity (excluding amounts at lines 4575 and 4630) |  |
| `4540` | Federal Funding | Currency | Total revenue received from federal government |  |
| `4550` | Provincial Funding | Currency | Total revenue received from provincial/territorial governments |  |
| `4560` | Municipal Funding | Currency | Total revenue received from municipal/regional governments |  |
| `4565` | Government Funding | Short Text(1) | Did the charity receive any revenue from any level of Canadian government? *(Pertains to section D only.  Value can be "Y", "N" or <empty>)* |  |
| `4570` | Gov Funding Total | Currency | Total amount revenue received from any level of Canadian government |  |
| `4571` | Foreign Tax Revenue | Currency | Total tax-receipted revenue from all sources outside of Canada (government and non-government) |  |
| `4575` | Foreign Non-Tax Revenue | Currency | Total non tax-receipted revenue from all sources outside of Canada (government and non-government) *(Field no longer exists in T3010 version 24)* |  |
| `4580` | Total Investment Income | Currency | Total interest and investment income received or earned |  |
| `4590` | Gross Asset Sales | Currency | Gross proceeds from disposition of assets |  |
| `4600` | Net Asset Sales | Currency | Net proceeds from disposition of assets |  |
| `4610` | Rental Income | Currency | Gross income received from rental of land and/or buildings |  |
| `4620` | Membership Revenue | Currency | Total non tax-receipted revenues received for memberships, dues and association fees |  |
| `4630` | Fundraising Revenue | Currency | Total non tax-receipted revenue from fundraising activities |  |
| `4640` | Sales Revenue | Currency | Total revenue from sale of goods and services (except to any level of Canadian government) |  |
| `4650` | Other Revenue | Currency | Other revenue (not already included in the amounts above) |  |
| `4655` | Other Revenue Type | Short Text(175) | Specify type(s) of revenue included in the amount reported at line 4650 |  |
| `4700` | Total Revenue | Currency | Total revenue |  |
| `4800` | Advertising Costs | Currency | Advertising and promotion |  |
| `4810` | Travel Costs | Currency | Travel and vehicle expenses |  |
| `4820` | Interest Expenses | Currency | Interest and bank charges |  |
| `4830` | License Fees | Currency | Licenses, memberships and dues |  |
| `4840` | Office Costs | Currency | Office supplies and expenses |  |
| `4850` | Occupancy Costs | Currency | Occupancy costs |  |
| `4860` | Consulting Fees | Currency | Charity's total expenditure on professional & consulting fees |  |
| `4870` | Training Costs | Currency | Education and training for staff and volunteers |  |
| `4880` | Total Comp Expenditure | Currency | Total expenditure on all compensation |  |
| `4890` | Donated Goods | Currency | Fair market value of all donated goods used in charity’s own activities |  |
| `4891` | Supplies/Assets | Currency | Total cost of all purchased supplies and assets |  |
| `4900` | Amortization Exp | Currency | Amortization of capitalized assets |  |
| `4910` | Research Grants | Currency | Research grants and scholarships as part of charity’s own activities |  |
| `4920` | Other Expenditures | Currency | All other expenditures not included in the amounts above (excluding gifts to qualified donees) |  |
| `4930` | Other Expenditure Types | Short Text(175) | Specify type(s) of expenditures included in amount reported at line 4920 |  |
| `4950` | Total Expenditures | Currency | Total expenditures (excluding qualifying disbursements) |  |
| `5000` | Charitable Activities | Currency | Total expenditures on charitable activities (of the amount at line 4950). |  |
| `5010` | Admin Total | Currency | Total expenditures on management and administration (of the amount at line 4950). |  |
| `5020` | Fundraising Costs | Currency | Total expenditures on fundraising (of the amount at line 4950). |  |
| `5030` |  | Currency | Total expenditures on political activities, inside or outside Canada (of the amount at line 4950). *(Field no longer exists in T3010 version 24)* | 23 |
| `5040` | Other Expenses | Currency | Total other expenditures (included in line 4950) |  |
| `5050` | Gifts to Donees | Currency | Total amount of gifts made to all qualified donees |  |
| `5100` | Total Expenses | Currency | Total expenditures (Add lines 4950 and 5050) |  |
| `5500` | Accumulated Funds | Currency | The amount accumulated for the fiscal period, including income earned on accumulated funds |  |
| `5510` | Disbursed Accumulated | Currency | The amount disbursed for the fiscal period for the specified purpose |  |
| `5750` | Quota Reduction | Currency | Pre-approved special reduction amount used in dispursement quota |  |
| `5900` | Prior Property Avg | Currency | Average value of property not used for charitable activities or administration during 24 months preceding the beginning of fiscal period |  |
| `5910` | Post Property Avg | Currency | Average value of property not used for charitable activities or administration during 24 months preceding the end of fiscal period |  |
| `5045` | Grants to Grantees | Currency | Total amount of grants made to all non-qualified donees (grantees) | 26 |
| `4101` | Cash | Currency(17) | Enter the total amounts in cash and bank accounts included on line 4100 | 27 |
| `4102` | Short-Term Investments | Currency(17) | Enter the value of all short-term investments included on line 4100 with an original term to maturity not greater than one year | 27 |
| `4157` | Program Use Assets | Currency(17) | Enter the cost or fair market value of all land and buildings in Canada used for the charity’s charitable programs or administration | 27 |
| `4158` | Non-Program Assets | Currency(17) | Enter the cost or fair market value of all land and buildings in Canada used for the charity’s charitable programs or administration | 27 |
| `4190` | Impact Investments | Currency(17) | Enter the value of all impact investments including those reported in any other line. For the purposes of this guide, impact investments are investments in companies or projects with the intention ... | 27 |
| `4576` | Impact Income | Currency(17) | Enter the amount from line 4580 that represents the total interest and other income the charity received or earned from impact investments | 27 |
| `4577` | Non-Arm's Income | Currency(17) | Enter the total amount from Line 4580 that represents the total amount of interest and investment income received from persons who do not deal at arm’s length with the charity | 27 |

## `schedule_1_foundations` (alias `s1`)

Source tab: *Sch1 Foundations* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `100` | Corporate Control | Short Text(1) | Did the foundation acquire control of a corporation during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |
| `110` | Non-Operating Debt | Short Text(1) | Did the foundation incur any debts (during the fiscal period) other than for current operating expenses, purchasing or selling investments, or in administering charitable activities? *(Value can be... |  |
| `111` | Restricted Funds | Currency(17) | What was the total value of all restricted funds held at the end of the fiscal period? | 27 |
| `112` | Unspendable Funds | Currency(17) | Of that amount, what amount was the foundation not permitted to spend due to a funder's written trust or direction? | 27 |
| `120` | Non-Qualified Investments | Short Text(1) | During fiscal period, did the foundation hold any shares, rights to acquire shares, or debts owing to it that meet the definition of a non-qualified investment? *(Value can be "Y", "N" or <empty>)* |  |
| `130` | Excess Shareholding | Short Text(1) | Did the foundation own more than 2% of any class of shares of a corporation at any time during the fiscal period? *(Value can be "Y", "N" or <empty>)* |  |

## `schedule_2_summary` (alias `s2s`)

Source tab: *Sch2 Activities Outside Canada* — 10 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `200` | Foreign Expenditures | Currency | Total expenditures on activities/programs/projects carried on outside Canada, excluding qualifying disbursements |  |
| `210` | Foreign Transfers | Short Text(1) | Were any of the charity's financial resources spent on programs outside of Canada under any kind of an arrangement including a contract, agency agreement, or joint venture to any other individual o... |  |
| `220` | Foreign Countries | Short Text(1) | Were any projects undertaken outside Canada funded by Global Affairs Canada? *(Value can be "Y", "N" or <empty>)* |  |
| `230` | GAC Funding | Currency | Total amount of funds expended under programs funded by Global Affairs Canada |  |
| `240` | Global Affairs Funding | Short Text(1) | Were any of the charity's activities outside of Canada carried out by employees of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `250` | Employee-Led Abroad | Short Text(1) | Were any of the charity's activities outside of Canada carried out by volunteers of the charity? *(Value can be "Y", "N" or <empty>)* |  |
| `260` | Goods Exported | Short Text(1) | Did the charity export goods as part of its charitable activities? *(Value can be "Y", "N" or <empty>)* |  |

## `schedule_2_recipients` (alias `s2r`)

Source tab: *Sch2 Activities Recipient* — 7 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(9) | Sequential number reporting the external fundraiser *(New in November 2020 (R4.1))* |  |
| `Name of individual/organization` |  | Text(175) | Name of individual/org that receives the charity's resources which was included in line 200 *(New in November 2020 (R4.1))* |  |
| `Country` |  | Text(2) | Country code where the program is carried out *(New in November 2020 (R4.1))* |  |
| `Amount` |  | Currency(14) | Amount transferred from charity to individual/org *(New in November 2020 (R4.1))* |  |

## `schedule_2_countries` (alias `s2c`)

Source tab: *Sch2 Activities Country* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Short Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the country *(New in November 2020 (R4.1))* |  |
| `Charity's Program Country Code` |  | Short Text(2) | Country where charity carries on program or provide resources *(New in November 2020 (R4.1))* |  |

## `schedule_2_destinations` (alias `s2d`)

Source tab: *Sch2 Activities Export* — 8 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN System. *(New in November 2020 (R4.1))* |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal Year End Period *(New in November 2020 (R4.1))* |  |
| 🔑 `Form ID` |  | Short Text(4) | Revision of Revenue Canada T3010 Form this T3010 was filed on. *(New in November 2020 (R4.1))* |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the export *(New in November 2020 (R4.1))* |  |
| `Item exported` |  | Short Text(30) | Item being exported *(New in November 2020 (R4.1))* |  |
| `Value (CAN)` |  | Currency | Value of item being exported |  |
| `Destination (city/region)` |  | Short Text(175) | Destination *(New in November 2020 (R4.1))* |  |
| `Country code` |  | Short Text(2) | Country code of exported item *(New in November 2020 (R4.1))* |  |

## `schedule_3_compensation` (alias `sc`)

Source tab: *Sch3 Compensation* — 16 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `300` | Full-Time Positions | Number(Long Integer) | Number of permanent, full-time, compensated positions in fiscal period, not including independent contractors |  |
| `305` |  | Number(Long Integer) | $1-39,999 (of the 10 highest compensated) |  |
| `310` |  | Number(Long Integer) | $40,000-$79,999 (of the 10 highest compensated) |  |
| `315` |  | Number(Long Integer) | $80,000-119,999 (of the 10 highest compensated) |  |
| `320` |  | Number(Long Integer) | $120,000-159,999 (of the 10 highest compensated) |  |
| `325` |  | Number(Long Integer) | $160,000-199,999 (of the 10 highest compensated) |  |
| `330` |  | Number(Long Integer) | $200,000-249,999 (of the 10 highest compensated) |  |
| `335` |  | Number(Long Integer) | $250,000-299,999 (of the 10 highest compensated) |  |
| `340` |  | Number(Long Integer) | $300,000-349,999 (of the 10 highest compensated) |  |
| `345` |  | Number(Long Integer) | $350,000-over (of the 10 highest compensated) |  |
| `370` | Part-Time Staff | Number(Long Integer) | The number of part-time or part-year employees the charity employed during the fiscal period. |  |
| `380` | Part-Time Costs | Currency | Total expenditure on compensation for part-time or part-year employees during the fiscal period. |  |
| `390` | Total Compensation | Currency | Total expenditure on all compensation during the fiscal period. |  |

## `schedule_5_noncash` (alias `s5`)

Source tab: *Sch5 NonCash Gifts* — 18 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| `500` |  | Short Text(1) | Charity issued receipts for artwork wine jewellery *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `505` |  | Short Text(1) | Charity issued receipts for building materials *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `510` |  | Short Text(1) | Charity issued receipts for clothing/furniture/food *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `515` |  | Short Text(1) | Charity issued receipts for vehicles *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `520` |  | Short Text(1) | Charity issued receipts for cultural properties *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `525` |  | Short Text(1) | Charity issued receipts for ecological properties *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `530` |  | Short Text(1) | Charity issued receipts for life insurance policies *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `535` |  | Short Text(1) | Charity issued receipts for medical equipment/supplies *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `540` |  | Short Text(1) | Charity issued receipts for privately-held securities *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `545` |  | Short Text(1) | Charity issued receipts for machinery/equipment/computers/software *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `550` |  | Short Text(1) | Charity issued receipts for publicly traded securities/commodities/mutual funds *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `555` |  | Short Text(1) | Charity issued receipts for books *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `560` |  | Short Text(1) | Other *("Y" indicates that the box was checked, where <empty> indicates that it was not checked.)* |  |
| `565` |  | Short Text(175) | Specify for others |  |
| `580` |  | Currency | Total amount of tax-receipted gifts in kind |  |

## `schedule_7_desc` (alias `s7d`)

Source tab: *Sch7 Desc* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23, 24 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23, 24 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23, 24 |
| `Political Activities Description` |  | Long Text | Describe the charity's political activities, including gifts to qualified donees intended for political activities, and explain how these relate to its charitable purposes. *(Column only populated ... | 23 |
| `Public Policy Description` |  | Long Text | Describe the charity’s public policy dialogue and development activities, and explain how these relate to its stated charitable purposes. *(Column only populated if Form ID = 24)* | 24 |

## `schedule_7_political_fund` (alias `s7f`)

Source tab: *Sch7 Political Activities Fund* — 7 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23 |
| 🔑 `Sequence Number` |  | Number(Long Integer) | Sequence number for political activities funded from outside of Canada | 23 |
| `Political Activity Description` |  | Short Text(175) | Description of the political activity funded from outside of Canada | 23 |
| `Funding Amount` |  | Currency | The amount received from the country outside Canada (CAN$) | 23 |
| `Country Code` |  | Short Text(2) | Country code from which the funding was received | 23 |

## `schedule_7_political_res` (alias `s7r`)

Source tab: *Sch7 Political Activities Res* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 23 |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date | 23 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 23 |
| 🔑 `Line Number (700 to 708)` |  | Number(Integer) | The way the charity participated in or carried out political activities during the fiscal period. *(This is sequence number field where the values will reflect line numbers 700 to 708.)* | 23 |
| `Staff Used?` |  | Short Text(1) | "X" if staff resource is used *(Value can be "X" or <empty>)* | 23 |
| `Volunteers Used?` |  | Short Text(1) | "X" if volunteers resource is used *(Value can be "X" or <empty>)* | 23 |
| `Financial Resource Used?` |  | Short Text(1) | "X" if financial resource is used *(Value can be "X" or <empty>)* | 23 |
| `Property Resource Used?` |  | Short Text(1) | "X" if property resource is used *(Value can be "X" or <empty>)* | 23 |
| `Other Descriptions` |  | Short Text(175) | Description of other way the charities participated in or carried out political activities (only applicable to line 708). | 23 |

## `gift` (alias `g`)

Source tab: *Gift* — 14 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Sequence number` |  | Number(Long Integer) | Sequential number reporting the gifts. |  |
| `Associated charity (Y/N)` |  | Short Text(1) | Is qualified donee an associated charity? *(Value can be "Y", "N" or <empty>)* |  |
| `Donee Business number` |  | Short Text(15) | Business number of qualified donee, if a charity. |  |
| `Donee Name` |  | Short Text(60) | Name of qualified donee. |  |
| `City` |  | Short Text(30) | Donee's city |  |
| `Province` |  | Short Text(2) | Donee's province |  |
| `Total amount gifts` |  | Currency | Total amount of gifts |  |
| `Amount of gifts in kind` |  | Currency | Amount of non-cash gifts (gifts-in-kind) |  |
| `Number of donees` |  | Number(Long Integer) | Number of reported donees |  |
| `Gift for Political Activities?` |  | Short Text(1) | Was any part of the gift intended for political activities? *(Value can be "Y", "N" or <empty>)* | 23 |
| `Political Activities Gift Amount` |  | Currency | Total amount of gifts intended for political activities *(Is entered if "Y" is answered for above indicator.)* | 23 |

## `programs` (alias `p`)

Source tab: *New and Ongoing Programs* — 5 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Program type OP=ongoing program NP=new program NA=not active` |  | Short Text(2) | OP = Active Ongoing program ; NP = New Program; NA = Not Active |  |
| `Program Description` |  | Long Text | Program activity freeform text description. |  |

## `trustee` (alias `t`)

Source tab: *Trustee* — 11 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. |  |
| 🔑 `Fiscal period end` |  | Date/Time | Fiscal period end date |  |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. |  |
| 🔑 `Officer Number` |  | Number(Long Integer) | Sequence number - maximum of 10 officer names |  |
| `Last Name` |  | Short Text(30) | Officer/director or trustee last name |  |
| `First Name` |  | Short Text(30) | Officer/director or trustee first name |  |
| `Initial` |  | Short Text(3) | Initial of director or trustee |  |
| `Position` |  | Short Text(30) | Officer/director or trustee position |  |
| `At arm's length` |  | Short Text(1) | Is the director at arm’s length? *(Value can be "Y", "N" or <empty>)* |  |
| `Appointed Date` |  | Date/Time | Date the director/officer was appointed to this title/postion |  |
| `Ceased Date` |  | Date/Time | End date of director/officer occupying title/postion |  |

## `grants` (alias `gn`)

Source tab: *Grants to Non-Qualified Donees* — 9 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 26 |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal period end date | 26 |
| 🔑 `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 26 |
| 🔑 `Sequence Number` |  | Number(10) | Sequence number to uniquely identify each grant recipient for a BN/FPE | 26 |
| `Grant Recipient Name` |  | Text(175) | Name of non-qualified donee | 26 |
| `Grant Purpose` |  | Text(1250) | Description of the purpose for the qualifying disbursements to non-qualified donee | 26 |
| `Amount of Cash Disbursed` |  | Currency(14) | Cash amount disbursed to non-qualified donee | 26 |
| `Amount of non-cash Disbursed` |  | Currency(14) | Non-cash amount disbursed to non-qualified donee | 26 |
| `Grant Country` |  | Text(125) | List of grant countries | 26 |

## `schedule_8_disbursement` (alias `s8`)

Source tab: *Disbursement Quota* — 21 columns. 

| Column | Short | Type | Description | Form Ver. |
|---|---|---|---|---|
| 🔑 `BN/Registration number` |  | Short Text(15) | Single business registration number - unique identifier to each individual charity account that exists in the BN system. | 27 |
| 🔑 `Fiscal period end` |  | Date/Time(10) | Fiscal period end date | 27 |
| `Form ID` |  | Short Text(4) | Version of T3010 form the T3010 was filed on. | 27 |
| `Line 805` |  | Currency(17) | Average value of property not used in charitable activities or administration (line 5900 from your return) | 27 |
| `Line 810` |  | Currency(17) | If permission to accumulate property has been granted, enter the total amount accumulated less all disbursements made for the specified purpose (add all amounts from lines 5500 minus all amounts at... | 27 |
| `Line 815` |  | Currency(17) | Must display the total of The amount at line 805 minus the amount at line 810 - “Line 1 minus line 2 (if negative, enter 0)” | 27 |
| `Line 820` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must display the total of line 815 multiplied by 3.5%;  If the amount at line 3 is more than 1,000,000, Must remain blank | 27 |
| `Line 825` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 815 minus $1,000,000 | 27 |
| `Line 830` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 825 multiplied by 5% | 27 |
| `Line 835` |  | Currency(17) | If the amount at line 3 is less than or equal to 1,000,000, Must remain blank If the amount at line 3 is more than 1,000,000, Must display the total of line 825 multiplied by 5% | 27 |
| `Line 840` |  | Currency(17) | Must be pre-populated with the amount from line 820 or 835 from Page 1 of Schedule 8 “Enter the amount from line 820 or line 835. This is your charity's disbursement quota requirement for the curre... | 27 |
| `Line 845` |  | Currency(17) | Must be pre-populated with the amount from line 5000 from Schedule 6 of this return “Total expenditures on charitable activities (line 5000 of your return)” | 27 |
| `Line 850` |  | Currency(17) | Must be pre-populated with the amount from line 5045 from Schedule 6 of this return “Total amount of grants made to non-qualified donees (line 5045 of your return)” | 27 |
| `Line 855` |  | Currency(17) | Must be pre-populated with the amount from line 5050 from Schedule 6 of this return “Total amount of gifts made to qualified donees (line 5050 of your return)” | 27 |
| `Line 860` |  | Currency(17) | Must display the total of adding lines 845, 850 and 855 | 27 |
| `Line 865` |  | Currency(17) | Must display the total of subtracting line 860 from line 840 “Line 860 minus line 840. This is your charity’s disbursement quota excess or shortfall for the current fiscal period.” | 27 |
| `Line 870` |  | Currency(17) | Must be pre-populated with the amount from line 5910 from Schedule 6 of this return “Average value of property not used in charitable activities or administration prior to the next fiscal period (l... | 27 |
| `Line 875` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must display the total of line 870 multiplied by 3.5% If the amount at line 870 is more than 1,000,000, Must remain blank “The amount s... | 27 |
| `Line 880` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 870 minus $1,000,000 | 27 |
| `Line 885` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 880 multiplied by 5% | 27 |
| `Line 890` |  | Currency(17) | If the amount at line 870 is less than or equal to 1,000,000, Must remain blank If the amount at line 870 is more than 1,000,000, Must display the total of line 885 plus $35,000 “The amount shown o... | 27 |

---

## Line Number Index (sortable, 162 entries)

From the T3010 Line Number and Contents Index 2024. Use this when a user references a "line 4700" style question — the Short column gives a compact label suitable for explanations.

| Line | Short | Full Question |
|---|---|---|
| `100` | Corporate Control | Foundation acquired corporate control? |
| `110` | Non-Operating Debt | Foundation non-operating debt? |
| `111` | Restricted Funds | Total restricted funds value |
| `112` | Unspendable Funds | Restricted funds unspendable |
| `120` | Non-Qualified Investments | Held non-qualified investments? |
| `130` | Excess Shareholding | Owned >2% of corporate shares? |
| `1510` | Subordinate to Head Body | Was the charity in a subordinate position to a head body? |
| `1570` | Wound-Up/Dissolved | Has the charity wound-up, dissolved, or terminated operations? |
| `1600` | Foundation Designation | Is the charity designated as a public foundation or private foundation? |
| `1800` | Active | Was the charity active during the fiscal period? |
| `200` | Foreign Expenditures | Foreign activity expenditures |
| `2000` | Gifts to Qualified Donees | Did the charity make gifts/transfers to qualified donees? |
| `210` | Foreign Transfers | Transferred funds to foreign entities? |
| `2100` | Foreign Activities | Did the charity conduct activities outside Canada? |
| `220` | Foreign Countries | Countries where programs conducted |
| `230` | GAC Funding | Global Affairs funding total |
| `240` | Global Affairs Funding | Funded by Global Affairs Canada? |
| `250` | Employee-Led Abroad | Foreign activities via employees? |
| `2500` | Advertising | Fundraising method: Advertisements/print/radio/TV |
| `2510` | Auctions | Fundraising method: Auctions |
| `2530` | Collection Boxes | Fundraising method: Collection plates/boxes |
| `2540` | Door-to-Door | Fundraising method: Door-to-door solicitation |
| `2550` | Lotteries | Fundraising method: Draws/lotteries |
| `2560` | Fundraising Events | Fundraising method: Dinners/galas/concerts |
| `2570` | Sales | Fundraising method: Sales |
| `2575` | Internet | Fundraising method: Internet |
| `2580` | Mail Campaigns | Fundraising method: Mail campaigns |
| `2590` | Planned Giving | Fundraising method: Planned-giving programs |
| `260` | Volunteer-Led Abroad | Foreign activities via volunteers? |
| `260` | Goods Exported | Exported goods for charity? |
| `2600` | Corporate Sponsorships | Fundraising method: Corporate sponsorships |
| `2610` | Targeted Contacts | Fundraising method: Targeted contacts |
| `2620` | Phone/TV Solicitations | Fundraising method: Telephone/TV solicitations |
| `2630` | Sporting Events | Fundraising method: Tournaments/sporting events |
| `2640` | Cause Marketing | Fundraising method: Cause-related marketing |
| `2650` | Other Fundraising | Fundraising method: Other |
| `2660` | Specify Fundraising | Specify other fundraising method |
| `2700` | External Fundraisers | Did the charity pay external fundraisers? |
| `2740` | Bonuses | Payment method: Bonuses |
| `2750` | Commissions | Payment method: Commissions |
| `2760` | Service Fee | Payment method: Set fee for services |
| `2770` | Honoraria | Payment method: Honoraria |
| `2780` | Other Payment | Payment method: Other |
| `2790` | Specify Payment | Specify other payment method |
| `2800` | Fundraiser Tax Receipts | Fundraiser issued tax receipts? |
| `300` | Full-Time Positions | Permanent full-time positions count |
| `3200` | Director Compensation | Compensation to directors/trustees? |
| `3400` | Employee Compensation | Employee compensation expenses? |
| `370` | Part-Time Staff | Part-time/seasonal employees count |
| `380` | Part-Time Costs | Part-time compensation total |
| `390` | Total Compensation | Total compensation expenses |
| `3900` | Foreign Donations ≥$10k | Foreign donations ≥$10k? |
| `4000` | Non-Cash Gifts | Non-cash gifts with receipts? |
| `4020` | Accounting Basis | Financial info basis (accrual/cash) |
| `4050` | Land/Buildings Owned | Own land/buildings? |
| `4100` | Cash & Investments | Cash/bank/short-term investments |
| `4101` | Cash | Cash and bank accounts |
| `4102` | Short-Term Investments | Short-term investments |
| `4110` | Non-Arm's Receivables | Receivables from non-arm's length |
| `4120` | Other Receivables | Receivables from others |
| `4130` | Non-Arm's Investments | Investments in non-arm's length |
| `4140` | Long-Term Investments | Long-term investments |
| `4150` | Inventory | Inventories |
| `4155` | Land/Buildings CA | Land/buildings in Canada |
| `4157` | Program Use Assets | Used for programs/admin |
| `4158` | Non-Program Assets | Used for other purposes |
| `4160` | Other CA Assets | Other capital assets in Canada |
| `4165` | Foreign Assets | Capital assets outside Canada |
| `4166` | Amortization | Accumulated amortization |
| `4170` | Other Assets | Other assets |
| `4190` | Impact Investments | Impact investments |
| `4200` | Total Assets | Total assets |
| `4350` | Total Liabilities | Total liabilities |
| `4400` | Non-Arm's Length | Transactions with non-arm's length? |
| `4490` | Tax Receipts Issued | Issued tax receipts for gifts? |
| `4500` | Tax-Receipted Gifts | Tax-receipted gifts total |
| `4510` | Charity Revenue | Revenue from other charities |
| `4530` | Non-Tax-Receipted Gifts | Non-tax-receipted gifts |
| `4540` | Federal Funding | Federal government revenue |
| `4550` | Provincial Funding | Provincial/territorial revenue |
| `4560` | Municipal Funding | Municipal/regional revenue |
| `4565` | Government Funding | Received government revenue? |
| `4570` | Gov Funding Total | Total government funding |
| `4571` | Foreign Tax Revenue | Foreign tax-receipted revenue |
| `4574` | Foreign Tax Rev | Foreign tax-receipted revenue |
| `4575` | Foreign Non-Tax Revenue | Foreign non-tax-receipted revenue |
| `4576` | Impact Income | Impact investment income |
| `4577` | Non-Arm's Income | Non-arm's length investment income |
| `4580` | Total Investment Income | Total interest/investment income |
| `4590` | Gross Asset Sales | Gross proceeds from asset sales |
| `4600` | Net Asset Sales | Net proceeds from asset sales |
| `4610` | Rental Income | Rental income from land/buildings |
| `4620` | Membership Revenue | Membership/dues revenue |
| `4630` | Fundraising Revenue | Fundraising revenue (non-tax) |
| `4640` | Sales Revenue | Goods/services sales revenue |
| `4650` | Other Revenue | Other revenue |
| `4655` | Other Revenue Type | Specify other revenue type |
| `4700` | Total Revenue | Total revenue |
| `4800` | Advertising Costs | Advertising/promotion costs |
| `4810` | Travel Costs | Travel/vehicle expenses |
| `4820` | Interest Expenses | Interest/bank charges |
| `4830` | License Fees | Licenses/memberships/dues |
| `4840` | Office Costs | Office supplies/expenses |
| `4850` | Occupancy Costs | Occupancy costs |
| `4860` | Consulting Fees | Professional/consulting fees |
| `4870` | Training Costs | Staff/volunteer training |
| `4880` | Total Comp Expenditure | Total compensation (from S3) |
| `4890` | Donated Goods | FMV of donated goods used |
| `4891` | Supplies/Assets | Purchased supplies/assets |
| `4900` | Amortization Exp | Amortization expense |
| `4910` | Research Grants | Research grants/scholarships |
| `4920` | Other Expenditures | Other expenditures |
| `4930` | Other Expenditure Types | Specify other expenditures |
| `4950` | Total Expenditures | Total expenditures (excl. disbursements) |
| `5000` | Charitable Spending | Expenditures on charitable activities |
| `5000` | Charitable Activities | Charitable activities total |
| `5010` | Admin Costs | Management/admin costs |
| `5010` | Admin Total | Management/admin total |
| `5020` | Fundraising Costs | Fundraising costs total |
| `5040` | Other Expenses | Other expenditures total |
| `5045` | Grants to Grantees | Grants to non-qualified donees |
| `5050` | Gifts to Donees | Gifts to qualified donees |
| `5100` | Total Expenses | Total expenditures |
| `5450` | Fundraiser Gross Revenue | Gross revenue collected by fundraisers |
| `5460` | Fundraiser Payments | Amounts paid/retained by fundraisers |
| `5500` | Accumulated Funds | Accumulated property amount |
| `5510` | Disbursed Accumulated | Disbursed accumulated funds |
| `5610` | Tuition Revenue | Tax-receipted tuition fees |
| `5750` | Quota Reduction | Disbursement quota reduction |
| `5800` | Non-Qualifying Security | Acquired non-qualifying security? |
| `5810` | Donor Property Use | Donor use of charity property? |
| `5820` | Third-Party Receipts | Issued receipts for another org? |
| `5830` | Partnership Holdings | Direct partnership holdings? |
| `5840` | Grants to Grantees | Grants to non-qualified donees? |
| `5841` | Large Grants (>$5k) | Grants >$5k to grantees? |
| `5842` | Small Grantee Count | Number of grantees ≤$5k |
| `5843` | Small Grant Total | Total grants ≤$5k |
| `5850` | DAF Held | Held donor advised funds (DAF)? |
| `5861` | DAF Accounts | DAF accounts count |
| `5862` | DAF Value | DAF total value |
| `5863` | DAF Donations | DAF donations received |
| `5864` | DAF Disbursements | DAF qualifying disbursements |
| `5900` | Prior Property Avg | Avg property not used (24mo prior) |
| `5910` | Post Property Avg | Avg property not used (24mo after) |
| `805` | Quota Base | Disbursement quota base amount |
| `810` | Net Accumulated | Accumulated funds net |
| `815` | Adjusted Base | Adjusted quota base |
| `820` | Quota 3.5% | Quota (≤$1M): 3.5% |
| `825` | Excess Over $1M | Excess over $1M |
| `830` | Quota 5% | Quota (>$1M): 5% |
| `835` | Total Quota | Total quota (>$1M) |
| `840` | Final Quota | Final disbursement quota |
| `845` | Charitable Total | Charitable spending total |
| `850` | Grants Total | Grants to grantees total |
| `855` | Gifts Total | Gifts to donees total |
| `860` | Total Disbursements | Total qualifying disbursements |
| `865` | Quota Balance | Quota excess/shortfall |
| `870` | Next Quota Base | Next period quota base |
| `875` | Next Quota 3.5% | Next quota (≤$1M): 3.5% |
| `880` | Next Excess | Next excess over $1M |
| `885` | Next Quota 5% | Next quota (>$1M): 5% |
| `890` | Next Total Quota | Next total quota (>$1M) |
