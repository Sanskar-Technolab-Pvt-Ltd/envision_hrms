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
		employee.employment_type = self.new_employment_type  # Replace with the desired value
		employee.save()
		
		frappe.msgprint(f"Employment type updated for Employee {employee.employee_name}.")
