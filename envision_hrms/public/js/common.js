frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        calculate_ot_hours(frm);
    }
});

function calculate_ot_hours(frm) {
    if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
        frappe.call({
            method: "envision_hrms.envision_hrms.custom_py.salary_ot_calculation.get_total_ot_hours",
            args: {
                employee: frm.doc.employee,
                from_date: frm.doc.start_date,
                to_date: frm.doc.end_date
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("custom_ot_hours", r.message);
                    frm.set_value('earnings', []);
                    frm.refresh_field('earnings');
                    frm.save()
                } else {
                    frm.set_value("custom_ot_hours", 0);
                }
            }
        });
    }
}