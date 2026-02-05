# Copyright (c) 2026, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip, _safe_eval, get_salary_component_data
from frappe.utils import (
    ceil, floor, flt, cint, get_first_day,
    get_last_day, getdate, rounded
)
from datetime import date
 
 
class EmployeeStandardSalary(Document):
    def before_save(self):
        # ? TOTAL GROSS PAY, DEDUCTIONS and NET PAY
        total_gross_pay = 0
        total_net_pay = 0
        total_deductions = 0
        total_employer_contributions = 0
        
        # ? Ensure required fields are present
        if not (self.employee and self.salary_structure_assignment):
            return
 
        # * Fetch Salary Structure Assignment
        salary_structure_assignment = frappe.get_doc(
            "Salary Structure Assignment", self.salary_structure_assignment
        )
 
        # ! Skip if Salary Structure not selected
        if not self.salary_structure:
            return
 
        # * Fetch Salary Structure
        self._salary_structure_doc = frappe.get_doc("Salary Structure", self.salary_structure)
 
        # * Setup globals for formula evaluation
        self.whitelisted_globals = {
            "int": int,
            "float": float,
            "long": int,
            "round": round,
            "rounded": rounded,
            "date": date,
            "getdate": getdate,
            "get_first_day": get_first_day,
            "get_last_day": get_last_day,
            "ceil": ceil,
            "floor": floor,
        }
 
        # Clear previous earnings/deductions
        self.earnings = []
        self.deductions = []
        self.employer_contribution = []
 
        # * Prepare data for evaluation
        self.data, self.default_data = self.get_data_for_eval(self.total_gross_pay)
        
        # * Add earnings
        for row in self._salary_structure_doc.get("earnings", []):
            component = self.create_component_row(row, "earnings")
            if component:
                self.append("earnings", component)
                self.data.update({"gross_pay": total_gross_pay})
                # Include statistical components in table but not in totals
                if not component.get("do_not_include_in_total") and not component.get("statistical_component"):
                    total_gross_pay += component.get("amount")
        
        self.data.update({"gross_pay": total_gross_pay})
        
        # * Add deductions
        for row in self._salary_structure_doc.get("deductions", []):
            component = self.create_component_row(row, "deductions")
            if component:
                self.append("deductions", component)
                self.data.update({"gross_pay": total_gross_pay})
                # Include statistical components in table but not in totals
                if not component.get("do_not_include_in_total") and not component.get("statistical_component"):
                    total_deductions += component.get("amount")
 
        self.total_gross_pay = total_gross_pay
        self.total_deductions = total_deductions
        self.total_employer_contribution = total_employer_contributions
        self.total_net_pay = total_gross_pay - total_deductions
        self.ctc = total_gross_pay + total_employer_contributions
 
    def on_update(self):
        # Add comment AFTER save (in on_update)
        if hasattr(self, '_missing_variable_components') and self._missing_variable_components:
            comment_text = "⚠️ Following components set to zero due to missing variables:\n" + "\n".join(self._missing_variable_components)
            self.add_comment("Comment", comment_text)
    
    def get_data_for_eval(self, gross_pay=None):
        # * Create merged dict for salary component evaluation
        data = frappe._dict()
        
        # Initialize gross_pay to 0 if not provided
        if gross_pay:
            data.update({"gross_pay": gross_pay})
        else:
            data.update({"gross_pay": 0})
 
        # * Merge Employee data
        if self.employee:
            try:
                employee = frappe.get_doc("Employee", self.employee).as_dict()
                data.update(employee)
            except frappe.DoesNotExistError:
                frappe.throw(f"Employee record not found for {self.employee}")
 
        # * Merge Salary Structure Assignment data
        if self.salary_structure_assignment:
            try:
                assignment = frappe.get_doc(
                    "Salary Structure Assignment", self.salary_structure_assignment
                ).as_dict()
                data.update(assignment)
            except frappe.DoesNotExistError:
                frappe.throw(f"Salary Structure Assignment not found for {self.salary_structure_assignment}")
 
        # * Merge fields from current document  
        data.update(self.as_dict())
        data.update(SalarySlip.get_component_abbr_map(self))
        
        # Map custom_standard_working_days to calendar_days for formula compatibility
        if data.get("custom_standard_working_days"):
            data["calendar_days"] = data.get("custom_standard_working_days")
            data["total_working_days"] = data.get("custom_standard_working_days")
            data["payment_days"] = data.get("custom_standard_working_days")
 
        # Prepare shallow copy for default data
        default_data = data.copy()
        
        # * Populate abbreviations
        for key in ("earnings", "deductions", "employer_contribution"):
            for d in self.get(key):
                default_data[d.abbr] = d.default_amount or 0
                data[d.abbr] = d.amount or 0
        # * Set fallback defaults
        data.setdefault("leave_without_pay", 0)
        data.setdefault("custom_lop_days", 0)
        data.setdefault("custom_total_arrear_payable", 0)
        data.setdefault("absent_days", 0)
        data.setdefault("custom_penalty_leave_days", 0)
        data.setdefault("custom_overtime", 0)
        
        return data, default_data
 
    def create_component_row(self, struct_row, component_type):
        """
        * Build a component row (earning or deduction) from Salary Structure row
        * Include statistical components in the table
        """
        amount = 0
        missing_variables = []
        
        try:
            # Evaluate condition & formula
            condition = (struct_row.condition or "True").strip()
            formula = (struct_row.formula or "0").strip().replace("\r", "").replace("\n", "")
            
            if _safe_eval(condition, self.whitelisted_globals, self.data):
                amount = flt(
                    _safe_eval(formula, self.whitelisted_globals, self.data),
                    struct_row.precision("amount")
                )
 
        except NameError as e:
            # Extract variable name from error message
            import re
            match = re.search(r"name '(\w+)' is not defined", str(e))
            if match:
                missing_var = match.group(1)
                missing_variables.append(f"{struct_row.salary_component} (missing: {missing_var})")
            amount = 0
            
        except Exception as e:
            frappe.throw(
                f"Error while evaluating the Salary Structure '{self.salary_structure}' at row {struct_row.idx}.\n"
                f"Component: {struct_row.salary_component}\n\n"
                f"Error: {e}\n\n"
                f"Hint: Check formula/condition syntax. Only valid Python expressions are allowed."
            )
        
        # Track missing variables
        if missing_variables:
            if not hasattr(self, '_missing_variable_components'):
                self._missing_variable_components = []
            self._missing_variable_components.extend(missing_variables)
        
        self.default_data[struct_row.abbr] = flt(amount)
        self.data[struct_row.abbr] = flt(amount)
        
        # Handle statistical components with payment days dependency
        if struct_row.statistical_component and struct_row.depends_on_payment_days:
            payment_days_amount = (
                flt(amount) * flt(self.data.get("payment_days", 30)) / cint(self.data.get("total_working_days", 30))
            )
            self.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))
        
        # Skip zero-amount components (based on settings)
        remove_if_zero = frappe.get_value(
            "Salary Component", struct_row.salary_component, "remove_if_zero_valued"
        )
 
        # ! IF CALCULATED AMOUNT IS ZERO AND NOT BASED ON FORMULA,
        # ! USE STATIC AMOUNT DEFINED IN THE SALARY COMPONENT
        if amount == 0 and not struct_row.amount_based_on_formula:
            amount = struct_row.amount
        
        if not (
            amount
            or (struct_row.amount_based_on_formula and amount is not None)
            or (not remove_if_zero and amount is not None)
        ):
            return None
 
        # Compute default_amount with default data
        try:
            default_amount = _safe_eval(
                (struct_row.formula or "0").strip(), self.whitelisted_globals, self.default_data
            )
        except Exception:
            default_amount = 0
        
        # Return final component row - INCLUDE statistical components now
        if not (remove_if_zero and not amount):
            return {
                "salary_component": struct_row.salary_component,
                "abbr": struct_row.abbr,
                "amount": flt(amount),
                "default_amount": flt(default_amount),
                "depends_on_payment_days": struct_row.depends_on_payment_days,
                "precision": struct_row.precision("amount"),
                "statistical_component": struct_row.statistical_component,
                "remove_if_zero_valued": remove_if_zero,
                "amount_based_on_formula": struct_row.amount_based_on_formula,
                "condition": struct_row.condition,
                "variable_based_on_taxable_salary": struct_row.variable_based_on_taxable_salary,
                "is_flexible_benefit": struct_row.is_flexible_benefit,
                "do_not_include_in_total": struct_row.do_not_include_in_total,
                "is_tax_applicable": struct_row.is_tax_applicable,
                "formula": formula
            }