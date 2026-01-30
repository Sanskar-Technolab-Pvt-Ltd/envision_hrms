import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

# ? UPDATE TOTAL NET SALARY IN PAYROLL ENTRY
def update_total_net_salary(doc, method=None):
    payroll_entry = None

    # ? DETERMINE PAYROLL ENTRY BASED ON DOCUMENT TYPE
    if doc.doctype == "Payroll Entry":
        payroll_entry = doc.name

    # ? IF SALARY SLIP, GET LINKED PAYROLL ENTRY
    elif doc.doctype == "Salary Slip":
        payroll_entry = doc.payroll_entry

        # ? RECALCULATE NET PAY IF SALARY SLIP IS IN DRAFT STATE
        if method not in ("on_trash", "on_delete") and doc.docstatus == 0:
            doc.calculate_net_pay()

    if not payroll_entry:
        return

    # ? FETCH ALL SALARY SLIPS LINKED TO THE PAYROLL ENTRY
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "payroll_entry": payroll_entry,
            "docstatus": ["!=", 2]
        },
        fields=["net_pay"]
    )

    # ? CALCULATE TOTAL NET SALARY
    total = sum(s.net_pay or 0 for s in salary_slips)
    print(f"==>> salary_slips: {salary_slips}")
    print("".center(50, "-"))
    print(f"==>> total: {total}")

    # ? UPDATE TOTAL NET SALARY IN PAYROLL ENTRY
    frappe.db.set_value(
        "Payroll Entry",
        payroll_entry,
        "custom_total_net_salary",
        total,
        update_modified=False
    )
