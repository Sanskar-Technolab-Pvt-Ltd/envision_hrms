import frappe
import json

@frappe.whitelist()
def get_employee_advance_account(employee, company):
    return frappe.db.get_value(
        "Employee Account Defaults",
        {"parent": employee, "company": company},
        "advance_account"
    )

def deduct_advance_limit(self, method):
    employee_doc = frappe.get_doc("Employee", self.employee)
    updated = False

    for row in employee_doc.custom_account_defaults:
        if row.company == self.company and row.advance_account == self.advance_account:
            row.advance_limit = (row.advance_limit or 0) - self.advance_amount
            updated = True
            break

    if updated:
        employee_doc.save(ignore_permissions=True)


def add_advance_limit(self, method):
    employee_doc = frappe.get_doc("Employee", self.employee)
    updated = False

    for row in employee_doc.custom_account_defaults:
        if row.company == self.company and row.advance_account == self.advance_account:
            row.advance_limit = (row.advance_limit or 0) + self.advance_amount
            updated = True
            break

    if updated:
        employee_doc.save(ignore_permissions=True)


def deduct_advance_limit_ec(self, method):
    if self.total_advance_amount:
        employee_doc = frappe.get_doc("Employee", self.employee)
        updated = False

        for row in employee_doc.custom_account_defaults:
            if row.company == self.company and row.advance_account == self.payable_account:
                row.advance_limit = (row.advance_limit or 0) + self.total_advance_amount
                updated = True
                break

        if updated:
            employee_doc.save(ignore_permissions=True)


def add_advance_limit_ec(self, method):
    if self.total_advance_amount:
        employee_doc = frappe.get_doc("Employee", self.employee)
        updated = False

        for row in employee_doc.custom_account_defaults:
            if row.company == self.company and row.advance_account == self.payable_account:
                row.advance_limit = (row.advance_limit or 0) - self.total_advance_amount
                updated = True
                break

        if updated:
            employee_doc.save(ignore_permissions=True)


@frappe.whitelist()
def calculate_totals(doc, method):
    total_earnings = 0
    total_deductions = 0

    for row in doc.earnings:
        total_earnings += row.amount or 0

    for row in doc.deductions:
        total_deductions += row.amount or 0

    doc.total_earnings = total_earnings
    doc.total_deductions = total_deductions


@frappe.whitelist()
def custom_validate_company_and_department(self):
		if self.department:
			company = frappe.db.get_value("Department", self.department, "company")
			if company and self.company != company:
				pass
               
import json

@frappe.whitelist()
def create_advance_permissions(user, employee_id, selected_doctypes, reports_to):
    if isinstance(selected_doctypes, str):
        try:
            selected_doctypes = json.loads(selected_doctypes)
        except json.JSONDecodeError:
            selected_doctypes = [dt.strip() for dt in selected_doctypes.split(",") if dt.strip()]

    if not isinstance(selected_doctypes, list):
        frappe.throw("Invalid input: selected_doctypes must be a list.")

    for dt in selected_doctypes:
        if not frappe.db.exists("DocType", dt):
            frappe.throw(f"Invalid DocType: {dt}")

        if not frappe.db.exists("User Permission", {
            "user": user,
            "allow": "Employee",
            "for_value": employee_id,
            "apply_to_all_doctypes": 0,
            "applicable_for": dt
        }):
            frappe.get_doc({
                "doctype": "User Permission",
                "user": user,
                "allow": "Employee",
                "for_value": employee_id,
                "apply_to_all_doctypes": 0,
                "applicable_for": dt
            }).insert(ignore_permissions=True)
        
    frappe.db.commit()
    user_permission = frappe.get_all("User Permission", 
            filters={
                "user": user,
                "allow": "Employee",
                "for_value": reports_to
            },
            fields=["name", "hide_descendants"]
        )

    if user_permission:
    # Update existing User Permission
        up = frappe.get_doc("User Permission", user_permission[0].name)
        up.hide_descendants = 1
        up.save(ignore_permissions=True)
        frappe.db.commit()
        return f"User Permission {up.name} updated (hide_descendants = 1)."
    else:
        frappe.throw("User Permission not found for the given criteria.")


@frappe.whitelist()
def get_salary_slip_docstatus(payroll_entry):
    docstatus = frappe.db.get_value("Salary Slip", {"payroll_entry": payroll_entry}, "docstatus")
    return docstatus


