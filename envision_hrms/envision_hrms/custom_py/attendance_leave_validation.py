import frappe
from frappe import _
from frappe.utils import getdate, formatdate

# ? VALIDATION TO FREEZE ATTENDANCE AND LEAVE APPLICATION CREATION/EDITING BASED ON HR SETTINGS
def freeze_attendance_validation(doc, method=None):

    hr_settings = frappe.get_single("HR Settings")

    # * FREEZE CHECK
    if not hr_settings.custom_freeze_attendance_for_payroll:
        return

    freeze_date = hr_settings.custom_attendance_frozen_till_date

    if not freeze_date:
        return

    freeze_date = getdate(freeze_date)

    # * ROLE CHECK - ALLOW IF USER HAS THE SPECIFIED ROLE IN HR SETTINGS
    allowed_role = hr_settings.custom_role_allowed_to_override_freeze_attendance_validation
    user_roles = frappe.get_roles(frappe.session.user)

    if allowed_role and allowed_role in user_roles:
        return

    # * GET DOCUMENT DATE BASED ON DOCTYPE
    if doc.doctype == "Attendance":
        doc_date = doc.attendance_date

    elif doc.doctype == "Attendance Request":
        doc_date = doc.from_date

    elif doc.doctype == "Leave Application":
        doc_date = doc.from_date

    else:
        return

    if not doc_date:
        return

    doc_date = getdate(doc_date)

    # * VALIDATION CHECK
    if doc_date <= freeze_date:
        frappe.throw(
            _("Attendance is frozen till {0}. You cannot create or edit records before this date.")
            .format(formatdate(freeze_date, "dd-mm-yyyy"))

        )
