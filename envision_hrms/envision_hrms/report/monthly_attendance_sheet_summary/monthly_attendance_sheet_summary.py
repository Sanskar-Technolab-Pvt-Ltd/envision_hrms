# Copyright (c) 2025, Pooja Vadher and contributors
# For license information, please see license.txt


import frappe
from frappe import _
import calendar
from frappe.utils import add_days, date_diff, flt, getdate # type: ignore


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
       {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 100},
       {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
   ]
  
   # Add only the selected group by column or all if no grouping
   group_by = filters.get("group_by") if filters else None
   if group_by == "department":
       columns.append({"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 120})
   elif group_by == "designation":
       columns.append({"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 120})
   elif group_by == "branch":
       columns.append({"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 120})
   elif not group_by:
       # Show all three columns when no grouping is selected
       columns.extend([
           {"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 120},
           {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 120},
           {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 120},
       ])
  
   # Add remaining columns
   columns.extend([
       {"label": _("Working Days"), "fieldname": "total_working_days", "fieldtype": "Float", "width": 120, "precision": 2},
       {"label": _("Calendar Days"), "fieldname": "calender_days", "fieldtype": "Int", "width": 120},
       {"label": _("Week Off"), "fieldname": "week_off", "fieldtype": "Float", "width": 100, "precision": 2},
       {"label": _("Leave Without Pay"), "fieldname": "leave_without_pay", "fieldtype": "Float", "width": 140, "precision": 2},
       {"label": _("Absent Days"), "fieldname": "absent_days", "fieldtype": "Float", "width": 100, "precision": 2},
       {"label": _("Payment Days"), "fieldname": "payment_days", "fieldtype": "Float", "width": 120, "precision": 2},
       {"label": _("Total OT Hours"), "fieldname": "custom_ot_hours", "fieldtype": "Float", "width": 120, "precision": 2},
       {"label": _("Total Public Holidays"), "fieldname": "total_public_holidays", "fieldtype": "Float", "width": 160, "precision": 2},
       {"label": _("Salary Slip Status"), "fieldname": "salary_slip_status", "fieldtype": "Data", "width": 140},
   ])
  
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
      
       # Add group header when group changes
       if current_group != group_value:
           current_group = group_value
          
           # Create group header row - show group name in employee_name column for better visibility
           group_header = {
               "employee": "",
               "employee_name": f"<b>{group_by_field.title()}: {group_value}</b>",
               "department": "",
               "designation": "",
               "branch": "",
               "calender_days": "",
               "total_working_days": "",
               "week_off": "",
               "leave_without_pay": "",
               "absent_days": "",
               "payment_days": "",
               "custom_ot_hours": "",
               "total_public_holidays": "",
               "salary_slip_status": "",
               "indent": 0,
               "is_group": 1,
               "parent_account": group_value
           }
          
           # Also put the group value in the correct column if it exists
           if group_by_field in group_header:
               group_header[group_by_field] = f"<b>{group_value}</b>"
              
           grouped_data.append(group_header)
      
       # Add employee row with indent
       employee_row = row.copy()
       employee_row["indent"] = 1
      
       # Keep the group field value for employee rows for reference
       # Don't clear it as it might be useful for filtering/sorting
          
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


def calculate_absent_days(employee, start_date, end_date):
   """Calculate absent days from attendance records"""
   absent_records = frappe.get_list(
       'Attendance',
       filters={
           'employee': employee,
           'attendance_date': ['between', [start_date, end_date]],
           'status': 'Absent',
           'docstatus': 1
       },
       fields=['name']
   )
   return len(absent_records)


def calculate_lwp_days(employee, start_date, end_date):
   """Calculate Leave Without Pay days from leave applications"""
   lwp_records = frappe.get_list(
       'Leave Application',
       filters={
           'employee': employee,
           'from_date': ['<=', end_date],
           'to_date': ['>=', start_date],
           'leave_type': ['in', ['Leave Without Pay', 'LWP']],
           'status': 'Approved',
           'docstatus': 1
       },
       fields=['total_leave_days']
   )
   return sum(float(record.get('total_leave_days', 0)) for record in lwp_records)


def calculate_attendance_data(employee, start_date, end_date):
   """Calculate week off, OT hours, and public holidays from attendance records"""
   attendance_records = frappe.get_list(
       'Attendance',
       filters={
           'employee': employee,
           'attendance_date': ['between', [start_date, end_date]],
           'docstatus': 1
       },
       fields=['ot_hours', 'public_holiday', "status"]
   )


   total_ot_hours = sum(float(attendance.get('ot_hours', 0)) for attendance in attendance_records)
   total_ph = sum(float(attendance.get('public_holiday', 0)) for attendance in attendance_records)
  
   # Calculate week off based on your salary slip logic
   total_wo = sum(
       1 if attendance.get('status') == "Week Off" else
       (float(attendance.get('status', 0)) if str(attendance.get('status', '')).replace('.', '', 1).isdigit() else 0)
       for attendance in attendance_records
   )


   return {
       'week_off': total_wo,
       'custom_ot_hours': total_ot_hours,
       'total_public_holidays': total_ph
   }


def get_data(filters):
    conditions = get_conditions(filters)
    monthly_days = get_monthly_days(filters.get("month"), filters.get("year"))

    start_date = None
    end_date = None
    if filters.get("month") and filters.get("year"):
        start_date = f"{filters.get('year')}-{str(filters.get('month')).zfill(2)}-01"
        end_date = f"{filters.get('year')}-{str(filters.get('month')).zfill(2)}-{monthly_days}"

    # Get ALL employees first
    query = """
        SELECT
            emp.name as employee,
            emp.employee_name,
            emp.department,
            emp.designation,
            emp.branch,
            emp.calender_days,
            emp.status,
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
        salary_slip_conditions=salary_slip_conditions
    )

    query_filters = dict(filters)
    query_filters["monthly_days"] = monthly_days

    employees_data = frappe.db.sql(final_query, query_filters, as_dict=1)

    # --- Filter employees who have attendance data in the selected period ---
    if start_date and end_date:
        filtered_employees = []
        for row in employees_data:
            attendance_count = frappe.db.count(
                'Attendance',
                {
                    'employee': row['employee'],
                    'attendance_date': ['between', [start_date, end_date]],
                    'docstatus': 1
                }
            )
            if attendance_count > 0:
                filtered_employees.append(row)
        employees_data = filtered_employees
    # ------------------------------------------------------------------------

    # Calculate attendance data for filtered employees
    for row in employees_data:
        if start_date and end_date:
            attendance_data = calculate_attendance_data(row.get('employee'), start_date, end_date)
            row['week_off'] = attendance_data['week_off']
            row['custom_ot_hours'] = attendance_data['custom_ot_hours']
            row['total_public_holidays'] = attendance_data['total_public_holidays']

            absent_days = calculate_absent_days(row.get('employee'), start_date, end_date)
            row['absent_days'] = absent_days

            lwp_days = calculate_lwp_days(row.get('employee'), start_date, end_date)
            row['leave_without_pay'] = lwp_days

            row['total_working_days'] = monthly_days

            if row.get('calender_days') and row.get('calender_days') > 0:
                row['payment_days'] = flt(row.get('calender_days', 0)) - flt(row['absent_days']) - flt(row['leave_without_pay'])
            else:
                row['payment_days'] = flt(monthly_days) - flt(row['week_off']) - flt(row['absent_days']) - flt(row['leave_without_pay'])

            if row['payment_days'] < 0:
                row['payment_days'] = 0
        else:
            row['total_working_days'] = monthly_days
            row['week_off'] = 0
            row['leave_without_pay'] = 0
            row['absent_days'] = 0
            row['payment_days'] = monthly_days
            row['custom_ot_hours'] = 0
            row['total_public_holidays'] = 0

    for row in employees_data:
        float_fields = ['total_working_days', 'week_off', 'leave_without_pay',
                       'absent_days', 'payment_days', 'custom_ot_hours', 'total_public_holidays']
        for field in float_fields:
            if row.get(field) is not None:
                row[field] = round(float(row[field]), 2)

    return employees_data


def get_conditions(filters):
   conditions = []
  
   if filters.get("month") and filters.get("year"):
       conditions.append(("salary_slip", "MONTH(ss.start_date) = %(month)s AND YEAR(ss.start_date) = %(year)s"))
  
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
  
   employee_cond_str = " AND " + " AND ".join(employee_conditions) if employee_conditions else ""
   salary_slip_cond_str = " AND " + " AND ".join(salary_slip_conditions) if salary_slip_conditions else ""
  
   return employee_cond_str, salary_slip_cond_str


def get_company_descendants(company):
   """Get all descendant companies including the parent company"""
   try:
       # Try using frappe's nested set utility
       from frappe.utils.nestedset import get_descendants_of # type: ignore
       companies = get_descendants_of("Company", company)
       companies.append(company)
       return companies
   except ImportError:
       pass
  
   # Alternative method: recursively get child companies
   try:
       companies = [company]
       child_companies = frappe.get_all("Company",
           filters={"parent_company": company},
           fields=["name"]
       )
      
       for child in child_companies:
           companies.extend(get_company_descendants(child.name))
      
       return list(set(companies))  # Remove duplicates
   except:
       # If all else fails, return just the parent company
       return [company]
