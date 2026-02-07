# npo_compliance.py
from datetime import datetime
import pandas as pd

class ComplianceCalculator:
    """Calculate various compliance requirements for NPOs"""
    
    @staticmethod
    def calculate_section_11_compliance(income, expenses, capital_exp=0, accumulation_rate=0.15):
        """Calculate Section 11 compliance for income tax"""
        
        # Revenue expenses (excluding depreciation)
        revenue_expenses = sum(expenses)
        
        # Total application
        total_application = revenue_expenses + capital_exp
        
        # Required application (85% of income)
        required_application = income * 0.85
        
        # Accumulation allowed (15% of income)
        max_accumulation = income * accumulation_rate
        
        # Actual accumulation
        actual_accumulation = income - total_application
        
        compliance_status = {
            'total_income': income,
            'revenue_expenses': revenue_expenses,
            'capital_expenditure': capital_exp,
            'total_application': total_application,
            'required_application': required_application,
            'compliance_85_percent': total_application >= required_application,
            'shortfall_excess': total_application - required_application,
            'accumulation_allowed': max_accumulation,
            'actual_accumulation': actual_accumulation,
            'accumulation_within_limit': actual_accumulation <= max_accumulation,
            'taxable_income': max(0, income - total_application - max_accumulation)
        }
        
        return compliance_status
    
    @staticmethod
    def calculate_fund_classification(data):
        """Classify funds as per NPO guidance"""
        fund_summary = {}
        
        for fund_type in ['General', 'Designated', 'Restricted', 'Corpus']:
            fund_data = [r for r in data if r.get('Fund_Type') == fund_type]
            fund_summary[fund_type] = {
                'count': len(fund_data),
                'total_cy': sum(r.get('Amount_CY', 0) for r in fund_data),
                'total_py': sum(r.get('Amount_PY', 0) for r in fund_data)
            }
        
        return fund_summary
    
    @staticmethod
    def check_gujarat_compliance(data, ppe_data=None):
        """Check compliance with Gujarat Trust Act requirements"""
        compliance_items = []
        
        # Check required schedules
        required_groups = ['Corpus Fund', 'Restricted Funds', 'Property, Plant & Equipment']
        missing_groups = []
        
        for group in required_groups:
            if not any(r['Group_Head'] == group for r in data):
                missing_groups.append(group)
        
        if missing_groups:
            compliance_items.append(f"Missing required groups: {', '.join(missing_groups)}")
        
        # Check PPE details if provided
        if ppe_data and len(ppe_data) > 0:
            has_immovable = any('Immovable' in str(r.get('Asset Name', '')) for r in ppe_data)
            has_movable = any('Movable' in str(r.get('Asset Name', '')) for r in ppe_data)
            
            if not has_immovable:
                compliance_items.append("Immovable property details not found")
            if not has_movable:
                compliance_items.append("Movable property details not found")
        
        # Check investment details
        investments = [r for r in data if 'Investment' in r.get('Group_Head', '')]
        if not investments:
            compliance_items.append("Investment details not found")
        
        return compliance_items
    
    @staticmethod
    def generate_compliance_report(data, income_total, expense_total, ppe_data=None):
        """Generate comprehensive compliance report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_ledgers': len(data),
                'total_income': income_total,
                'total_expenses': expense_total,
                'surplus_deficit': income_total - expense_total
            },
            'section_11': ComplianceCalculator.calculate_section_11_compliance(
                income_total, [expense_total]
            ),
            'fund_classification': ComplianceCalculator.calculate_fund_classification(data),
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
    def calculate_program_effectiveness(program_expenses, total_expenses, beneficiaries=None):
        """Calculate program effectiveness ratios"""
        if total_expenses == 0:
            return {}
        
        program_ratio = (program_expenses / total_expenses) * 100
        admin_ratio = 100 - program_ratio
        
        effectiveness = {
            'program_expenditure_ratio': program_ratio,
            'administrative_expenditure_ratio': admin_ratio,
            'compliance_status': program_ratio >= 85,  # Typically 85% for charities
            'efficiency_score': min(100, program_ratio * 1.2)  # Simple scoring
        }
        
        if beneficiaries:
            cost_per_beneficiary = program_expenses / beneficiaries if beneficiaries > 0 else 0
            effectiveness['cost_per_beneficiary'] = cost_per_beneficiary
        
        return effectiveness

class ITFormsGenerator:
    """Generate IT forms for NPOs"""
    
    @staticmethod
    def prepare_form_10b(data, assessment_year):
        """Prepare Form 10B for audit report"""
        form = {
            'form_name': 'Form 10B',
            'assessment_year': assessment_year,
            'trust_name': '',
            'pan_number': '',
            'registration_number': '',
            'sections': {
                '1': 'Particulars of registration under section 12A/12AA',
                '2': 'Audit of accounts',
                '3': 'Computation of income',
                '4': 'Application of income',
                '5': 'Accumulation of income',
                '6': 'Investments',
                '7': 'Voluntary contributions',
                '8': 'Auditor\'s certificate'
            }
        }
        return form
    
    @staticmethod
    def prepare_form_10bb(data, assessment_year):
        """Prepare Form 10BB for certain types of trusts"""
        form = {
            'form_name': 'Form 10BB',
            'assessment_year': assessment_year,
            'trust_name': '',
            'sections': {
                '1': 'Basic information',
                '2': 'Activities undertaken',
                '3': 'Receipt and application of income',
                '4': 'Statement of income',
                '5': 'Certificate'
            }
        }
        return form