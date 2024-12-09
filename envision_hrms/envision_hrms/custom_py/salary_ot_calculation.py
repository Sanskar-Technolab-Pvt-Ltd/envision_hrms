import frappe
from frappe import _

@frappe.whitelist()
def get_total_ot_hours(employee, from_date, to_date):
    attendance_records = frappe.get_all(
        'Attendance',
        filters={
            'employee': employee,
            'attendance_date': ['between', [from_date, to_date]],
            'docstatus': 1
        },
        fields=['custom_ot_hours']
    )
    
    total_ot_hours = 0
    # print("Fetched Attendance Records:", attendance_records)

    for attendance in attendance_records:
        try:
            ot_hours = float(attendance.get('custom_ot_hours', 0))
            # print(f"Adding OT Hours: {ot_hours}")
            total_ot_hours += ot_hours
        except ValueError as e:
            frappe.log_error(f"Invalid OT Hours: {attendance.get('custom_ot_hours')}, Error: {str(e)}", 
                             "OT Calculation Error")
    
    # print(f"Total OT Hours: {total_ot_hours}")
    return total_ot_hours

