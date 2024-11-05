from frappe import _
from frappe.utils import add_days, getdate, nowdate
import frappe

@frappe.whitelist()
def get_upcoming_birthdays():
    # Get the current date
    today = getdate(nowdate())
    
    # Calculate the start and end of the current week (Monday to Sunday)
    week_start = today if today.weekday() == 0 else add_days(today, -today.weekday())
    week_end = add_days(week_start, 6)

    # Query to fetch employees whose birthdays fall within this week along with their images
    upcoming_birthdays = frappe.db.sql("""
        SELECT name, employee_name, date_of_birth, image
        FROM `tabEmployee`
        WHERE DAYOFYEAR(date_of_birth) BETWEEN DAYOFYEAR(%s) AND DAYOFYEAR(%s)
        ORDER BY date_of_birth ASC, employee_name ASC
    """, (week_start, week_end), as_dict=True)

    return upcoming_birthdays
