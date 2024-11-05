import frappe
from frappe import _

@frappe.whitelist()
def get_total_ot_hours(employee, from_date, to_date):
    attendance_records = frappe.get_all('Attendance', 
                                        filters={
                                            'employee': employee,
                                            'attendance_date': ['between', [from_date, to_date]],
                                            'docstatus': 1
                                        },
                                        fields=['custom_ot_hours'])
    total_ot_hours = 0

    for attendance in attendance_records:
        ot_hours = attendance.get('custom_ot_hours') or 0
        try:
            total_ot_hours += float(ot_hours)
        except ValueError:
            frappe.log_error(f"Invalid OT Hours: {ot_hours} for employee {employee}", "OT Calculation Error")
            continue

    return total_ot_hours
