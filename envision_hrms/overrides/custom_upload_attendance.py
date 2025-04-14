import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate

from erpnext.setup.doctype.employee.employee import is_holiday

import frappe.utils
from hrms.hr.utils import validate_active_employee, validate_dates
from hrms.hr.doctype.attendance.attendance import mark_attendance

def custom_validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day", "Work From Home", "Week Off"])
		validate_active_employee(self.employee)
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.validate_overlapping_shift_attendance()
		self.validate_employee_status()
		self.check_leave_record()


def add_header(w):
	status = ", ".join((frappe.get_meta("Attendance").get_field("status").options or "").strip().split("\n"))
	w.writerow(["Notes:"])
	w.writerow(["Please do not change the template headings"])
	w.writerow(["Status should be one of these values: " + status + ",Week Off"])
	w.writerow(["If you are overwriting existing attendance records, 'ID' column mandatory"])
	w.writerow(
		["ID", "Employee", "Employee Name", "Date", "Status", "Leave Type", "Company", "Naming Series", "OT Hours", "Public Holiday"]
	)
	return w