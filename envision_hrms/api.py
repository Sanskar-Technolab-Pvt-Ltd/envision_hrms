import frappe

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
            if row.company == self.company and row.advance_account == self.advance_account:
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
            if row.company == self.company and row.advance_account == self.advance_account:
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