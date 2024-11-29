// Copyright (c) 2024, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Increment Register"] = {
    filters: [
		{
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
        },
        {
            fieldname: "payroll_period",
            label: "Payroll Period",
            fieldtype: "Link",
            options: "Payroll Period",
            reqd: 1
        },
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        },
        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee",
			get_query: function () {
                const company = frappe.query_report.get_filter_value("company");
                if (company) {
                    return {
                        filters: { company: company }
                    };
                }
                return {};
            }
        }
    ],

    onload: function (report) {
        // Automatically set the current payroll period
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Payroll Period",
                filters: [
                    ["start_date", "<=", frappe.datetime.get_today()],
                    ["end_date", ">=", frappe.datetime.get_today()]
                ],
                fields: ["name"],
                limit_page_length: 1
            },
            callback: function (response) {
                if (response.message && response.message.length > 0) {
                    const currentPayrollPeriod = response.message[0].name;
                    report.set_filter_value("payroll_period", currentPayrollPeriod);
                }
            }
        });
    },

    refresh: function (report) {
        // Clear the employee filter when the report is refreshed
        report.set_filter_value('employee', null);
    }
};
