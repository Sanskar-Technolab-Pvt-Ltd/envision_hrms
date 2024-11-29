# Copyright (c) 2024, Pooja Vadher and contributors
# For license information, please see license.txt

# Report script for "Salary Increment Register"
import frappe

def execute(filters=None):
    # Columns for the report
    columns = [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "department", "label": "Department", "fieldtype": "Link","options": "Department", "width": 200},
        {"fieldname": "promotion_date", "label": "Promotion Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "current_ctc", "label": "Old CTC", "fieldtype": "Currency", "options": "currency", "width": 150},
        {"fieldname": "revised_ctc", "label": "Revised CTC", "fieldtype": "Currency", "options": "currency", "width": 150},
    ]

    # Validate filters
    if not filters.get("payroll_period"):
        frappe.throw("Please select a Payroll Period to filter Promotion Date.")

    # Fetch Payroll Period details
    payroll_period = frappe.get_doc("Payroll Period", filters["payroll_period"])
    start_date = payroll_period.start_date
    end_date = payroll_period.end_date

    # Build conditions
    conditions = [f"ep.promotion_date BETWEEN '{start_date}' AND '{end_date}'"]
    if filters.get("company"):
        conditions.append(f"e.company = '{filters['company']}'")
    if filters.get("department"):
        conditions.append(f"e.department = '{filters['department']}'")
    if filters.get("employee"):
        conditions.append(f"ep.employee = '{filters['employee']}'")

    where_clause = " AND ".join(conditions)

    # Query data
    data = frappe.db.sql(f"""
        SELECT
            ep.employee,
            ep.employee_name,
            ep.promotion_date,
            ep.current_ctc,
            ep.revised_ctc
        FROM
            `tabEmployee Promotion` ep
        LEFT JOIN
            `tabEmployee` e ON ep.employee = e.name
        WHERE
            {where_clause}
        ORDER BY
            ep.promotion_date DESC
    """, as_dict=True)

    return columns, data


