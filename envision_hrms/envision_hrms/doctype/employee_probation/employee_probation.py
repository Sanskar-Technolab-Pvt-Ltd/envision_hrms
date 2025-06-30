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
		
		# Update the Employment Type
		if self.transfer and self.new_company:
			new_emp = frappe.copy_doc(employee)

			new_emp.name = None
			new_emp.naming_series = ".{companycode}.{site_location}.###"
			new_emp.user_id = None
			new_emp.date_of_joining = frappe.utils.nowdate()
			new_emp.company = self.new_company
			new_emp.site_location = self.site_location
			new_emp.department = self.department
			new_emp.designation = self.designation
			new_emp.grade = self.grade
			new_emp.custom_skill_level = self.skill_level
			new_emp.calender_days = 0
			new_emp.employment_type = self.new_employment_type

			new_emp.insert()

			employee.status = "Inactive"
			employee.save()

			frappe.msgprint(f"New Employee {new_emp.name} created.")
		else:
			employee.employment_type = self.new_employment_type
			employee.custom_employee_probation = self.name 
			employee.save()
			frappe.msgprint(f"Employment type updated for Employee {employee.employee_name}.")
	
	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee) 

		if not self.new_company:
			employee.employment_type = self.current_employment_type
			employee.custom_probation = ""
			employee.save()
