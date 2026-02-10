# # Copyright (c) 2026, Pooja Vadher and contributors
# # For license information, please see license.txt

# ?
import frappe
from frappe import _
from frappe.utils import flt


# EXECUTE
def execute(filters=None):
    filters = filters or {}

    columns, earning_components, deduction_components = get_columns(
        filters,
        grouped=bool(filters.get("consolidate_department"))
    )

    data = get_flat_data(filters, earning_components, deduction_components)

    if not filters.get("consolidate_department"):
        return columns, data

    grouped_data = get_grouped_department_data(data, columns)
    return columns, grouped_data

# ? COLUMNS
def get_columns(filters, grouped=False):

    columns = []

    if grouped:
        columns.append({
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 160,
        })

    columns.extend([
        {"label": "Emp Code", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
    ])

    if not grouped:
        columns.append({
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 140,
        })

    columns.extend([
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 140},
        {"label": "DOJ", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 110},
        {"label": "SSA From Date", "fieldname": "salary_structure_assignment_from_date", "fieldtype": "Date", "width": 110},
        {"label": "Base Salary", "fieldname": "base", "fieldtype": "Currency", "width": 120},
        {"label": "Wage Per Day", "fieldname": "rate_per_day", "fieldtype": "Currency", "width": 120},
    ])

    # Get ONLY Employee Standard Salary components
    # all_earnings = frappe.get_all(
    #     "Salary Detail",
    #     filters={
    #         "parentfield": "earnings",
    #         "parenttype": "Employee Standard Salary"
    #     },
    #     fields=["salary_component"],
    #     distinct=True
    # )
    earning_components = []
    seen = set()

    all_earnings = frappe.get_all(
        "Salary Detail",
        filters={
            "parentfield": "earnings",
            "parenttype": "Employee Standard Salary"
        },
        fields=["salary_component", "idx"],
        order_by="idx asc"
    )

    for e in all_earnings:

        if e.salary_component in seen:
            continue

        comp = frappe.db.get_value(
            "Salary Component",
            e.salary_component,
            ["statistical_component", "do_not_include_in_total"],
            as_dict=True
        )

        if comp and not comp.statistical_component and not comp.do_not_include_in_total:
            earning_components.append(e)
            seen.add(e.salary_component)


    # all_deductions = frappe.get_all(
    #     "Salary Detail",
    #     filters={
    #         "parentfield": "deductions",
    #         "parenttype": "Employee Standard Salary"
    #     },
    #     fields=["salary_component"],
    #     distinct=True
    # )
    deduction_components = []
    seen = set()

    all_deductions = frappe.get_all(
        "Salary Detail",
        filters={
            "parentfield": "deductions",
            "parenttype": "Employee Standard Salary"
        },
        fields=["salary_component", "idx"],
        order_by="idx asc"
    )

    for d in all_deductions:

        if d.salary_component in seen:
            continue

        comp = frappe.db.get_value(
            "Salary Component",
            d.salary_component,
            ["statistical_component", "do_not_include_in_total"],
            as_dict=True
        )

        if comp and not comp.statistical_component and not comp.do_not_include_in_total:
            deduction_components.append(d)
            seen.add(d.salary_component)

    
    

    # earning_components = []
    # deduction_components = []

    # # Filter salary components
    # for e in all_earnings:

    #     comp = frappe.db.get_value(
    #         "Salary Component",
    #         e.salary_component,
    #         ["statistical_component", "do_not_include_in_total"],
    #         as_dict=True
    #     )

    #     if comp and not comp.statistical_component and not comp.do_not_include_in_total:
    #         earning_components.append(e)

    # for d in all_deductions:

    #     comp = frappe.db.get_value(
    #         "Salary Component",
    #         d.salary_component,
    #         ["statistical_component", "do_not_include_in_total"],
    #         as_dict=True
    #     )

    #     if comp and not comp.statistical_component and not comp.do_not_include_in_total:
    #         deduction_components.append(d)

    # Earnings columns
    for e in earning_components:
        columns.append({
            "label": e.salary_component,
            "fieldname": frappe.scrub(e.salary_component),
            "fieldtype": "Currency",
            "width": 120,
        })

    # Gross Pay
    columns.append({
        "label": "Gross Pay",
        "fieldname": "custom_standard_gross_pay",
        "fieldtype": "Currency",
        "width": 130,
    })

    # Deduction columns
    for d in deduction_components:
        columns.append({
            "label": d.salary_component,
            "fieldname": frappe.scrub(d.salary_component),
            "fieldtype": "Currency",
            "width": 120,
        })

    columns.extend([
        {"label": "Total Deductions", "fieldname": "custom_standard_deductions", "fieldtype": "Currency", "width": 130},
        {"label": "Net Pay Salary", "fieldname": "custom_standard_net_pay", "fieldtype": "Currency", "width": 130},
    ])

    return columns, earning_components, deduction_components


# DATA
def get_flat_data(filters, earning_components, deduction_components):

    data = []
    conditions = build_conditions(filters)

    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters=conditions,
        fields=[
            "name", "employee", "employee_name", "department",
            "designation", "base", "rate_per_day",
            "custom_standard_working_days", "from_date"
        ],
        order_by="department, employee"
    )

    for a in assignments:

        doj, branch = frappe.db.get_value(
            "Employee", a.employee, ["date_of_joining", "branch"]
        )

        if filters.get("branch") and branch != filters["branch"]:
            continue

        wage_per_day = a.rate_per_day or (
            a.base / a.custom_standard_working_days
            if a.custom_standard_working_days else 0
        )

        comp_name = frappe.db.get_value(
            "Employee Standard Salary",
            {"salary_structure_assignment": a.name},
            "name"
        )

        comp_doc = frappe.get_doc("Employee Standard Salary", comp_name) if comp_name else None

        row = {
            "department": a.department,
            "employee": a.employee,
            "employee_name": a.employee_name,
            "designation": a.designation,
            "date_of_joining": doj,
            "salary_structure_assignment_from_date": a.from_date,
            "base": a.base,
            "rate_per_day": wage_per_day,
            "custom_standard_gross_pay": comp_doc.total_gross_pay if comp_doc else 0,
            "custom_standard_deductions": comp_doc.total_deductions if comp_doc else 0,
            "custom_standard_net_pay": comp_doc.total_net_pay if comp_doc else 0,
        }

        # initialize dynamic fields
        for e in earning_components:
            row[frappe.scrub(e["salary_component"])] = 0

        for d in deduction_components:
            row[frappe.scrub(d["salary_component"])] = 0

        if comp_doc:

            # earnings
            for e in comp_doc.earnings:
                row[frappe.scrub(e.salary_component)] = e.amount

            # deductions
            for d in comp_doc.deductions:
                row[frappe.scrub(d.salary_component)] = d.amount

        data.append(row)

    return data


# GROUPED VIEW
def get_grouped_department_data(data, columns):
    grouped = {}
    totals_map = {}

    for row in data:
        dept = row.get("department") or _("Not Set")
        grouped.setdefault(dept, [])
        totals_map.setdefault(dept, init_totals(columns))

        row["indent"] = 1
        row["department"] = ""
        grouped[dept].append(row)

        for field in totals_map[dept]:
            totals_map[dept][field] += flt(row.get(field))

    final_data = []

    for dept, rows in grouped.items():
        final_data.append({
            "department": dept,
            "indent": 0,
            "is_group": 1
        })

        final_data.extend(rows)

        total_row = totals_map[dept]
        total_row.update({
            "department": _("Total"),
            "indent": 1
        })

        final_data.append(total_row)

    return final_data


# TOTAL INIT
def init_totals(columns):
    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Currency", "Float", "Int"):
            totals[col["fieldname"]] = 0
    return totals


# FILTER CONDITIONS
def build_conditions(filters):
    conditions = {}

    for f in ["employee", "department", "designation", "company", "currency"]:
        if filters.get(f):
            conditions[f] = filters[f]
            
    docstatus_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
    if filters.get("docstatus"):
        conditions["docstatus"] = docstatus_map[filters["docstatus"]]

    if filters.get("from_date") and filters.get("to_date"):
        conditions["from_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
        conditions["from_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
        conditions["from_date"] = ["<=", filters["to_date"]]

    return conditions
