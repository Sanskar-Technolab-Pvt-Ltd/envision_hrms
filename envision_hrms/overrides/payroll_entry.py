
import erpnext
import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_accounting_dimensions


def custom_make_accrual_jv_entry(self, submitted_salary_slips):
    self.check_permission("write")
    employee_wise_accounting_enabled = frappe.db.get_single_value(
        "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
    )
    self.employee_based_payroll_payable_entries = {}
    self._advance_deduction_entries = []

    earnings = (
        self.get_salary_component_total(
            component_type="earnings",
            employee_wise_accounting_enabled=employee_wise_accounting_enabled,
        )
        or {}
    )

    deductions = (
        self.get_salary_component_total(
            component_type="deductions",
            employee_wise_accounting_enabled=employee_wise_accounting_enabled,
        )
        or {}
    )

    precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

    if earnings or deductions:
        accounts = []
        currencies = []
        payable_amount = 0
        accounting_dimensions = get_accounting_dimensions() or []
        company_currency = erpnext.get_company_currency(self.company)

        payable_amount = self.get_payable_amount_for_earnings_and_deductions(
            accounts,
            earnings,
            deductions,
            currencies,
            company_currency,
            accounting_dimensions,
            precision,
            payable_amount,
        )

        payable_amount = self.set_accounting_entries_for_advance_deductions(
            accounts,
            currencies,
            company_currency,
            accounting_dimensions,
            precision,
            payable_amount,
        )

        self.set_payable_amount_against_payroll_payable_account(
            accounts,
            currencies,
            company_currency,
            accounting_dimensions,
            precision,
            payable_amount,
            self.payroll_payable_account,
            employee_wise_accounting_enabled,
        )

        self.make_journal_entry(
            accounts,
            currencies,
            self.payroll_payable_account,
            voucher_type="Journal Entry",
            user_remark=_("Accrual Journal Entry for salaries from {0} to {1}").format(
                self.start_date, self.end_date
            ),
            # submit_journal_entry=True,
            submitted_salary_slips=submitted_salary_slips,
        )