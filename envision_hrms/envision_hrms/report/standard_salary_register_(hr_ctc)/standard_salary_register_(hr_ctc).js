// Copyright (c) 2026, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.query_reports["Standard Salary Register (HR CTC)"] = {
	"filters": [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            required: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            required: 1
        },
		 {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee",
            only_select: true,
        },
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department",
            only_select: true,
        },
        {
            fieldname: "designation",
            label: "Designation",
            fieldtype: "Link",
            options: "Designation",
            only_select: true,
        },
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            only_select: true,
        },
        {
            fieldname: "currency",
            label: "Currency",
            fieldtype: "Link",
            options: "Currency",
            only_select: true,
        },
        {
            fieldname: "branch",
            label: "Branch",
            fieldtype: "Link",
            options: "Branch",
            only_select: true,
        },
        {
            fieldname: "docstatus",
            label: "Document Status",
            fieldtype: "Select",
            options: "Draft\nSubmitted\nCancelled",
            default: "Submitted"
        },
        {
            fieldname: "consolidate_department",
            label: "Group by Department",
            fieldtype: "Check",
            default: 0
        },
		// {
        //     fieldname: "salary_structure_assignment",
        //     label: "Salary Structure Assignment",
        //     fieldtype: "Link",
        //     options: "Salary Structure Assignment",
        //     only_select: true,
        // }
	]
};
