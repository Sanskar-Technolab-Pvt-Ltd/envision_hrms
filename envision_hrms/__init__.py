__version__ = "0.0.1"

import hrms.hr.doctype.employee_checkin.employee_checkin
from envision_hrms.overrides.employee_checkin import (
    add_log_based_on_employee_field, custom_validate_duplicate_log)

import hrms.hr.doctype.upload_attendance.upload_attendance

# ----------------------Override add checkin logs method to commit database----------------------------

hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field = (
    add_log_based_on_employee_field
)

# ----------------------Override validate duplicate log to add validation for log type----------------------------

hrms.hr.doctype.employee_checkin.employee_checkin.EmployeeCheckin.validate_duplicate_log = (
    custom_validate_duplicate_log
)

import hrms.hr.doctype.attendance.attendance
from envision_hrms.overrides.custom_upload_attendance import (
    custom_validate, add_header)

# ----------------------Override attendance validate function----------------------------

hrms.hr.doctype.attendance.attendance.Attendance.validate = custom_validate

# ----------------------Override upload attendance template header format----------------------------

hrms.hr.doctype.upload_attendance.upload_attendance.add_header = (
    add_header
)


# ----------------------Calculate calender days and payable days to salary slip----------------------------


from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from envision_hrms.overrides.salary_slip import custom_get_working_days_details

SalarySlip.get_working_days_details = custom_get_working_days_details


# ----------------------Override validations for company from department to expense claim----------------------------

from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim
from envision_hrms.api import custom_validate_company_and_department

ExpenseClaim.validate_company_and_department = custom_validate_company_and_department


# ----------------------Calculate encashment amount to leave encashment----------------------------


from hrms.hr.doctype.leave_encashment.leave_encashment import LeaveEncashment
from envision_hrms.overrides.leave_encashment import custom_set_encashment_amount

LeaveEncashment.set_encashment_amount = custom_set_encashment_amount


# ----------------------Compensatory Leave Request validation----------------------------


from hrms.hr.doctype.compensatory_leave_request.compensatory_leave_request import CompensatoryLeaveRequest
from envision_hrms.overrides.compensatory_leave_request import custom_validate_attendance

CompensatoryLeaveRequest.validate_attendance = custom_validate_attendance


# --------------------Overrided methods for monthly attendance sheet----------------------

from hrms.hr.report.monthly_attendance_sheet import monthly_attendance_sheet
from envision_hrms.overrides.monthly_attendance_sheet import (
     execute_override, 
     get_employee_related_details_override,
     get_attendance_status_for_detailed_view_override,
     get_holiday_status_override,
     get_attendance_map_override,
     get_attendance_records_override
)

monthly_attendance_sheet.execute = execute_override
monthly_attendance_sheet.get_employee_related_details = get_employee_related_details_override
monthly_attendance_sheet.get_holiday_status = get_holiday_status_override
monthly_attendance_sheet.get_attendance_status_for_detailed_view = get_attendance_status_for_detailed_view_override
monthly_attendance_sheet.get_attendance_map = get_attendance_map_override
monthly_attendance_sheet.get_attendance_records = get_attendance_records_override


# ----------------------Compensatory Leave Request validation----------------------------


from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from envision_hrms.overrides.payroll_entry import custom_make_accrual_jv_entry

PayrollEntry.make_accrual_jv_entry = custom_make_accrual_jv_entry


