__version__ = "0.0.1"

import hrms.hr.doctype.employee_checkin.employee_checkin
import envision_hrms.overrides.employee_checkin

import hrms.hr.doctype.upload_attendance.upload_attendance

hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field = (
    envision_hrms.overrides.employee_checkin.add_log_based_on_employee_field
)

hrms.hr.doctype.employee_checkin.employee_checkin.EmployeeCheckin.validate_duplicate_log = (
    envision_hrms.overrides.employee_checkin.custom_validate_duplicate_log
)

import hrms.hr.doctype.attendance.attendance
import envision_hrms.overrides.custom_upload_attendance

hrms.hr.doctype.attendance.attendance.Attendance.validate = envision_hrms.overrides.custom_upload_attendance.custom_validate

hrms.hr.doctype.upload_attendance.upload_attendance.add_header = (
    envision_hrms.overrides.custom_upload_attendance.add_header
)

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from envision_hrms.overrides.salary_slip import custom_get_working_days_details

SalarySlip.get_working_days_details = custom_get_working_days_details