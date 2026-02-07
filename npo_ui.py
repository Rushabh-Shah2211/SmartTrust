# npo_ui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from datetime import datetime
from npo_config import *
from npo_data import DataManager
from npo_excel import ExcelGenerator
from npo_compliance import ComplianceCalculator, ITFormsGenerator
from npo_security import InputValidator
from npo_audit import AuditLogger, UserActivityTracker
from npo_templates import TemplateManager, ReportPreset

class NPOApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1800x1000")
        
        # Initialize managers
        self.audit_logger = AuditLogger()
        self.activity_tracker = UserActivityTracker()
        self.template_manager = TemplateManager()
        self.input_validator = InputValidator()
        
        # Create default templates if none exist
        if not self.template_manager.list_templates():
            self.template_manager.create_default_templates()
        
        # Load Logo if available
        try: 
            root.iconbitmap("rb_logo.ico")
        except: 
            pass

        self._setup_styles()
        self.is_validated = False
        self.current_data_hash = None
        self.progress = None
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.setup_org_tab()
        self.setup_mapping_tab()
        self.setup_schedules_tab()
        self.setup_unit_analysis_tab()
        self.setup_compliance_tab()
        self.setup_10b_tab()
        self.setup_templates_tab()
        self.setup_policies_tab()
        
        # Footer
        f_bar = tk.Frame(root, bg="#2C3E50", height=80)
        f_bar.pack(fill='x', side='bottom')
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(f_bar, mode='indeterminate', length=200)
        self.progress_bar.pack(side='left', padx=20)
        
        # Status label
        self.status_label = tk.Label(f_bar, text="Ready", bg="#2C3E50", fg="white", 
                                   font=("Segoe UI", 9))
        self.status_label.pack(side='left', padx=10)
        
        # Theme Selector
        tk.Label(f_bar, text="Color Theme:", bg="#2C3E50", fg="white", 
                font=("Segoe UI", 10)).pack(side='left', padx=(20, 5))
        self.theme_var = tk.StringVar(value="RB Blue")
        ttk.Combobox(f_bar, textvariable=self.theme_var, 
                    values=list(COLOR_THEMES.keys()), 
                    state="readonly", width=20).pack(side='left')
        
        # Preset selector
        tk.Label(f_bar, text="Report Preset:", bg="#2C3E50", fg="white",
                font=("Segoe UI", 10)).pack(side='left', padx=(20, 5))
        self.preset_var = tk.StringVar(value="full_compliance")
        self.preset_combo = ttk.Combobox(f_bar, textvariable=self.preset_var,
                                        values=ReportPreset.list_presets(),
                                        state="readonly", width=20)
        self.preset_combo.pack(side='left')
        
        self.btn_gen = tk.Button(f_bar, text="🚀 GENERATE FINANCIAL STATEMENTS", 
                  bg="#95a5a6", fg="white", font=("Segoe UI", 12, "bold"), 
                  state="disabled", command=self.start_generation, padx=20)
        self.btn_gen.pack(side='right', padx=20, pady=10)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#ECF0F1")
        style.configure("TNotebook.Tab", padding=[20, 10], font=('Segoe UI', 10, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", "#3498DB")], 
                 foreground=[("selected", "white")])

    def update_status(self, message, is_error=False):
        """Update status label"""
        color = "red" if is_error else "white"
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()

    def start_generation(self):
        """Start generation in separate thread"""
        if not self.is_validated:
            messagebox.showerror("Locked", "Please Validate first.")
            return
        
        # Start progress bar
        self.progress_bar.start()
        self.btn_gen.config(state="disabled", text="Generating...")
        self.update_status("Generating report...")
        
        # Run in separate thread
        thread = threading.Thread(target=self.generate)
        thread.daemon = True
        thread.start()

    def generate(self):
        """Generate reports"""
        try:
            org = {k: v.get() for k, v in self.org_vars.items()}
            pol = self.txt_pol.get("1.0", tk.END)
            tgt = self.unit_var.get()
            theme = COLOR_THEMES[self.theme_var.get()]
            preset = self.preset_var.get()
            
            # Collect data
            tb = self.collect_mapping_data(tgt)
            
            ppe = []
            for i in self.ppe_tree.get_children():
                values = self.ppe_tree.item(i, "values")
                if len(values) >= 7:
                    ppe.append({
                        'Asset Name': values[0],
                        'Gross_Op': values[1],
                        'Additions': values[2],
                        'Deletions': values[3],
                        'Dep_Op': values[4],
                        'Dep_Year': values[5],
                        'Dep_Del': values[6]
                    })
            
            fund = []
            for i in self.fund_tree.get_children():
                values = self.fund_tree.item(i, "values")
                if len(values) >= 5:
                    fund.append({
                        'Fund Name': values[0],
                        'Type': values[1],
                        'Opening': values[2],
                        'Received': values[3],
                        'Utilized': values[4]
                    })
            
            # Get include options
            include_gujarat = self.gujarat_var.get() if hasattr(self, 'gujarat_var') else True
            include_ica = self.ica_var.get() if hasattr(self, 'ica_var') else True
            
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx", 
                filetypes=[("Excel", "*.xlsx")],
                initialfile=f"NPO_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            )
            
            if path:
                eng = ExcelGenerator(org, tb, ppe, fund, pol, theme, 
                                   include_gujarat, include_ica)
                eng.generate(path, preset)
                
                # Log the generation
                self.audit_logger.log_generation(
                    org.get('Name', 'Unknown'),
                    path,
                    {'unit': tgt, 'preset': preset}
                )
                
                # Show success
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Financial statements saved to:\n{path}\n\n" +
                    f"Generated with preset: {preset}"
                ))
                
                # Open file location
                import os
                os.startfile(os.path.dirname(path))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.audit_logger.log_error("generation", str(e), {'preset': preset})
        finally:
            self.root.after(0, self.stop_progress)

    def stop_progress(self):
        """Stop progress bar and update UI"""
        self.progress_bar.stop()
        self.btn_gen.config(state="normal", text="🚀 GENERATE FINANCIAL STATEMENTS")
        self.update_status("Ready")

    def collect_mapping_data(self, target_unit):
        """Collect data from mapping tab"""
        tb = []
        for r in self.map_rows:
            if r['frame'].winfo_exists():
                u = r['w']['unit'].get()
                if target_unit == "Consolidated" or u == target_unit:
                    tb.append({
                        'Ledger Name': r['w']['name'].get(),
                        'Amount_CY': r['w']['cy'].get(),
                        'Amount_PY': r['w']['py'].get(),
                        'Group_Head': r['w']['grp'].get(),
                        'Sub_Group': r['w']['sub'].get(),
                        'Fund_Type': r['w']['fund'].get(),
                        'Unit': u
                    })
        return tb

    def setup_org_tab(self):
        f = ttk.Frame(self.notebook); self.notebook.add(f, text=" 🏢 Organization ")
        self.org_vars = {}
        
        lf = tk.LabelFrame(f, text="Entity Details", font=("Segoe UI", 11, "bold"), 
                          bg="white", padx=20, pady=20)
        lf.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        
        fields = [
            ("Name of Trust/NPO", "Name"),
            ("Trust Reg No.", "RegNo"),
            ("PAN Number", "PAN"),
            ("Date of Signing", "Date"),
            ("Place", "Place"),
            ("Assessment Year", "AY")
        ]
        
        for i, (l, k) in enumerate(fields):
            tk.Label(lf, text=l, bg="white").grid(row=i, column=0, sticky='w', pady=5)
            self.org_vars[k] = ttk.Entry(lf, width=40)
            self.org_vars[k].grid(row=i, column=1, padx=10)
            if k == 'Date':
                self.org_vars[k].insert(0, datetime.now().strftime('%d-%m-%Y'))
            elif k == 'AY':
                current_year = datetime.now().year
                self.org_vars[k].insert(0, f"{current_year}-{current_year+1}")

        tk.Label(lf, text="Defined Units (comma sep):", bg="white").grid(
            row=len(fields), column=0, sticky='w', pady=10)
        self.org_vars['Units'] = ttk.Entry(lf, width=40)
        self.org_vars['Units'].insert(0, "Main Unit")
        self.org_vars['Units'].grid(row=len(fields), column=1, padx=10)

        rf = tk.LabelFrame(f, text="Signatories", font=("Segoe UI", 11, "bold"), 
                          bg="white", padx=20, pady=20)
        rf.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        
        sigs = [
            ("President Name", "President"),
            ("Secretary Name", "Secretary"),
            ("Treasurer Name", "Treasurer"),
            ("Auditor Firm", "Firm"),
            ("Firm Reg No", "FRN"),
            ("Partner Name", "Partner"),
            ("M.No", "MNo")
        ]
        
        for i, (l, k) in enumerate(sigs):
            tk.Label(rf, text=l, bg="white").grid(row=i, column=0, sticky='w', pady=5)
            self.org_vars[k] = ttk.Entry(rf, width=40)
            self.org_vars[k].grid(row=i, column=1, padx=10)

    def setup_mapping_tab(self):
        f = ttk.Frame(self.notebook); self.notebook.add(f, text=" 📊 Ledger Mapping ")
        
        t_bar = tk.Frame(f, bg="#BDC3C7", pady=8)
        t_bar.pack(fill='x')
        
        tk.Button(t_bar, text="📂 Import CSV", command=self.load_csv, 
                 bg="#2980B9", fg="white", font=("Segoe UI", 9, "bold")).pack(side='left', padx=10)
        tk.Button(t_bar, text="➕ Add Row", command=self.add_map_row, bg="white").pack(side='left', padx=5)
        tk.Button(t_bar, text="🗑️ Clear All", command=self.clear_mapping, bg="white").pack(side='left', padx=5)
        tk.Button(t_bar, text="↻ Refresh Units", command=self.update_units, bg="white").pack(side='left', padx=5)
        
        tk.Label(t_bar, text="Filter Unit:", bg="#BDC3C7", font=("Segoe UI", 9, "bold")).pack(side='left', padx=(20,5))
        self.unit_var = tk.StringVar(value="Consolidated")
        self.cmb_unit = ttk.Combobox(t_bar, textvariable=self.unit_var, 
                                    values=["Consolidated", "Main Unit"], 
                                    state="readonly", width=15)
        self.cmb_unit.pack(side='left')
        self.cmb_unit.bind('<<ComboboxSelected>>', lambda e: self.filter_by_unit())
        
        self.lbl_valid = tk.Label(t_bar, text="⚠️ Not Validated", bg="#E74C3C", 
                                fg="white", font=("Segoe UI", 9, "bold"), padx=10)
        self.lbl_valid.pack(side='right', padx=10)
        
        tk.Button(t_bar, text="✅ Validate", command=self.validate, 
                 bg="#2ECC71", fg="white", font=("Segoe UI", 9, "bold")).pack(side='right')
        
        tk.Button(t_bar, text="📈 Data Quality", command=self.show_data_quality, 
                 bg="#9B59B6", fg="white").pack(side='right', padx=5)

        h_frame = tk.Frame(f, bg="#2C3E50", height=30)
        h_frame.pack(fill='x')
        
        self.col_cfg = [
            ("Unit", 15), ("Ledger Name", 35), ("Amt CY", 12), ("Amt PY", 12), 
            ("Group Head", 25), ("Sub Group", 20), ("Fund", 12), ("X", 5)
        ]
        
        for i, (t, w) in enumerate(self.col_cfg):
            tk.Label(h_frame, text=t, fg="white", bg="#2C3E50", 
                    font=("Segoe UI", 9, "bold"), width=w).grid(row=0, column=i, padx=1)

        # Create scrollable frame
        canvas_frame = tk.Frame(f)
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="white")
        sb = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="white")
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.map_rows = []

    def add_map_row(self, data=None):
        r = len(self.map_rows)
        bg = "#f8f9fa" if r%2==0 else "white"
        fr = tk.Frame(self.scroll_frame, bg=bg)
        fr.pack(fill='x', pady=1)
        
        vals = {
            'unit': data.get('Unit', '') if data else '',
            'name': data.get('Ledger Name', '') if data else '',
            'cy': data.get('Amount_CY', 0) if data else 0,
            'py': data.get('Amount_PY', 0) if data else 0,
            'grp': data.get('Group_Head', '') if data else '',
            'sub': data.get('Sub_Group', '') if data else '',
            'fund': data.get('Fund_Type', 'General') if data else 'General'
        }
        
        w = {}
        units = self.get_unit_list()
        w['unit'] = ttk.Combobox(fr, values=units, width=17, state="readonly")
        w['unit'].set(vals['unit'] or (units[0] if units else ''))
        w['unit'].grid(row=0, column=0, padx=1)
        
        w['name'] = tk.Entry(fr, width=47)
        w['name'].insert(0, vals['name'])
        w['name'].grid(row=0, column=1, padx=1)
        
        w['cy'] = tk.Entry(fr, width=14, justify='right')
        w['cy'].insert(0, vals['cy'])
        w['cy'].grid(row=0, column=2, padx=1)
        
        w['py'] = tk.Entry(fr, width=14, justify='right')
        w['py'].insert(0, vals['py'])
        w['py'].grid(row=0, column=3, padx=1)
        
        w['grp'] = ttk.Combobox(fr, values=ALL_GROUPS, width=32, state="readonly")
        w['grp'].set(vals['grp'])
        w['grp'].grid(row=0, column=4, padx=1)
        
        w['sub'] = ttk.Combobox(fr, width=25)
        w['sub'].set(vals['sub'])
        w['sub'].grid(row=0, column=5, padx=1)
        
        def on_grp(e):
            w['sub']['values'] = SUB_GROUP_MAPPING.get(w['grp'].get(), [])
        
        w['grp'].bind("<<ComboboxSelected>>", on_grp)
        if vals['grp']: 
            on_grp(None)
        
        w['fund'] = ttk.Combobox(fr, values=FUND_TYPES, width=14, state="readonly")
        w['fund'].set(vals['fund'])
        w['fund'].grid(row=0, column=6, padx=1)
        
        tk.Button(fr, text="×", fg="red", relief='flat', bg=bg, 
                 command=lambda: self.remove_map_row(fr)).grid(row=0, column=7)
        
        self.map_rows.append({'frame': fr, 'w': w})
        self.activity_tracker.track_activity('add_row', {'row': r})

    def remove_map_row(self, frame):
        """Remove a mapping row"""
        for i, row in enumerate(self.map_rows):
            if row['frame'] == frame:
                self.map_rows.pop(i)
                frame.destroy()
                break

    def clear_mapping(self):
        """Clear all mapping rows"""
        if messagebox.askyesno("Confirm", "Clear all mapping data?"):
            for row in self.map_rows[:]:
                if row['frame'].winfo_exists():
                    row['frame'].destroy()
            self.map_rows = []
            self.is_validated = False
            self.lbl_valid.config(text="⚠️ Not Validated", bg="#E74C3C")
            self.btn_gen.config(state="disabled")

    def filter_by_unit(self):
        """Filter rows by selected unit"""
        unit = self.unit_var.get()
        for row in self.map_rows:
            if row['frame'].winfo_exists():
                row_unit = row['w']['unit'].get()
                if unit == "Consolidated" or row_unit == unit:
                    row['frame'].pack(fill='x', pady=1)
                else:
                    row['frame'].pack_forget()

    def show_data_quality(self):
        """Show data quality analysis"""
        data = self.collect_mapping_data("Consolidated")
        if not data:
            messagebox.showinfo("Data Quality", "No data available for analysis")
            return
        
        metrics = DataManager.analyze_data_quality(data)
        
        quality_window = tk.Toplevel(self.root)
        quality_window.title("Data Quality Analysis")
        quality_window.geometry("400x300")
        
        tk.Label(quality_window, text="📊 Data Quality Metrics", 
                font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        frame = tk.Frame(quality_window)
        frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        metrics_text = f"""
        Total Records: {metrics['total_records']}
        Records with CY Amount: {metrics['records_with_cy']}
        Records with PY Amount: {metrics['records_with_py']}
        Records with Group Head: {metrics['records_with_group']}
        Total CY Amount: ₹{metrics['total_cy_amount']:,.2f}
        Total PY Amount: ₹{metrics['total_py_amount']:,.2f}
        """
        
        tk.Label(frame, text=metrics_text, justify='left', 
                font=("Consolas", 10)).pack()
        
        quality_score = (metrics['records_with_group'] / metrics['total_records']) * 100
        status = "✓ GOOD" if quality_score > 80 else "⚠️ NEEDS IMPROVEMENT"
        color = "green" if quality_score > 80 else "orange"
        
        tk.Label(frame, text=f"\nData Quality Score: {quality_score:.1f}% ({status})", 
                fg=color, font=("Segoe UI", 10, "bold")).pack(pady=10)

    def get_unit_list(self):
        """Get list of units from organization data"""
        units_str = self.org_vars.get('Units', '').get() if self.org_vars.get('Units') else "Main Unit"
        units = [u.strip() for u in units_str.split(',') if u.strip()]
        
        # Always include "Consolidated" and "Main Unit"
        all_units = ["Consolidated"]
        all_units.extend(units)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_units = []
        for unit in all_units:
            if unit not in seen:
                seen.add(unit)
                unique_units.append(unit)
        
        return unique_units

    def update_units(self):
        """Update unit dropdowns with current unit list"""
        units = self.get_unit_list()
        
        # Update unit dropdown in mapping tab
        self.cmb_unit['values'] = units
        
        # Update unit analysis tab dropdown
        if hasattr(self, 'unit_analysis_cmb'):
            self.unit_analysis_cmb['values'] = [u for u in units if u != "Consolidated"]

    def load_csv(self):
        """Load trial balance from CSV file"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Use DataManager to load and validate data
            data, error = DataManager.load_tb(filename)
            
            if error:
                messagebox.showerror("Load Error", error)
                return
            
            if not data:
                messagebox.showwarning("Warning", "No data found in file")
                return
            
            # Clear existing rows
            self.clear_mapping()
            
            # Add new rows
            for item in data:
                self.add_map_row(item)
            
            # Update units from loaded data
            units = set(row.get('Unit', 'Main Unit') for row in data)
            units_str = ', '.join(units)
            if 'Units' in self.org_vars:
                self.org_vars['Units'].delete(0, tk.END)
                self.org_vars['Units'].insert(0, units_str)
            
            # Refresh unit dropdowns
            self.update_units()
            
            # Log the activity
            self.audit_logger.log_generation(
                self.org_vars.get('Name', tk.StringVar(value='Unknown')).get(),
                filename,
                {'rows_loaded': len(data)}
            )
            
            self.activity_tracker.track_activity('load_csv', {
                'filename': filename,
                'rows': len(data)
            })
            
            messagebox.showinfo("Success", f"Loaded {len(data)} records from {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            self.audit_logger.log_error("file_load", str(e), {'filename': filename})

    def setup_unit_analysis_tab(self):
        """New tab for unit-wise analysis"""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text=" 📈 Unit Analysis ")
        
        # Control panel
        control_frame = tk.Frame(f, bg="#ECF0F1", padx=20, pady=10)
        control_frame.pack(fill='x')
        
        tk.Label(control_frame, text="Select Unit:", bg="#ECF0F1").pack(side='left')
        self.unit_analysis_var = tk.StringVar()
        self.unit_analysis_cmb = ttk.Combobox(control_frame, 
                                             textvariable=self.unit_analysis_var,
                                             values=self.get_unit_list(),
                                             state="readonly", width=20)
        self.unit_analysis_cmb.pack(side='left', padx=10)
        
        tk.Button(control_frame, text="Generate Unit Report",
                 command=self.generate_unit_report, bg="#3498DB", fg="white").pack(side='left', padx=5)
        
        tk.Button(control_frame, text="Compare All Units",
                 command=self.compare_all_units, bg="#9B59B6", fg="white").pack(side='left', padx=5)
        
        # Results frame
        results_frame = tk.Frame(f, padx=20, pady=10)
        results_frame.pack(fill='both', expand=True)
        
        # Treeview for unit results
        self.unit_tree = ttk.Treeview(results_frame, 
                                     columns=("Metric", "Value", "Percentage"),
                                     show="headings", height=15)
        
        self.unit_tree.heading("Metric", text="Metric")
        self.unit_tree.column("Metric", width=300)
        self.unit_tree.heading("Value", text="Value (₹)")
        self.unit_tree.column("Value", width=150, anchor="e")
        self.unit_tree.heading("Percentage", text="% of Total")
        self.unit_tree.column("Percentage", width=100, anchor="e")
        
        self.unit_tree.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", 
                                 command=self.unit_tree.yview)
        self.unit_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def generate_unit_report(self):
        """Generate report for selected unit"""
        unit = self.unit_analysis_var.get()
        if not unit:
            messagebox.showwarning("Warning", "Please select a unit")
            return
        
        # Clear tree
        for item in self.unit_tree.get_children():
            self.unit_tree.delete(item)
        
        # Get unit data
        data = self.collect_mapping_data(unit)
        if not data:
            self.unit_tree.insert("", "end", values=("No data available", "", ""))
            return
        
        # Calculate metrics
        income = sum(r.get('Amount_CY', 0) for r in data 
                    if r.get('Group_Head') in PL_INCOME)
        expenses = sum(r.get('Amount_CY', 0) for r in data 
                      if r.get('Group_Head') in PL_EXPENSE)
        surplus = income - expenses
        
        # Get consolidated totals for comparison
        consolidated = self.collect_mapping_data("Consolidated")
        total_income = sum(r.get('Amount_CY', 0) for r in consolidated 
                          if r.get('Group_Head') in PL_INCOME)
        total_expenses = sum(r.get('Amount_CY', 0) for r in consolidated 
                            if r.get('Group_Head') in PL_EXPENSE)
        
        # Insert metrics
        self.unit_tree.insert("", "end", values=("INCOME", f"₹{income:,.2f}", 
                                               f"{(income/total_income*100 if total_income>0 else 0):.1f}%"))
        self.unit_tree.insert("", "end", values=("EXPENSES", f"₹{expenses:,.2f}", 
                                               f"{(expenses/total_expenses*100 if total_expenses>0 else 0):.1f}%"))
        self.unit_tree.insert("", "end", values=("SURPLUS/DEFICIT", f"₹{surplus:,.2f}", ""))
        
        # Program expenses ratio
        prog_exp = sum(r.get('Amount_CY', 0) for r in data 
                      if r.get('Group_Head') == 'Programme Expenses')
        prog_ratio = (prog_exp/expenses*100) if expenses > 0 else 0
        self.unit_tree.insert("", "end", values=("Program Expense Ratio", 
                                               f"{prog_ratio:.1f}%", ""))

    def compare_all_units(self):
        """Compare all units"""
        units = self.get_unit_list()
        if not units:
            messagebox.showinfo("Info", "No units defined")
            return
        
        # Create comparison window
        compare_window = tk.Toplevel(self.root)
        compare_window.title("Unit Comparison")
        compare_window.geometry("800x500")
        
        # Create treeview
        tree = ttk.Treeview(compare_window, 
                           columns=("Unit", "Income", "Expenses", "Surplus", "% Income"),
                           show="headings", height=20)
        
        tree.heading("Unit", text="Unit")
        tree.column("Unit", width=150)
        tree.heading("Income", text="Income (₹)")
        tree.column("Income", width=150, anchor="e")
        tree.heading("Expenses", text="Expenses (₹)")
        tree.column("Expenses", width=150, anchor="e")
        tree.heading("Surplus", text="Surplus (₹)")
        tree.column("Surplus", width=150, anchor="e")
        tree.heading("% Income", text="% of Total Income")
        tree.column("% Income", width=100, anchor="e")
        
        tree.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Calculate totals
        consolidated = self.collect_mapping_data("Consolidated")
        total_income = sum(r.get('Amount_CY', 0) for r in consolidated 
                          if r.get('Group_Head') in PL_INCOME)
        
        # Add data for each unit
        for unit in units:
            data = self.collect_mapping_data(unit)
            income = sum(r.get('Amount_CY', 0) for r in data 
                        if r.get('Group_Head') in PL_INCOME)
            expenses = sum(r.get('Amount_CY', 0) for r in data 
                          if r.get('Group_Head') in PL_EXPENSE)
            surplus = income - expenses
            income_pct = (income/total_income*100) if total_income > 0 else 0
            
            tree.insert("", "end", values=(
                unit,
                f"{income:,.2f}",
                f"{expenses:,.2f}",
                f"{surplus:,.2f}",
                f"{income_pct:.1f}%"
            ))
        
        # Add total row
        total_expenses = sum(r.get('Amount_CY', 0) for r in consolidated 
                            if r.get('Group_Head') in PL_EXPENSE)
        total_surplus = total_income - total_expenses
        
        tree.insert("", "end", values=(
            "TOTAL/CONSOLIDATED",
            f"{total_income:,.2f}",
            f"{total_expenses:,.2f}",
            f"{total_surplus:,.2f}",
            "100.0%"
        ))

    def setup_compliance_tab(self):
        """Tab for compliance checking"""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text=" ✅ Compliance ")
        
        # Options frame
        options_frame = tk.Frame(f, padx=20, pady=10)
        options_frame.pack(fill='x')
        
        self.gujarat_var = tk.BooleanVar(value=True)
        self.ica_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(options_frame, text="Include Gujarat Trust Act Formats", 
                      variable=self.gujarat_var, font=("Segoe UI", 10)).pack(anchor='w')
        tk.Checkbutton(options_frame, text="Include ICAI NPO Guidance Schedules", 
                      variable=self.ica_var, font=("Segoe UI", 10)).pack(anchor='w')
        
        # Button frame
        button_frame = tk.Frame(f, padx=20, pady=10)
        button_frame.pack(fill='x')
        
        tk.Button(button_frame, text="Run Full Compliance Check", 
                 command=self.run_compliance_check, bg="#2ECC71", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Generate Form 10B", 
                 command=self.generate_form_10b, bg="#3498DB", fg="white").pack(side='left', padx=5)
        
        tk.Button(button_frame, text="View Compliance Checklist", 
                 command=self.show_compliance_checklist, bg="#9B59B6", fg="white").pack(side='left', padx=5)
        
        # Results frame
        results_frame = tk.Frame(f, padx=20, pady=10)
        results_frame.pack(fill='both', expand=True)
        
        # Text widget for results
        self.compliance_text = scrolledtext.ScrolledText(results_frame, 
                                                       wrap=tk.WORD, 
                                                       width=80, 
                                                       height=20,
                                                       font=("Consolas", 10))
        self.compliance_text.pack(fill='both', expand=True)

    def run_compliance_check(self):
        """Run comprehensive compliance check"""
        data = self.collect_mapping_data("Consolidated")
        if not data:
            messagebox.showwarning("Warning", "No data available for compliance check")
            return
        
        # Clear text
        self.compliance_text.delete(1.0, tk.END)
        
        # Calculate totals
        income_total = sum(r.get('Amount_CY', 0) for r in data 
                          if r.get('Group_Head') in PL_INCOME)
        expense_total = sum(r.get('Amount_CY', 0) for r in data 
                           if r.get('Group_Head') in PL_EXPENSE)
        
        # Get PPE data
        ppe_data = []
        for i in self.ppe_tree.get_children():
            values = self.ppe_tree.item(i, "values")
            if len(values) >= 7:
                ppe_data.append({
                    'Asset Name': values[0],
                    'Additions': values[2]
                })
        
        # Generate compliance report
        report = ComplianceCalculator.generate_compliance_report(
            data, income_total, expense_total, ppe_data
        )
        
        # Display report
        self.compliance_text.insert(tk.END, "="*60 + "\n")
        self.compliance_text.insert(tk.END, "COMPLIANCE STATUS REPORT\n")
        self.compliance_text.insert(tk.END, "="*60 + "\n\n")
        
        # Section 11
        sec11 = report.get('section_11', {})
        self.compliance_text.insert(tk.END, "INCOME TAX ACT (SECTION 11)\n")
        self.compliance_text.insert(tk.END, "-"*40 + "\n")
        self.compliance_text.insert(tk.END, f"Total Income: ₹{sec11.get('total_income',0):,.2f}\n")
        self.compliance_text.insert(tk.END, f"Total Application: ₹{sec11.get('total_application',0):,.2f}\n")
        self.compliance_text.insert(tk.END, f"Required (85%): ₹{sec11.get('required_application',0):,.2f}\n")
        
        if sec11.get('compliance_85_percent'):
            self.compliance_text.insert(tk.END, "✓ COMPLIANT with 85% application requirement\n")
        else:
            self.compliance_text.insert(tk.END, f"⚠️ SHORTFALL: ₹{abs(sec11.get('shortfall_excess',0)):,.2f}\n")
        
        self.compliance_text.insert(tk.END, "\n")
        
        # Gujarat Compliance
        guj = report.get('gujarat_compliance', {})
        self.compliance_text.insert(tk.END, "GUJARAT TRUST ACT\n")
        self.compliance_text.insert(tk.END, "-"*40 + "\n")
        
        if guj.get('issues'):
            self.compliance_text.insert(tk.END, "⚠️ Issues found:\n")
            for issue in guj.get('issues', [])[:3]:
                self.compliance_text.insert(tk.END, f"  • {issue}\n")
        else:
            self.compliance_text.insert(tk.END, "✓ All requirements met\n")
        
        self.compliance_text.insert(tk.END, f"Forms required: {', '.join(guj.get('forms_required', []))}\n")
        
        self.compliance_text.insert(tk.END, "\n")
        
        # Log the check
        self.audit_logger.log_compliance_check("full", report)

    def generate_form_10b(self):
        """Generate Form 10B preview"""
        data = self.collect_mapping_data("Consolidated")
        if not data:
            return
        
        ay = self.org_vars.get('AY', '').get() if self.org_vars.get('AY') else '2024-25'
        form = ITFormsGenerator.prepare_form_10b(data, ay)
        
        # Show form preview
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Form 10B Preview")
        preview_window.geometry("600x400")
        
        tk.Label(preview_window, text="FORM 10B PREVIEW", 
                font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        text = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD, 
                                       width=70, height=20)
        text.pack(fill='both', expand=True, padx=20, pady=10)
        
        text.insert(tk.END, f"Form: {form['form_name']}\n")
        text.insert(tk.END, f"Assessment Year: {form['assessment_year']}\n")
        text.insert(tk.END, "\nSections:\n")
        
        for section, title in form['sections'].items():
            text.insert(tk.END, f"{section}. {title}\n")
        
        text.insert(tk.END, "\nNote: Complete form will be generated in Excel.")

    def show_compliance_checklist(self):
        """Show compliance checklist"""
        checklist_window = tk.Toplevel(self.root)
        checklist_window.title("Compliance Checklist")
        checklist_window.geometry("800x600")
        
        notebook = ttk.Notebook(checklist_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        for area, items in COMPLIANCE_CHECKLISTS.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=area)
            
            # Create checklist
            for i, item in enumerate(items):
                var = tk.BooleanVar()
                cb = tk.Checkbutton(frame, text=item, variable=var, 
                                   font=("Segoe UI", 10), anchor='w')
                cb.pack(fill='x', padx=20, pady=2)
                
                # Store variable for later use
                if not hasattr(frame, 'check_vars'):
                    frame.check_vars = []
                frame.check_vars.append((var, item))

    def setup_templates_tab(self):
        """Tab for template management"""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text=" 📁 Templates ")
        
        # Left panel - Template list
        left_frame = tk.Frame(f)
        left_frame.pack(side='left', fill='y', padx=20, pady=20)
        
        tk.Label(left_frame, text="Available Templates", 
                font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=(0, 10))
        
        # Listbox for templates
        self.template_listbox = tk.Listbox(left_frame, width=30, height=15,
                                          font=("Segoe UI", 10))
        self.template_listbox.pack(fill='y', expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(left_frame)
        scrollbar.pack(side='right', fill='y')
        self.template_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.template_listbox.yview)
        
        # Refresh button
        tk.Button(left_frame, text="Refresh List", 
                 command=self.refresh_template_list).pack(pady=10)
        
        # Right panel - Template operations
        right_frame = tk.Frame(f)
        right_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)
        
        # Template name entry
        tk.Label(right_frame, text="Template Name:", 
                font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        
        self.template_name_var = tk.StringVar()
        tk.Entry(right_frame, textvariable=self.template_name_var, 
                width=40).pack(anchor='w', pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill='x', pady=10)
        
        tk.Button(button_frame, text="💾 Save Current as Template", 
                 command=self.save_as_template, bg="#3498DB", fg="white",
                 width=25).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="📂 Load Selected Template", 
                 command=self.load_template, bg="#2ECC71", fg="white",
                 width=25).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="🗑️ Delete Selected", 
                 command=self.delete_template, bg="#E74C3C", fg="white",
                 width=25).pack(side='left', padx=5)
        
        # Template info
        self.template_info_text = scrolledtext.ScrolledText(right_frame, 
                                                          wrap=tk.WORD, 
                                                          width=60, 
                                                          height=15,
                                                          font=("Consolas", 9))
        self.template_info_text.pack(fill='both', expand=True, pady=10)
        
        # Load templates initially
        self.refresh_template_list()

    def refresh_template_list(self):
        """Refresh template list"""
        self.template_listbox.delete(0, tk.END)
        templates = self.template_manager.list_templates()
        
        for template in templates:
            name = template.get('name', 'Unnamed')
            default = " (Default)" if template.get('is_default') else ""
            self.template_listbox.insert(tk.END, f"{name}{default}")

    def save_as_template(self):
        """Save current configuration as template"""
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showwarning("Warning", "Please enter template name")
            return
        
        # Collect current configuration
        config_data = {
            'theme': self.theme_var.get(),
            'preset': self.preset_var.get(),
            'include_gujarat': self.gujarat_var.get() if hasattr(self, 'gujarat_var') else True,
            'include_ica': self.ica_var.get() if hasattr(self, 'ica_var') else True
        }
        
        # Collect organization data
        org_data = {k: v.get() for k, v in self.org_vars.items()}
        
        # Save template
        success, result = self.template_manager.save_template(
            template_name, config_data, org_data
        )
        
        if success:
            messagebox.showinfo("Success", f"Template '{template_name}' saved successfully")
            self.refresh_template_list()
            self.template_name_var.set("")  # Clear the entry
        else:
            messagebox.showerror("Error", f"Failed to save template: {result}")

    def load_template(self):
        """Load selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        template_name = self.template_listbox.get(selection[0]).split(" (")[0]
        
        success, template = self.template_manager.load_template(template_name)
        if not success:
            messagebox.showerror("Error", template)  # template contains error message
            return
        
        # Show template info
        self.template_info_text.delete(1.0, tk.END)
        self.template_info_text.insert(tk.END, f"Template: {template['name']}\n")
        self.template_info_text.insert(tk.END, f"Created: {template['created_at']}\n")
        self.template_info_text.insert(tk.END, f"Default: {'Yes' if template['is_default'] else 'No'}\n")
        self.template_info_text.insert(tk.END, "\nConfiguration:\n")
        
        import json
        self.template_info_text.insert(tk.END, 
                                      json.dumps(template['config'], indent=2))
        
        # Ask if user wants to apply
        if messagebox.askyesno("Load Template", 
                              f"Apply template '{template_name}' to current configuration?"):
            self.apply_template(template)

    def apply_template(self, template):
        """Apply template configuration"""
        config = template['config']
        org = template['organization']
        
        # Apply theme
        if 'theme' in config:
            self.theme_var.set(config['theme'])
        
        # Apply preset
        if 'preset' in config:
            self.preset_var.set(config['preset'])
        
        # Apply organization data
        for key, value in org.items():
            if key in self.org_vars:
                self.org_vars[key].delete(0, tk.END)
                self.org_vars[key].insert(0, value)
        
        messagebox.showinfo("Success", "Template applied successfully")

    def delete_template(self):
        """Delete selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        template_name = self.template_listbox.get(selection[0]).split(" (")[0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete template '{template_name}'?"):
            success, message = self.template_manager.delete_template(template_name)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_template_list()
            else:
                messagebox.showerror("Error", message)

    def setup_schedules_tab(self):
        f = ttk.Frame(self.notebook); self.notebook.add(f, text=" 📅 Schedules ")
        # PPE
        lf1 = tk.LabelFrame(f, text="Fixed Assets Schedule", padx=10, pady=10)
        lf1.pack(fill='both', expand=True, padx=10, pady=5)
        c = ["Asset Name", "Gross_Op", "Additions", "Deletions", "Dep_Op", "Dep_Year", "Dep_Del"]
        self.ppe_tree = self._create_tree(lf1, c)
        btn_frame = tk.Frame(lf1)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Add Asset", 
                 command=lambda: self.ppe_tree.insert('', 'end', values=("New Asset",0,0,0,0,0,0))).pack(side='left')
        tk.Button(btn_frame, text="Delete Selected", 
                 command=lambda: self.ppe_tree.delete(*self.ppe_tree.selection())).pack(side='left', padx=5)
        
        # Funds
        lf2 = tk.LabelFrame(f, text="Funds Movement", padx=10, pady=10)
        lf2.pack(fill='both', expand=True, padx=10, pady=5)
        fc = ["Fund Name", "Type", "Opening", "Received", "Utilized"]
        self.fund_tree = self._create_tree(lf2, fc)
        btn_frame2 = tk.Frame(lf2)
        btn_frame2.pack(fill='x', pady=5)
        tk.Button(btn_frame2, text="Add Fund", 
                 command=lambda: self.fund_tree.insert('', 'end', values=("New Fund","Restricted",0,0,0))).pack(side='left')
        tk.Button(btn_frame2, text="Delete Selected", 
                 command=lambda: self.fund_tree.delete(*self.fund_tree.selection())).pack(side='left', padx=5)

    def setup_10b_tab(self):
        f = ttk.Frame(self.notebook); self.notebook.add(f, text=" 📋 10B/BB Calculator ")
        mf = tk.Frame(f, bg="white", padx=30, pady=30); mf.pack(fill='both', expand=True)
        tk.Label(mf, text="Draft Computation of Income (Sec 11)", 
                font=("Segoe UI", 16, "bold"), bg="white", fg="#2C3E50").pack(pady=15)
        
        self.calc_tree = ttk.Treeview(mf, columns=("Particulars", "Amount"), show="headings", height=15)
        self.calc_tree.heading("Particulars", text="Particulars")
        self.calc_tree.column("Particulars", width=500)
        self.calc_tree.heading("Amount", text="Amount (Rs.)")
        self.calc_tree.column("Amount", width=200, anchor="e")
        self.calc_tree.pack(fill='both', expand=True, pady=10)
        
        tk.Button(mf, text="🔄 Refresh Calculation", command=self.refresh_10b, 
                 bg="#3498DB", fg="white", font=("Segoe UI", 10)).pack(pady=15)

    def setup_policies_tab(self):
        f = ttk.Frame(self.notebook); self.notebook.add(f, text=" 📝 Policies ")
        self.txt_pol = tk.Text(f, font=("Consolas", 10))
        self.txt_pol.pack(fill='both', expand=True, padx=20, pady=20)
        self.txt_pol.insert(tk.END, DEFAULT_POLICIES)
        
        # Add save/load buttons
        btn_frame = tk.Frame(f)
        btn_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Button(btn_frame, text="Save Policies", 
                 command=self.save_policies).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Load Policies", 
                 command=self.load_policies).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Reset to Default", 
                 command=self.reset_policies).pack(side='left', padx=5)

    def save_policies(self):
        """Save policies to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.txt_pol.get("1.0", tk.END))
            messagebox.showinfo("Success", f"Policies saved to {filename}")

    def load_policies(self):
        """Load policies from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'r') as f:
                content = f.read()
            self.txt_pol.delete("1.0", tk.END)
            self.txt_pol.insert(tk.END, content)
            messagebox.showinfo("Success", f"Policies loaded from {filename}")

    def reset_policies(self):
        """Reset policies to default"""
        if messagebox.askyesno("Confirm", "Reset policies to default?"):
            self.txt_pol.delete("1.0", tk.END)
            self.txt_pol.insert(tk.END, DEFAULT_POLICIES)

    def _create_tree(self, p, c):
        t = ttk.Treeview(p, columns=c, show='headings', height=8)
        for col in c: 
            t.heading(col, text=col)
            t.column(col, width=100)
        t.pack(fill='both', expand=True)
        
        def edit(event):
            item = t.selection()[0]
            col_idx = int(t.identify_column(event.x).replace('#', ''))-1
            old = t.item(item, 'values')[col_idx]
            
            top = tk.Toplevel(self.root)
            top.geometry("300x150")
            top.title(f"Edit {c[col_idx]}")
            
            tk.Label(top, text=f"Edit {c[col_idx]}:").pack(pady=10)
            e = tk.Entry(top, width=30)
            e.insert(0, old)
            e.pack(pady=10)
            e.focus_set()
            
            def save(x=None):
                vals = list(t.item(item, 'values'))
                vals[col_idx] = e.get()
                t.item(item, values=vals)
                top.destroy()
            
            top.bind('<Return>', save)
            tk.Button(top, text="Save", command=save, bg="#2ECC71", fg="white").pack(pady=10)
        
        t.bind("<Double-1>", edit)
        return t

    def refresh_10b(self):
        inc = 0; rev_exp = 0; cap_exp = 0
        u = self.unit_var.get()
        
        # Revenue Exp & Income
        data = self.collect_mapping_data(u)
        for r in data:
            try:
                v = float(r.get('Amount_CY', 0))
                g = r.get('Group_Head', '')
                if g in PL_INCOME: inc += v
                if g in PL_EXPENSE and g != 'Depreciation': rev_exp += v
            except: pass
        
        # Capital Exp
        for child in self.ppe_tree.get_children():
            try: 
                cap_exp += float(self.ppe_tree.item(child, 'values')[2])
            except: pass
            
        ded = inc * 0.15
        tot_app = rev_exp + cap_exp
        
        rows = [
            ("A. Total Income as per P&L", inc),
            ("B. 15% Accumulation allowed (15% of A)", ded),
            ("C. Application - Revenue Expenditure (Excl. Dep)", rev_exp),
            ("D. Application - Capital Expenditure (Additions)", cap_exp),
            ("E. Total Application (C + D)", tot_app),
            ("F. Surplus / (Shortfall) [A - B - E]", inc - ded - tot_app),
            ("G. Compliance with 85% Rule", "✓ Yes" if tot_app >= inc*0.85 else "✗ No")
        ]
        
        for i in self.calc_tree.get_children(): 
            self.calc_tree.delete(i)
        
        for r in rows:
            if isinstance(r[1], (int, float)):
                self.calc_tree.insert('', 'end', values=(r[0], f"₹{r[1]:,.2f}"))
            else:
                self.calc_tree.insert('', 'end', values=(r[0], r[1]))

    def validate(self):
        """Validate the trial balance"""
        try:
            data = self.collect_mapping_data(self.unit_var.get())
            
            # Validate data structure
            is_valid, message = DataManager.validate_tb_data(data)
            if not is_valid:
                messagebox.showerror("Validation Error", message)
                return
            
            # Perform accounting validation
            assets, liab, inc, exp = 0, 0, 0, 0
            u = self.unit_var.get()
            
            for r in data:
                try:
                    v = float(r.get('Amount_CY', 0))
                    g = r.get('Group_Head', '')
                    
                    if g in BS_ASSETS: assets += v
                    elif g in BS_LIABILITIES: liab += v
                    elif g in PL_INCOME: inc += v
                    elif g in PL_EXPENSE: exp += v
                except ValueError:
                    pass
            
            diff = assets - (liab + (inc - exp))
            
            if abs(diff) < 1:
                self.lbl_valid.config(text="✅ VALIDATED", bg="#2ECC71")
                self.is_validated = True
                self.btn_gen.config(state="normal", bg="#28a745")
                
                # Log successful validation
                self.audit_logger.log_validation(
                    self.current_data_hash,
                    (True, "Validation successful"),
                    self.unit_var.get()
                )
                
                messagebox.showinfo("Success", "Validation Successful!")
            else:
                self.lbl_valid.config(text=f"❌ DIFF: {diff:,.2f}", bg="#E74C3C")
                self.is_validated = False
                self.btn_gen.config(state="disabled", bg="#95a5a6")
                messagebox.showwarning("Error", 
                                      f"Balance Sheet not matched.\nDiff: ₹{diff:,.2f}")
                
        except Exception as e:
            messagebox.showerror("Validation Error", str(e))
            self.audit_logger.log_error("validation", str(e), None)