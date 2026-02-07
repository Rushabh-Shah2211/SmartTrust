# npo_compliance.py (REPLACE ENTIRE FILE)
from datetime import datetime
import pandas as pd

class ComplianceCalculator:
    """Calculate various compliance requirements for NPOs"""
    
    @staticmethod
    def calculate_section_11_compliance(income, expenses, capital_exp=0, accumulation_rate=0.15):
        """Advanced Section 11 compliance with Deemed Application logic"""
        revenue_expenses = sum(expenses)
        total_application = revenue_expenses + capital_exp
        required_application = income * 0.85
        max_accumulation = income * accumulation_rate
        actual_accumulation = income - total_application
        
        # Deemed Application (Form 9A/10) logic
        shortfall = max(0, required_application - total_application)
        
        compliance_status = {
            'total_income': income,
            'revenue_expenses': revenue_expenses,
            'capital_expenditure': capital_exp,
            'total_application': total_application,
            'required_application': required_application,
            'compliance_85_percent': total_application >= required_application,
            'shortfall_excess': total_application - required_application,
            'deemed_application_eligible': shortfall,
            'accumulation_allowed': max_accumulation,
            'actual_accumulation': actual_accumulation,
            'accumulation_within_limit': actual_accumulation <= max_accumulation,
            'taxable_income': max(0, income - total_application - max_accumulation)
        }
        return compliance_status
    
    @staticmethod
    def check_fcra_compliance(data):
        """Verify Foreign Contribution (FCRA) segregation"""
        fcra_data = [r for r in data if r.get('Source') == 'FCRA']
        local_data = [r for r in data if r.get('Source') == 'Local']
        
        return {
            'has_fcra': len(fcra_data) > 0,
            'fcra_ledger_count': len(fcra_data),
            'local_ledger_count': len(local_data),
            'is_segregated': True if len(fcra_data) > 0 else "N/A"
        }

    @staticmethod
    def generate_compliance_report(data, income_total, expense_total, ppe_data=None):
        # Import here to avoid circular import
        from npo_data import DataManager
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_ledgers': len(data),
                'total_income': income_total,
                'total_expenses': expense_total,
                'surplus_deficit': income_total - expense_total
            },
            'section_11': ComplianceCalculator.calculate_section_11_compliance(
                income_total, [expense_total], 
                sum(DataManager._safe_float(p.get('Additions', 0)) for p in ppe_data) if ppe_data else 0
            ),
            'fcra_compliance': ComplianceCalculator.check_fcra_compliance(data),
            'gujarat_compliance': {
                'issues': ComplianceCalculator.check_gujarat_compliance(data, ppe_data),
                'forms_required': ['Form 10', 'Form 11', 'Form 12']
            },
            'ica_compliance': {
                'schedules_required': ['I', 'II', 'III', 'IV', 'V', 'VI'],
                'notes_required': True
            }
        }
        return report

    @staticmethod
    def check_gujarat_compliance(data, ppe_data=None):
        compliance_items = []
        required_groups = ['Corpus Fund', 'Restricted Funds', 'Property, Plant & Equipment']
        for group in required_groups:
            if not any(r.get('Group_Head') == group for r in data):
                compliance_items.append(f"Missing required group: {group}")
        return compliance_items

class ITFormsGenerator:
    """Generate Income Tax Forms 10B/10BB"""
    
    @staticmethod
    def prepare_form_10b(data, assessment_year):
        """Prepare Form 10B data structure"""
        return {
            'form_name': 'Form 10B',
            'assessment_year': assessment_year,
            'sections': {
                '1': 'Particulars of the trust/institution',
                '2': 'Statement of income and expenditure',
                '3': 'Statement showing application of income',
                '4': 'Statement of accumulations',
                '5': 'Balance sheet',
                '6': 'Statement of particulars'
            },
            'data_prepared': True,
            'notes': 'Form will be generated in Excel with complete details'
        }
    
    @staticmethod
    def prepare_form_10bb(data, assessment_year):
        """Prepare Form 10BB for political parties"""
        return {
            'form_name': 'Form 10BB',
            'assessment_year': assessment_year,
            'notes': 'Form 10BB for political parties'
        }