# npo_data.py
import pandas as pd
import hashlib
import json
from datetime import datetime

class DataStore:
    """Centralized Store for Application State to ensure data integrity"""
    def __init__(self):
        self.ledger_data = []
        self.ppe_data = []
        self.fund_data = []
        self.org_info = {}
        self.last_sync = None

    def sync_from_ui(self, mapping_list, ppe_list, fund_list, org_dict):
        """Atomic update of all data states before generation"""
        self.ledger_data = mapping_list
        self.ppe_data = ppe_list
        self.fund_data = fund_list
        self.org_info = org_dict
        self.last_sync = datetime.now()

class DataManager:
    @staticmethod
    def load_tb(file_path):
        """Load trial balance with validation"""
        try:
            df = pd.read_csv(file_path)
            cols = {c.lower().strip(): c for c in df.columns}
            
            # Detect Columns
            name_col = next((cols[c] for c in cols if any(x in c for x in ['ledger', 'particular', 'head'])), None)
            amt_candidates = [c for c in cols if any(x in c for x in ['amount', 'debit', 'balance', 'rs'])]
            
            cy_col = None; py_col = None
            for c in amt_candidates:
                if 'prev' in c.lower() or 'py' in c.lower(): py_col = cols[c]
                elif 'curr' in c.lower() or 'cy' in c.lower(): cy_col = cols[c]
            
            if not cy_col and len(amt_candidates) > 0: cy_col = cols[amt_candidates[0]]
            if not py_col and len(amt_candidates) > 1: py_col = cols[amt_candidates[1]]

            unit_col = next((cols[c] for c in cols if 'unit' in c or 'branch' in c), None)

            if not name_col or not cy_col: 
                return None, "Could not identify Ledger/Amount columns."

            # Validate data
            validation_result = DataManager._validate_dataframe(df, name_col, cy_col, py_col)
            if not validation_result[0]:
                return None, validation_result[1]

            processed_data = []
            for _, row in df.iterrows():
                row_data = {
                    'Unit': row[unit_col] if unit_col else 'Main Unit',
                    'Ledger Name': str(row[name_col]).strip(),
                    'Amount_CY': DataManager._safe_float(row[cy_col]) if cy_col else 0,
                    'Amount_PY': DataManager._safe_float(row[py_col]) if py_col else 0,
                    'Group_Head': '', 'Sub_Group': '', 'L3_Group': '', 'Fund_Type': 'General', 'Source': 'Local'
                }
                # Auto-Map
                for c in df.columns:
                    cl = c.lower()
                    if 'group' in cl and 'sub' not in cl and cl not in ['subgroup', 'sub_group']: 
                        row_data['Group_Head'] = str(row[c]).strip()
                    if 'sub' in cl and 'group' in cl: 
                        row_data['Sub_Group'] = str(row[c]).strip()
                    if 'fund' in cl and 'type' in cl: 
                        row_data['Fund_Type'] = str(row[c]).strip()
                processed_data.append(row_data)
            
            return processed_data, None
        except Exception as e: 
            return None, f"Error loading file: {str(e)}"

    @staticmethod
    def calculate_wdv_depreciation(ppe_records):
        """Automated Depreciation Engine using Income Tax Act rates"""
        from npo_config import DEPRECIATION_RATES
        for record in ppe_records:
            asset_name = str(record.get('Asset Name', ''))
            # Auto-detect rate from name or config
            rate = 0.15 # Default
            for category, r in DEPRECIATION_RATES.items():
                if category.lower() in asset_name.lower():
                    rate = r
                    break
            
            opening = DataManager._safe_float(record.get('Gross_Op', 0))
            additions = DataManager._safe_float(record.get('Additions', 0))
            deletions = DataManager._safe_float(record.get('Deletions', 0))
            
            # WDV Calculation: (Opening + Additions - Deletions) * Rate
            record['Dep_Year'] = round((opening + additions - deletions) * rate, 2)
        return ppe_records

    @staticmethod
    def _safe_float(value):
        try:
            if pd.isna(value): return 0.0
            if isinstance(value, str): value = value.replace(',', '').strip()
            return float(value)
        except: return 0.0

    @staticmethod
    def _validate_dataframe(df, name_col, cy_col, py_col):
        if df.empty: return False, "File is empty"
        if name_col not in df.columns: return False, f"Column '{name_col}' not found"
        return True, "Valid"

    @staticmethod
    def validate_tb_data(data):
        required_fields = ['Ledger Name', 'Amount_CY', 'Group_Head']
        for i, row in enumerate(data):
            for field in required_fields:
                if field not in row or not str(row[field]).strip():
                    return False, f"Row {i+1}: Missing '{field}'"
        return True, "Success"

    @staticmethod
    def analyze_data_quality(data):
        metrics = {
            'total_records': len(data),
            'records_with_cy': sum(1 for r in data if r.get('Amount_CY', 0) != 0),
            'records_with_py': sum(1 for r in data if r.get('Amount_PY', 0) != 0),
            'records_with_group': sum(1 for r in data if r.get('Group_Head')),
            'total_cy_amount': sum(r.get('Amount_CY', 0) for r in data),
            'total_py_amount': sum(r.get('Amount_PY', 0) for r in data),
        }
        return metrics