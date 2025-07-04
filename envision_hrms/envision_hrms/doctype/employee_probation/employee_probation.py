# Copyright (c) 2024, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeProbation(Document):
	def on_submit(self):
		# Ensure Employee is mentioned in the EmployeeProbation Form
		if not self.employee:
			frappe.throw("Employee is not mentioned in the EmployeeProbation Form.")
		
		# Fetch the Employee record
		employee = frappe.get_doc("Employee", self.employee)
		companycode = frappe.db.get_value("Company",self.new_company,'custom_company_code')
		
		# Update the Employment Type
		if self.transfer and self.new_company:
			employee.status = "Inactive"
			employee.attendance_device_id = ""
			employee.save()

			new_emp = frappe.copy_doc(employee)
			new_emp.name = None
			new_emp.status = "Active"
			new_emp.naming_series = employee.naming_series
			new_emp.companycode = companycode
			new_emp.user_id = None
			new_emp.date_of_joining = self.date_of_joining
			new_emp.company = self.new_company
			new_emp.site_location = self.site_location
			new_emp.department = self.department
			new_emp.designation = self.designation
			new_emp.grade = self.grade
			new_emp.custom_skill_level = self.skill_level
			new_emp.calender_days = 0
			new_emp.employment_type = self.new_employment_type
			new_emp.custom_probation = self.name
			new_emp.custom_probation = self.custom_advance_permissions_created = 0

			new_emp.insert()
			frappe.msgprint(f"New Employee {new_emp.name} created.")
		else:
			employee.employment_type = self.new_employment_type
			employee.save()
			frappe.msgprint(f"Employment type updated for Employee {employee.employee_name}.")
	
	def on_cancel(self):
		if self.new_company:
			linked_emp = frappe.get_value('Employee',{ 'probation' : self.name }, ['name'])
			employee = frappe.get_doc("Employee", linked_emp) 
			employee.employment_type = self.current_employment_type
			employee.custom_probation = ""
			employee.save()
