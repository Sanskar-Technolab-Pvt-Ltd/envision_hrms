import frappe

def deduct_advance_limit(self, method):
    employee_doc = frappe.get_doc("Employee",self.employee)
    new_limit = employee_doc.advance_limit - self.advance_amount
    frappe.db.set_value("Employee",self.employee,"advance_limit",new_limit)

def add_advance_limit(self, method):
    employee_doc = frappe.get_doc("Employee",self.employee)
    new_limit = employee_doc.advance_limit + self.advance_amount
    frappe.db.set_value("Employee",self.employee,"advance_limit",new_limit)

def deduct_advance_limit_ec(self, method):
    if self.total_advance_amount:
        employee_doc = frappe.get_doc("Employee",self.employee)
        new_limit = employee_doc.advance_limit + self.total_advance_amount
        frappe.db.set_value("Employee",self.employee,"advance_limit",new_limit)

def add_advance_limit_ec(self, method):
    if self.total_advance_amount:
        employee_doc = frappe.get_doc("Employee",self.employee)
        new_limit = employee_doc.advance_limit - self.total_advance_amount
        frappe.db.set_value("Employee",self.employee,"advance_limit",new_limit)


