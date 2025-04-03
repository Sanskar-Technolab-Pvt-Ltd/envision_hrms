import frappe
from frappe import _

@frappe.whitelist()
def get_total_ot_hours(employee, from_date, to_date):
    attendance_records = frappe.get_list(
        'Attendance',
        filters={
            'employee': employee,
            'attendance_date': ['between', [from_date, to_date]],
            'docstatus': 1
        },
        fields=['ot_hours', 'public_holiday']
    )

    total_ot_hours = sum(float(attendance.get('ot_hours', 0)) for attendance in attendance_records)
    total_ph = sum(float(attendance.get('public_holiday', 0)) for attendance in attendance_records)

    # hard reset changes

    return {"total_ot_hours": total_ot_hours, "total_ph": total_ph}



