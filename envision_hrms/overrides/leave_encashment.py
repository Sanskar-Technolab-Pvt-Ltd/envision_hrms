import frappe

@frappe.whitelist()
def custom_set_encashment_amount(self):
		if not hasattr(self, "_salary_structure"):
			self.set_salary_structure()

		per_day_encashment = frappe.db.get_value(
			"Employee", self.employee, "custom_leave_encashment_amount"
		)

		if per_day_encashment:
			self.encashment_amount = self.encashment_days * per_day_encashment if per_day_encashment > 0 else 0
		else:
			frappe.throw("Please set Leave Encashment Amount to Employee master")