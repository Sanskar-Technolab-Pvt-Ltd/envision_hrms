# Copyright (c) 2026, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate, add_months, get_first_day, get_last_day, getdate


# ? REPORT EXECUTION
def execute(filters=None):
    validate_filters(filters)
    companies = filters.company
    # MultiSelectList safety
    if isinstance(companies, str):
        companies = frappe.parse_json(companies) or [companies]

    filters.start_date = getdate(filters.from_date)
    filters.end_date = getdate(filters.to_date)

    departments = get_departments_multi_company(companies)

    columns = get_columns(departments)

    data = get_data_multi_company(filters, companies, departments)

    return columns, data

# ? VALIDATION
def validate_filters(filters):

    if not filters.company:
        frappe.throw("Company is required")

    if not filters.from_date or not filters.to_date:
        frappe.throw("From Date and To Date required")

# ? GET ALL DEPARTMENTS FROM SELECTED COMPANIES
def get_departments_multi_company(companies):

    depts = frappe.get_all(
        "Department",
        filters={"company": ["in", companies]},
        pluck="name"
    )

    return sorted(list(set(depts)))

# ? DYNAMIC COLUMNS
def get_columns(departments):
    columns = [
        {
            "label": "Month",
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 140
        }
    ]

    for dept in departments:
        key = frappe.scrub(dept)

        columns.append({
            "label": f"{dept} Gross Salary",
            "fieldname": f"{key}_gross",
            "fieldtype": "Currency",
            "width": 130
        })

        columns.append({
            "label": f"{dept} Net Salary",
            "fieldname": f"{key}_net",
            "fieldtype": "Currency",
            "width": 130
        })

    columns.append({
        "label": "Total Net Salary",
        "fieldname": "total",
        "fieldtype": "Currency",
        "width": 150
    })

    return columns


# ? MAIN DATA LOGIC
def get_data_multi_company(filters, companies, departments):
    final_data = []

    # Fetch ALL salary slips once (performance improvement)
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "company": ["in", companies],
            "start_date": ["between", [filters.start_date, filters.end_date]],
            "docstatus": 1
        },
        fields=[
            "company",
            "start_date",
            "department",
            "gross_pay",
            "net_pay"
        ],
        order_by="company, start_date asc"
    )

    # ? GROUP SLIPS BY COMPANY TO AVOID MULTIPLE LOOPS
    slips_by_company = {}

    for slip in salary_slips:
        slips_by_company.setdefault(slip.company, []).append(slip)

    # ? LOOP THROUGH COMPANIES
    for company in companies:

        # ? COMPANY ROW (GROUP HEADER)
        company_row = {
			"month": company,
			"indent": 0,     
			"is_group": 1    
		}

		# ? INITIALIZE DEPARTMENT COLUMNS TO AVOID KEY ERRORS LATER
        for dept in departments:
            key = frappe.scrub(dept)
            company_row[f"{key}_gross"] = None
            company_row[f"{key}_net"] = None

        company_row["total"] = None

        final_data.append(company_row)

        company_slips = slips_by_company.get(company, [])

        month_map = {}

        # ? ADD: GENERATE MONTHS IN RANGE
        current = get_first_day(filters.start_date)
        end = get_last_day(filters.end_date)

        while current <= end:
            month = formatdate(current, "MMM-yyyy")
            row = init_month_row(month, departments)
            row["indent"] = 1     # child level
            month_map[month] = row
            current = add_months(current, 1)

        # ? PROCESS SALARY SLIPS FOR THIS COMPANY
        for slip in company_slips:

            month = formatdate(slip.start_date, "MMM-yyyy")

            if month not in month_map:
                continue

            dept_key = frappe.scrub(slip.department)

            gross_key = f"{dept_key}_gross"
            net_key = f"{dept_key}_net"

            if gross_key not in month_map[month]:
                continue

            month_map[month][gross_key] += slip.gross_pay
            month_map[month][net_key] += slip.net_pay

            month_map[month]["net_total"] += slip.net_pay
            month_map[month]["total"] = month_map[month]["net_total"]

		# ? ADD MONTH ROWS TO FINAL DATA
        final_data.extend(list(month_map.values()))
              
        # ? for exact month of payroll data 
        # for row in month_map.values():
		# 	# check if any department has value
        #     has_value = False

        #     for dept in departments:
        #         key = frappe.scrub(dept)

        #         if row.get(f"{key}_gross") or row.get(f"{key}_net"):
        #             has_value = True
        #             break

        #     if has_value:
        #         final_data.append(row)

        # ? END OF COMPANY LOOP # ? FINAL FILTER TO REMOVE MONTHS WITHOUT ANY DATA
        final_data = [row for row in final_data if row.get("month")]

    return final_data

# ? HELPER TO INITIALIZE MONTH ROW WITH DEPARTMENTS
def init_month_row(month, departments):
    row = {
        "month": month,
        "gross_total": 0,
        "net_total": 0,
        "total": 0
    }

    for dept in departments:
        key = frappe.scrub(dept)
        row[f"{key}_gross"] = 0
        row[f"{key}_net"] = 0

    return row
