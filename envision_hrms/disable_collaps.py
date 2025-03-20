import frappe

def after_migrate():
    try:
        frappe.db.sql("""
            UPDATE `tabDocField`
            SET collapsible = 0
            WHERE collapsible = 1
        """)
        
        # doc = frappe.get_doc("DocType", "Item")
        # doc.in_create = 0
        # doc.save()
        frappe.db.commit()
       
    except Exception as e:
        frappe.log_error("Error: While updating collapsible fields", f"Error: {e}")
