# Copyright (c) 2025, Pooja Vadher and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import flt

import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")
payroll_entry = frappe.qb.DocType("Payroll Entry")

# ? CLEAN ZERO VALUES
def clean_zero_values(row, keep_fields=None):
    keep_fields = keep_fields or []
    for k, v in list(row.items()):
        if k in keep_fields:
            continue
        if isinstance(v, (int, float)) and v == 0:
            row[k] = None

# ? MAIN EXECUTE FUNCTION
def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips)

	# ? GENERATE COLUMNS
	columns = get_columns(earning_types, ded_types)
 
	if filters.get("consolidate_department"):
		dept_col = None
		other_cols = []

		for c in columns:
			if c.get("fieldname") == "department":
				dept_col = c
			else:
				other_cols.append(c)

		if dept_col:
			columns = [dept_col] + other_cols

	# ? UPDATE COLUMN WIDTH BASED ON DATA
	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")
	doj_map = get_employee_doj_map()

	# ? IF NOT CONSOLIDATED
	if not filters.get("consolidate_department"):
		data = []
		for ss in salary_slips:
			row = {
				"salary_slip_id": ss.name,
				"employee": ss.employee,
				"employee_name": ss.employee_name,
				"data_of_joining": doj_map.get(ss.employee),
				"branch": ss.branch,
				"department": ss.department,
				"designation": ss.designation,
				"company": ss.company,
				"start_date": ss.start_date,
				"end_date": ss.end_date,
				"leave_without_pay": ss.leave_without_pay,
				"absent_days": ss.absent_days,
				"payment_days": ss.payment_days,
				"currency": currency or company_currency,
				"total_loan_repayment": ss.total_loan_repayment,
			}

			for e in earning_types:
				row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

			for d in ded_types:
				row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})

			if currency == company_currency:
				row.update(
					{
						"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
						"total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
						"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
					}
				)
			else:
				row.update(
					{
						"gross_pay": ss.gross_pay,
						"total_deduction": ss.total_deduction,
						"net_pay": ss.net_pay,
					}
				)

			data.append(row)

		return columns, data

	# ? IF CONSOLIDATED DEPARTMENT WISE
	grouped_rows = {}
	dept_totals = {}
	shown_dept = set()

	for ss in salary_slips:
		dept = ss.department or _("Not Set")

		grouped_rows.setdefault(dept, [])
		dept_totals.setdefault(dept, {
			"department": _("Total"),
			"employee_name": "",
			"currency": currency or company_currency,
			"leave_without_pay": 0,
			"absent_days": 0,
			"payment_days": 0,
			"gross_pay": 0,
			"total_deduction": 0,
			"net_pay": 0,
			"total_loan_repayment": 0,
		})

		for e in earning_types:
			dept_totals[dept].setdefault(frappe.scrub(e), 0)
		for d in ded_types:
			dept_totals[dept].setdefault(frappe.scrub(d), 0)

		# ? EMPLOYEE ROW
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"data_of_joining": doj_map.get(ss.employee),
			"data_of_joining": doj_map.get(ss.employee),
			"branch": ss.branch,
			"department": "",
			"designation": ss.designation,
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"absent_days": ss.absent_days,
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
			"total_loan_repayment": ss.total_loan_repayment,
   			"indent": 1,
		}

		# ? ADD EARNINGS AND DEDUCTIONS
		for e in earning_types:
			val = flt(ss_earning_map.get(ss.name, {}).get(e))
			row[frappe.scrub(e)] = val
			dept_totals[dept][frappe.scrub(e)] += val

		# ? DEDUCTIONS
		for d in ded_types:
			val = flt(ss_ded_map.get(ss.name, {}).get(d))
			row[frappe.scrub(d)] = val
			dept_totals[dept][frappe.scrub(d)] += val

		gross = flt(ss.gross_pay)
		ded = flt(ss.total_deduction)
		net = flt(ss.net_pay)

		if currency == company_currency:
			gross *= flt(ss.exchange_rate)
			ded *= flt(ss.exchange_rate)
			net *= flt(ss.exchange_rate)

		row.update({
			"gross_pay": gross,
			"total_deduction": ded,
			"net_pay": net,
		})

		# ? ADD TO DEPT TOTALS
		dept_totals[dept]["gross_pay"] += gross
		dept_totals[dept]["total_deduction"] += ded
		dept_totals[dept]["net_pay"] += net
		dept_totals[dept]["leave_without_pay"] += flt(ss.leave_without_pay)
		dept_totals[dept]["absent_days"] += flt(ss.absent_days)
		dept_totals[dept]["payment_days"] += flt(ss.payment_days)
		dept_totals[dept]["total_loan_repayment"] += flt(ss.total_loan_repayment)

		grouped_rows[dept].append(row)
		shown_dept.add(dept)

	# ? BUILD FINAL DATA WITH HEADERS AND TOTALS
	final_data = []

	for dept in grouped_rows:
		# ? DEPT HEADER ROW
		dept_row = {
			"department": dept,
			"is_group": 1,
			"indent": 0,
		}

		# ? CREATE ZERO VALUES FOR NUMERIC COLUMNS
		for col in columns:
			if col.get("fieldtype") in ("Float", "Currency"):
				dept_row[col["fieldname"]] = 0

		clean_zero_values(
			dept_row,
			keep_fields=["department", "indent", "is_group"]
		)

		final_data.append(dept_row)

		# ? EMPLOYEE ROWS
		for row in grouped_rows[dept]:
			row["indent"] = 1
			final_data.append(row)

		# ? TOTAL ROW
		total_row = dept_totals[dept]
		total_row["department"] = _("Total")
		total_row["indent"] = 1

		# ? HIDE EMPLOYEE DETAILS IN TOTAL ROW
		for k in [
			"employee", "employee_name", "data_of_joining",
			"branch", "designation", "company",
			"start_date", "end_date"
		]:
			total_row[k] = None

		clean_zero_values(
			total_row,
			keep_fields=["department", "indent", "currency"]
		)

		final_data.append(total_row)
	
	return columns, final_data

# ? HELPER FUNCTIONS
def get_earning_and_deduction_types(salary_slips):
	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}

	for salary_component in get_salary_components(salary_slips):
		component_type = get_salary_component_type(salary_component)
		salary_component_and_type[_(component_type)].append(salary_component)

	return sorted(salary_component_and_type[_("Earning")]), sorted(salary_component_and_type[_("Deduction")])

# ? UPDATE COLUMN WIDTH BASED ON DATA
def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})

# ? GENERATE COLUMNS
def get_columns(earning_types, ded_types):
	columns = [
		{
			"label": _("Salary Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "data_of_joining",
			"fieldtype": "Date",
			"width": 80,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 100,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 100,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Leave Without Pay"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Float",
			"width": 50,
		},
		{
			"label": _("Absent Days"),
			"fieldname": "absent_days",
			"fieldtype": "Float",
			"width": 50,
		},
		{
			"label": _("Payment Days"),
			"fieldname": "payment_days",
			"fieldtype": "Float",
			"width": 120,
		},
	]

	for earning in earning_types:
		columns.append(
			{
				"label": earning,
				"fieldname": frappe.scrub(earning),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	columns.append(
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	)

	for deduction in ded_types:
		columns.append(
			{
				"label": deduction,
				"fieldname": frappe.scrub(deduction),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	columns.extend(
		[
			{
				"label": _("Loan Repayment"),
				"fieldname": "total_loan_repayment",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Total Deduction"),
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Net Pay"),
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldtype": "Data",
				"fieldname": "currency",
				"options": "Currency",
				"hidden": 1,
			},
		]
	)
	return columns

# ? FETCH SALARY COMPONENTS
def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
		.select(salary_detail.salary_component)
		.distinct()
	).run(pluck=True)

# ? FETCH SALARY COMPONENT TYPE
def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)

# ?	 FETCH SALARY SLIPS BASED ON FILTERS
def get_salary_slips(filters, company_currency):
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

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

	if filters.get("payroll_entry"):
		query = query.where(salary_slip.payroll_entry == filters["payroll_entry"])

	salary_slips = query.run(as_dict=1)

	return salary_slips or []

# ? FETCH EMPLOYEE DOJ MAP
def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)

# ? FETCH SALARY SLIP DETAILS
def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map
