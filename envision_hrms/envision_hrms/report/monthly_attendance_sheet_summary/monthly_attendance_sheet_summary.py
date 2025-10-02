# Copyright (c) 2025, Pooja Vadher and contributors
# For license information, please see license.txt


import frappe
from frappe import _
import calendar
from frappe.utils import add_days, date_diff, flt, getdate  # type: ignore


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)

    # Apply grouping if group_by filter is selected
    if filters.get("group_by"):
        data = apply_grouping(data, filters.get("group_by"))

    return columns, data


def get_columns(filters=None):
    # Base columns without department, designation, branch
    columns = [
        {
            "label": _("Employee ID"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 100,
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Date of Joining"),
            "fieldname": "date_of_joining",
            "fieldtype": "Date",
            "width": 110,
        },
    ]

    # Add only the selected group by column or all if no grouping
    group_by = filters.get("group_by") if filters else None
    if group_by == "department":
        columns.append(
            {
                "label": _("Department"),
                "fieldname": "department",
                "fieldtype": "Data",
                "width": 120,
            }
        )
    elif group_by == "designation":
        columns.append(
            {
                "label": _("Designation"),
                "fieldname": "designation",
                "fieldtype": "Data",
                "width": 120,
            }
        )
    elif group_by == "branch":
        columns.append(
            {
                "label": _("Branch"),
                "fieldname": "branch",
                "fieldtype": "Data",
                "width": 120,
            }
        )
    elif not group_by:
        # Show all three columns when no grouping is selected
        columns.extend(
            [
                {
                    "label": _("Department"),
                    "fieldname": "department",
                    "fieldtype": "Data",
                    "width": 120,
                },
                {
                    "label": _("Designation"),
                    "fieldname": "designation",
                    "fieldtype": "Data",
                    "width": 120,
                },
                {
                    "label": _("Branch"),
                    "fieldname": "branch",
                    "fieldtype": "Data",
                    "width": 120,
                },
            ]
        )

    # Add remaining columns
    columns.extend(
        [
            {
                "label": _("Employment Type"),
                "fieldname": "employment_type",
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "label": _("Working Days"),
                "fieldname": "total_working_days",
                "fieldtype": "Float",
                "width": 120,
                "precision": 2,
            },
            {
                "label": _("Calendar Days (From Employee Master)"),
                "fieldname": "calender_days_from_employee_master",
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "label": _("Calendar Days (From Salary Slip)"),
                "fieldname": "calender_days_from_salary_slip",
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "label": _("Present Days"),
                "fieldname": "present_days",
                "fieldtype": "Float",
                "width": 120,
                "precision": 2,
            },
            {
                "label": _("Half Day"),
                "fieldname": "half_day",
                "fieldtype": "Int",
                "width": 100,
            },
            {
                "label": _("Week Off (From Holiday List)"),
                "fieldname": "week_off_from_holiday_list",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Week Off (From Attendance)"),
                "fieldname": "week_off_from_attendance",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Public Holiday"),
                "fieldname": "total_public_holidays",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Privilege Leave"),
                "fieldname": "privilege_leave",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Compensatory Leave"),
                "fieldname": "compensatory_leave",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Special Leave"),
                "fieldname": "special_leave",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Absent Days"),
                "fieldname": "absent_days",
                "fieldtype": "Float",
                "width": 100,
                "precision": 2,
            },
            {
                "label": _("Leave Without Pay"),
                "fieldname": "leave_without_pay",
                "fieldtype": "Float",
                "width": 140,
                "precision": 2,
            },
            {
                "label": _("Unmarked Days"),
                "fieldname": "unmarked_days",
                "fieldtype": "Float",
                "width": 140,
                "precision": 2,
            },
            {
                "label": _("Late Mark"),
                "fieldname": "late_mark",
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "label": _("Early Mark"),
                "fieldname": "early_mark",
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "label": _("Payment Days (From Absent)"),
                "fieldname": "payment_days_from_absent",
                "fieldtype": "Float",
                "width": 120,
                "precision": 2,
            },
            # {
            #     "label": _("Payment Days (From Present)"),
            #     "fieldname": "payment_days_from_present",
            #     "fieldtype": "Float",
            #     "width": 120,
            #     "precision": 2,
            # },
            {
                "label": _("Total OT Hours"),
                "fieldname": "custom_ot_hours",
                "fieldtype": "Float",
                "width": 120,
                "precision": 2,
            },
            {
                "label": _("Salary Slip Status"),
                "fieldname": "salary_slip_status",
                "fieldtype": "Data",
                "width": 140,
            },
        ]
    )

    return columns


def apply_grouping(data, group_by_field):
    """Apply grouping to the data based on the selected field"""
    if not group_by_field or not data:
        return data

    grouped_data = []
    current_group = None

    # Filter out rows with empty/null group values and sort data by the group field first
    filtered_data = [row for row in data if row.get(group_by_field)]
    filtered_data.sort(key=lambda x: x.get(group_by_field, ""))
    for row in filtered_data:
        group_value = row.get(group_by_field)

        if current_group != group_value:
            current_group = group_value
            group_header = {field: "" for field in row.keys()}
            group_header["employee_name"] = f"<b>{group_by_field.title()}: {group_value}</b>"
            group_header["is_group"] = 1
            grouped_data.append(group_header)

        employee_row = row.copy()
        employee_row["indent"] = 1
        grouped_data.append(employee_row)

    return grouped_data


def get_monthly_days(month, year):
    """Get total days in the selected month"""
    if month and year:
        try:
            return calendar.monthrange(int(year), int(month))[1]
        except (ValueError, TypeError):
            return 0
    return 0


def calculate_present_days(employee, start_date, end_date):
    """Calculate pesent days from attendance records, including half days and half_day_status"""
    attendance_records = frappe.get_list(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=[
            "status",
            "attendance_date",
            "half_day_status",
            "leave_type",
            "custom_purpose",
            "late_entry",
            "early_exit",
            "ot_hours",
            "public_holiday",
        ],
    )

    total_present = 0
    total_absent = 0
    total_half_days = 0
    total_unmarked_half_days = 0
    total_privileged_leaves = 0
    total_compensatory_leaves = 0
    total_special_leaves = 0
    total_lwp = 0
    late_marks = 0
    early_marks = 0
    total_ot_hours = 0
    total_ph = 0
    total_wo = 0

    for record in attendance_records:
        total_ot_hours += record.get("ot_hours", 0)
        total_ph += record.get("public_holiday", 0)

        if record["custom_purpose"] != "Office Reason":
            if record.get("late_entry"):
                late_marks += 1
            if record.get("early_exit"):
                early_marks += 1

        if record["status"] == "Present" or record["status"] == "Work From Home":
            total_present += 1
        elif record["status"] == "Absent":
            total_absent += 1
        elif record["status"] == "On Leave":
            if record.get("leave_type") == "Compensatory Leave":
                total_compensatory_leaves += 1
            elif (
                record.get("leave_type") == "Privilege Leave-Do not use"
                or record.get("leave_type") == "Privilege Leave - SMVE"
            ):
                total_privileged_leaves += 1
            elif record.get("leave_type") == "Special Leave":
                total_special_leaves += 1
            elif record.get("leave_type") == "Leave Without Pay":
                total_lwp += 1
        elif record["status"] == "Half Day": 
            if record.get("leave_type") == "Leave Without Pay":
                total_lwp += 0.5
            elif record.get("leave_type") == "Compensatory Leave":
                total_compensatory_leaves += 0.5
            elif (record.get("leave_type") == "Privilege Leave-Do not use"
				or record.get("leave_type") == "Privilege Leave - SMVE"):
                total_privileged_leaves += 0.5
            elif record.get("leave_type") == "Special Leave":
                total_special_leaves += 0.5
            else:
                total_lwp += 0.5
                
            if record.get("half_day_status") == "Present":
                total_half_days += 1
            elif record.get("half_day_status") == "Absent":
                total_absent += 0.5
            else:
                total_unmarked_half_days += 0.5
        elif record["status"] == "Week Off":
            total_wo += 1

    # return total_present, total_absent, total_half_days, total_unmarked_half_days
    return {
        "total_present": total_present,
        "total_absent": total_absent,
        "total_half_days": total_half_days,
        "total_unmarked_half_days": total_unmarked_half_days,
        "total_privileged_leaves": total_privileged_leaves,
        "total_compensatory_leaves": total_compensatory_leaves,
        "total_special_leaves": total_special_leaves,
        "total_lwp": total_lwp,
        "late_marks": late_marks,
        "early_marks": early_marks,
        "total_ot_hours": total_ot_hours,
        "total_ph": total_ph,
        "total_wo": total_wo,
    }


def calculate_holiday_and_weekoff_dates(employee, start_date, end_date):
    start_date = getdate(start_date)
    end_date = getdate(end_date)
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=["attendance_date"],
    )
    attendance_dates = set(getdate(a["attendance_date"]) for a in attendance_records)
    all_dates = set(
        add_days(start_date, i) for i in range((end_date - start_date).days + 1)
    )

    if holiday_list:
        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list},
            fields=["holiday_date", "weekly_off"],
        )

        holiday_dates = [
            holiday.holiday_date
            for holiday in holidays
            if start_date <= getdate(holiday.holiday_date) <= end_date
            and not holiday.weekly_off
        ]

        week_off_dates = [
            holiday.holiday_date
            for holiday in holidays
            if start_date <= getdate(holiday.holiday_date) <= end_date
            and holiday.weekly_off
        ]

        non_holiday_dates = all_dates - set(holiday_dates) - set(week_off_dates)
        unmarked_days = len(non_holiday_dates - attendance_dates)
        worked_on_holidays = len(attendance_dates - non_holiday_dates)

        return {
            "holiday_dates": ", ".join(str(date) for date in holiday_dates),
            "public_holiday_count": len(holiday_dates),
            "week_off_dates": ", ".join(str(date) for date in week_off_dates),
            "week_off_count": len(week_off_dates),
            "unmarked_days": unmarked_days,
            "worked_on_holidays": worked_on_holidays
        }
    else:
        unmarked_days = len(all_dates - attendance_dates)
        return {
            "holiday_dates": "",
            "public_holiday_count": 0,
            "week_off_dates": "",
            "week_off_count": 0,
            "unmarked_days": unmarked_days,
            "worked_on_holidays": 0
        }


def get_data(filters):
    conditions = get_conditions(filters)
    monthly_days = get_monthly_days(filters.get("month"), filters.get("year"))

    start_date = None
    end_date = None
    if filters.get("month") and filters.get("year"):
        start_date = f"{filters.get('year')}-{str(filters.get('month')).zfill(2)}-01"
        end_date = (
            f"{filters.get('year')}-{str(filters.get('month')).zfill(2)}-{monthly_days}"
        )

    # Get ALL employees first
    query = """
        SELECT
            emp.name as employee,
            emp.employee_name,
            emp.date_of_joining,
            emp.department,
            emp.designation,
            emp.employment_type,
            emp.branch,
            emp.calender_days as calender_days_from_employee_master,
            emp.status,
            ss.calendar_days as calender_days_from_salary_slip,
            CASE
                WHEN ss.name IS NOT NULL THEN 'Generated'
                ELSE 'Not Generated'
            END as salary_slip_status
        FROM `tabEmployee` emp
        LEFT JOIN `tabSalary Slip` ss ON emp.name = ss.employee
            AND ss.docstatus = 1 {salary_slip_conditions}
        WHERE emp.status = 'Active' {employee_conditions}
        ORDER BY emp.name ASC
    """

    employee_conditions, salary_slip_conditions = split_conditions(conditions, filters)

    final_query = query.format(
        employee_conditions=employee_conditions,
        salary_slip_conditions=salary_slip_conditions,
    )

    query_filters = dict(filters)
    query_filters["monthly_days"] = monthly_days

    employees_data = frappe.db.sql(final_query, query_filters, as_dict=1)

    # --- Filter employees who have attendance data in the selected period ---
    if start_date and end_date:
        filtered_employees = []
        for row in employees_data:
            attendance_count = frappe.db.count(
                "Attendance",
                {
                    "employee": row["employee"],
                    "attendance_date": ["between", [start_date, end_date]],
                    "docstatus": 1,
                },
            )
            if attendance_count > 0:
                filtered_employees.append(row)
        employees_data = filtered_employees
    # ------------------------------------------------------------------------

    # Calculate attendance data for filtered employees
    for row in employees_data:
        if start_date and end_date:

            if (
                row.get("salary_slip_status") == "Generated"
                and row.get("calender_days_from_salary_slip") is not None
            ):
                row["calender_days_from_salary_slip"] = row[
                    "calender_days_from_salary_slip"
                ]
            else:
                row["calender_days_from_salary_slip"] = 0

            holiday_data = calculate_holiday_and_weekoff_dates(
                row.get("employee"), start_date, end_date
            )
            row["total_public_holidays"] = holiday_data["public_holiday_count"]
            row["week_off_from_holiday_list"] = holiday_data["week_off_count"]
            unmarked_days = holiday_data.get("unmarked_days", 0)
            worked_on_holidays = holiday_data.get("worked_on_holidays", 0)

            attendance = calculate_present_days(
                row.get("employee"), start_date, end_date
            )
            row["week_off_from_attendance"] = attendance["total_wo"]
            row["custom_ot_hours"] = attendance["total_ot_hours"]
            row["present_days"] = attendance["total_present"] - (flt(worked_on_holidays))
            if row["present_days"] < 0:
                row["present_days"] = 0
            row["absent_days"] = attendance["total_absent"]
            row["half_day"] = attendance["total_half_days"]
            unmarked_days += attendance["total_unmarked_half_days"]
            row["unmarked_days"] = unmarked_days
            row["privilege_leave"] = attendance["total_privileged_leaves"]
            row["compensatory_leave"] = attendance["total_compensatory_leaves"]
            row["special_leave"] = attendance["total_special_leaves"]
            row["late_mark"] = attendance["late_marks"]
            row["early_mark"] = attendance["early_marks"]
            row["leave_without_pay"] = attendance["total_lwp"]

            row["total_working_days"] = monthly_days

            if (
                row.get("calender_days_from_employee_master")
                and row.get("calender_days_from_employee_master") > 0
            ):
                row["payment_days_from_absent"] = (
                    flt(row.get("calender_days_from_employee_master", 0))
                    - flt(row["absent_days"])
                    - flt(row["leave_without_pay"])
                    - flt(row["unmarked_days"])
                )

                row["payment_days_from_present"] = (
                    flt(row["present_days"])
                    + (flt(row["half_day"])) * 0.5
                    + flt(row["privilege_leave"])
                    + flt(row["compensatory_leave"])
                    + flt(row["special_leave"])
                )
            else:
                row["payment_days_from_absent"] = (
                    flt(monthly_days)
                    - flt(row["absent_days"])
                    - flt(row["leave_without_pay"])
                    - flt(row["unmarked_days"])
                )

                row["payment_days_from_present"] = (
                    flt(row["present_days"])
                    + (flt(row["half_day"])) * 0.5
                    + flt(row["week_off_from_holiday_list"])
                    + flt(row["total_public_holidays"])
                    + flt(row["privilege_leave"])
                    + flt(row["compensatory_leave"])
                    + flt(row["special_leave"])
                )

            if row["payment_days_from_absent"] < 0:
                row["payment_days_from_absent"] = 0

    for row in employees_data:
        float_fields = [
            "total_working_days",
            "week_off_from_holiday_list",
            "leave_without_pay",
            "present_days",
            "half_day",
            "absent_days",
            "payment_days_from_absent",
            "custom_ot_hours",
            "total_public_holidays",
        ]
        for field in float_fields:
            if row.get(field) is not None:
                row[field] = round(float(row[field]), 2)

    return employees_data


def get_conditions(filters):
    conditions = []

    if filters.get("month") and filters.get("year"):
        conditions.append(
            (
                "salary_slip",
                "MONTH(ss.start_date) = %(month)s AND YEAR(ss.start_date) = %(year)s",
            )
        )

    if filters.get("employee"):
        conditions.append(("employee", "emp.name = %(employee)s"))

    if filters.get("company"):
        if filters.get("include_company_descendants"):
            # Get all descendant companies
            companies = get_company_descendants(filters.get("company"))
            if companies:
                conditions.append(("employee", "emp.company IN %(companies)s"))
                filters["companies"] = companies
            else:
                conditions.append(("employee", "emp.company = %(company)s"))
        else:
            conditions.append(("employee", "emp.company = %(company)s"))

    if filters.get("department"):
        conditions.append(("employee", "emp.department = %(department)s"))

    if filters.get("designation"):
        conditions.append(("employee", "emp.designation = %(designation)s"))

    return conditions


def split_conditions(conditions, filters):
    """Split conditions into employee and salary slip conditions"""
    employee_conditions = []
    salary_slip_conditions = []

    for condition_type, condition in conditions:
        if condition_type == "employee":
            employee_conditions.append(condition)
        elif condition_type == "salary_slip":
            salary_slip_conditions.append(condition)

    employee_cond_str = (
        " AND " + " AND ".join(employee_conditions) if employee_conditions else ""
    )
    salary_slip_cond_str = (
        " AND " + " AND ".join(salary_slip_conditions) if salary_slip_conditions else ""
    )

    return employee_cond_str, salary_slip_cond_str


def get_company_descendants(company):
    """Get all descendant companies including the parent company"""
    try:
        # Try using frappe's nested set utility
        from frappe.utils.nestedset import get_descendants_of  # type: ignore

        companies = get_descendants_of("Company", company)
        companies.append(company)
        return companies
    except ImportError:
        pass

    # Alternative method: recursively get child companies
    try:
        companies = [company]
        child_companies = frappe.get_all(
            "Company", filters={"parent_company": company}, fields=["name"]
        )

        for child in child_companies:
            companies.extend(get_company_descendants(child.name))

        return list(set(companies))  # Remove duplicates
    except:
        # If all else fails, return just the parent company
        return [company]
