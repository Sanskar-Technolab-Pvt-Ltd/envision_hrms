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

frappe.ui.form.on('Employee', {
    document_template: function (frm) {
        if (frm.doc.document_template) {
            // Fetch the Document Template details
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Employee Document Template",
                    name: frm.doc.document_template
                },
                callback: function (r) {
                    if (r.message) {
                        const document_template = r.message;
                        console.log(document_template)
                        const documents = document_template.documents || [];

                        // Clear the existing document_checklist table
                        frm.clear_table('document_checklist');

                        // Add each document to the checklist table
                        documents.forEach(doc => {
                            const row = frm.add_child('document_checklist');
                            row.document = doc.document; // Update the field name based on your field's actual name
                        });

                        // Refresh the table
                        frm.refresh_field('document_checklist');
                    }
                }
            });
        } else {
            // Clear the checklist table if no template is selected
            frm.clear_table('document_checklist');
            frm.refresh_field('document_checklist');
        }
    }
});
