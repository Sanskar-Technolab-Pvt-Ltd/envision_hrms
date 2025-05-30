import frappe
from frappe import _
from frappe.utils import date_diff, format_date, getdate

def custom_validate_attendance(self):
		attendance_records = frappe.get_all(
			"Attendance",
			filters={
				"attendance_date": ["between", (self.work_from_date, self.work_end_date)],
				"status": ("in", ["Present", "Work From Home", "Half Day"]),
				# "half_day_status": ("!=", "Absent"),
				"docstatus": 1,
				"employee": self.employee,
			},
			fields=["attendance_date", "status"],
		)

		half_days = [entry.attendance_date for entry in attendance_records if entry.status == "Half Day"]

		if half_days and (not self.half_day or getdate(self.half_day_date) not in half_days):
			frappe.throw(
				_(
					"You were only present for Half Day on {}. Cannot apply for a full day compensatory leave"
				).format(", ".join([frappe.bold(format_date(half_day)) for half_day in half_days]))
			)

		if len(attendance_records) < date_diff(self.work_end_date, self.work_from_date) + 1:
			frappe.throw(_("You are not present all day(s) between compensatory leave request days"))