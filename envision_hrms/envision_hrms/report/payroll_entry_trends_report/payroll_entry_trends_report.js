// Copyright (c) 2025, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.query_reports["Payroll Entry Trends Report"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1]
		},
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
			"default": erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2]
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company"
        },
        {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch"
        },
    ]
};
