# npo_security.py
import hashlib
import json
from datetime import datetime
import base64

class DataSecurity:
    """Handle data security and integrity without external dependencies"""
    
    @staticmethod
    def create_integrity_hash(data, data_type):
        """Create integrity hash for data"""
        if isinstance(data, list):
            # Create hash from sorted data
            sorted_data = sorted(data, key=lambda x: str(x.get('Ledger Name', '')))
            data_str = json.dumps(sorted_data, sort_keys=True)
        else:
            data_str = json.dumps(data, sort_keys=True)
        
        hash_obj = hashlib.sha256(data_str.encode())
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_integrity(data, data_type, expected_hash):
        """Verify data integrity"""
        current_hash = DataSecurity.create_integrity_hash(data, data_type)
        return current_hash == expected_hash

class InputValidator:
    """Validate all user inputs"""
    
    @staticmethod
    def validate_amount(amount_str):
        """Validate amount input"""
        try:
            # Remove commas and whitespace
            if amount_str is None:
                return True, 0.0
                
            cleaned = str(amount_str).replace(',', '').strip()
            if not cleaned:
                return True, 0.0
            
            amount = float(cleaned)
            if amount < 0:
                return False, "Amount cannot be negative"
            
            return True, amount
        except ValueError:
            return False, "Invalid amount format"
    
    @staticmethod
    def validate_ledger_name(name):
        """Validate ledger name"""
        if not name or not name.strip():
            return False, "Ledger name cannot be empty"
        
        if len(name.strip()) > 200:
            return False, "Ledger name too long (max 200 characters)"
        
        # Check for potentially dangerous characters
        dangerous_chars = ['<', '>', ';', '|', '&', '$']
        for char in dangerous_chars:
            if char in name:
                return False, f"Invalid character '{char}' in ledger name"
        
        return True, name.strip()
    
    @staticmethod
    def validate_group_head(group):
        """Validate group head"""
        # Import here to avoid circular import
        try:
            from npo_config import ALL_GROUPS
        except ImportError:
            ALL_GROUPS = []
        
        if not group:
            return False, "Group head cannot be empty"
        
        if group not in ALL_GROUPS:
            # Allow custom groups with warning
            return True, group
        
        return True, group
    
    @staticmethod
    def validate_date(date_str):
        """Validate date string"""
        try:
            # Try multiple date formats
            for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d'):
                try:
                    datetime.strptime(date_str, fmt)
                    return True, date_str
                except ValueError:
                    continue
            return False, "Invalid date format. Use DD-MM-YYYY"
        except Exception:
            return False, "Invalid date format"
    
    @staticmethod
    def validate_email(email):
        """Simple email validation"""
        if not email:
            return True, ""
        
        if '@' in email and '.' in email:
            return True, email.strip()
        return False, "Invalid email format"
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        if not phone:
            return True, ""
        
        # Remove spaces, hyphens, parentheses
        cleaned = ''.join(c for c in phone if c.isdigit())
        
        if len(cleaned) >= 10:
            return True, cleaned
        return False, "Phone number must have at least 10 digits"