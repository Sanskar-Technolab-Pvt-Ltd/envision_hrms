import datetime
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_employee_bonus(employee, from_date, to_date):
    if not (employee and from_date and to_date):
        return None  

    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')

    salary_slips = frappe.get_all("Salary Slip", filters={
        "docstatus": 1,
        "employee": employee,
        "start_date": (">=", from_date),
        "end_date": ("<=", to_date)
    }, fields=['name', 'start_date', 'end_date','base_gross_pay'])

    if not salary_slips:
        return None  

    get_salary_data = frappe.get_all('Salary Detail', filters={
        'parent': ['in', [ss['name'] for ss in salary_slips]],
        'salary_component': 'Professional Tax'  
    }, fields=['amount'])
    
    return salary_slips, get_salary_data