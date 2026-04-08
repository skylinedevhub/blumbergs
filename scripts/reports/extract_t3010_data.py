#!/usr/bin/env python3
"""
Extract annotation data from snapshot Excel workbooks into JSON files
matching the format expected by annotate_t3010_2024.py.
"""

import json
import os
import sys
import openpyxl


def extract_data(workbook_path):
    """Read Summary sheet from a snapshot workbook and return data dict."""
    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    ws = wb['Summary']

    # Build lookup: line_number (str from col A) -> {A, B, C, D, E values}
    rows = {}
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=5):
        a, b, c, d_val, e = [cell.value for cell in row]
        row_num = row[0].row
        rows[row_num] = {'A': a, 'B': b, 'C': c, 'D': d_val, 'E': e}

    # Also build by line number (col A value) for quick lookup
    by_line = {}
    for r, vals in rows.items():
        if vals['A'] is not None:
            by_line[str(vals['A'])] = vals

    def val(line):
        """Get C value for a line number."""
        return by_line.get(str(line), {}).get('C', 0) or 0

    def yes_no(line):
        """Get {yes, no} for a line number."""
        entry = by_line.get(str(line), {})
        return {'yes': entry.get('C', 0) or 0, 'no': entry.get('D', 0) or 0}

    # Parse 4050 which has "Yes: 5,508  No: 18,913" format in C column
    def parse_yes_no_text(line):
        entry = by_line.get(str(line), {})
        text = str(entry.get('C', ''))
        if 'Yes:' in text and 'No:' in text:
            parts = text.split('No:')
            yes_part = parts[0].replace('Yes:', '').strip().replace(',', '')
            no_part = parts[1].strip().replace(',', '')
            return {'yes': int(yes_part), 'no': int(no_part)}
        return {'yes': 0, 'no': 0}

    # Title from row 1
    title = rows.get(1, {}).get('A', 'Blumbergs Snapshot 2024')

    d = {}

    # Section A
    d['title'] = title
    d['total_charities'] = val(None)  # placeholder, get from row 7
    # Row 7 has total charities in C
    for r, v in rows.items():
        if v['B'] and 'Total registered charities' in str(v['B']):
            d['total_charities'] = v['C'] or 0
            break

    # Designation breakdown from rows 8-10
    d['designation_breakdown'] = {}
    for r, v in rows.items():
        b = str(v['B'] or '')
        if 'A: Public Foundation' in b:
            d['designation_breakdown']['A'] = v['C'] or 0
        elif 'B: Private Foundation' in b:
            d['designation_breakdown']['B'] = v['C'] or 0
        elif 'C: Charitable Organization' in b:
            d['designation_breakdown']['C'] = v['C'] or 0

    # Phone/email/website — match exact metric labels from rows 11-13
    for r, v in rows.items():
        b = str(v['B'] or '')
        if b == 'Provided phone numbers':
            d['charities_with_phone'] = v['C'] or 0
        elif b == 'Provided email addresses':
            d['charities_with_email'] = v['C'] or 0
        elif b == 'Provided websites':
            d['charities_with_website'] = v['C'] or 0

    # Yes/No questions
    d['A1_1510_subordinate'] = yes_no('1510')
    d['A2_1570_wound_up'] = yes_no('1570')
    d['A3_1600_foundation'] = yes_no('1600')

    # B1 - Directors (find rows with "directors listed")
    d['B1_total_directors'] = 0
    d['B1_arms_length_yes'] = 0
    d['B1_arms_length_no'] = 0
    d['B1_arms_length_blank'] = 0
    # These aren't in the Summary sheet typically - check if they exist
    for r, v in rows.items():
        b = str(v['B'] or '')
        if 'Total directors' in b:
            d['B1_total_directors'] = v['C'] or 0
        elif "Arm's length: Yes" in b or "arms_length_yes" in b.lower():
            d['B1_arms_length_yes'] = v['C'] or 0
        elif "Arm's length: No" in b or "arms_length_no" in b.lower():
            d['B1_arms_length_no'] = v['C'] or 0
        elif 'did not list' in b.lower() or "arms_length_blank" in b.lower():
            d['B1_arms_length_blank'] = v['C'] or 0

    # Section C
    d['C1_1800_active'] = yes_no('1800')

    # Programs
    d['C2_programs'] = {'OP': 0, 'NP': 0}
    for r, v in rows.items():
        b = str(v['B'] or '')
        if 'Ongoing programs' in b:
            d['C2_programs']['OP'] = v['C'] or 0
        elif 'New programs' in b:
            d['C2_programs']['NP'] = v['C'] or 0

    d['C3_2000_gifts_to_QDs'] = yes_no('2000')
    d['C4_2100_activities_outside'] = yes_no('2100')

    # C6 fundraising methods
    fm_lines = ['2500', '2510', '2530', '2540', '2550', '2560',
                '2570', '2575', '2580', '2590', '2600', '2610',
                '2620', '2630', '2640', '2650']
    d['C6_fundraising_methods'] = {l: val(l) for l in fm_lines}

    # C7
    d['C7_2700_external_fundraisers'] = yes_no('2700')
    d['line_5450_sum'] = val('5450')
    d['line_5460_sum'] = val('5460')

    # Fundraiser payment methods
    fpm_lines = ['2730', '2740', '2750', '2760', '2770', '2780']
    d['fundraiser_payment_methods'] = {l: val(l) for l in fpm_lines}

    # C8-C15
    # C8 has two questions: 2800 (fundraiser receipts) and 3200 (compensate directors)
    # 2800 may not be in summary - check
    d['C8_2800_fundraiser_receipts'] = yes_no('2800')
    d['C8_3200_compensate_directors'] = yes_no('3200')
    d['C9_3400_employment_expenses'] = yes_no('3400')
    d['C10_3900_foreign_donations'] = yes_no('3900')
    d['C11_4000_noncash_gifts'] = yes_no('4000')
    d['C12_5800'] = yes_no('5800')
    d['C13_5810'] = yes_no('5810')
    d['C14_5820'] = yes_no('5820')
    d['C15_5830'] = yes_no('5830')

    # C16-C18
    d['C16_5840'] = yes_no('5840')
    d['line_5841'] = yes_no('5841')
    d['line_5842_sum'] = val('5842')
    d['line_5843_sum'] = val('5843')
    d['C17_5850'] = yes_no('5850')
    d['C18_5860'] = yes_no('5860')
    d['line_5861_sum'] = val('5861')
    d['line_5862_sum'] = val('5862')
    d['line_5863_sum'] = val('5863')
    d['line_5864_sum'] = val('5864')

    # Section D
    d['D_4020_accounting_method'] = {'A': 0, 'C': 0}
    for r, v in rows.items():
        b = str(v['B'] or '')
        if 'Accrual basis' in b or 'D1: Accrual' in b:
            d['D_4020_accounting_method']['A'] = v['C'] or 0
        elif 'Cash basis' in b:
            d['D_4020_accounting_method']['C'] = v['C'] or 0

    d['D_4050'] = parse_yes_no_text('4050')
    d['D_4400'] = parse_yes_no_text('4400')
    d['D_4490'] = parse_yes_no_text('4490')
    d['D_4565'] = parse_yes_no_text('4565')

    # Dollar sums from Section D
    dollar_lines = ['4200', '4350', '4500', '4510', '4530', '4540', '4550', '4560',
                    '4571', '4575', '4630', '4640', '4650', '4700',
                    '4860', '4810', '4920', '4950', '5000', '5010', '5045', '5050', '5100']
    d['D_dollar_sums'] = {}
    for l in dollar_lines:
        d['D_dollar_sums'][l] = val(l)
    # 4570 — total government. May be stored as '4570*' in summary
    d['D_dollar_sums']['4570'] = val('4570') or val('4570*')

    # Schedule 1
    d['S1_100'] = yes_no('100')
    d['S1_110'] = yes_no('110')
    d['S1_111_sum'] = val('111')
    d['S1_112_sum'] = val('112')
    d['S1_120'] = yes_no('120')
    d['S1_130'] = yes_no('130')

    # Schedule 2
    d['S2_200_sum'] = val('200')
    d['S2_210'] = yes_no('210')
    d['S2_220'] = yes_no('220')
    d['S2_230_sum'] = val('230')
    d['S2_240'] = yes_no('240')
    d['S2_250'] = yes_no('250')
    d['S2_260'] = yes_no('260')

    # Schedule 3
    s3_lines = ['300', '305', '310', '315', '320', '325', '330', '335', '340', '345', '370']
    d['S3_employee_counts'] = {l: val(l) for l in s3_lines}
    d['S3_380_sum'] = val('380')
    d['S3_390_sum'] = val('390')

    # Schedule 5
    s5_lines = ['500', '505', '510', '515', '520', '525', '530', '535', '540', '545', '550', '555', '560']
    d['S5_gift_types'] = {l: val(l) for l in s5_lines}
    d['S5_580_sum'] = val('580')

    # Schedule 6 - Assets
    asset_lines = ['4100', '4101', '4102', '4110', '4120', '4130', '4140',
                   '4150', '4155', '4157', '4158', '4160', '4165', '4166', '4170', '4190']
    d['S6_assets'] = {l: val(l) for l in asset_lines}

    # Schedule 6 - Liabilities
    liab_lines = ['4300', '4310', '4320', '4330']
    d['S6_liabilities'] = {l: val(l) for l in liab_lines}

    # Schedule 6 - Revenue
    rev_lines = ['4500', '5610', '4510', '4530', '4540', '4550', '4560',
                 '4571', '4575', '4576', '4577', '4580', '4590', '4600',
                 '4610', '4620', '4630', '4640', '4650']
    d['S6_revenue'] = {l: val(l) for l in rev_lines}

    # Schedule 6 - Expenditures
    exp_lines = ['4800', '4810', '4820', '4830', '4840', '4850', '4860', '4870',
                 '4880', '4890', '4891', '4900', '4910', '4920',
                 '5000', '5010', '5020', '5040', '5045', '5050']
    d['S6_expenditures'] = {l: val(l) for l in exp_lines}

    # Schedule 6 - Other
    other_lines = ['5500', '5510', '5750', '5900', '5910']
    d['S6_other'] = {l: val(l) for l in other_lines}

    # 4250 — property not used in charitable activities
    d['line_4250'] = val('4250')

    # Schedule 8
    s8_lines = ['805', '810', '815', '820', '825', '830', '835', '840',
                '845', '850', '855', '860', '865', '870', '875', '880', '885', '890']
    d['S8_disbursement'] = {l: val(l) for l in s8_lines}

    wb.close()
    return d


def main():
    workbook_dir = "data/exports/snapshots_2024"
    output_dir = "data/exports/t3010_data"
    os.makedirs(output_dir, exist_ok=True)

    workbooks = sorted(f for f in os.listdir(workbook_dir) if f.endswith('.xlsx'))

    for wb_file in workbooks:
        wb_path = os.path.join(workbook_dir, wb_file)
        # snapshot_2024_canada.xlsx -> t3010_2024_canada.json
        scope = wb_file.replace('snapshot_2024_', '').replace('.xlsx', '')
        json_path = os.path.join(output_dir, f"t3010_2024_{scope}.json")

        print(f"Extracting {wb_file} -> {json_path}")
        data = extract_data(wb_path)
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

    print(f"\nExtracted {len(workbooks)} workbooks to {output_dir}/")


if __name__ == '__main__':
    main()
