# npo_excel.py
import xlsxwriter
import pandas as pd
from datetime import datetime
from npo_config import *
from npo_compliance import ComplianceCalculator

class ExcelGenerator:
    def __init__(self, org_data, tb_data, ppe_data, fund_data, policies_text, theme, include_gujarat=True, include_ica=True):
        self.org = org_data
        self.tb = pd.DataFrame(tb_data)
        self.ppe = pd.DataFrame(ppe_data)
        self.fund = pd.DataFrame(fund_data)
        self.policies = policies_text
        self.theme = theme
        self.include_gujarat = include_gujarat
        self.include_ica = include_ica
        self.note_map = {}
        self.compliance_report = None

    def generate(self, filename, preset=None):
        """Generate Excel report with optional preset"""
        # Convert amounts to numeric
        for col in ['Amount_CY', 'Amount_PY']:
            self.tb[col] = pd.to_numeric(self.tb[col], errors='coerce').fillna(0)
        
        # Generate compliance report
        self.compliance_report = self._generate_compliance_report()
        
        self._assign_notes()
        wb = xlsxwriter.Workbook(filename)
        self._init_formats(wb)
        
        # Generate sheets based on preset or default
        if preset:
            self._generate_by_preset(wb, preset)
        else:
            self._generate_all_sheets(wb)
        
        wb.close()

    def _generate_by_preset(self, wb, preset_name):
        """Generate sheets based on preset"""
        from npo_templates import ReportPreset
        preset = ReportPreset.get_preset(preset_name)
        
        if not preset:
            self._generate_all_sheets(wb)
            return
        
        # Generate sheets in preset order
        sheet_generators = {
            'Balance Sheet': self._write_bs,
            'Income & Expenditure': self._write_pl,
            'Notes to Accounts': self._write_notes,
            'Policies': self._write_policies,
            'PPE Schedule': self._write_ppe,
            'Asset Register (IAR)': self._write_iar,
            'Sch VIII (Guj BS)': self._write_gujarat_sch8,
            'Sch IX (Guj IE)': self._write_gujarat_sch9,
            'ICAI NPO Schedules': self._write_ica_schedules,
            'Fund Flow': self._write_fund_flow,
            'Receipts & Payments': self._write_receipts_payments,
            'Compliance Report': self._write_compliance_report
        }
        
        for sheet_name in preset['sheets']:
            if sheet_name in sheet_generators:
                try:
                    sheet_generators[sheet_name](wb)
                except Exception as e:
                    print(f"Error generating {sheet_name}: {e}")

    def _generate_all_sheets(self, wb):
        """Generate all sheets"""
        self._write_bs(wb)
        self._write_pl(wb)
        self._write_policies(wb)
        self._write_notes(wb)
        if not self.ppe.empty: 
            self._write_ppe(wb)
        self._write_iar(wb)
        
        if self.include_gujarat:
            self._write_gujarat_sch8(wb)
            self._write_gujarat_sch9(wb)
            self._write_gujarat_schedule10(wb)
        
        if self.include_ica:
            self._write_ica_schedules(wb)
        
        self._write_fund_flow(wb)
        self._write_receipts_payments(wb)
        self._write_compliance_report(wb)
        self._write_unit_analysis(wb)

    def _init_formats(self, wb):
        h_bg = self.theme['head']; h_font = self.theme['font']; h_bord = self.theme['border']
        self.fmt = {
            'head': wb.add_format({'bold': True, 'align': 'center', 'bg_color': h_bg, 
                                 'font_color': h_font, 'border': 1, 'border_color': h_bord}),
            'bold': wb.add_format({'bold': True}),
            'curr': wb.add_format({'num_format': '#,##0.00'}),
            'border': wb.add_format({'border': 1}),
            'title': wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'font_color': '#2C3E50'}),
            'sub_group': wb.add_format({'bold': True, 'italic': True, 'indent': 1, 'font_color': '#555555'}),
            'ledger': wb.add_format({'indent': 3}),
            'wrap': wb.add_format({'text_wrap': True, 'valign': 'top'}),
            'sign_name': wb.add_format({'bold': True, 'align': 'center'}),
            'sign_line': wb.add_format({'top': 1, 'align': 'center'}),
            'success': wb.add_format({'bg_color': '#d4edda', 'font_color': '#155724'}),
            'warning': wb.add_format({'bg_color': '#fff3cd', 'font_color': '#856404'}),
            'error': wb.add_format({'bg_color': '#f8d7da', 'font_color': '#721c24'})
        }

    def _assign_notes(self):
        used = self.tb['Group_Head'].unique()
        counter = 1
        self.note_map['Entity Info'] = counter; counter += 1
        self.note_map['Policies'] = counter; counter += 1
        if not self.fund.empty: self.note_map['Fund Movement'] = counter; counter += 1
        for g in ALL_GROUPS:
            if g in used or (g == 'Property, Plant & Equipment' and not self.ppe.empty):
                self.note_map[g] = counter; counter += 1

    def _write_iar(self, wb):
        ws = wb.add_worksheet('Asset Register (IAR)')
        ws.set_column('A:A', 8); ws.set_column('B:B', 40); ws.set_column('C:H', 15)
        ws.merge_range('A1:H1', "INCOME AND ASSET REGISTER (Movable/Immovable)", self.fmt['title'])
        h = ["Sr", "Description", "Op Balance", "Additions", "Deletions", "Total Cost", "Depreciation", "Net Block"]
        for i, t in enumerate(h): ws.write(2, i, t, self.fmt['head'])
        
        row = 3
        if not self.ppe.empty:
            for idx, r in self.ppe.iterrows():
                r = pd.to_numeric(r, errors='ignore')
                gross = r['Gross_Op'] + r['Additions'] - r['Deletions']
                net = gross - (r['Dep_Op'] + r['Dep_Year'])
                ws.write(row, 0, idx+1)
                ws.write(row, 1, r['Asset Name'])
                ws.write(row, 2, r['Gross_Op'], self.fmt['curr'])
                ws.write(row, 3, r['Additions'], self.fmt['curr'])
                ws.write(row, 4, r['Deletions'], self.fmt['curr'])
                ws.write(row, 5, gross, self.fmt['curr'])
                ws.write(row, 6, r['Dep_Year'], self.fmt['curr'])
                ws.write(row, 7, net, self.fmt['curr'])
                row += 1

    def _write_gujarat_sch8(self, wb):
        ws = wb.add_worksheet('Sch VIII (Guj BS)')
        ws.set_column('A:A', 50); ws.set_column('B:B', 20)
        ws.merge_range('A1:B1', "SCHEDULE VIII [Vide Rule 17(1)]", self.fmt['title'])
        ws.merge_range('A2:B2', f"Balance Sheet of {self.org.get('Name','')} as at {self.org.get('Date','')}", self.fmt['bold'])
        ws.write(3, 0, "FUNDS & LIABILITIES", self.fmt['head']); ws.write(3, 1, "Rs.", self.fmt['head'])
        
        row = 4
        for guj_h, groups in GUJ_BS_LIAB_MAP.items():
            ws.write(row, 0, guj_h, self.fmt['bold'])
            val = self.tb[self.tb['Group_Head'].isin(groups)]['Amount_CY'].sum()
            ws.write(row, 1, val, self.fmt['curr']); row += 1
            
        row += 2
        ws.write(row, 0, "PROPERTY AND ASSETS", self.fmt['head']); ws.write(row, 1, "Rs.", self.fmt['head']); row += 1
        for guj_h, groups in GUJ_BS_ASSETS_MAP.items():
            ws.write(row, 0, guj_h, self.fmt['bold'])
            val = self.tb[self.tb['Group_Head'].isin(groups)]['Amount_CY'].sum()
            if 'Property, Plant & Equipment' in groups and not self.ppe.empty:
                for _,r in self.ppe.iterrows(): 
                    r = pd.to_numeric(r, errors='ignore')
                    val += (r['Gross_Op']+r['Additions']-r['Deletions']) - (r['Dep_Op']+r['Dep_Year'])
            ws.write(row, 1, val, self.fmt['curr']); row += 1

    def _write_gujarat_sch9(self, wb):
        ws = wb.add_worksheet('Sch IX (Guj IE)')
        ws.set_column('A:A', 50); ws.set_column('B:B', 20)
        ws.merge_range('A1:B1', "SCHEDULE IX [Vide Rule 17(1)]", self.fmt['title'])
        ws.write(3, 0, "EXPENDITURE", self.fmt['head']); ws.write(3, 1, "Rs.", self.fmt['head']); row = 4
        for guj_h, groups in GUJ_IE_EXP_MAP.items():
            ws.write(row, 0, guj_h)
            val = self.tb[self.tb['Group_Head'].isin(groups)]['Amount_CY'].sum()
            ws.write(row, 1, val, self.fmt['curr']); row += 1
            
        row += 2
        ws.write(row, 0, "INCOME", self.fmt['head']); ws.write(row, 1, "Rs.", self.fmt['head']); row += 1
        for guj_h, groups in GUJ_IE_INC_MAP.items():
            ws.write(row, 0, guj_h)
            val = self.tb[self.tb['Group_Head'].isin(groups)]['Amount_CY'].sum()
            ws.write(row, 1, val, self.fmt['curr']); row += 1

    def _write_gujarat_schedule10(self, wb):
        ws = wb.add_worksheet('Sch X (Property)')
        ws.set_column('A:A', 30); ws.set_column('B:F', 15)
        ws.merge_range('A1:F1', "SCHEDULE X - PROPERTY & INVESTMENTS", self.fmt['title'])
        ws.write(2, 0, "IMMOVABLE PROPERTY", self.fmt['head'])
        headers = ['Location', 'Survey No', 'Area', 'Year of Acquisition', 'Cost']
        for i, h in enumerate(headers): ws.write(3, i, h, self.fmt['head'])
        
        # This would be populated from detailed property data
        ws.write(4, 0, "Details to be filled manually")
        
        row = 7
        ws.write(row, 0, "MOVABLE PROPERTY", self.fmt['head']); row += 1
        m_headers = ['Description', 'Quantity', 'Value', 'Location']
        for i, h in enumerate(m_headers): ws.write(row, i, h, self.fmt['head']); row += 1
        ws.write(row, 0, "Details to be filled manually")

    def _write_ica_schedules(self, wb):
        ws = wb.add_worksheet('ICAI NPO Schedules')
        ws.set_column('A:A', 40); ws.set_column('B:E', 15)
        ws.merge_range('A1:E1', "SCHEDULE I - CLASSIFICATION OF FUNDS", self.fmt['title'])
        
        headers = ['Fund Type', 'Opening Balance', 'Additions', 'Utilizations', 'Closing Balance']
        for i, h in enumerate(headers): ws.write(2, i, h, self.fmt['head'])
        
        row = 3
        for fund_type in FUND_TYPES:
            fund_data = self.fund[self.fund['Type'] == fund_type]
            if not fund_data.empty:
                for _, f in fund_data.iterrows():
                    closing = float(f['Opening']) + float(f['Received']) - float(f['Utilized'])
                    vals = [f['Fund Name'], f['Opening'], f['Received'], f['Utilized'], closing]
                    for i, v in enumerate(vals): 
                        ws.write(row, i, v, self.fmt['curr'] if i > 0 else None)
                    row += 1
        
        # Schedule II - Application of Funds
        row += 2
        ws.merge_range(f'A{row}:E{row}', "SCHEDULE II - APPLICATION OF FUNDS", self.fmt['title']); row += 1
        app_headers = ['Purpose', 'Budgeted', 'Actual', 'Variance %']
        for i, h in enumerate(app_headers): ws.write(row, i, h, self.fmt['head']); row += 1

    def _write_fund_flow(self, wb):
        ws = wb.add_worksheet('Fund Flow')
        ws.set_column('A:A', 40); ws.set_column('B:C', 15)
        ws.merge_range('A1:C1', "FUND FLOW STATEMENT", self.fmt['title'])
        
        # Calculate sources and applications
        income_total = self.tb[self.tb['Group_Head'].isin(PL_INCOME)]['Amount_CY'].sum()
        expense_total = self.tb[self.tb['Group_Head'].isin(PL_EXPENSE)]['Amount_CY'].sum()
        surplus = income_total - expense_total
        
        sources = [
            ('Operating Surplus', surplus),
            ('Donations Received', self.tb[self.tb['Group_Head'] == 'Donations and Grants']['Amount_CY'].sum()),
            ('Other Sources', 0)
        ]
        
        applications = [
            ('Fixed Assets', self.ppe['Additions'].sum() if not self.ppe.empty else 0),
            ('Investments', self.tb[self.tb['Group_Head'].isin(['Investments - Long Term', 'Investments - Current'])]['Amount_CY'].sum()),
            ('Loan Repayments', 0)
        ]
        
        ws.write(2, 0, "SOURCES OF FUNDS", self.fmt['head']); ws.write(2, 1, "Amount", self.fmt['head'])
        row = 3
        for desc, amount in sources:
            if amount != 0:
                ws.write(row, 0, desc); ws.write(row, 1, amount, self.fmt['curr']); row += 1
        
        row += 1
        ws.write(row, 0, "APPLICATION OF FUNDS", self.fmt['head']); ws.write(row, 1, "Amount", self.fmt['head']); row += 1
        for desc, amount in applications:
            if amount != 0:
                ws.write(row, 0, desc); ws.write(row, 1, amount, self.fmt['curr']); row += 1

    def _write_receipts_payments(self, wb):
        ws = wb.add_worksheet('Receipts & Payments')
        ws.set_column('A:A', 40); ws.set_column('B:C', 15)
        ws.merge_range('A1:C1', "RECEIPTS AND PAYMENTS ACCOUNT", self.fmt['title'])
        ws.merge_range('A2:C2', f"For the year ended {self.org.get('Date','')}", self.fmt['bold'])
        
        # This would need cash/bank transaction data
        ws.write(3, 0, "Note: Receipts & Payments account requires cash/bank transaction data.", self.fmt['wrap'])
        ws.write(4, 0, "Please maintain separate cash book for this purpose.")

    def _write_compliance_report(self, wb):
        ws = wb.add_worksheet('Compliance Report')
        ws.set_column('A:A', 50); ws.set_column('B:B', 30); ws.set_column('C:C', 20)
        ws.merge_range('A1:C1', "COMPLIANCE STATUS REPORT", self.fmt['title'])
        
        if self.compliance_report:
            row = 2
            ws.write(row, 0, "Compliance Area", self.fmt['head'])
            ws.write(row, 1, "Status", self.fmt['head'])
            ws.write(row, 2, "Remarks", self.fmt['head'])
            row += 1
            
            # Section 11 Compliance
            sec11 = self.compliance_report.get('section_11', {})
            status = "✅ COMPLIANT" if sec11.get('compliance_85_percent') else "❌ NON-COMPLIANT"
            remarks = f"Application: {sec11.get('total_application',0):,.2f} / Required: {sec11.get('required_application',0):,.2f}"
            ws.write(row, 0, "Income Tax Section 11")
            ws.write(row, 1, status, self.fmt['success'] if 'COMPLIANT' in status else self.fmt['error'])
            ws.write(row, 2, remarks); row += 1
            
            # Gujarat Compliance
            guj_issues = self.compliance_report.get('gujarat_compliance', {}).get('issues', [])
            status = "✅ COMPLIANT" if not guj_issues else f"⚠️ {len(guj_issues)} ISSUES"
            ws.write(row, 0, "Gujarat Trust Act")
            ws.write(row, 1, status, self.fmt['success'] if 'COMPLIANT' in status else self.fmt['warning'])
            ws.write(row, 2, "; ".join(guj_issues[:2]) if guj_issues else "All requirements met"); row += 1
            
            # ICAI Compliance
            ica_status = self.compliance_report.get('ica_compliance', {})
            status = "✅ SCHEDULES READY" if ica_status.get('notes_required') else "⚠️ INCOMPLETE"
            ws.write(row, 0, "ICAI NPO Guidance")
            ws.write(row, 1, status, self.fmt['success'] if 'READY' in status else self.fmt['warning'])
            ws.write(row, 2, f"Schedules: {', '.join(ica_status.get('schedules_required', []))}"); row += 2
            
            # Recommendations
            ws.write(row, 0, "RECOMMENDATIONS", self.fmt['bold']); row += 1
            recommendations = []
            if not sec11.get('compliance_85_percent'):
                recommendations.append(f"Increase application by {abs(sec11.get('shortfall_excess',0)):,.2f} to meet 85% requirement")
            if guj_issues:
                recommendations.extend(guj_issues[:3])
            
            for rec in recommendations:
                ws.write(row, 0, f"• {rec}", self.fmt['wrap'])
                row += 1

    def _write_unit_analysis(self, wb):
        if 'Unit' not in self.tb.columns:
            return
        
        ws = wb.add_worksheet('Unit Analysis')
        ws.set_column('A:A', 25); ws.set_column('B:E', 15)
        ws.merge_range('A1:E1', "UNIT-WISE PERFORMANCE ANALYSIS", self.fmt['title'])
        
        headers = ['Unit', 'Income', 'Expenses', 'Surplus/(Deficit)', '% of Total']
        for i, h in enumerate(headers): ws.write(2, i, h, self.fmt['head'])
        
        units = self.tb['Unit'].unique()
        total_income = self.tb[self.tb['Group_Head'].isin(PL_INCOME)]['Amount_CY'].sum()
        total_expense = self.tb[self.tb['Group_Head'].isin(PL_EXPENSE)]['Amount_CY'].sum()
        
        row = 3
        for unit in units:
            unit_data = self.tb[self.tb['Unit'] == unit]
            unit_income = unit_data[unit_data['Group_Head'].isin(PL_INCOME)]['Amount_CY'].sum()
            unit_expense = unit_data[unit_data['Group_Head'].isin(PL_EXPENSE)]['Amount_CY'].sum()
            unit_surplus = unit_income - unit_expense
            
            if total_income != 0:
                income_pct = (unit_income / total_income) * 100
            else:
                income_pct = 0
            
            ws.write(row, 0, unit)
            ws.write(row, 1, unit_income, self.fmt['curr'])
            ws.write(row, 2, unit_expense, self.fmt['curr'])
            ws.write(row, 3, unit_surplus, self.fmt['curr'])
            ws.write(row, 4, f"{income_pct:.1f}%")
            row += 1

    def _generate_compliance_report(self):
        """Generate compliance report data"""
        income_total = self.tb[self.tb['Group_Head'].isin(PL_INCOME)]['Amount_CY'].sum()
        expense_total = self.tb[self.tb['Group_Head'].isin(PL_EXPENSE)]['Amount_CY'].sum()
        
        ppe_total = self.ppe['Additions'].sum() if not self.ppe.empty else 0
        
        return ComplianceCalculator.generate_compliance_report(
            self.tb.to_dict('records'),
            income_total,
            expense_total,
            self.ppe.to_dict('records') if not self.ppe.empty else None
        )

    # Previous methods (_write_bs, _write_pl, _write_policies, _write_notes, 
    # _write_ppe, _write_signatories) remain the same as in original code
    # but add this at the end of _write_bs and _write_pl:
    
    def _write_bs(self, wb):
        # ... existing code ...
        # Add compliance status at bottom
        row += 10
        if self.compliance_report:
            sec11 = self.compliance_report.get('section_11', {})
            if sec11.get('compliance_85_percent'):
                ws.write(row, 0, "✓ COMPLIANT WITH SECTION 11 REQUIREMENTS", self.fmt['success'])
            else:
                ws.write(row, 0, "⚠️ REVIEW SECTION 11 COMPLIANCE", self.fmt['warning'])
    
    def _write_pl(self, wb):
        # ... existing code ...
        # Add program effectiveness
        row += 10
        prog_exp = self.tb[self.tb['Group_Head'] == 'Programme Expenses']['Amount_CY'].sum()
        total_exp = self.tb[self.tb['Group_Head'].isin(PL_EXPENSE)]['Amount_CY'].sum()
        
        if total_exp > 0:
            prog_ratio = (prog_exp / total_exp) * 100
            status = "✓ GOOD" if prog_ratio >= 85 else "⚠️ NEEDS IMPROVEMENT"
            ws.write(row, 0, f"Program Expenditure Ratio: {prog_ratio:.1f}% ({status})", 
                    self.fmt['success'] if 'GOOD' in status else self.fmt['warning'])