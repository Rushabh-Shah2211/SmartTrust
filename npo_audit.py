# npo_audit.py
import logging
import json
from datetime import datetime
import os

class AuditLogger:
    """Handle audit logging for the application"""
    
    def __init__(self, log_dir='audit_logs'):
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Configure logging
        log_file = os.path.join(self.log_dir, f"npo_audit_{datetime.now().strftime('%Y%m')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('NPOLogger')
    
    def log_generation(self, user_info, filename, parameters):
        """Log report generation"""
        log_entry = {
            'event': 'report_generation',
            'timestamp': datetime.now().isoformat(),
            'user': user_info,
            'filename': filename,
            'parameters': parameters,
            'status': 'success'
        }
        
        self.logger.info(json.dumps(log_entry))
        return log_entry
    
    def log_validation(self, data_hash, validation_result, unit=None):
        """Log data validation"""
        log_entry = {
            'event': 'data_validation',
            'timestamp': datetime.now().isoformat(),
            'data_hash': data_hash,
            'validation_result': validation_result,
            'unit': unit,
            'status': 'valid' if validation_result[0] else 'invalid'
        }
        
        self.logger.info(json.dumps(log_entry))
        return log_entry
    
    def log_error(self, error_type, error_message, context=None):
        """Log errors"""
        log_entry = {
            'event': 'error',
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'status': 'error'
        }
        
        self.logger.error(json.dumps(log_entry))
        return log_entry
    
    def log_compliance_check(self, compliance_type, results):
        """Log compliance checks"""
        log_entry = {
            'event': 'compliance_check',
            'timestamp': datetime.now().isoformat(),
            'compliance_type': compliance_type,
            'results': results,
            'status': 'completed'
        }
        
        self.logger.info(json.dumps(log_entry))
        return log_entry
    
    def get_audit_trail(self, start_date=None, end_date=None):
        """Get audit trail for specified period"""
        # This would read from log files
        # Simplified version
        return {
            'period': f"{start_date} to {end_date}" if start_date and end_date else "All",
            'logs_available': True
        }
    
    def export_audit_log(self, output_file):
        """Export audit log to file"""
        try:
            # Collect all log entries (simplified)
            logs = []
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    log_file = handler.baseFilename
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            logs.extend(f.readlines())
            
            with open(output_file, 'w') as f:
                json.dump({'audit_logs': logs}, f, indent=2)
            
            return True, output_file
        except Exception as e:
            return False, str(e)

class UserActivityTracker:
    """Track user activities"""
    
    def __init__(self):
        self.activities = []
    
    def track_activity(self, activity_type, details):
        """Track user activity"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'details': details
        }
        self.activities.append(activity)
        return activity
    
    def get_recent_activities(self, limit=50):
        """Get recent activities"""
        return self.activities[-limit:] if self.activities else []
    
    def clear_activities(self):
        """Clear activity log"""
        self.activities = []