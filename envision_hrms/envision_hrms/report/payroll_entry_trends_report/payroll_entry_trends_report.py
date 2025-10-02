# Copyright (c) 2025, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
import calendar
from frappe import _
from frappe.utils import getdate
import datetime
import erpnext


def execute(filters=None):
    if not filters:
        filters = {}

    # default to current fiscal year if dates not provided
    if not filters.get("from_date") or not filters.get("to_date"):
        fy = erpnext.utils.get_fiscal_year(frappe.utils.nowdate(), True)
        filters.setdefault("from_date", fy[1])
        filters.setdefault("to_date", fy[2])

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    months = _months_between(from_date, to_date)

    columns = _build_columns(months)
    data = _build_data(filters, months)

    return columns, data


def _months_between(start_date, end_date):
    months = []
    cur = datetime.date(start_date.year, start_date.month, 1)
    last = datetime.date(end_date.year, end_date.month, 1)
    while cur <= last:
        label = cur.strftime("%b-%y")  # e.g. May-25
        months.append({"year": cur.year, "month": cur.month, "label": label})
        # increment month
        if cur.month == 12:
            cur = datetime.date(cur.year + 1, 1, 1)
        else:
            cur = datetime.date(cur.year, cur.month + 1, 1)
    return months


def _build_columns(months):
    cols = [
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180},
    ]
    for m in months:
        cols.append({"label": m["label"], "fieldname": f"m_{m['year']}_{m['month']}", "fieldtype": "Float", "precision": 2, "width": 120})
    cols.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Float", "precision": 2, "width": 120})
    return cols


def _build_data(filters, months):
    # aggregate totals by company, branch, year, month
    query_filters = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    }
    
    conditions = ["pe.docstatus = 1", "pe.start_date BETWEEN %(from_date)s AND %(to_date)s"]
    if filters.get("company"):
        conditions.append("pe.company = %(company)s")
        query_filters["company"] = filters.get("company")
    if filters.get("branch"):
        conditions.append("pe.branch = %(branch)s")
        query_filters["branch"] = filters.get("branch")

    condition_sql = " AND ".join(conditions)

    sql = f"""
        SELECT
            IFNULL(pe.company, '') AS company,
            IFNULL(pe.branch, '') AS branch,
            YEAR(pe.start_date) AS year,
            MONTH(pe.start_date) AS month,
            SUM(IFNULL(pe.custom_total_net_salary, 0)) AS total
        FROM `tabPayroll Entry` pe
        WHERE {condition_sql}
        GROUP BY pe.company, pe.branch, YEAR(pe.start_date), MONTH(pe.start_date)
    """

    rows = frappe.db.sql(sql, query_filters, as_dict=1)

    # build lookup
    data_map = {}
    keys = set()
    for r in rows:
        key = (r["company"], r["branch"])
        keys.add(key)
        data_map.setdefault(key, {})
        data_map[key][(r["year"], r["month"])] = float(r["total"] or 0.0)

    # if no results but company filter given, ensure at least branches list from payroll entries or Branch master
    if not keys and filters.get("company"):
        company_branch_rows = frappe.db.sql(
            """
            SELECT DISTINCT company, branch
            FROM `tabPayroll Entry`
            WHERE start_date BETWEEN %(from_date)s AND %(to_date)s
            """,
            query_filters,
            as_dict=1,
        )
        for r in company_branch_rows:
            key = (r.get("company") or "", r.get("branch") or "")
            keys.add(key)
            data_map.setdefault(key, {})

    # prepare final data list
    final = []
    for company, branch in sorted(keys):
        row = {"company": company, "branch": branch or ""}
        total = 0.0
        for m in months:
            val = data_map.get((company, branch), {}).get((m["year"], m["month"]), 0.0)
            field = f"m_{m['year']}_{m['month']}"
            row[field] = round(val, 2)
            total += val
        row["total"] = round(total, 2)
        final.append(row)

    return final

