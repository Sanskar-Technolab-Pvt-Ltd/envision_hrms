__version__ = "0.0.1"

import hrms.hr.doctype.attendance_request.attendance_request
import envision_hrms.overrides.attendance_request

hrms.hr.doctype.attendance_request.attendance_request.AttendanceRequest.create_attendance_records = envision_hrms.overrides.attendance_request.AttendanceRequest.create_attendance_records
