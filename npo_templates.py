# npo_templates.py
import json
import os
from datetime import datetime
import shutil

class TemplateManager:
    """Manage report templates"""
    
    def __init__(self, template_dir='templates'):
        self.template_dir = template_dir
        self.ensure_template_dir()
    
    def ensure_template_dir(self):
        """Ensure template directory exists"""
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
    
    def save_template(self, template_name, config_data, org_data, is_default=False):
        """Save current configuration as template"""
        template = {
            'name': template_name,
            'created_at': datetime.now().isoformat(),
            'is_default': is_default,
            'config': config_data,
            'organization': org_data
        }
        
        filename = f"{template_name.replace(' ', '_')}.json"
        filepath = os.path.join(self.template_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2)
            return True, filepath
        except Exception as e:
            return False, str(e)
    
    def load_template(self, template_name):
        """Load template by name"""
        filename = f"{template_name.replace(' ', '_')}.json"
        filepath = os.path.join(self.template_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                template = json.load(f)
            return True, template
        except FileNotFoundError:
            return False, f"Template '{template_name}' not found"
        except Exception as e:
            return False, str(e)
    
    def list_templates(self):
        """List all available templates"""
        templates = []
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.template_dir, filename), 'r') as f:
                        template = json.load(f)
                    templates.append({
                        'name': template.get('name', filename),
                        'created_at': template.get('created_at'),
                        'is_default': template.get('is_default', False)
                    })
                except:
                    continue
        
        return templates
    
    def delete_template(self, template_name):
        """Delete a template"""
        filename = f"{template_name.replace(' ', '_')}.json"
        filepath = os.path.join(self.template_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, f"Template '{template_name}' deleted"
            else:
                return False, f"Template '{template_name}' not found"
        except Exception as e:
            return False, str(e)
    
    def create_default_templates(self):
        """Create default templates"""
        default_templates = [
            {
                'name': 'Standard NPO Template',
                'config': {
                    'groups': 'standard',
                    'color_theme': 'RB Blue',
                    'include_gujarat': True,
                    'include_ica': True
                },
                'organization': {
                    'type': 'Trust',
                    'category': 'Educational'
                }
            },
            {
                'name': 'Gujarat Trust Template',
                'config': {
                    'groups': 'gujarat',
                    'color_theme': 'Professional (Gray)',
                    'include_gujarat': True,
                    'include_ica': False
                },
                'organization': {
                    'type': 'Public Trust',
                    'category': 'Charitable'
                }
            }
        ]
        
        for template in default_templates:
            self.save_template(
                template['name'],
                template['config'],
                template['organization'],
                is_default=True
            )
    
    def backup_templates(self, backup_path):
        """Backup all templates"""
        try:
            if os.path.exists(self.template_dir):
                backup_file = shutil.make_archive(
                    backup_path,
                    'zip',
                    self.template_dir
                )
                return True, backup_file
            else:
                return False, "Template directory not found"
        except Exception as e:
            return False, str(e)

class ReportPreset:
    """Define report presets"""
    
    PRESETS = {
        'full_compliance': {
            'name': 'Full Compliance Report',
            'sheets': [
                'Balance Sheet',
                'Income & Expenditure',
                'Notes to Accounts',
                'Policies',
                'PPE Schedule',
                'Sch VIII (Guj BS)',
                'Sch IX (Guj IE)',
                'ICAI NPO Schedules',
                'Fund Flow',
                'Receipts & Payments',
                'Compliance Report'
            ],
            'include_notes': True,
            'include_signatures': True,
            'include_compliance': True
        },
        'gujarat_only': {
            'name': 'Gujarat Trust Report',
            'sheets': [
                'Balance Sheet',
                'Income & Expenditure',
                'Sch VIII (Guj BS)',
                'Sch IX (Guj IE)',
                'Asset Register (IAR)'
            ],
            'include_notes': True,
            'include_signatures': True,
            'include_compliance': False
        },
        'quick_report': {
            'name': 'Quick Financials',
            'sheets': [
                'Balance Sheet',
                'Income & Expenditure',
                'Notes to Accounts'
            ],
            'include_notes': False,
            'include_signatures': False,
            'include_compliance': False
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name):
        """Get preset configuration"""
        return cls.PRESETS.get(preset_name)
    
    @classmethod
    def list_presets(cls):
        """List all available presets"""
        return list(cls.PRESETS.keys())