# npo_config.py
import json
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================

APP_NAME = "RB Smart FS"
VERSION = "13.1"

# --- AUTOMATED DEPRECIATION RATES (Income Tax Act) ---
DEPRECIATION_RATES = {
    'Immovable Properties': 0.10,
    'Movable Properties': 0.15,
    'Vehicles': 0.15,
    'Furniture': 0.10,
    'Computers': 0.40,
    'Intangible Assets': 0.25
}

# --- GROUPS ---
BS_ASSETS = [
    'Property, Plant & Equipment', 'Intangible Assets', 'Capital Work in Progress',
    'Investments - Long Term', 'Investments - Current',
    'Inventories', 'Receivables', 'Loans & Advances', 'Cash and Bank Balances',
    'Other Current Assets', 'Other Non-Current Assets'
]

BS_LIABILITIES = [
    'Corpus Fund', 'General Fund', 'Designated Funds', 'Restricted Funds',
    'Long Term Borrowings', 'Long Term Provisions', 'Other Long Term Liabilities',
    'Current Liabilities', 'Short Term Provisions', 'Short Term Borrowings',
    'Trade Payables', 'Income Received in Advance'
]

PL_INCOME = [
    'Donations and Grants', 'Fees / Subscriptions', 'Interest Income', 
    'Dividend Income', 'Other Income', 'Sale of Goods', 'Rent Income'
]

PL_EXPENSE = [
    'Programme Expenses', 'Staff Payments & Benefits', 'Admin Expenses',
    'Rent, Rates & Taxes', 'Repairs & Maintenance', 'Finance Costs', 
    'Depreciation', 'Other Expenses', 'Audit Fees', 'Legal Expenses'
]

ALL_GROUPS = sorted(BS_LIABILITIES + BS_ASSETS + PL_INCOME + PL_EXPENSE)
FUND_TYPES = ['General', 'Designated', 'Restricted', 'Corpus']
SOURCE_TYPES = ['Local', 'FCRA']

SUB_GROUP_MAPPING = {
    'Long Term Borrowings': ['Secured', 'Unsecured', 'From Trustees', 'From Banks'],
    'Cash and Bank Balances': ['Cash on Hand', 'Savings Bank', 'Current Account', 'Fixed Deposits'],
    'Property, Plant & Equipment': ['Immovable Properties', 'Movable Properties', 'Vehicles', 'Furniture', 'Computers'],
    'Donations and Grants': ['Cash Donations', 'Grant-in-Aid', 'Corporate Donations', 'Foreign Donations'],
    'Programme Expenses': ['Scholarships', 'Medical Aid', 'Relief Work', 'Education Programs'],
}

# --- COLOR THEMES ---
COLOR_THEMES = {
    "Professional (Gray)": {'head': '#D3D3D3', 'font': '#000000', 'border': '#000000'},
    "RB Blue": {'head': '#4A90E2', 'font': '#FFFFFF', 'border': '#2C3E50'},
    "Eco Green": {'head': '#2ECC71', 'font': '#FFFFFF', 'border': '#27AE60'},
    "Royal Teal": {'head': '#008080', 'font': '#FFFFFF', 'border': '#004d4d'},
    "Crimson Red": {'head': '#C0392B', 'font': '#FFFFFF', 'border': '#922B21'}
}

# --- GUJARAT CHARITY FORMAT MAPPINGS ---
GUJ_BS_ASSETS_MAP = {
    'Immovable Properties': ['Property, Plant & Equipment'],
    'Investments': ['Investments - Long Term', 'Investments - Current'],
    'Furniture & Fixtures': ['Property, Plant & Equipment'],
    'Loans (Scholarships/Other)': ['Loans & Advances'],
    'Advances': ['Loans & Advances'],
    'Cash and Bank Balances': ['Cash and Bank Balances']
}

GUJ_BS_LIAB_MAP = {
    'Trust Funds or Corpus': ['Corpus Fund'],
    'Other Earmarked Funds': ['Restricted Funds', 'Designated Funds'],
    'Loans (Secured/Unsecured)': ['Long Term Borrowings', 'Short Term Borrowings'],
    'Liabilities': ['Current Liabilities', 'Trade Payables', 'Provisions']
}

GUJ_IE_EXP_MAP = {
    'To Rent, Rates, Taxes': ['Rent, Rates & Taxes'],
    'To Repairs & Maintenance': ['Repairs & Maintenance'],
    'To Salaries': ['Staff Payments & Benefits'],
    'To Audit Fees': ['Audit Fees'],
    'To Establishment Expenses': ['Admin Expenses', 'Other Expenses'],
    'To Depreciation': ['Depreciation'],
    'To Expenditure on Objects of Trust': ['Programme Expenses']
}

GUJ_IE_INC_MAP = {
    'By Rent (Accrued/Realised)': ['Rent Income'],
    'By Interest (Accrued/Realised)': ['Interest Income'],
    'By Dividend': ['Dividend Income'],
    'By Donations in Cash or Kind': ['Donations and Grants'],
    'By Grants': ['Donations and Grants'],
    'By Income from other sources': ['Other Income', 'Fees / Subscriptions', 'Sale of Goods']
}

# --- GUJARAT FORMS AND SCHEDULES ---
GUJ_FORMS = {
    'Form 10': 'Annual Statement of Accounts',
    'Form 11': 'Balance Sheet',
    'Form 12': 'Income & Expenditure Account'
}

GUJ_SCHEDULE_10 = {
    'Immovable Property Details': ['Location', 'Survey No', 'Area', 'Year of Acquisition', 'Cost'],
    'Movable Property Details': ['Description', 'Quantity', 'Value', 'Location'],
    'Investments Details': ['Particulars', 'Face Value', 'Book Value', 'Market Value', 'Nature']
}

# --- ICAI NPO GUIDANCE NOTE SCHEDULES ---
ICAI_SCHEDULES = {
    'Schedule I': 'Classification of Funds',
    'Schedule II': 'Application of Funds',
    'Schedule III': 'Receipts and Payments',
    'Schedule IV': 'Income and Expenditure',
    'Schedule V': 'Balance Sheet',
    'Schedule VI': 'Notes to Accounts'
}

DEFAULT_POLICIES = """1. BASIS OF PREPARATION
The financial statements have been prepared on accrual basis under the historical cost convention.

2. REVENUE RECOGNITION
(a) Grants & Donations: Recognized when there is reasonable assurance of compliance and receipt.
(b) Interest Income: Recognized on a time proportion basis.

3. PROPERTY, PLANT AND EQUIPMENT
Stated at cost less accumulated depreciation.

4. DEPRECIATION
Provided on WDV basis as per Income Tax Act, 1961.

5. INVESTMENTS
Long-term investments are stated at cost.

6. EMPLOYEE BENEFITS
Defined contribution plans are charged to P&L as incurred.

7. FOREIGN CURRENCY TRANSACTIONS
Transactions in foreign currency are recorded at the exchange rate prevailing on the date of transaction.

8. PROVISIONS AND CONTINGENCIES
Provisions are recognized when there is a present obligation.

9. TAXES ON INCOME
Current tax is determined as per the provisions of Income Tax Act, 1961.
"""

# --- COMPLIANCE CHECKLISTS ---
COMPLIANCE_CHECKLISTS = {
    'ICAI NPO Guidance': [
        'Fund Classification as per Schedule I',
        'Schedule II - Application of Funds prepared',
        'Receipts & Payments Account prepared',
        'Notes to Accounts include all required disclosures',
        'Segment reporting for multiple activities',
        'Related party disclosures included'
    ],
    'Income Tax Act': [
        'Section 11 compliance calculation',
        '85% application requirement verified',
        'Accumulation within 15% limit',
        'Form 10B/10BB requirements met',
        'Capital vs Revenue expenditure segregated',
        'Prior period adjustments disclosed'
    ],
    'Gujarat Trust Act': [
        'Schedule VIII (Balance Sheet) prepared',
        'Schedule IX (Income & Expenditure) prepared',
        'Form 10 - Annual Statement attached',
        'Movable/Immovable property schedule',
        'Investment details schedule',
        'Trustee declarations included'
    ]
}

def save_config(config_data, filename='npo_config_backup.json'):
    try:
        with open(filename, 'w') as f:
            json.dump({
                'saved_at': datetime.now().isoformat(),
                'config': config_data
            }, f, indent=2)
        return True
    except Exception as e:
        return False, str(e)

def load_config(filename='npo_config_backup.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['config']
    except FileNotFoundError:
        return None
    except Exception as e:
        return None, str(e)