import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate
from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from frappe.utils import cint
from datetime import timedelta


def custom_get_working_days_details(self, lwp=None, for_preview=0):
	payroll_settings = frappe.get_cached_value(
		"Payroll Settings",
		None,
		(
			"payroll_based_on",
			"include_holidays_in_total_working_days",
			"consider_marked_attendance_on_holidays",
			"daily_wages_fraction_for_half_day",
			"consider_unmarked_attendance_as",
		),
		as_dict=1,
	)

	# Calculates total week off,public holidays and overtime hours
	attendance_records = frappe.get_list(
    'Attendance',
    filters={
        'employee': self.employee,  # Changed 'employee' to 'self.employee'
        'attendance_date': ['between', [self.start_date, self.end_date]],
        'docstatus': 1
    },
    fields=['ot_hours', 'public_holiday', "status", 'late_entry']
	)

	total_ot_hours = sum(float(attendance.get('ot_hours', 0)) for attendance in attendance_records)
	total_ph = sum(float(attendance.get('public_holiday', 0)) for attendance in attendance_records)
	total_late_entry = sum(float(attendance.get('late_entry', 0)) for attendance in attendance_records)
	total_wo = sum(
		1 if attendance.get('status') == "Week Off" else 
		(float(attendance.get('status', 0)) if attendance.get('status').replace('.', '', 1).isdigit() else 0)
		for attendance in attendance_records
	)

	self.total_late_entry = total_late_entry
	self.week_off = total_wo
	self.custom_ot_hours = total_ot_hours
	self.total_public_holidays = total_ph

	consider_marked_attendance_on_holidays = (
		payroll_settings.include_holidays_in_total_working_days
		and payroll_settings.consider_marked_attendance_on_holidays
	)

	daily_wages_fraction_for_half_day = flt(payroll_settings.daily_wages_fraction_for_half_day) or 0.5

	working_days = date_diff(self.end_date, self.start_date) + 1
	if for_preview:
		self.total_working_days = working_days
		self.payment_days = working_days
		return

	holidays = self.get_holidays_for_employee(self.start_date, self.end_date)
	working_days_list = [add_days(getdate(self.start_date), days=day) for day in range(0, working_days)]

	if not cint(payroll_settings.include_holidays_in_total_working_days):
		working_days_list = [i for i in working_days_list if i not in holidays]

		working_days -= len(holidays)
		if working_days < 0:
			frappe.throw(_("There are more holidays than working days this month."))

	if not payroll_settings.payroll_based_on:
		frappe.throw(_("Please set Payroll based on in Payroll settings"))

	if payroll_settings.payroll_based_on == "Attendance":
		actual_lwp, absent = self.calculate_lwp_ppl_and_absent_days_based_on_attendance(
			holidays, daily_wages_fraction_for_half_day, consider_marked_attendance_on_holidays
		)
		self.absent_days = absent
	else:
		actual_lwp = self.calculate_lwp_or_ppl_based_on_leave_application(
			holidays, working_days_list, daily_wages_fraction_for_half_day
		)

	if not lwp:
		lwp = actual_lwp
	elif lwp != actual_lwp:
		frappe.msgprint(
			_("Leave Without Pay does not match with approved {} records").format(
				payroll_settings.payroll_based_on
			)
		)

	self.leave_without_pay = lwp
	self.total_working_days = working_days

	payment_days = self.get_payment_days(payroll_settings.include_holidays_in_total_working_days)

	# if self.calendar_days != 0:
	# 	# self.calendar_days = self.total_working_days - self.week_off
	# 	payment_days = self.calendar_days
	# # else:
	# # 	self.calendar_days = self.total_working_days
	
	if flt(payment_days) > flt(lwp):
		self.payment_days = flt(payment_days) - flt(lwp)

		if payroll_settings.payroll_based_on == "Attendance":
			self.payment_days -= flt(absent)

		consider_unmarked_attendance_as = payroll_settings.consider_unmarked_attendance_as or "Present"

		if (
			payroll_settings.payroll_based_on == "Attendance"
			and consider_unmarked_attendance_as == "Absent"
		):
			unmarked_days = self.get_unmarked_days(
				payroll_settings.include_holidays_in_total_working_days, holidays
			)
			self.absent_days += unmarked_days  # will be treated as absent
			self.payment_days -= unmarked_days
	else:
		self.payment_days = 0

	#Use calendar_days if full-month attendance and calendar_days is set
	if self.calendar_days and self.start_date and self.end_date:
		month_start = getdate(self.start_date).replace(day=1)
		month_end = getdate(add_days(self.start_date, 32)).replace(day=1) - timedelta(days=1)
	
		# Check if full-month attendance is covered
		if getdate(self.start_date) == month_start and getdate(self.end_date) == month_end:
			
			# Fetch employee joining and relieving dates
			employee_data = frappe.get_value(
				"Employee",
				self.employee,
				["date_of_joining", "relieving_date"],
				as_dict=True
			)

			employee_joining_date = employee_data.get("date_of_joining")
			relieving_date = employee_data.get("relieving_date")
	
			#joined on/before month_start AND not relieved mid-month
			if (
				employee_joining_date and getdate(employee_joining_date) <= month_start
				and (not relieving_date or getdate(relieving_date) >= month_end)
			):
				# Make sure employee is not absent for all days
				if self.absent_days != self.total_working_days:
					self.payment_days = self.calendar_days - flt(self.absent_days) - flt(lwp)

			else:
				self.payment_days = self.payment_days - flt(self.week_off) - flt(lwp)