__version__ = "0.0.1"

import hrms.hr.doctype.attendance_request.attendance_request
import envision_hrms.overrides.attendance_request

import hrms.hr.doctype.employee_checkin.employee_checkin
import envision_hrms.overrides.employee_checkin

# hrms.hr.doctype.attendance_request.attendance_request.AttendanceRequest.create_attendance_records = envision_hrms.overrides.attendance_request.AttendanceRequest.create_attendance_records

# hrms.hr.doctype.attendance_request.attendance_request.AttendanceRequest.validate_no_attendance_to_create = envision_hrms.overrides.attendance_request.AttendanceRequest.validate_no_attendance_to_create

hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field = (
    envision_hrms.overrides.employee_checkin.add_log_based_on_employee_field
)
hrms.hr.doctype.employee_checkin.employee_checkin.add_header = (
    envision_hrms.overrides.employee_checkin.add_header
)

