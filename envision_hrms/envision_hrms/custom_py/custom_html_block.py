from frappe import _
from frappe.utils import add_days, getdate, nowdate
import frappe
from datetime import datetime, timedelta

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

@frappe.whitelist()
def get_upcoming_work_anniversaries():
    from datetime import datetime, timedelta

    today = datetime.today().date()  # Use `.date()` to get a datetime.date object
    one_week_later = today + timedelta(days=7)  # Also a datetime.date object

    employees = frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "date_of_joining", "image"],
        filters={
            "status": "Active",
            "date_of_joining": ["<=", one_week_later.strftime("%Y-%m-%d")]
        }
    )

    # Filter employees whose work anniversary falls in the next week
    anniversaries = []
    for emp in employees:
        date_of_joining = emp["date_of_joining"]

        # Ensure date_of_joining is a datetime.date object
        if isinstance(date_of_joining, datetime):
            date_of_joining = date_of_joining.date()

        anniversary_date = date_of_joining.replace(year=today.year)
        years_completed = today.year - date_of_joining.year

        # Compare only datetime.date objects
        if today <= anniversary_date <= one_week_later:
            anniversaries.append({
                "employee_name": emp["employee_name"],
                "date_of_joining": date_of_joining.strftime("%Y-%m-%d"),  # Convert to string for JSON
                "image": emp["image"],
                "years_completed": years_completed
            })

    return anniversaries





