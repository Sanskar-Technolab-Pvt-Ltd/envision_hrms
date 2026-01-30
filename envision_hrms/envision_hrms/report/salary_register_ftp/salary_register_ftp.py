# Copyright (c) 2026, Pooja Vadher and contributors
# For license information, please see license.txt
import frappe
from frappe.utils import formatdate, add_months, get_first_day, get_last_day, getdate

# ? REPORT EXECUTION
def execute(filters=None):
    validate_filters(filters)

    # ? FETCH PERIOD DATES
    start_date, end_date = get_period_dates(filters.payroll_period)

    # ? SET FILTER DATES
    filters.start_date = start_date
    filters.end_date = end_date

    departments = get_departments(filters.company)
    columns = get_columns(departments)
    data = get_data(filters, departments)

    return columns, data

# ? VALIDATION
def validate_filters(filters):
    if not filters.company:
        frappe.throw("Company is required")
    if not filters.payroll_period:
        frappe.throw("Payroll Period is required")

# ? DYNAMIC DEPARTMENTS
def get_departments(company):
    return frappe.get_all(
        "Department",
        filters={"company": company},
        pluck="name"
    )

# ? DYNAMIC COLUMNS
def get_columns(departments):
    columns = [
        {
            "label": "Month",
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 120
        }
    ]

    for dept in departments:
        columns.append({
            "label": f"{dept} Gross Salary",
            "fieldname": f"{frappe.scrub(dept)}_gross",
            "fieldtype": "Currency",
            "width": 130
        })
        columns.append({
            "label": f"{dept} Net Salary",
            "fieldname": f"{frappe.scrub(dept)}_net",
            "fieldtype": "Currency",
            "width": 130
        })

    columns.extend([
        {
            "label": "Total Net Salary",
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 150
        }
    ])

    return columns


# ? FETCH DATA
def get_data(filters, departments):
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "company": filters.company,
            "start_date": ["between", [filters.start_date, filters.end_date]],
            "docstatus": 1
        },
        fields=[
            "start_date",
            "department",
            "gross_pay",
            "net_pay"
        ],
        order_by="start_date asc"
    )

    month_map = {}

    # ? ADD: GENERATE MONTHS IN RANGE
    current = get_first_day(filters.start_date)
    end = get_last_day(filters.end_date)

    while current <= end:
        month = formatdate(current, "MMM-yyyy")
        month_map[month] = init_month_row(month, departments)
        current = add_months(current, 1)

    # ? PROCESS SALARY SLIPS
    for slip in salary_slips:
        month = formatdate(slip.start_date, "MMM-yyyy")

        dept_key = frappe.scrub(slip.department)

        month_map[month][f"{dept_key}_gross"] += slip.gross_pay
        month_map[month][f"{dept_key}_net"] += slip.net_pay

        month_map[month]["gross_total"] += slip.gross_pay
        month_map[month]["net_total"] += slip.net_pay
        month_map[month]["total"] = (
            month_map[month]["net_total"]
        )

    return list(month_map.values())

# ? HELPERS
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

# ? FETCH PERIOD DATES
def get_period_dates(payroll_period):
    period = frappe.get_doc("Payroll Period", payroll_period)
    return period.start_date, period.end_date
