#!/usr/bin/env python3
"""
Annotate blank T3010-24e.pdf with 2024 aggregate sector data in blue text,
matching the Blumbergs Snapshot style used for the 2023 version.
"""

import json
import sys
import fitz  # pymupdf

# ── helpers ──────────────────────────────────────────────────────────────────
BLUE = (0, 0, 0.8)  # dark blue matching the 2023 style
FONT = "helv"
X_OFFSET = 10  # Global horizontal shift (positive = right); tweak to align with form fields

# Per-section horizontal adjustments (added ON TOP of X_OFFSET).
# Positive = shift right, negative = shift left.
SECTION_X = {
    "section_a":    0,   # Page 0 — Section A: Identification + B + C start
    "section_c":    0,   # Page 1 — Section C continued
    "section_c2":   0,   # Page 2 — C16-C18, DAF
    "section_d":    0,   # Page 3 — Section D: Financial Information
    "schedule_1_2": 0,   # Page 5 — Schedule 1 (Foundations) + Schedule 2
    "schedule_3_5": 0,   # Page 7 — Schedule 3 (Compensation) + Schedule 5
    "schedule_6a":  0,   # Page 8 — Schedule 6: Assets, Liabilities, Revenue
    "schedule_6b":  0,   # Page 9 — Schedule 6: Expenditures + Other
    "schedule_8":   0,   # Page 10 — Schedule 8: Disbursement Quota
}

_section_x = 0  # current section offset (set via set_section)

def set_section(name):
    """Set the active section for per-section X offset adjustments."""
    global _section_x
    _section_x = SECTION_X.get(name, 0)

def fmt_num(n):
    """Format integer with commas: 83275 → '83,275'"""
    if n is None:
        return "N/A"
    return f"{int(n):,}"

def fmt_money(n):
    """Format dollar amount: 439086935797 → '439,086,935,797' (no $ — form already has it)."""
    if n is None:
        return "N/A"
    return f"{int(n):,}"

def add_text(page, x, y, text, size=7, align="left"):
    """Insert blue text at given coordinates (X_OFFSET + section offset applied).
    align='right' treats x as the right edge of the text."""
    text = str(text)
    effective_x = x + X_OFFSET + _section_x
    if align == "right":
        text_width = fitz.get_text_length(text, fontname=FONT, fontsize=size)
        effective_x -= text_width
    page.insert_text(fitz.Point(effective_x, y), text,
                     fontsize=size, fontname=FONT, color=BLUE)

def add_yes_no(page, line_y, yes_count, no_count, yes_x=524, no_x=565):
    """Add yes/no counts below the Yes and No checkboxes."""
    add_text(page, yes_x, line_y + 10, fmt_num(yes_count))
    add_text(page, no_x, line_y + 10, fmt_num(no_count))

def add_dollar_field(page, line_y, amount, x=510):
    """Add dollar amount next to a line number field."""
    add_text(page, x, line_y + 8, fmt_money(amount))

# ── load data ────────────────────────────────────────────────────────────────
json_path = sys.argv[1] if len(sys.argv) > 1 else "data/exports/t3010_2024_data.json"
output_path = sys.argv[2] if len(sys.argv) > 2 else "data/exports/Blumbergs-Snapshot-T3010-2024.pdf"
with open(json_path) as f:
    d = json.load(f)

# ── open PDF ─────────────────────────────────────────────────────────────────
doc = fitz.open("docs/reference/t3010-24e.pdf")

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 0 — Section A: Identification + B + C start
# ═══════════════════════════════════════════════════════════════════════════════
set_section("section_a")
p = doc[0]

# Title — from JSON or default
title = d.get('title', 'Blumbergs Snapshot 2024 — Canadian Charity Sector')
add_text(p, 177, 44, title, size=10)

# Charity name field: total charities
add_text(p, 55, 165, f"{fmt_num(d['total_charities'])} Registered Charities in the Database", size=12)

# Phone/Email/Website counts (right side of charity name area)
add_text(p, 430, 158, f"{fmt_num(d['charities_with_phone'])} Provided Phone Numbers", size=8)
add_text(p, 430, 169, f"{fmt_num(d['charities_with_email'])} Provided Emails", size=8)

# Web address field
add_text(p, 430, 202, f"{fmt_num(d['charities_with_website'])} Provided Websites", size=8)

# A1 (1510) - Subordinate — Yes at ~524, No at ~568, line y ≈ 223
add_text(p, 520, 239, fmt_num(d['A1_1510_subordinate']['yes']), size=6.5)
add_text(p, 558, 239, fmt_num(d['A1_1510_subordinate']['no']), size=6.5)

# A2 (1570) - Wound up — Yes/No labels at y≈286-294
add_text(p, 520, 302, fmt_num(d['A2_1570_wound_up']['yes']), size=6.5)
add_text(p, 558, 302, fmt_num(d['A2_1570_wound_up']['no']), size=6.5)

# A3 (1600) - Foundation — Yes/No labels at y≈305-313
# Yes count and designation breakdown
a3_yes = d['A3_1600_foundation']['yes']
a3_no = d['A3_1600_foundation']['no']
desig = d['designation_breakdown']
add_text(p, 520, 320, fmt_num(a3_yes), size=6.5)
add_text(p, 558, 320, fmt_num(a3_no), size=6.5)

# B1 - Directors info (in B section white space, after "available to the public.")
b1_total = d['B1_total_directors']
b1_arm = d['B1_arms_length_yes']
b1_nonarm = d['B1_arms_length_no']
b1_blank = d['B1_arms_length_blank']
add_text(p, 145, 377, f"{fmt_num(b1_total)} directors listed by all charities. Arm's length ({fmt_num(b1_arm)}) and non-arm's length ({fmt_num(b1_nonarm)}).", size=6.5)
add_text(p, 145, 386, f"{fmt_num(b1_blank)} did not list whether arm's length or not.", size=6.5)

# C1 (1800) - Active — line y ≈ 471
add_text(p, 520, 486, fmt_num(d['C1_1800_active']['yes']), size=6.5)
add_text(p, 558, 486, fmt_num(d['C1_1800_active']['no']), size=6.5)

# C2 - Ongoing programs count (in the "Ongoing programs" box)
add_text(p, 30, 625, fmt_num(d['C2_programs']['OP']), size=8)

# C2 - New programs count (in the "New programs" box)
add_text(p, 30, 680, fmt_num(d['C2_programs']['NP']), size=8)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — Section C continued (page 2 of form)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("section_c")
p = doc[1]

# C3 (2000) — Gifts to QDs — line y ≈ 77
add_text(p, 520, 92, fmt_num(d['C3_2000_gifts_to_QDs']['yes']), size=6.5)
add_text(p, 558, 92, fmt_num(d['C3_2000_gifts_to_QDs']['no']), size=6.5)

# C4 (2100) — Activities outside Canada — line y ≈ 127
add_text(p, 520, 143, fmt_num(d['C4_2100_activities_outside']['yes']), size=6.5)
add_text(p, 558, 143, fmt_num(d['C4_2100_activities_outside']['no']), size=6.5)

# C6 Fundraising methods — counts next to each checkbox
fm = d['C6_fundraising_methods']
# Left column (2500-2560)
add_text(p, 33, 234, fmt_num(fm.get('2500', 0)), size=6.5, align="right")   # Ads/print/radio
add_text(p, 33, 255, fmt_num(fm.get('2510', 0)), size=6.5, align="right")   # Auctions
add_text(p, 33, 273, fmt_num(fm.get('2530', 0)), size=6.5, align="right")   # Collection plate
add_text(p, 33, 290, fmt_num(fm.get('2540', 0)), size=6.5, align="right")   # Door-to-door
add_text(p, 33, 308, fmt_num(fm.get('2550', 0)), size=6.5, align="right")   # Draws/lotteries
add_text(p, 33, 329, fmt_num(fm.get('2560', 0)), size=6.5, align="right")   # Dinners/galas

# Middle column (2570-2610)
add_text(p, 225, 235, fmt_num(fm.get('2570', 0)), size=6.5, align="right")  # Sales
add_text(p, 225, 256, fmt_num(fm.get('2575', 0)), size=6.5, align="right")  # Internet
add_text(p, 225, 274, fmt_num(fm.get('2580', 0)), size=6.5, align="right")  # Mail campaigns
add_text(p, 225, 291, fmt_num(fm.get('2590', 0)), size=6.5, align="right")  # Planned-giving
add_text(p, 225, 308, fmt_num(fm.get('2600', 0)), size=6.5, align="right")  # Corporate/sponsorships
add_text(p, 225, 329, fmt_num(fm.get('2610', 0)), size=6.5, align="right")  # Targeted contacts

# Right column (2620-2650)
add_text(p, 413, 236, fmt_num(fm.get('2620', 0)), size=6.5, align="right")  # Telephone/TV
add_text(p, 413, 257, fmt_num(fm.get('2630', 0)), size=6.5, align="right")  # Tournament/sporting
add_text(p, 413, 275, fmt_num(fm.get('2640', 0)), size=6.5, align="right")  # Cause-related
add_text(p, 413, 292, fmt_num(fm.get('2650', 0)), size=6.5, align="right")  # Other

# C7 (2700) — External fundraisers
add_text(p, 520, 371, fmt_num(d['C7_2700_external_fundraisers']['yes']), size=6.5)
add_text(p, 558, 371, fmt_num(d['C7_2700_external_fundraisers']['no']), size=6.5)

# 5450 — Gross revenue from fundraisers
add_text(p, 505, 390, fmt_money(d['line_5450_sum']), size=7.5)

# 5460 — Amounts paid to fundraisers
add_text(p, 505, 403, fmt_money(d['line_5460_sum']), size=7.5)

# Fundraiser payment methods (2730-2780)
fpm = d['fundraiser_payment_methods']
add_text(p, 33, 436, fmt_num(fpm.get('2730', 0)), size=6.5, align="right")   # Commissions
add_text(p, 33, 452, fmt_num(fpm.get('2740', 0)), size=6.5, align="right")   # Bonuses
add_text(p, 225, 436, fmt_num(fpm.get('2750', 0)), size=6.5, align="right")  # Finder's fee
add_text(p, 225, 452, fmt_num(fpm.get('2760', 0)), size=6.5, align="right")  # Set fee for services
add_text(p, 435, 436, fmt_num(fpm.get('2770', 0)), size=6.5, align="right")  # Honoraria
add_text(p, 435, 452, fmt_num(fpm.get('2780', 0)), size=6.5, align="right")  # Other

# 2800 — Fundraiser tax receipts
add_text(p, 520, 495, fmt_num(d['C8_2800_fundraiser_receipts']['yes']), size=6.5)
add_text(p, 558, 495, fmt_num(d['C8_2800_fundraiser_receipts']['no']), size=6.5)

# C8 (3200) — Compensate directors
add_text(p, 520, 522, fmt_num(d['C8_3200_compensate_directors']['yes']), size=6.5)
add_text(p, 558, 522, fmt_num(d['C8_3200_compensate_directors']['no']), size=6.5)

# C9 (3400) — Employment expenses
add_text(p, 520, 540, fmt_num(d['C9_3400_employment_expenses']['yes']), size=6.5)
add_text(p, 558, 540, fmt_num(d['C9_3400_employment_expenses']['no']), size=6.5)

# C10 (3900) — Foreign donations $10K+
add_text(p, 520, 576, fmt_num(d['C10_3900_foreign_donations']['yes']), size=6.5)
add_text(p, 558, 576, fmt_num(d['C10_3900_foreign_donations']['no']), size=6.5)

# C11 (4000) — Non-cash gifts
add_text(p, 520, 659, fmt_num(d['C11_4000_noncash_gifts']['yes']), size=6.5)
add_text(p, 558, 659, fmt_num(d['C11_4000_noncash_gifts']['no']), size=6.5)

# C12 (5800) — Non-qualifying security
add_text(p, 520, 685, fmt_num(d['C12_5800']['yes']), size=6.5)
add_text(p, 558, 685, fmt_num(d['C12_5800']['no']), size=6.5)

# C13 (5810) — Donor property use
add_text(p, 520, 702, fmt_num(d['C13_5810']['yes']), size=6.5)
add_text(p, 558, 702, fmt_num(d['C13_5810']['no']), size=6.5)

# C14 (5820) — Tax receipts for another org
add_text(p, 520, 720, fmt_num(d['C14_5820']['yes']), size=6.5)
add_text(p, 558, 720, fmt_num(d['C14_5820']['no']), size=6.5)

# C15 (5830) — Partnership holdings
add_text(p, 520, 740, fmt_num(d['C15_5830']['yes']), size=6.5)
add_text(p, 558, 740, fmt_num(d['C15_5830']['no']), size=6.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — C16-C18 (page 3 of form)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("section_c2")
p = doc[2]

# C16 (5840) — Grants to NQDs
add_text(p, 520, 83, fmt_num(d['C16_5840']['yes']), size=6.5)
add_text(p, 558, 83, fmt_num(d['C16_5840']['no']), size=6.5)

# 5841 — Grants > $5,000
add_text(p, 520, 112, fmt_num(d['line_5841']['yes']), size=6.5)
add_text(p, 558, 112, fmt_num(d['line_5841']['no']), size=6.5)

# 5842 — Number of grantees
add_text(p, 504, 131, fmt_num(d['line_5842_sum']), size=8)

# 5843 — Total amount to grantees
add_text(p, 504, 149, fmt_money(d['line_5843_sum']), size=8)

# C17 (5850) — Disbursement quota
add_text(p, 520, 212, fmt_num(d['C17_5850']['yes']), size=6.5)
add_text(p, 558, 212, fmt_num(d['C17_5850']['no']), size=6.5)

# C18 (5860) — DAF
add_text(p, 520, 252, fmt_num(d['C18_5860']['yes']), size=6.5)
add_text(p, 558, 252, fmt_num(d['C18_5860']['no']), size=6.5)

# 5861 — Total DAF accounts
add_text(p, 504, 269, fmt_num(d['line_5861_sum']), size=8)

# 5862 — Total value of DAF accounts
add_text(p, 504, 287, fmt_money(d['line_5862_sum']), size=8)

# 5863 — Total DAF donations received
add_text(p, 504, 305, fmt_money(d['line_5863_sum']), size=8)

# 5864 — Total DAF disbursements
add_text(p, 504, 323, fmt_money(d['line_5864_sum']), size=8)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — Section D: Financial Information (page 4 of form)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("section_d")
p = doc[3]

# D1 (4020) — Accrual vs Cash
acct = d['D_4020_accounting_method']
add_text(p, 520, 164, fmt_num(acct.get('A', 0)), size=6.5)  # Accrual
add_text(p, 567, 164, fmt_num(acct.get('C', 0)), size=6.5)  # Cash

# D2 — Summary of financial position
# 4050 — Own land/buildings
add_text(p, 520, 189, fmt_num(d['D_4050']['yes']), size=6.5)
add_text(p, 558, 189, fmt_num(d['D_4050']['no']), size=6.5)

# 4200 — Total assets
dd = d['D_dollar_sums']
add_text(p, 505, 219, fmt_money(dd['4200']), size=7.5)

# 4350 — Total liabilities
add_text(p, 505, 236, fmt_money(dd['4350']), size=7.5)

# 4400 — Borrow/loan
add_text(p, 520, 260, fmt_num(d['D_4400']['yes']), size=6.5)
add_text(p, 558, 260, fmt_num(d['D_4400']['no']), size=6.5)

# D3 — Revenue
# 4490 — Issue tax receipts
add_text(p, 520, 294, fmt_num(d['D_4490']['yes']), size=6.5)
add_text(p, 558, 294, fmt_num(d['D_4490']['no']), size=6.5)

# 4500 — Tax-receipted gifts
add_text(p, 505, 302, fmt_money(dd['4500']), size=7.5)

# 4510 — Gifts from other charities
add_text(p, 505, 320, fmt_money(dd['4510']), size=7.5)

# 4530 — Other gifts (no receipt)
add_text(p, 505, 342, fmt_money(dd['4530']), size=7.5)

# 4565 — Government revenue Y/N
add_text(p, 520, 366, fmt_num(d['D_4565']['yes']), size=6.5)
add_text(p, 558, 366, fmt_num(d['D_4565']['no']), size=6.5)

# 4570 — Total government revenue
add_text(p, 505, 374, fmt_money(dd['4570']), size=7.5)

# 4571 — Tax-receipted from outside Canada
add_text(p, 385, 396, fmt_money(dd['4571']), size=7.5)

# 4575 — Non tax-receipted from outside Canada
add_text(p, 505, 410, fmt_money(dd['4575']), size=7.5)

# 4630 — Non tax-receipted from fundraising
add_text(p, 505, 423, fmt_money(dd['4630']), size=7.5)

# 4640 — Sale of goods/services
add_text(p, 505, 435, fmt_money(dd['4640']), size=7.5)

# 4650 — Other revenue
add_text(p, 505, 448, fmt_money(dd['4650']), size=7.5)

# 4700 — Total revenue
add_text(p, 505, 460, fmt_money(dd['4700']), size=7.5)

# D4 — Expenditures
# 4860 — Professional/consulting
add_text(p, 505, 489, fmt_money(dd['4860']), size=7.5)

# 4810 — Travel and vehicle
add_text(p, 505, 501, fmt_money(dd['4810']), size=7.5)

# 4920 — Other expenditures
add_text(p, 505, 513, fmt_money(dd['4920']), size=7.5)

# 4950 — Total expenditures excl. qualifying disbursements
add_text(p, 505, 526, fmt_money(dd['4950']), size=7.5)

# 5000 — Charitable activities
add_text(p, 385, 556, fmt_money(dd['5000']), size=7.5)

# 5010 — Management and admin
add_text(p, 385, 569, fmt_money(dd['5010']), size=7.5)

# 5045 — Grants to NQDs
add_text(p, 505, 585, fmt_money(dd['5045']), size=7.5)

# 5050 — Gifts to QDs
add_text(p, 505, 598, fmt_money(dd['5050']), size=7.5)

# 5100 — Total expenditures
add_text(p, 505, 611, fmt_money(dd['5100']), size=7.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — Schedule 1 (Foundations) + Schedule 2 (Activities outside Canada)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("schedule_1_2")
p = doc[5]

# Schedule 1: Foundations
# 100 — Acquire control of corporation
add_text(p, 520, 75, fmt_num(d['S1_100']['yes']), size=6.5)
add_text(p, 558, 75, fmt_num(d['S1_100']['no']), size=6.5)

# 110 — Incur debts
add_text(p, 520, 101, fmt_num(d['S1_110']['yes']), size=6.5)
add_text(p, 558, 101, fmt_num(d['S1_110']['no']), size=6.5)

# 111 — Restricted funds total
add_text(p, 500, 116, fmt_money(d['S1_111_sum']), size=7.5)

# 112 — Funder's written trust amount
add_text(p, 500, 132, fmt_money(d['S1_112_sum']), size=7.5)

# 120 — Non-qualified investment (private foundations)
add_text(p, 520, 187, fmt_num(d['S1_120']['yes']), size=6.5)
add_text(p, 558, 187, fmt_num(d['S1_120']['no']), size=6.5)

# 130 — Own >2% of corp shares
add_text(p, 520, 204, fmt_num(d['S1_130']['yes']), size=6.5)
add_text(p, 558, 204, fmt_num(d['S1_130']['no']), size=6.5)

# Schedule 2: Activities outside Canada
# 200 — Total foreign expenditures
add_text(p, 500, 301, fmt_money(d['S2_200_sum']), size=7.5)

# 210 — Intermediaries
add_text(p, 520, 345, fmt_num(d['S2_210']['yes']), size=6.5)
add_text(p, 558, 345, fmt_num(d['S2_210']['no']), size=6.5)

# 220 — Global Affairs funded
add_text(p, 520, 580, fmt_num(d['S2_220']['yes']), size=6.5)
add_text(p, 558, 580, fmt_num(d['S2_220']['no']), size=6.5)

# 230 — Amount from Global Affairs
add_text(p, 500, 589, fmt_money(d['S2_230_sum']), size=7.5)

# 240 — Employees outside Canada
add_text(p, 520, 614, fmt_num(d['S2_240']['yes']), size=6.5)
add_text(p, 558, 614, fmt_num(d['S2_240']['no']), size=6.5)

# 250 — Volunteers outside Canada
add_text(p, 520, 631, fmt_num(d['S2_250']['yes']), size=6.5)
add_text(p, 558, 631, fmt_num(d['S2_250']['no']), size=6.5)

# 260 — Export goods
add_text(p, 520, 648, fmt_num(d['S2_260']['yes']), size=6.5)
add_text(p, 558, 648, fmt_num(d['S2_260']['no']), size=6.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 7 — Schedule 3 (Compensation) + Schedule 5 (Non-cash gifts)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("schedule_3_5")
p = doc[7]

# Schedule 3: Compensation
s3 = d['S3_employee_counts']

# 300 — FT employees
add_text(p, 500, 87, fmt_num(s3['300']), size=7)

# Salary bands (305-345)
add_text(p, 45, 133, fmt_num(s3['305']), size=6.5, align="right")   # $1-$39,999
add_text(p, 210, 133, fmt_num(s3['310']), size=6.5, align="right")  # $40K-$79,999
add_text(p, 380, 133, fmt_num(s3['315']), size=6.5, align="right")  # $80K-$119,999
add_text(p, 45, 150, fmt_num(s3['320']), size=6.5, align="right")   # $120K-$159,999
add_text(p, 210, 150, fmt_num(s3['325']), size=6.5, align="right")  # $160K-$199,999
add_text(p, 380, 150, fmt_num(s3['330']), size=6.5, align="right")  # $200K-$249,999
add_text(p, 45, 168, fmt_num(s3['335']), size=6.5, align="right")   # $250K-$299,999
add_text(p, 210, 168, fmt_num(s3['340']), size=6.5, align="right")  # $300K-$349,999
add_text(p, 380, 168, fmt_num(s3['345']), size=6.5, align="right")  # $350K+

# 370 — PT employees
add_text(p, 500, 192, fmt_num(s3['370']), size=7)

# 380 — PT compensation
add_text(p, 500, 209, fmt_money(d['S3_380_sum']), size=7.5)

# 390 — Total compensation
add_text(p, 500, 226, fmt_money(d['S3_390_sum']), size=7.5)

# Schedule 5: Non-cash gifts
s5 = d['S5_gift_types']

# Left column (500-520)
add_text(p, 33, 655, fmt_num(s5.get('500', 0)), size=6.5, align="right")  # Artwork/wine/jewellery
add_text(p, 33, 677, fmt_num(s5.get('505', 0)), size=6.5, align="right")  # Building materials
add_text(p, 33, 694, fmt_num(s5.get('510', 0)), size=6.5, align="right")  # Clothing/furniture/food
add_text(p, 33, 711, fmt_num(s5.get('515', 0)), size=6.5, align="right")  # Vehicles
add_text(p, 33, 729, fmt_num(s5.get('520', 0)), size=6.5, align="right")  # Cultural properties

# Middle column (525-545)
add_text(p, 211, 656, fmt_num(s5.get('525', 0)), size=6.5, align="right")  # Ecological properties
add_text(p, 211, 678, fmt_num(s5.get('530', 0)), size=6.5, align="right")  # Life insurance
add_text(p, 211, 695, fmt_num(s5.get('535', 0)), size=6.5, align="right")  # Medical equipment
add_text(p, 211, 712, fmt_num(s5.get('540', 0)), size=6.5, align="right")  # Privately-held securities
add_text(p, 211, 730, fmt_num(s5.get('545', 0)), size=6.5, align="right")  # Machinery/computers

# Right column (550-560)
add_text(p, 399, 657, fmt_num(s5.get('550', 0)), size=6.5, align="right")  # Publicly traded
add_text(p, 399, 679, fmt_num(s5.get('555', 0)), size=6.5, align="right")  # Books
add_text(p, 399, 696, fmt_num(s5.get('560', 0)), size=6.5, align="right")  # Other

# 580 — Total non-cash gifts
add_text(p, 500, 750, fmt_money(d['S5_580_sum']), size=8)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 8 — Schedule 6 (Detailed financial) — Assets, Liabilities, Revenue
# ═══════════════════════════════════════════════════════════════════════════════
set_section("schedule_6a")
p = doc[8]

# Accrual/Cash (same data as page 3)
add_text(p, 513, 125, fmt_num(acct.get('A', 0)), size=6.5)
add_text(p, 564, 125, fmt_num(acct.get('C', 0)), size=6.5)

s6a = d['S6_assets']
s6l = d['S6_liabilities']
s6r = d['S6_revenue']

# Assets
add_text(p, 240, 177, fmt_money(s6a['4100']), size=7.5)  # Cash/ST investments
add_text(p, 144, 197, fmt_money(s6a['4101']), size=7)     # Cash and bank
add_text(p, 144, 217, fmt_money(s6a['4102']), size=7)     # Short-term investments
add_text(p, 240, 231, fmt_money(s6a['4110']), size=7.5)   # AR non-arm's length
add_text(p, 240, 244, fmt_money(s6a['4120']), size=7.5)   # AR others
add_text(p, 240, 257, fmt_money(s6a['4130']), size=7.5)   # Investments non-arm's
add_text(p, 240, 269, fmt_money(s6a['4140']), size=7.5)   # Long-term investments
add_text(p, 240, 282, fmt_money(s6a['4150']), size=7.5)   # Inventories
add_text(p, 240, 295, fmt_money(s6a['4155']), size=7.5)   # Land and buildings
add_text(p, 144, 325, fmt_money(s6a['4157']), size=7)     # Used for charitable
add_text(p, 144, 348, fmt_money(s6a['4158']), size=7)     # Used for other
add_text(p, 240, 362, fmt_money(s6a['4160']), size=7.5)   # Other capital assets
add_text(p, 240, 375, fmt_money(s6a['4165']), size=7.5)   # Capital outside Canada
add_text(p, 240, 387, fmt_money(s6a['4166']), size=7.5)   # Accumulated amortization
add_text(p, 240, 400, fmt_money(s6a['4170']), size=7.5)   # Other assets
add_text(p, 144, 414, fmt_money(s6a['4190']), size=7)     # Impact investments
# 4200 — Total assets
add_text(p, 245, 434, fmt_money(d['D_dollar_sums']['4200']), size=8)

# Liabilities
add_text(p, 515, 177, fmt_money(s6l['4300']), size=7.5)   # AP and accrued
add_text(p, 515, 190, fmt_money(s6l['4310']), size=7.5)   # Deferred revenue
add_text(p, 515, 203, fmt_money(s6l['4320']), size=7.5)   # Amounts owing non-arm's
add_text(p, 515, 216, fmt_money(s6l['4330']), size=7.5)   # Other liabilities
add_text(p, 515, 229, fmt_money(d['D_dollar_sums']['4350']), size=8)  # Total liabilities

# 4250 — Amount not used in charitable activities
add_text(p, 515, 311, fmt_money(d.get('line_4250', 0)), size=7.5)

# Revenue lines
add_text(p, 515, 479, fmt_money(s6r['4500']), size=7.5)   # Tax-receipted gifts
add_text(p, 406, 492, fmt_money(s6r['5610']), size=7)     # Tuition
add_text(p, 515, 507, fmt_money(s6r['4510']), size=7.5)   # From other charities
add_text(p, 515, 520, fmt_money(s6r['4530']), size=7.5)   # Other gifts no receipt
add_text(p, 515, 533, fmt_money(s6r['4540']), size=7.5)   # Federal government
add_text(p, 515, 546, fmt_money(s6r['4550']), size=7.5)   # Provincial
add_text(p, 515, 559, fmt_money(s6r['4560']), size=7.5)   # Municipal
add_text(p, 406, 579, fmt_money(s6r['4571']), size=7)     # Tax-receipted from outside
add_text(p, 515, 592, fmt_money(s6r['4575']), size=7.5)   # Non tax-receipted outside
add_text(p, 406, 606, fmt_money(s6r['4576']), size=7)     # Impact investment income
add_text(p, 406, 620, fmt_money(s6r['4577']), size=7)     # Interest non-arm's
add_text(p, 515, 631, fmt_money(s6r['4580']), size=7.5)   # Total interest/investment
add_text(p, 406, 648, fmt_money(s6r['4590']), size=7)     # Gross proceeds
add_text(p, 515, 660, fmt_money(s6r['4600']), size=7.5)   # Net proceeds
add_text(p, 515, 673, fmt_money(s6r['4610']), size=7.5)   # Rental income
add_text(p, 515, 686, fmt_money(s6r['4620']), size=7.5)   # Memberships
add_text(p, 515, 699, fmt_money(s6r['4630']), size=7.5)   # Non tax-receipted fundraising
add_text(p, 515, 712, fmt_money(s6r['4640']), size=7.5)   # Sale of goods
add_text(p, 515, 725, fmt_money(s6r['4650']), size=7.5)   # Other revenue
add_text(p, 515, 751, fmt_money(d['D_dollar_sums']['4700']), size=8)  # Total revenue


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 9 — Schedule 6 continued — Expenditures + Other financial
# ═══════════════════════════════════════════════════════════════════════════════
set_section("schedule_6b")
p = doc[9]

s6e = d['S6_expenditures']
s6o = d['S6_other']

# Expenditures
add_text(p, 515, 58, fmt_money(s6e['4800']), size=7.5)    # Advertising
add_text(p, 515, 71, fmt_money(s6e['4810']), size=7.5)    # Travel
add_text(p, 515, 84, fmt_money(s6e['4820']), size=7.5)    # Interest/bank
add_text(p, 515, 97, fmt_money(s6e['4830']), size=7.5)    # Licences/memberships
add_text(p, 515, 110, fmt_money(s6e['4840']), size=7.5)   # Office supplies
add_text(p, 515, 123, fmt_money(s6e['4850']), size=7.5)   # Occupancy
add_text(p, 515, 136, fmt_money(s6e['4860']), size=7.5)   # Professional/consulting
add_text(p, 515, 149, fmt_money(s6e['4870']), size=7.5)   # Education/training
add_text(p, 515, 162, fmt_money(s6e['4880']), size=7.5)   # Total compensation
add_text(p, 515, 175, fmt_money(s6e['4890']), size=7.5)   # Fair market donated goods
add_text(p, 515, 188, fmt_money(s6e['4891']), size=7.5)   # Purchased supplies
add_text(p, 515, 201, fmt_money(s6e['4900']), size=7.5)   # Amortization
add_text(p, 515, 214, fmt_money(s6e['4910']), size=7.5)   # Research grants
add_text(p, 515, 227, fmt_money(s6e['4920']), size=7.5)   # Other expenditures

# 4930 — N/A (specify type)
add_text(p, 298, 246, "N/A", size=6.5)

# 4950 — Total expenditures before qualifying disbursements
add_text(p, 515, 263, fmt_money(d['D_dollar_sums']['4950']), size=8)

# Of amounts at 4950:
add_text(p, 406, 296, fmt_money(s6e['5000']), size=7)   # Charitable activities
add_text(p, 406, 309, fmt_money(s6e['5010']), size=7)   # Management/admin
add_text(p, 406, 322, fmt_money(s6e['5020']), size=7)   # Fundraising
add_text(p, 406, 335, fmt_money(s6e['5040']), size=7)   # Other in 4950

# 5045 — Grants to NQDs
add_text(p, 515, 358, fmt_money(s6e['5045']), size=7.5)

# 5050 — Gifts to QDs
add_text(p, 515, 371, fmt_money(s6e['5050']), size=7.5)

# 5100 — Total expenditures
add_text(p, 515, 384, fmt_money(d['D_dollar_sums']['5100']), size=8)

# Other financial information
# 5500 — Amount accumulated
add_text(p, 515, 456, fmt_money(s6o['5500']), size=7.5)

# 5510 — Amount disbursed
add_text(p, 515, 468, fmt_money(s6o['5510']), size=7.5)

# 5750 — DQ reduction
add_text(p, 515, 507, fmt_money(s6o['5750']), size=7.5)

# 5900 — Property not used (beginning)
add_text(p, 515, 557, fmt_money(s6o['5900']), size=7.5)

# 5910 — Property not used (end)
add_text(p, 515, 569, fmt_money(s6o['5910']), size=7.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 10 — Schedule 8 (Disbursement Quota)
# ═══════════════════════════════════════════════════════════════════════════════
set_section("schedule_8")
p = doc[10]

s8 = d['S8_disbursement']

# Step 1
add_text(p, 503, 115, fmt_money(s8['805']), size=7.5)   # 805
add_text(p, 503, 146, fmt_money(s8['810']), size=7.5)   # 810
add_text(p, 503, 167, fmt_money(s8['815']), size=7.5)   # 815

# If 815 <= $1M
add_text(p, 225, 233, fmt_money(s8['820']), size=7.5)   # 820

# If 815 > $1M
add_text(p, 503, 207, fmt_money(s8['825']), size=7.5)   # 825
add_text(p, 503, 220, fmt_money(s8['830']), size=7.5)   # 830
add_text(p, 503, 233, fmt_money(s8['835']), size=7.5)   # 835

# 840 — DQ requirement
add_text(p, 503, 263, fmt_money(s8['840']), size=7.5)

# 845-855 — Expenditures/grants/gifts
add_text(p, 503, 282, fmt_money(s8['845']), size=7.5)
add_text(p, 503, 295, fmt_money(s8['850']), size=7.5)
add_text(p, 503, 307, fmt_money(s8['855']), size=7.5)

# 860 — Add lines
add_text(p, 503, 323, fmt_money(s8['860']), size=7.5)

# 865 — DQ excess/shortfall
add_text(p, 503, 337, fmt_money(s8['865']), size=7.5)

# Step 2
# 870 — Average value of property
add_text(p, 503, 426, fmt_money(s8['870']), size=7.5)

# If 870 <= $1M
add_text(p, 225, 495, fmt_money(s8['875']), size=7.5)   # 875

# If 870 > $1M
add_text(p, 503, 467, fmt_money(s8['880']), size=7.5)   # 880
add_text(p, 503, 480, fmt_money(s8['885']), size=7.5)   # 885
add_text(p, 503, 493, fmt_money(s8['890']), size=7.5)   # 890


# ═══════════════════════════════════════════════════════════════════════════════
#  SAVE
# ═══════════════════════════════════════════════════════════════════════════════
doc.save(output_path)
doc.close()
print(f"Annotated T3010 saved to: {output_path}")
