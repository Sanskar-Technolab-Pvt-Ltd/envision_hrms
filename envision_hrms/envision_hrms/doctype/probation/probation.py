# Copyright (c) 2024, Pooja Vadher and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Probation(Document):
	def on_submit(self):
		# Ensure Employee is mentioned in the Probation Form
		if not self.employee:
			frappe.throw("Employee is not mentioned in the Probation Form.")
		
		# Fetch the Employee record
		employee = frappe.get_doc("Employee", self.employee)
		
		# Update the Employment Type
		if self.new_company:
			doc = frappe.new_doc('Employee')
			doc.naming_series = ".{companycode}.{site_location}.### "
			doc.first_name = employee.first_name
			doc.middle_name = employee.middle_name
			doc.last_name = employee.last_name
			doc.gender = employee.gender
			doc.date_of_birth = employee.date_of_birth
			doc.date_of_joining = frappe.utils.nowdate()
			doc.company = self.new_company
			doc.site_location = self.site_location
			doc.department =  self.department
			doc.designation =  self.designation
			doc.grade =  self.grade
			doc.custom_skill_level =  self.skill_level
			doc.calender_days = 0
			doc.employment_type = self.new_employment_type
			doc.custom_probation = self.name  # Replace with the desired value
			doc.insert()
			employee.status = "Inactive"
			employee.save()
			frappe.msgprint(f"New Employee has been created.")
		else:
			employee.employment_type = self.new_employment_type
			employee.custom_probation = self.name  # Replace with the desired value
			employee.save()
			
			frappe.msgprint(f"Employment type updated for Employee {employee.employee_name}.")
	
	def on_Cancel(self):
		employee = frappe.get_doc("Employee", self.employee) 

		if not self.new_company:
			employee.employment_type = self.current_employment_type
			employee.custom_probation = ""  # Replace with the desired value
			employee.save()
