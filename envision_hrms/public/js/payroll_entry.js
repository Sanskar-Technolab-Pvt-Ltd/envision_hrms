frappe.ui.form.on('Payroll Entry', {
    refresh(frm) {
        frm.add_custom_button(__('View Salary Register'), function () {
            frappe.call({
                method: "envision_hrms.api.get_salary_slip_docstatus",
                args: {
                    payroll_entry: frm.doc.name
                },
                callback: function(r) {
                    // Map docstatus integer to report filter label
                    const docstatusMap = {
                        0: "Draft",
                        1: "Submitted",
                        2: "Cancelled"
                    };
                    let slip_docstatus = docstatusMap[r.message] || "Submitted";

                    frappe.route_options = {
                        "from_date": frm.doc.start_date,
                        "to_date": frm.doc.end_date,
                        "company": frm.doc.company,
                        "docstatus": slip_docstatus,
                        "department": frm.doc.department || "",
                        "designation": frm.doc.designation || "",
                        "branch": frm.doc.branch || "",
                        "account": frm.doc.payment_account || ""
                    };

                    frappe.set_route("query-report", "Salary Register New");
                }
            });
        }).addClass('btn btn-primary btn-sm primary-action');
    }
    
});
