# Copyright (c) 2025, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def execute(filters=None):
    columns = [
		{
            "label": "UAN", 
            "fieldname": "uan", 
            "fieldtype": "Data", 
            "width": 100
        },
        {
            "label": "Member Name",
            "fieldname": "member_name",
            "fieldtype": "Data",
            "width": 220
        },
        {
            "label": "Gross Wages",
            "fieldname": "gross_wages",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "EPF Wages", 
            "fieldname": "epf_wages", 
            "fieldtype": "Data", 
            "width": 100
        },
		{
            "label": "EPS Wages",
            "fieldname": "eps_wages",
            "fieldtype": "Data",
            "width": 100
        },
		{
            "label": "EDLI Wages",
            "fieldname": "edli_wages",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "EPF Contribution remitted",
            "fieldname": "epf_contribution_remitted",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "EPS Contribution remitted",
            "fieldname": "eps_contribution_remitted",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "EPF and EPS Diff remitted",
            "fieldname": "epf_and_eps_diff_remitted",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "NCP Days",
            "fieldname": "ncp_days",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": "Refund of Advances",
            "fieldname": "refund_of_advances",
            "fieldtype": "Data",
            "width": 100
        }
    ]

    data = []
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    salary_slips = frappe.get_all("Salary Slip", filters={
        "start_date": ["<=", from_date],
        "end_date": [">=", to_date],
        "docstatus": 1
    }, fields=['name', 'employee', 'employee_name', 'gross_pay', 'leave_without_pay', 'absent_days'])
    
    for slip in salary_slips:
        
        # Extracting required data from the salary slip
        gross_pay = slip.get('gross_pay')
        employee = slip.get('uan')
        uan = frappe.db.get_value("Employee",employee,'uan') or ""
        employee_name = slip.get('employee_name')
        ncp_days = slip.get('leave_without_pay', 0) + slip.get('absent_days', 0)
        
        # Calculating EPF Wages as per the given formula
        salary_detail_data = frappe.get_all('Salary Detail', filters={'parent': slip['name'],'salary_component': ['in', ['House Rent Allowance','HRA']]}, fields=['amount'])
        house_rent_allowance = sum(detail['amount'] for detail in salary_detail_data)
        epf_wages = gross_pay - house_rent_allowance
        
        if epf_wages > 15000:
            epf_wages = 15000
        
        epf_contribution_remitted = epf_wages * (12 / 100)
        eps_contribution_remitted = epf_wages * (8.33 / 100)
        epf_and_eps_diff_remitted = epf_wages * (3.67 / 100)
        
        if epf_and_eps_diff_remitted > 550:
            epf_and_eps_diff_remitted = 550
        
        # Appending data to the list
        data.append({
            "uan": uan,
            "member_name": employee_name,
            "gross_wages": gross_pay,
            "epf_wages": math.ceil(epf_wages),
            "eps_wages": math.ceil(epf_wages),
            "edli_wages": math.ceil(epf_wages),
            "epf_contribution_remitted": math.ceil(epf_contribution_remitted),
            "eps_contribution_remitted": math.ceil(eps_contribution_remitted),
            "epf_and_eps_diff_remitted": math.ceil(epf_and_eps_diff_remitted),
            "ncp_days": math.ceil(ncp_days),
            "refund_of_advances": "0"
        })

    return columns, data