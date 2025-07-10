frappe.ui.form.on('Payroll Entry', {
    refresh(frm) {
        frm.add_custom_button(__('View Salary Register'), function () {
            // Map docstatus integer to report filter label
            const docstatusMap = {
                0: "Draft",
                1: "Submitted",
                2: "Cancelled"
            };

            frappe.route_options = {
                "from_date": frm.doc.start_date,
                "to_date": frm.doc.end_date,
                "company": frm.doc.company,
                "docstatus": docstatusMap[frm.doc.docstatus] || "Submitted",  // fallback to Submitted
                "department": frm.doc.department || "",
                "designation": frm.doc.designation || "",
                "branch": frm.doc.branch || ""
            };

            frappe.set_route("query-report", "Salary Register");
        }).addClass('btn btn-primary btn-sm primary-action');
    }
});
