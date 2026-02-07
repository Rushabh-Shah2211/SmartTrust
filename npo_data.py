# npo_data.py
import pandas as pd
import hashlib
import json
from datetime import datetime

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
                    'Group_Head': '', 'Sub_Group': '', 'L3_Group': '', 'Fund_Type': 'General'
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
            
            # Create data integrity hash
            data_hash = DataManager._create_data_hash(processed_data)
            
            return processed_data, None
        except Exception as e: 
            return None, f"Error loading file: {str(e)}"

    @staticmethod
    def _safe_float(value):
        """Safely convert to float"""
        try:
            if pd.isna(value):
                return 0.0
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except:
            return 0.0

    @staticmethod
    def _validate_dataframe(df, name_col, cy_col, py_col):
        """Validate DataFrame structure and data"""
        errors = []
        
        # Check for empty dataframe
        if df.empty:
            return False, "File is empty"
        
        # Check required columns
        if name_col not in df.columns:
            errors.append(f"Column '{name_col}' not found")
        if cy_col not in df.columns:
            errors.append(f"Column '{cy_col}' not found")
        
        # Check for duplicate ledger names
        duplicates = df[name_col][df[name_col].duplicated()].tolist()
        if duplicates:
            errors.append(f"Duplicate ledger names: {duplicates[:5]}")
        
        # Check for invalid amounts
        invalid_cy = df[cy_col][~pd.to_numeric(df[cy_col], errors='coerce').notna()].index.tolist()
        if invalid_cy:
            errors.append(f"Invalid current year amounts at rows: {invalid_cy[:5]}")
        
        if py_col:
            invalid_py = df[py_col][~pd.to_numeric(df[py_col], errors='coerce').notna()].index.tolist()
            if invalid_py:
                errors.append(f"Invalid previous year amounts at rows: {invalid_py[:5]}")
        
        if errors:
            return False, " | ".join(errors[:3])  # Return first 3 errors
        
        return True, "Valid"

    @staticmethod
    def _create_data_hash(data):
        """Create hash for data integrity"""
        hash_data = {
            'records': len(data),
            'total_cy': sum(row['Amount_CY'] for row in data),
            'total_py': sum(row['Amount_PY'] for row in data),
            'timestamp': datetime.now().isoformat()
        }
        hash_input = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @staticmethod
    def validate_tb_data(data):
        """Validate trial balance data structure"""
        required_fields = ['Ledger Name', 'Amount_CY', 'Group_Head']
        
        for i, row in enumerate(data):
            # Check required fields
            for field in required_fields:
                if field not in row or not row[field]:
                    return False, f"Row {i+1}: Missing '{field}'"
            
            # Validate amount formats
            try:
                cy = float(row['Amount_CY'])
                if cy < 0:
                    return False, f"Row {i+1}: Negative amount not allowed"
            except ValueError:
                return False, f"Row {i+1}: Invalid amount format for CY"
            
            if 'Amount_PY' in row and row['Amount_PY']:
                try:
                    float(row['Amount_PY'])
                except ValueError:
                    return False, f"Row {i+1}: Invalid amount format for PY"
        
        return True, "Data validation successful"

    @staticmethod
    def prepare_unit_data(data, unit_name):
        """Prepare data for specific unit"""
        if unit_name == "Consolidated":
            return data
        else:
            return [row for row in data if row.get('Unit') == unit_name]

    @staticmethod
    def analyze_data_quality(data):
        """Analyze data quality metrics"""
        metrics = {
            'total_records': len(data),
            'records_with_cy': sum(1 for r in data if r.get('Amount_CY', 0) != 0),
            'records_with_py': sum(1 for r in data if r.get('Amount_PY', 0) != 0),
            'records_with_group': sum(1 for r in data if r.get('Group_Head')),
            'total_cy_amount': sum(r.get('Amount_CY', 0) for r in data),
            'total_py_amount': sum(r.get('Amount_PY', 0) for r in data),
        }
        return metrics