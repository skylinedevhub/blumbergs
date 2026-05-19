/* eslint-disable */
// T3010 Data Explorer — pure functions module.
// Dual-load: ESM `import` from Node tests; browser <script> assigns to
// globalThis.Explorer for the legacy inline script in index.html.

// ── CRA T3010 metric catalog ───────────────────────────────────
// Label conventions:
//   - Exact CRA wording from the T3010 form
//   - Line number appended as "(line NNNN)" so users know which line is being queried
//   - tb (table alias): fd=financial_d, sc=schedule_3_compensation, cc=charity_counts,
//                       s5=schedule_5_noncash, gagg=gift_agg, tagg=trustee_agg, pagg=program_agg
//   - t: '$' currency (TEXT in DB, needs money()), 'i' integer, 'n' numeric already
const M = [
  // ── Revenue (Section D) ──
  {id:'total_revenue',      l:'Total revenue (line 4700)',                                    ln:'4700',t:'$',g:'Revenue',                tb:'fd'},
  {id:'tax_receipted',      l:'Tax-receipted gifts (line 4500)',                              ln:'4500',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'ten_year_gifts_in',  l:'10-year gifts received (line 4505)',                           ln:'4505',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'gifts_charities',    l:'Gifts from other registered charities (line 4510)',           ln:'4510',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'non_receipted',      l:'Other gifts not tax-receipted (line 4530)',                    ln:'4530',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'govt_federal',       l:'Federal government funding (line 4540)',                       ln:'4540',t:'$',g:'Revenue',                tb:'fd'},
  {id:'govt_provincial',    l:'Provincial/territorial government funding (line 4550)',        ln:'4550',t:'$',g:'Revenue',                tb:'fd'},
  {id:'govt_municipal',     l:'Municipal/regional government funding (line 4560)',            ln:'4560',t:'$',g:'Revenue',                tb:'fd'},
  {id:'receipted_outside',  l:'Tax-receipted from outside Canada (line 4575, V24)',           ln:'4575',t:'$',g:'Revenue',                tb:'fd'},
  {id:'investment_income',  l:'Interest and investment income (line 4580, V24)',              ln:'4580',t:'$',g:'Revenue',                tb:'fd'},
  {id:'fundraising_rev',    l:'Revenue from fundraising (line 4630)',                         ln:'4630',t:'$',g:'Revenue',                tb:'fd'},
  {id:'sale_goods',         l:'Revenue from sale of goods/services (line 4640)',              ln:'4640',t:'$',g:'Revenue',                tb:'fd'},
  {id:'other_revenue',      l:'Revenue from all other sources (line 4650)',                   ln:'4650',t:'$',g:'Revenue',                tb:'fd'},

  // ── Expenditures (Section D) ──
  {id:'total_expenditures', l:'Total expenditures (line 5100)',                               ln:'5100',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'charitable_programs',l:'Charitable activities (line 5000)',                            ln:'5000',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'mgmt_admin',         l:'Management and administration (line 5010)',                    ln:'5010',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'fundraising_exp',    l:'Fundraising (line 5020)',                                      ln:'5020',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'political',          l:'Political activities (line 5030)',                             ln:'5030',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'gifts_to_qds',       l:'Gifts to qualified donees (line 5050)',                        ln:'5050',t:'$',g:'Expenditures — Gifts Out',tb:'fd'},
  {id:'grants_non_qds',     l:'Grants to non-qualified donees (line 5045)',                   ln:'5045',t:'$',g:'Expenditures — Gifts Out',tb:'fd'},

  // ── Balance Sheet ──
  {id:'total_assets',       l:'Total assets (line 4200)',                                     ln:'4200',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'total_liabilities',  l:'Total liabilities (line 4350)',                                ln:'4350',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'cash_investments',   l:'Cash, bank accounts, and short-term investments (line 4100)', ln:'4100',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'long_term_invest',   l:'Long-term investments (line 4140)',                            ln:'4140',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'assets_non_charit',  l:'Assets not used in charitable activities (line 4250)',         ln:'4250',t:'$',g:'Balance Sheet',          tb:'fd'},

  // ── Employment (Schedule 3) ──
  {id:'ft_employees',       l:'Permanent full-time positions (Sch 3 line 300)',               col:'"300"',t:'i',g:'Employment',         tb:'sc'},
  {id:'pt_employees',       l:'Part-time / part-year positions (Sch 3 line 370)',             col:'"370"',t:'i',g:'Employment',         tb:'sc'},
  {id:'total_compensation', l:'Total expenditure on compensation (Sch 3 line 390)',           col:'"390"',t:'$',g:'Employment',         tb:'sc'},
  {id:'compensation_fd',    l:'Total compensation reported in Section D (line 4880)',         ln:'4880',  t:'$',g:'Employment',         tb:'fd'},

  // ── Schedule 6: Detailed gifts to qualified donees (T1236) ──
  {id:'gift_total_amount',  l:'Total gifts to qualified donees (Sch 6 sum)',                  col:'total_gifts',          t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_in_kind',       l:'Gifts in kind to qualified donees (Sch 6 sum)',                col:'total_gifts_in_kind',  t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_donee_count',   l:'Number of qualified donees gifted to (Sch 6)',                 col:'num_donees',           t:'i',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_political',     l:'Gifts for political activities (Sch 6 sum)',                   col:'total_political_gifts',t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},

  // ── Schedule 5: Non-cash gifts received ──
  {id:'noncash_total',      l:'Total non-cash gifts received (Sch 5 line 580)',               ln:'580',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},
  {id:'noncash_securities', l:'Non-cash gifts: publicly traded securities (Sch 5 line 500)',  ln:'500',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},
  {id:'noncash_real_prop',  l:'Non-cash gifts: real property (Sch 5 line 540)',               ln:'540',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},

  // ── Trustees / Directors (Section B) ──
  {id:'num_trustees',         l:'Number of directors/trustees',                               col:'num_trustees',         t:'i',g:'Directors & Trustees', tb:'tagg'},
  {id:'num_arm_trustees',     l:'Directors/trustees at arm’s length',                    col:'num_arm_trustees',     t:'i',g:'Directors & Trustees', tb:'tagg'},
  {id:'num_non_arm_trustees', l:'Directors/trustees not at arm’s length',                col:'num_non_arm_trustees', t:'i',g:'Directors & Trustees', tb:'tagg'},

  // ── Programs (Section C) ──
  {id:'num_programs',         l:'Number of programs reported',                                col:'num_programs',          t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_ongoing_programs', l:'Ongoing programs (OP)',                                      col:'num_ongoing_programs',  t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_new_programs',     l:'New programs (NP)',                                          col:'num_new_programs',      t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_inactive_programs',l:'Inactive programs (NA)',                                     col:'num_inactive_programs', t:'i',g:'Programs (Section C)', tb:'pagg'},

  // ── Foreign activity (charity_counts) ──
  {id:'num_grants',         l:'Number of grants to non-qualified donees',     col:'num_grants',             t:'i',g:'Foreign Activity',tb:'cc'},
  {id:'num_countries',      l:'Number of countries of operation',             col:'num_operating_countries',t:'i',g:'Foreign Activity',tb:'cc'},
];


// ── Filter-only catalog (auto-generated from web/lib/schema-index.json) ──
// Every T3010 line not already in M, so the Filter dropdown can target ANY field.
// These are NOT shown as metric chips — only selectable in the Filter dropdown.
// Same shape as M entries: {id, l, ln|col, t, g, tb}.
const FILTER_EXTRAS = [
  {id:'fd_4020', l:'Accounting Basis (line 4020)', ln:'4020', t:'s', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4050', l:'Land/Buildings Owned (line 4050)', ln:'4050', t:'s', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4101', l:'Cash (line 4101)', ln:'4101', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4102', l:'Short-Term Investments (line 4102)', ln:'4102', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4110', l:'Non-Arm\'s Receivables (line 4110)', ln:'4110', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4120', l:'Other Receivables (line 4120)', ln:'4120', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4130', l:'Non-Arm\'s Investments (line 4130)', ln:'4130', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4150', l:'Inventory (line 4150)', ln:'4150', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4155', l:'Land/Buildings CA (line 4155)', ln:'4155', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4157', l:'Program Use Assets (line 4157)', ln:'4157', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4158', l:'Non-Program Assets (line 4158)', ln:'4158', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4160', l:'Other CA Assets (line 4160)', ln:'4160', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4165', l:'Foreign Assets (line 4165)', ln:'4165', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4166', l:'Amortization (line 4166)', ln:'4166', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4170', l:'Other Assets (line 4170)', ln:'4170', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4180', l:'10 year gifts (line 4180)', ln:'4180', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4190', l:'Impact Investments (line 4190)', ln:'4190', t:'$', g:'Balance Sheet — Assets', tb:'fd'},
  {id:'fd_4300', l:'Accounts payable and accrued liabilities (line 4300)', ln:'4300', t:'$', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4310', l:'Deferred revenue (line 4310)', ln:'4310', t:'$', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4320', l:'Amounts owing to non-arm\'s length parties (line 4320)', ln:'4320', t:'$', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4330', l:'Other liabilities (line 4330)', ln:'4330', t:'$', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4400', l:'Non-Arm\'s Length (line 4400)', ln:'4400', t:'s', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4490', l:'Tax Receipts Issued (line 4490)', ln:'4490', t:'s', g:'Balance Sheet — Liabilities & Equity', tb:'fd'},
  {id:'fd_4565', l:'Government Funding (line 4565)', ln:'4565', t:'s', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4570', l:'Gov Funding Total (line 4570)', ln:'4570', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4571', l:'Foreign Tax Revenue (line 4571)', ln:'4571', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4576', l:'Impact Income (line 4576)', ln:'4576', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4577', l:'Non-Arm\'s Income (line 4577)', ln:'4577', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4590', l:'Gross Asset Sales (line 4590)', ln:'4590', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4600', l:'Net Asset Sales (line 4600)', ln:'4600', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4610', l:'Rental Income (line 4610)', ln:'4610', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4620', l:'Membership Revenue (line 4620)', ln:'4620', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4655', l:'Other Revenue Type (line 4655)', ln:'4655', t:'$', g:'Revenue — Detail', tb:'fd'},
  {id:'fd_4800', l:'Advertising Costs (line 4800)', ln:'4800', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4810', l:'Travel Costs (line 4810)', ln:'4810', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4820', l:'Interest Expenses (line 4820)', ln:'4820', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4830', l:'License Fees (line 4830)', ln:'4830', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4840', l:'Office Costs (line 4840)', ln:'4840', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4850', l:'Occupancy Costs (line 4850)', ln:'4850', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4860', l:'Consulting Fees (line 4860)', ln:'4860', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4870', l:'Training Costs (line 4870)', ln:'4870', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4890', l:'Donated Goods (line 4890)', ln:'4890', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4891', l:'Supplies/Assets (line 4891)', ln:'4891', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4900', l:'Amortization Exp (line 4900)', ln:'4900', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4910', l:'Research Grants (line 4910)', ln:'4910', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4920', l:'Other Expenditures (line 4920)', ln:'4920', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4930', l:'Other Expenditure Types (line 4930)', ln:'4930', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_4950', l:'Total Expenditures (line 4950)', ln:'4950', t:'$', g:'Expenditures — Detail', tb:'fd'},
  {id:'fd_5040', l:'Other Expenses (line 5040)', ln:'5040', t:'$', g:'Expenditures — Totals', tb:'fd'},
  {id:'fd_5500', l:'Accumulated Funds (line 5500)', ln:'5500', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'fd_5510', l:'Disbursed Accumulated (line 5510)', ln:'5510', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'fd_5610', l:'Tuition Revenue (line 5610)', ln:'5610', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'fd_5750', l:'Quota Reduction (line 5750)', ln:'5750', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'fd_5900', l:'Prior Property Avg (line 5900)', ln:'5900', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'fd_5910', l:'Post Property Avg (line 5910)', ln:'5910', t:'$', g:'Other (Sch 6 / Compensation Mirror)', tb:'fd'},
  {id:'sc_305', l:'$1-39,999 (of the 10 highest compensated) (line 305)', ln:'305', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_310', l:'$40,000-$79,999 (of the 10 highest compensated) (line 310)', ln:'310', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_315', l:'$80,000-119,999 (of the 10 highest compensated) (line 315)', ln:'315', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_320', l:'$120,000-159,999 (of the 10 highest compensated) (line 320)', ln:'320', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_325', l:'$160,000-199,999 (of the 10 highest compensated) (line 325)', ln:'325', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_330', l:'$200,000-249,999 (of the 10 highest compensated) (line 330)', ln:'330', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_335', l:'$250,000-299,999 (of the 10 highest compensated) (line 335)', ln:'335', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_340', l:'$300,000-349,999 (of the 10 highest compensated) (line 340)', ln:'340', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_345', l:'$350,000-over (of the 10 highest compensated) (line 345)', ln:'345', t:'i', g:'Compensation — Employee Counts', tb:'sc'},
  {id:'sc_380', l:'Part-Time Costs (line 380)', ln:'380', t:'$', g:'Compensation — Totals', tb:'sc'},
  {id:'s5_505', l:'Charity issued receipts for building materials (line 505)', ln:'505', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_510', l:'Charity issued receipts for clothing/furniture/food (line 510)', ln:'510', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_515', l:'Charity issued receipts for vehicles (line 515)', ln:'515', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_520', l:'Charity issued receipts for cultural properties (line 520)', ln:'520', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_525', l:'Charity issued receipts for ecological properties (line 525)', ln:'525', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_530', l:'Charity issued receipts for life insurance policies (line 530)', ln:'530', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_535', l:'Charity issued receipts for medical equipment/supplies (line 535)', ln:'535', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_545', l:'Charity issued receipts for machinery/equipment/computers… (li…', ln:'545', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_550', l:'Charity issued receipts for publicly traded securities/co… (li…', ln:'550', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_555', l:'Charity issued receipts for books (line 555)', ln:'555', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_560', l:'Other (line 560)', ln:'560', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s5_565', l:'Specify for others (line 565)', ln:'565', t:'$', g:'Non-Cash Gifts (Sch 5)', tb:'s5'},
  {id:'s8_805', l:'Charitable activities using own staff and volunteers (line 805)', ln:'805', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_810', l:'Gifts to qualified donees (line 810)', ln:'810', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_815', l:'Administrative expenditures attributable to charitable ac… (li…', ln:'815', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_820', l:'Total qualifying disbursements (=805+810+815) (line 820)', ln:'820', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_825', l:'Prior year excess disbursements applied (line 825)', ln:'825', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_830', l:'Net qualifying disbursements (line 830)', ln:'830', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_835', l:'Value of charitable gifts — 3.5% base (line 835)', ln:'835', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_840', l:'Value of other property — 3.5% base (line 840)', ln:'840', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_845', l:'Total disbursement quota base (line 845)', ln:'845', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_850', l:'Disbursement quota (3.5% of 845) (line 850)', ln:'850', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_855', l:'Shortfall (850 minus 830) (line 855)', ln:'855', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_860', l:'Accumulated disbursement shortfall (line 860)', ln:'860', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_865', l:'Reduction approved by Minister (line 865)', ln:'865', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_870', l:'Excess disbursements carried forward (line 870)', ln:'870', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_875', l:'10-year gifts received (line 875)', ln:'875', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_880', l:'10-year gifts disbursed (line 880)', ln:'880', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_885', l:'Enduring property held (line 885)', ln:'885', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s8_890', l:'Net enduring property (line 890)', ln:'890', t:'$', g:'Disbursement Quota (Sch 8)', tb:'s8'},
  {id:'s1_100', l:'Corporate Control (line 100)', ln:'100', t:'s', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'s1_110', l:'Non-Operating Debt (line 110)', ln:'110', t:'s', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'s1_111', l:'Restricted Funds (line 111)', ln:'111', t:'$', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'s1_112', l:'Unspendable Funds (line 112)', ln:'112', t:'$', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'s1_120', l:'Non-Qualified Investments (line 120)', ln:'120', t:'s', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'s1_130', l:'Excess Shareholding (line 130)', ln:'130', t:'s', g:'Foundations (Sch 1)', tb:'s1'},
  {id:'fabc_1570', l:'Wound-Up/Dissolved (line 1570)', ln:'1570', t:'s', g:'Identification (fabc 1500s)', tb:'fabc'},
  {id:'fabc_1600', l:'Foundation Designation (line 1600)', ln:'1600', t:'s', g:'Status & Activity Flags', tb:'fabc'},
  {id:'fabc_1800', l:'Active (line 1800)', ln:'1800', t:'s', g:'Status & Activity Flags', tb:'fabc'},
  {id:'fabc_2000', l:'Gifts to Qualified Donees (line 2000)', ln:'2000', t:'s', g:'Gifts & Foreign Activity Flags', tb:'fabc'},
  {id:'fabc_2100', l:'Foreign Activities (line 2100)', ln:'2100', t:'s', g:'Section C — Other', tb:'fabc'},
  {id:'fabc_2400', l:'Did charity carry out any political activities during the… (li…', ln:'2400', t:'s', g:'Public Policy / Political (V23)', tb:'fabc'},
  {id:'fabc_2500', l:'Advertising (line 2500)', ln:'2500', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2510', l:'Auctions (line 2510)', ln:'2510', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2530', l:'Collection Boxes (line 2530)', ln:'2530', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2540', l:'Door-to-Door (line 2540)', ln:'2540', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2550', l:'Lotteries (line 2550)', ln:'2550', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2560', l:'Fundraising Events (line 2560)', ln:'2560', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2570', l:'Sales (line 2570)', ln:'2570', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2575', l:'Internet (line 2575)', ln:'2575', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2580', l:'Mail Campaigns (line 2580)', ln:'2580', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2590', l:'Planned Giving (line 2590)', ln:'2590', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2600', l:'Corporate Sponsorships (line 2600)', ln:'2600', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2610', l:'Targeted Contacts (line 2610)', ln:'2610', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2620', l:'Phone/TV Solicitations (line 2620)', ln:'2620', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2630', l:'Sporting Events (line 2630)', ln:'2630', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2640', l:'Cause Marketing (line 2640)', ln:'2640', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2650', l:'Other Fundraising (line 2650)', ln:'2650', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2660', l:'Specify Fundraising (line 2660)', ln:'2660', t:'$', g:'Fundraising Methods', tb:'fabc'},
  {id:'fabc_2700', l:'External Fundraisers (line 2700)', ln:'2700', t:'s', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2730', l:'Method of payment to fundraisers: Commissions (line 2730)', ln:'2730', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2740', l:'Bonuses (line 2740)', ln:'2740', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2750', l:'Commissions (line 2750)', ln:'2750', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2760', l:'Service Fee (line 2760)', ln:'2760', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2770', l:'Honoraria (line 2770)', ln:'2770', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2780', l:'Other Payment (line 2780)', ln:'2780', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2790', l:'Specify Payment (line 2790)', ln:'2790', t:'$', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_2800', l:'Fundraiser Tax Receipts (line 2800)', ln:'2800', t:'s', g:'Fundraiser Engagement', tb:'fabc'},
  {id:'fabc_3200', l:'Director Compensation (line 3200)', ln:'3200', t:'s', g:'Other Section C Flags', tb:'fabc'},
  {id:'fabc_3400', l:'Employee Compensation (line 3400)', ln:'3400', t:'s', g:'Other Section C Flags', tb:'fabc'},
  {id:'fabc_3900', l:'Foreign Donations ≥$10k (line 3900)', ln:'3900', t:'s', g:'Other Section C Flags', tb:'fabc'},
  {id:'fabc_4000', l:'Non-Cash Gifts (line 4000)', ln:'4000', t:'s', g:'Foreign Funding', tb:'fabc'},
  {id:'fabc_5030', l:'Total expenditures on political activities spent by the c… (li…', ln:'5030', t:'$', g:'Political Activity Gifts (V23)', tb:'fabc'},
  {id:'fabc_5031', l:'Total amount of 5030 gifts made for qualified donees (line 5031)', ln:'5031', t:'$', g:'Political Activity Gifts (V23)', tb:'fabc'},
  {id:'fabc_5032', l:'Total amount received from outside Canada that was direct… (li…', ln:'5032', t:'$', g:'Political Activity Gifts (V23)', tb:'fabc'},
  {id:'fabc_5450', l:'Fundraiser Gross Revenue (line 5450)', ln:'5450', t:'$', g:'Fundraiser Amounts', tb:'fabc'},
  {id:'fabc_5460', l:'Fundraiser Payments (line 5460)', ln:'5460', t:'$', g:'Fundraiser Amounts', tb:'fabc'},
  {id:'fabc_5800', l:'Non-Qualifying Security (line 5800)', ln:'5800', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5810', l:'Donor Property Use (line 5810)', ln:'5810', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5820', l:'Third-Party Receipts (line 5820)', ln:'5820', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5830', l:'Partnership Holdings (line 5830)', ln:'5830', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5840', l:'Grants to Grantees (line 5840)', ln:'5840', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5841', l:'Large Grants (>$5k) (line 5841)', ln:'5841', t:'s', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5842', l:'Small Grantee Count (line 5842)', ln:'5842', t:'i', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5843', l:'Small Grant Total (line 5843)', ln:'5843', t:'$', g:'Non-Qualifying Securities / Grants V26', tb:'fabc'},
  {id:'fabc_5850', l:'DAF Held (line 5850)', ln:'5850', t:'s', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_5860', l:'Did the charity hold any donor advised funds (DAF) during… (li…', ln:'5860', t:'s', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_5861', l:'DAF Accounts (line 5861)', ln:'5861', t:'i', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_5862', l:'DAF Value (line 5862)', ln:'5862', t:'$', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_5863', l:'DAF Donations (line 5863)', ln:'5863', t:'$', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_5864', l:'DAF Disbursements (line 5864)', ln:'5864', t:'$', g:'Donor-Advised Funds (V27)', tb:'fabc'},
  {id:'fabc_1200_percent', l:'Most important field of operations percentage - program a…', col:'"1200 Percent"', t:'i', g:'Section A/B/C Questions', tb:'fabc'},
  {id:'fabc_1210_percent', l:'Second most important field of operations percentage - pr…', col:'"1210 Percent"', t:'i', g:'Section A/B/C Questions', tb:'fabc'},
  {id:'fabc_1220_percent', l:'Third most important field of operations percentage - pro…', col:'"1220 Percent"', t:'i', g:'Section A/B/C Questions', tb:'fabc'},
  {id:'fabc_1510_subordinate_position_to_a', l:'Is the charity subordinate to a parent organization?', col:'"1510 Subordinate position to a parent organization?"', t:'s', g:'Section A/B/C Questions', tb:'fabc'},
];

// Combined catalog used by SQL generation and filter lookup.
// Metric chips still iterate M only; filters iterate ALL_METRICS.
const ALL_METRICS = M.concat(FILTER_EXTRAS);
const getFilterMetric = function(id){ return ALL_METRICS.find(function(m){return m.id===id}); };

const PRESETS = [
  {n:'Sector Overview', s:{mode:'aggregate',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','total_assets','total_compensation'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'By Province', s:{mode:'aggregate',prov:'',desig:'',cat:'',gb:'province',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','ft_employees'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Top 25 Revenue', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','total_assets'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Top Employers', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['ft_employees','pt_employees','total_compensation'],
    filters:[],sort:'ft_employees',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Foreign Activity', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','num_countries','num_grants'],
    filters:[{f:'num_countries',op:'>',v:'0'}],sort:'num_countries',dir:'DESC',lim:50,search:'',customWhere:''}},
  {n:'Foundations Only', s:{mode:'detail',prov:'',desig:'A',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_assets','gifts_to_qds'],
    filters:[],sort:'total_assets',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'All Gifts', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['tax_receipted','gifts_charities','non_receipted','ten_year_gifts_in','gifts_to_qds','grants_non_qds','noncash_total'],
    filters:[],sort:'tax_receipted',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Trustees & Programs', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['num_trustees','num_arm_trustees','num_non_arm_trustees','num_programs','num_ongoing_programs'],
    filters:[],sort:'num_trustees',dir:'DESC',lim:25,search:'',customWhere:''}},
];

// ── Helpers ─────────────────────────────────────────────────────
const getMetric = function(id, catalog){ catalog = catalog || M; return catalog.find(function(m){return m.id===id}); };

const needsTable = function(state, alias, catalog){
  catalog = catalog || M;
  // Metrics are always picked from M (or the test-supplied catalog).
  // Filters can reference FILTER_EXTRAS too, so fall back to getFilterMetric for unknown IDs.
  return state.metrics.some(function(id){var m=getMetric(id,catalog);return m&&m.tb===alias;}) ||
         state.filters.some(function(f){var m=getMetric(f.f,catalog) || getFilterMetric(f.f);return m&&m.tb===alias;});
};

function colRef(m){
  // Numeric T3010 line columns are quoted by line number in any table:
  //   fd."4700", s5."580", s8."805", s1."111", fabc."1570", sc."300"
  if(m.ln) return m.tb+'."'+m.ln+'"';
  // Named columns (the metric provides 'col' already pre-quoted if needed):
  return m.tb+'.'+m.col;
}

// CTE-derived tables (gift_agg, trustee_agg, program_agg) already produce
// numeric columns inside the CTE — no outer money() wrapper needed.
const CTE_TABLES = ['gagg','tagg','pagg'];
function isAlreadyNumeric(m){
  return m.t === 'i' || m.t === 'n' || CTE_TABLES.indexOf(m.tb) >= 0;
}

function moneyExpr(m){
  if(isAlreadyNumeric(m)) return colRef(m);
  return 'money('+colRef(m)+')';
}

function aggExpr(m, fn){
  if(fn==='MEDIAN'){
    var expr = isAlreadyNumeric(m) ? colRef(m) : 'money('+colRef(m)+')';
    return 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY '+expr+')';
  }
  if(isAlreadyNumeric(m)) return fn+'('+colRef(m)+')';
  return fn+'(money('+colRef(m)+'))';
}

function escSql(s){ return String(s).replace(/'/g,"''"); }

// ── Derived sub-aggregate CTE templates ─────────────────────────
// These produce one row per BN so downstream LEFT JOINs are 1:1 with charity_base.

const GIFT_AGG_CTE =
  'gift_agg AS (\n' +
  '  SELECT g."BN/Registration number" AS bn,\n' +
  '         SUM(money(g."Total amount gifts")) AS total_gifts,\n' +
  '         SUM(money(g."Amount of gifts in kind")) AS total_gifts_in_kind,\n' +
  '         COUNT(*) AS num_donees,\n' +
  '         SUM(money(g."Political Activities Gift Amount")) AS total_political_gifts\n' +
  '  FROM gift g\n' +
  '  WHERE g.data_year = (SELECT MAX(data_year) FROM gift)\n' +
  '  GROUP BY g."BN/Registration number"\n' +
  ')';

// Trustee table column uses a straight ASCII apostrophe ("At arm's length").
// We escape it inside the single-quoted JS string with \' so the emitted SQL
// has the bare apostrophe inside a double-quoted Postgres identifier.
const TRUSTEE_AGG_CTE =
  'trustee_agg AS (\n' +
  '  SELECT t."BN/Registration number" AS bn,\n' +
  '         COUNT(*) AS num_trustees,\n' +
  '         SUM(CASE WHEN UPPER(LEFT(t."At arm\'s length", 1)) = \'Y\' THEN 1 ELSE 0 END) AS num_arm_trustees,\n' +
  '         SUM(CASE WHEN UPPER(LEFT(t."At arm\'s length", 1)) = \'N\' THEN 1 ELSE 0 END) AS num_non_arm_trustees\n' +
  '  FROM trustee t\n' +
  '  WHERE t.data_year = (SELECT MAX(data_year) FROM trustee)\n' +
  '  GROUP BY t."BN/Registration number"\n' +
  ')';

const PROGRAM_AGG_CTE =
  'program_agg AS (\n' +
  '  SELECT p."BN/Registration number" AS bn,\n' +
  '         COUNT(*) AS num_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'OP\' THEN 1 ELSE 0 END) AS num_ongoing_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'NP\' THEN 1 ELSE 0 END) AS num_new_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'NA\' THEN 1 ELSE 0 END) AS num_inactive_programs\n' +
  '  FROM programs p\n' +
  '  WHERE p.data_year = (SELECT MAX(data_year) FROM programs)\n' +
  '  GROUP BY p."BN/Registration number"\n' +
  ')';

// ── SQL generation ──────────────────────────────────────────────
function genSQL(state, catalog){
  catalog = catalog || M;
  const sel = state.metrics.map(function(id){return getMetric(id,catalog);}).filter(Boolean);
  if(!sel.length) return '-- Select at least one metric';

  const uses = {
    fd:   needsTable(state,'fd',catalog),
    sc:   needsTable(state,'sc',catalog),
    cc:   needsTable(state,'cc',catalog),
    s5:   needsTable(state,'s5',catalog),
    s8:   needsTable(state,'s8',catalog),
    s1:   needsTable(state,'s1',catalog),
    fabc: needsTable(state,'fabc',catalog),
    gagg: needsTable(state,'gagg',catalog),
    tagg: needsTable(state,'tagg',catalog),
    pagg: needsTable(state,'pagg',catalog),
  };

  const ctes = [];
  if(uses.gagg) ctes.push(GIFT_AGG_CTE);
  if(uses.tagg) ctes.push(TRUSTEE_AGG_CTE);
  if(uses.pagg) ctes.push(PROGRAM_AGG_CTE);

  let q = '';
  if(ctes.length) q += 'WITH ' + ctes.join(',\n') + '\n';

  if(state.mode === 'detail'){
    q += 'SELECT\n  cb.bn,\n  cb.legal_name,\n  cb.designation_desc,\n  cb.province';
    sel.forEach(function(m){ q += ',\n  ' + moneyExpr(m) + ' AS ' + m.id; });
    q += '\n';
  } else {
    const gc = state.gb === 'designation' ? 'cb.designation_desc'
             : state.gb === 'province'    ? 'cb.province'
             : 'cb.category_desc';
    q += 'SELECT\n  ' + gc + ',\n  COUNT(*) AS charity_count';
    sel.forEach(function(m){ q += ',\n  ' + aggExpr(m, state.aggfn) + ' AS ' + m.id; });
    q += '\n';
  }

  q += 'FROM charity_base cb\n';
  if(uses.fd)   q += 'LEFT JOIN financial_d fd ON fd."BN/Registration Number" = cb.bn\n';
  if(uses.sc)   q += 'LEFT JOIN schedule_3_compensation sc ON sc."BN/Registration number" = cb.bn\n';
  if(uses.cc)   q += 'LEFT JOIN charity_counts cc ON cc.bn = cb.bn\n';
  if(uses.s5)   q += 'LEFT JOIN schedule_5_noncash s5 ON s5."BN/Registration number" = cb.bn\n';
  if(uses.s8)   q += 'LEFT JOIN schedule_8_disbursement s8 ON s8."BN/Registration Number" = cb.bn\n';
  if(uses.s1)   q += 'LEFT JOIN schedule_1_foundations s1 ON s1."BN/Registration number" = cb.bn\n';
  if(uses.fabc) q += 'LEFT JOIN financial_abc fabc ON fabc."BN/Registration number" = cb.bn\n';
  if(uses.gagg) q += 'LEFT JOIN gift_agg gagg ON gagg.bn = cb.bn\n';
  if(uses.tagg) q += 'LEFT JOIN trustee_agg tagg ON tagg.bn = cb.bn\n';
  if(uses.pagg) q += 'LEFT JOIN program_agg pagg ON pagg.bn = cb.bn\n';

  const w = [];
  if(state.prov)  w.push("cb.province = '"+state.prov+"'");
  if(state.desig) w.push("cb.designation_code = '"+state.desig+"'");
  if(state.cat)   w.push("cb.category_code = '"+escSql(state.cat)+"'");
  if(state.search && state.search.trim()){
    const term = escSql(state.search.trim());
    w.push("(cb.legal_name ILIKE '%"+term+"%' OR cb.bn ILIKE '%"+term+"%')");
  }
  state.filters.forEach(function(f){
    // Filters can target M or FILTER_EXTRAS — fall back to the combined catalog.
    const m = getMetric(f.f, catalog) || getFilterMetric(f.f);
    if(!m || !f.v) return;
    let val = String(f.v).trim();
    let lhs;
    if(m.t === 's'){
      // String/Y-N column — compare raw text. Wrap unquoted single-token values in quotes.
      lhs = colRef(m);
      if(!/^'.*'$/.test(val) && !/^-?\d+(\.\d+)?$/.test(val)){
        val = "'" + escSql(val) + "'";
      }
    } else if(isAlreadyNumeric(m)){
      lhs = colRef(m);
    } else {
      // Currency VARCHAR — convert with money().
      lhs = 'money('+colRef(m)+')';
    }
    w.push(lhs+' '+f.op+' '+val);
  });
  if(state.customWhere && state.customWhere.trim()) w.push('('+state.customWhere.trim()+')');
  if(w.length) q += 'WHERE ' + w.join('\n  AND ') + '\n';

  if(state.mode === 'aggregate'){
    const gc2 = state.gb === 'designation' ? 'cb.designation_desc'
              : state.gb === 'province'    ? 'cb.province'
              : 'cb.category_desc';
    q += 'GROUP BY ' + gc2 + '\n';
  }

  const sm = getMetric(state.sort, catalog);
  if(sm){
    const se = state.mode === 'aggregate' ? state.sort : moneyExpr(sm);
    q += 'ORDER BY ' + se + ' ' + state.dir + ' NULLS LAST\n';
  } else if(state.sort === 'charity_count' && state.mode === 'aggregate'){
    q += 'ORDER BY charity_count ' + state.dir + '\n';
  }
  q += 'LIMIT ' + state.lim + ';';
  return q;
}

// ── Number formatting ───────────────────────────────────────────
// `t` is the metric's type marker: '$' for currency, 'i' for integer, undefined → guess.
function formatValue(val, t){
  if(val === null || val === undefined || val === '') return '—';
  if(typeof val === 'number'){
    if(t === '$'){
      const sign = val < 0 ? '-' : '';
      return sign + '$' + Math.abs(Math.round(val)).toLocaleString('en-CA');
    }
    if(t === 'i'){
      return Math.round(val).toLocaleString('en-CA');
    }
    if(Math.abs(val) >= 1 || val === 0){
      return val.toLocaleString('en-CA', {maximumFractionDigits:0});
    }
    return val.toLocaleString('en-CA', {maximumFractionDigits:2});
  }
  return String(val);
}

// Build a lookup: columnName (alias used in SQL) -> metric so the table renderer
// can apply $ vs integer formatting.
function columnTypeMap(metrics, catalog){
  catalog = catalog || M;
  const map = {};
  metrics.forEach(function(id){
    const m = getMetric(id, catalog);
    if(m) map[id] = m.t;
  });
  return map;
}

const Explorer = {
  M: M,
  FILTER_EXTRAS: FILTER_EXTRAS,
  ALL_METRICS: ALL_METRICS,
  PRESETS: PRESETS,
  getMetric: getMetric,
  getFilterMetric: getFilterMetric,
  needsTable: needsTable,
  genSQL: genSQL,
  formatValue: formatValue,
  columnTypeMap: columnTypeMap,
  escSql: escSql,
};

// Browser: expose as a global so the inline classic <script> in index.html
// can still reach M, PRESETS, genSQL, etc. without becoming a module itself.
if (typeof globalThis !== 'undefined') {
  globalThis.Explorer = Explorer;
}

export { M, FILTER_EXTRAS, ALL_METRICS, PRESETS, getMetric, getFilterMetric, needsTable, genSQL, formatValue, columnTypeMap, escSql };
export default Explorer;
