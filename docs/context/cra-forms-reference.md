# CRA Forms Reference

Authoritative reference for the CRA forms behind the T3010 Registered Charity Information Return. Source files in `docs/reference/cra-forms/`. Per-form summaries below are derived from CRA's own descriptions (T4033 guide + each form's preamble) and from Mark Blumberg's contextual notes.

When interpreting database fields, treat these definitions as ground truth — they override prior assumptions in scripts and earlier docs.

---

## T3010 — Registered Charity Information Return (T3010-24e)

Annual information return filed by every registered Canadian charity within 6 months of fiscal year-end. The core public reporting document; the source of every record in this database.

Sections:
| Section | Contents | DB Table |
|---|---|---|
| A — Identification | BN, legal name, addresses, designation, category | `ident`, `charity_base` |
| B — Directors/Trustees | Board composition (T1235 worksheet) | `trustee` |
| C — Programs & General Info | Fundraising methods, political activities, Y/N questions, DAF data, gifts to qualified donees | `financial_abc`, `programs`, `gift` |
| D — Financial Information | Balance sheet + income statement | `financial_d` |
| Schedule 1 | Foundations only | `schedule_1_foundations` |
| Schedule 2 | Activities outside Canada | `schedule_2_*` |
| Schedule 3 | Compensation (salary bands, top 10) | `schedule_3_compensation` |
| Schedule 5 | Non-cash gifts received | `schedule_5_noncash` |
| Schedule 6 | Alternative financial section (small charities) | merged into `financial_d` with `Section Used (D or 6) = 6` |
| Schedule 7 | Political activities (V23 only; removed in V24) | `schedule_7_*` |
| Schedule 8 | Disbursement quota | `schedule_8_disbursement` |

**Form versioning**: The T3010 evolves. The `Form ID` column on every transactional table identifies the version a particular return used. The active version for 2024 data is V24. A few line numbers were repurposed between V23→V24 (see "Form version pitfalls" below).

**Confidentiality note**: A small portion of the T3010 (e.g. directors' home addresses, signing officer info) is *not* in the public data. Everything you see in our DuckDB is public; absence of a field does not mean a charity didn't file it.

---

## T4033 — Completing the Registered Charity Information Return (T4033-24e)

CRA's official guide for completing the T3010. The starting point for understanding how CRA *expects* charities to report any given item. Use this when interpreting a field's intended meaning or judging whether a charity is misclassifying revenue/expenditures.

Key interpretive principles (paraphrased from T4033):
- **Cash vs accrual** (line 4020): Charities self-select. Mixed accounting across years is common.
- **Fair market value vs cost** (line 4200): For donated assets, charities report FMV at receipt; for purchased assets, at cost. Lines 4200 and 4350 are *not* expected to balance — the difference rolls into a balancing net-assets account.
- **Total revenue (4700)** = 4500 + 4510 + 4530 + 4570 + 4575 + 4630 + 4640 + 4650 (per T4033). Other sub-lines (4540, 4550, 4560, 4565, 4571, 4580, 4590, 4600, 4610, 4620, 4655) are detail that feeds into the larger buckets, not additive.
- **Government funding (4570)** is meant to be the sum of 4540 + 4550 + 4560. T4033 acknowledges this is self-totalled and not validated by CRA — hence our convention to recompute it from 4540/4550/4560.
- **Charitable activities (5000)** + **Mgmt/admin (5010)** + **Fundraising (5020)** should equal 4950 (Total operating expenditures from D4). Total expenditures (5100) = 4950 + 5045 + 5050.
- **Schedule 6 vs Section D**: Smaller charities may use Schedule 6 in lieu of Section D. The `Section Used (D or 6)` column on `financial_d` flags which they used. Field semantics are identical; CRA merges them into the same dataset.

---

## T1235 — Directors/Trustees and Like Officials Worksheet (T1235-20e)

Detailed disclosure of directors, trustees, and similar officials. Supplements Section B governance disclosures. Feeds the `trustee` DB table.

Per-row fields include:
- Position (Director, Trustee, etc.)
- First/Last Name
- Appointed Date / Ceased Date
- **At arm's length** (Y/N) — STRAIGHT ASCII apostrophe in the column header; not curly.

Use this table to assess:
- Board size and turnover
- Arm's-length ratio (governance independence proxy)
- Founder/family entrenchment in private foundations (cross-reference `cb.legal_name`)

Note: directors' home addresses are confidential and NOT in the public data.

---

## T1236 — Qualified Donees Worksheet (T1236-19e)

Disclosure of amounts the charity gave to *qualified donees* (other registered charities, RNASOs, registered amateur athletic associations, registered universities outside Canada listed on Schedule VIII, the United Nations and its agencies, etc.). Feeds the `gift` DB table.

Per-row fields include:
- Donee name, BN (if a Canadian registered charity), city, province
- Total amount of gifts (cash)
- Amount of gifts in kind (non-cash)
- Political Activities Gift Amount (legacy V23 field; deprecated in V24)
- Number of donees

The financial total on T1236 should reconcile to line 5050 on the T3010 (gifts to qualified donees). When it doesn't, the T1236 detail is generally more reliable than 5050.

---

## T1441 — Qualifying Disbursements: Grants to Non-Qualified Donees

Introduced June 2022 by the *qualifying disbursements* regime (Bill C-19). Lets registered charities grant to organizations that are NOT qualified donees (i.e. non-profits, foreign NGOs, etc.) provided certain accountability conditions are met. Feeds the `grants` DB table.

Per-row fields:
- Grantee name, country
- Purpose of the grant
- Cash amount and non-cash amount
- Active monitoring / accountability description

This is *only* available from V26 onward. Records exist only for fiscal years ending after June 23, 2022. The total flows to line 5045 on the T3010.

Practical implication: grants to non-qualified donees are a **new sector activity**. Year-over-year growth on line 5045 reflects regime adoption, not necessarily increased giving.

---

## T2081 — Excess Corporate Holdings Worksheet for Private Foundations (T2081-10e)

Applies only to private foundations subject to the *excess corporate holdings* regime (s. 149.1 of the Income Tax Act, in effect since 2007), which caps a private foundation's holdings of any single class of corporate shares. Tracks holdings, divestment obligations, and any divestment shortfall taxes payable.

Few charities are affected; relevant when analyzing large family-foundation portfolios. Not currently represented as a separate DB table — relevant flags live on `schedule_1_foundations` (line 130 "Excess corporate holdings?").

---

## Confidential CRA Reference Materials (NOT in repo)

The following files are CRA partner-distributed materials, marked confidential by Mark Blumberg. They are stored locally in `docs/reference/cra-internal/` (gitignored) and used only to enrich documentation:

1. **T3010 Public Data Dictionary 2024** — Authoritative field-by-field schema for every table in the public data download. Provides the `DESCRIPTION` text used throughout `t3010-field-dictionary.md` and the `web/lib/schema-index.json` column descriptions.
2. **T3010 Public Data Dictionary 2023** — Prior-year version. Useful for diffing field definitions when investigating V23 vs V24 discrepancies.
3. **T3010 Line Number and Contents Index 2024** — Canonical line-number → short-label + full-question mapping (162 entries). Source for short labels in the field dictionary.

Their content is paraphrased and integrated into the project docs; the source XLSX files themselves should not be committed to the public repo.

---

## Form Version Pitfalls (V23 → V24)

Per the data dictionary's per-column FORM VERSION metadata, these lines changed definition between versions. Direct year-over-year comparison on these lines is **invalid**:

| Line | V23 meaning | V24 meaning |
|---|---|---|
| 4101 | Receivables breakdown | Cash in bank accounts (subset of 4100) |
| 4102 | Receivables breakdown | Short-term investments (subset of 4100) |
| 4575 | Tax-receipted from outside Canada | Non-tax-receipted revenue from outside Canada |
| 4580 | Non-tax-receipted from outside Canada | Interest and investment income |
| 4576 | (new in V24) | Foreign business/investment activities subset of 4580 |
| 4577 | (new in V24) | Related business activities subset of 4580 |
| 4157/4158 | (new in V24) | Canadian land/buildings used for charitable activity |
| 4190 | (new in V24) | Value of all impact investments |
| Schedule 7 | Political activities (Sch7 Desc, Sch7 Political Activities Fund, Sch7 Political Activities Res) | Schedule 7 removed (political activities reform) |

For cross-version analysis, filter on `Form ID` and treat changed lines as separate series, not a continuous metric.
