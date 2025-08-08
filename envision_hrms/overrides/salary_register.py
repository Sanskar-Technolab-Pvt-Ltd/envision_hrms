import frappe

salary_slip = frappe.qb.DocType("Salary Slip")

def get_salary_slips_override(filters, company_currency):
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	payroll_entry = frappe.qb.DocType("Payroll Entry")

	query = (
		frappe.qb.from_(salary_slip)
		.left_join(payroll_entry)
		.on(salary_slip.payroll_entry == payroll_entry.name)
		.select(salary_slip.star)
	)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))

	if filters.get("department"):
		query = query.where(salary_slip.department == filters["department"])

	if filters.get("designation"):
		query = query.where(salary_slip.designation == filters["designation"])

	if filters.get("branch"):
		query = query.where(salary_slip.branch == filters["branch"])

	if filters.get("account"):
		query = query.where(payroll_entry.payment_account == filters["account"])

	salary_slips = query.run(as_dict=1)

	return salary_slips or []

