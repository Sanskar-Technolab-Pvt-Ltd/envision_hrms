// Copyright (c) 2026, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Register FTP"] = {
    "filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			on_change: function () {
                // Clear Payroll Period when Company changes
                frappe.query_report.set_filter_value("payroll_period", "");
            }
		},
		{
			fieldname: "payroll_period",
			label: __("Payroll Period"),
			fieldtype: "Link",
			options: "Payroll Period",
			reqd: 1,
			only_select: true,
			get_query: function () {
				const company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company
					}
				};
			}
		}
	]
};
