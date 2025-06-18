import frappe
from frappe import _
from itertools import groupby
from frappe.query_builder.functions import Extract
Filters = frappe._dict

from hrms.hr.report.monthly_attendance_sheet import monthly_attendance_sheet

def execute_override(filters: Filters | None = None) -> tuple:
	filters = frappe._dict(filters or {})

	if not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	if not filters.company:
		frappe.throw(_("Please select company."))

	if filters.company:
		filters.companies = [filters.company]
		if filters.include_company_descendants:
			filters.companies.extend(monthly_attendance_sheet.get_descendants_of("Company", filters.company))

	attendance_map = monthly_attendance_sheet.get_attendance_map(filters)
	if not attendance_map:
		frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
		return [], [], None, None

	columns = monthly_attendance_sheet.get_columns(filters)
	data = monthly_attendance_sheet.get_data(filters, attendance_map)

	if not data:
		frappe.msgprint(_("No attendance records found for this criteria."), alert=True, indicator="orange")
		return columns, [], None, None

	message = monthly_attendance_sheet.get_message() if not filters.summarized_view else ""
	chart = monthly_attendance_sheet.get_chart_data(attendance_map, filters)

	return columns, data, message, chart

def get_employee_related_details_override(filters):
    """Returns
    1. nested dict for employee details (including employment_type)
    2. list of values for the group by filter
    """
    
    Employee = frappe.qb.DocType("Employee")
    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.employee_name,
            Employee.designation,
            Employee.grade,
            Employee.department,
            Employee.branch,
            Employee.company,
            Employee.holiday_list,
            Employee.employment_type,  # Add employment_type field
        )
        .where(Employee.company.isin(filters.companies))
    )

    if filters.employee:
        query = query.where(Employee.name == filters.employee)

    group_by = filters.group_by
    if group_by:
        group_by = group_by.lower()
        query = query.orderby(group_by)

    employee_details = query.run(as_dict=True)

    group_by_param_values = []
    emp_map = {}

    if group_by:
        group_key = lambda d: "" if d[group_by] is None else d[group_by]  # noqa
        for parameter, employees in groupby(sorted(employee_details, key=group_key), key=group_key):
            group_by_param_values.append(parameter)
            emp_map.setdefault(parameter, frappe._dict())

            for emp in employees:
                emp_map[parameter][emp.name] = emp
    else:
        for emp in employee_details:
            emp_map[emp.name] = emp

    return emp_map, group_by_param_values

def get_attendance_status_for_detailed_view_override(employee, filters, employee_attendance, holidays):
    """Returns list of shift-wise attendance status for employee
    Modified to show Week Off (WO) for Contract employees
    """
    from frappe.utils import cint, cstr, getdate
    
    # Get employee details to check employment type
    employee_doc = frappe.get_doc("Employee", employee)
    employment_type = employee_doc.employment_type
    
    total_days = get_total_days_in_month_override(filters)
    attendance_values = []
    
    status_map = {
        "Present": "P",
        "Absent": "A",
        "Half Day": "HD",
        "Work From Home": "WFH",
        "On Leave": "L",
        "Holiday": "H",
        "Weekly Off": "WO",
    }

    for shift, status_dict in employee_attendance.items():
        row = {"shift": shift}

        for day in range(1, total_days + 1):
            status = status_dict.get(day)
            
            # If no status and holidays exist, get holiday status
            if status is None and holidays:
                status = get_holiday_status_override(day, holidays)
            
            # Special handling for Contract employees and Week Off
            if employment_type == "Contract" and status == "Weekly Off":
                abbr = "WO"  # Show WO for contract employees
            else:
                abbr = status_map.get(status, "")

            row[cstr(day)] = abbr

        attendance_values.append(row)

    return attendance_values

def get_holiday_status_override(day, holidays):
    """Modified to return 'Weekly Off' instead of 'Week Off' for consistency"""
    status = None
    if holidays:
        for holiday in holidays:
            if day == holiday.get("day_of_month"):
                if holiday.get("weekly_off"):
                    status = "Weekly Off"  # Changed from "Week Off" to "Weekly Off"
                else:
                    status = "Holiday"
                break
    return status

def get_total_days_in_month_override(filters):
    """Helper function to get total days in month"""
    from calendar import monthrange
    from frappe.utils import cint
    return monthrange(cint(filters.year), cint(filters.month))[1]

def get_attendance_map_override(filters):
    """Modified attendance map to properly handle Week Off status for Contract employees"""
    attendance_list = get_attendance_records_override(filters)
    attendance_map = {}
    leave_map = {}

    for d in attendance_list:
        if d.status == "On Leave":
            leave_map.setdefault(d.employee, {}).setdefault(d.shift, []).append(d.day_of_month)
            continue

        if d.shift is None:
            d.shift = ""

        attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
        
        # Handle Week Off status specially
        if d.status == "Week Off":
            attendance_map[d.employee][d.shift][d.day_of_month] = "Weekly Off"
        else:
            attendance_map[d.employee][d.shift][d.day_of_month] = d.status

    # leave is applicable for the entire day so all shifts should show the leave entry
    for employee, leave_days in leave_map.items():
        for assigned_shift, days in leave_days.items():
            # no attendance records exist except leaves
            if employee not in attendance_map:
                attendance_map.setdefault(employee, {}).setdefault(assigned_shift, {})

            for day in days:
                for shift in attendance_map[employee].keys():
                    attendance_map[employee][shift][day] = "On Leave"

    return attendance_map

def get_attendance_records_override(filters):
    """Get attendance records including Week Off status"""
    Attendance = frappe.qb.DocType("Attendance")
    query = (
        frappe.qb.from_(Attendance)
        .select(
            Attendance.employee,
            Extract("day", Attendance.attendance_date).as_("day_of_month"),
            Attendance.status,
            Attendance.shift,
        )
        .where(
            (Attendance.docstatus == 1)
            & (Attendance.company.isin(filters.companies))
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
        )
    )

    if filters.employee:
        query = query.where(Attendance.employee == filters.employee)
    query = query.orderby(Attendance.employee, Attendance.attendance_date)

    return query.run(as_dict=1)