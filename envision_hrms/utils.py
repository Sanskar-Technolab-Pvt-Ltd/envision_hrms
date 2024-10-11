import frappe
from frappe import _
import datetime
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from frappe.utils.data import getdate, now, today
from frappe.utils import getdate, today, add_days, date_diff



# If anyone forgot for checkout then after making attendance create checkout of particular date
@frappe.whitelist()
def process_employee_checkouts():
   
    current_date = datetime.now().date()

    
    checkin_in_records = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "custom_date": current_date,
            "log_type": "IN"
        },
        fields=["employee", "time"]
    )

    
    checkin_out_records = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "custom_date": current_date,
            "log_type": "OUT"
        },
        fields=["employee"]
    )

    
    employees_with_out_logs = {record["employee"] for record in checkin_out_records}

    
    employees_only_in = [
        record for record in checkin_in_records
        if record["employee"] not in employees_with_out_logs
    ]

    for employee_record in employees_only_in:
      
        new_checkout = frappe.get_doc({
            "doctype": "Employee Checkin",
            "employee": employee_record["employee"],
            "time": datetime.now(),  
            "log_type": "OUT",
            "custom_remarks": "Auto-Checkout"
             
        })

        
        new_checkout.insert()
        frappe.db.commit()

   


# Custom attendance flow
@frappe.whitelist(allow_guest=True)
def mark_attendance(date, shift):
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()

    success_message_printed = False
    
    emp_records = frappe.db.get_all("Employee",
                                    filters={
                                        "status": 'Active'
                                    },
                                    fields=["employee"],
                                    )
    
    employee_checkins = {}

    for emp in emp_records:
        emp_name = emp.employee

        checkin_records = frappe.db.get_all(
            "Employee Checkin",
            filters={
                "employee": emp_name,
                "shift": shift,
                "custom_date": date
            },
            fields=["employee", "name", "custom_date", "log_type"],
            order_by="custom_date"
        )
        
        if checkin_records:
            for checkin in checkin_records:
                date_key = checkin['custom_date']
                if emp_name not in employee_checkins:
                    employee_checkins[emp_name] = {}
                if date_key not in employee_checkins[emp_name]:
                    employee_checkins[emp_name][date_key] = []
                employee_checkins[emp_name][date_key].append({
                    'name': checkin['name'],
                    'log_type': checkin['log_type']
                })
                
        # frappe.msgprint(str(employee_checkins))

        # if no checkin adn checkout found it marks absent
        else:
            
            holiday_list = frappe.db.get_value('Employee', emp_name, 'holiday_list')
            is_holiday = False
            
            if holiday_list:
                holiday_doc = frappe.get_doc('Holiday List', holiday_list)
                holidays = holiday_doc.get("holidays")
                
                for holiday in holidays:
                    holiday_dt = holiday.holiday_date
                    if date == holiday_dt:
                        is_holiday = True
                        break
            
            if not is_holiday:
                exists_atte = frappe.db.get_value('Attendance', {'employee': emp_name, 'attendance_date': date, 'docstatus': 1}, ['name'])
                if not exists_atte:
                    attendance = frappe.new_doc("Attendance")
                    attendance.employee = emp_name
                    attendance.attendance_date = date
                    attendance.shift = shift
                    attendance.status = "Absent"
                    attendance.custom_remarks = "No Checkin found"
                    attendance.insert(ignore_permissions=True)
                    attendance.submit()
                    frappe.db.commit()

    # Extract and print values from employee_checkins dictionary
    for emp_name, dates in employee_checkins.items():
        for checkin_date, logs in dates.items():
            first_chkin = None
            last_chkout = None

            for log in logs:
                name = log['name']
                log_type = log['log_type']

                if log_type == "IN" and first_chkin is None:
                    first_chkin = name

                if log_type == "OUT":
                    last_chkout = name
      
        
            if first_chkin and last_chkout:
                
                exists_atte = frappe.db.get_value('Attendance', {'employee': emp_name, 'attendance_date': checkin_date, 'docstatus': 1}, ['name'])
                if not exists_atte:
                    
                    
                    att_status = 'Present'
                    att_remarks = ''
                    final_OT = 0
                    final_wh_new = 0
                    att_late_entry = 0
                    att_early_exit = 0


                    chkin_datetime = frappe.db.get_value('Employee Checkin', first_chkin, 'time')
                    chkout_datetime = frappe.db.get_value('Employee Checkin', last_chkout, 'time')

                    chkin_time = frappe.utils.get_time(chkin_datetime)
                    chkout_time = frappe.utils.get_time(chkout_datetime)


                     # Calculate Work hours
                    shift_Hour = frappe.db.get_value('Shift Type', shift, ['custom_shift_hours'])
                    shift_Hour_Str = str(shift_Hour)
                    half_day_hour = frappe.db.get_value('Shift Type', shift, ['working_hours_threshold_for_half_day'])
                    absent_hour = frappe.db.get_value('Shift Type', shift, ['working_hours_threshold_for_absent'])
                    late_entry_grace_period = frappe.db.get_value('Shift Type', shift, ['late_entry_grace_period'])
                    early_exit_grace_period = frappe.db.get_value('Shift Type', shift, ['early_exit_grace_period'])
                    

                    # Calculate Work hours
                    WorkHours = frappe.utils.time_diff(str(chkout_time), str(chkin_time))
                    WorkHours_Str = str(WorkHours)
                    final_wh_new = frappe.utils.format_time(WorkHours_Str, 'H.m')

                    if WorkHours > shift_Hour:
                        diff = frappe.utils.time_diff(WorkHours_Str, str(shift_Hour))
                        final_OT = frappe.utils.format_time(diff, 'H.m')

                    # Check late entry grace
                    shift_start_time = frappe.db.get_value('Shift Type', shift, 'start_time')
                    shift_start_time = frappe.utils.get_time(shift_start_time)
                    shift_start_datetime = datetime.combine(checkin_date, shift_start_time)
                    grace_late_datetime = frappe.utils.add_to_date(shift_start_datetime, minutes=late_entry_grace_period)
                    grace_late_time = grace_late_datetime.time()

                     # Check early exit grace
                    shift_end_time = frappe.db.get_value('Shift Type', shift, 'end_time')
                    shift_end_time = frappe.utils.get_time(shift_end_time)
                    shift_end_datetime = datetime.combine(checkin_date, shift_end_time)
                    grace_early_datetime = frappe.utils.add_to_date(shift_end_datetime, minutes=-early_exit_grace_period)
                    grace_early_time = grace_early_datetime.time()
                    

                    # Determine checkout remarks and final status
                    checkout_remarks = frappe.db.get_value('Employee Checkin', last_chkout, 'custom_remarks')
                    if checkout_remarks == "Auto-Checkout":
                        att_status = 'Absent'
                        att_remarks = 'Auto-Checkout'
                    else:
                        if chkin_time > grace_late_time:
                            att_status = 'Half Day'
                            att_remarks = f"Late Entry, checked in after grace period of {late_entry_grace_period} minutes"
                            att_late_entry = 1

                        # frappe.msgprint(str(chkout_time))
                        # frappe.msgprint(str(grace_early_time))

                        if chkout_time < grace_early_time:
                            att_early_exit = 1

                        if float(final_wh_new) < half_day_hour:
                            att_status = 'Half Day'
                        if float(final_wh_new) < absent_hour:
                            att_status = 'Absent'


                    attendance = frappe.new_doc("Attendance")
                    attendance.employee = emp_name
                    attendance.attendance_date = checkin_date
                    attendance.shift = shift
                    attendance.in_time = chkin_datetime
                    attendance.out_time = chkout_datetime
                    attendance.check_in_time = chkin_time
                    attendance.check_out_time = chkout_time
                    attendance.custom_employee_checkin = first_chkin
                    attendance.custom_employee_checkout = last_chkout
                    attendance.custom_work_hours = final_wh_new
                    attendance.custom_overtime = final_OT
                    attendance.status = att_status
                    attendance.custom_remarks = att_remarks
                    attendance.late_entry = att_late_entry
                    attendance.early_exit = att_early_exit

                    attendance.insert(ignore_permissions=True)
                    attendance.submit()
                    frappe.db.commit()

                    if not success_message_printed:
                        frappe.msgprint("Attendance is Marked Successfully")
                        success_message_printed = True
                else:
                    
                    formatted_date = checkin_date.strftime("%d-%m-%Y")
                    attendance_link = frappe.utils.get_link_to_form("Attendance", exists_atte)
                    frappe.msgprint(f"Attendance already marked for Employee:{emp_name} for date {formatted_date}: {attendance_link}")


@frappe.whitelist(allow_guest=True)
def set_attendance_date():
    
    # yesterday_date = add_to_date(datetime.now(), days=-1)
    # date = yesterday_date.strftime('%Y-%m-%d')

    date = today()

    shift_types = frappe.get_all("Shift Type", filters={'enable_auto_attendance':1},fields=['name'])
    if shift_types:
        for shifts in shift_types:
            shift = shifts.name

            mark_attendance(date, shift)

