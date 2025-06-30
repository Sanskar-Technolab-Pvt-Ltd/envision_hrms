// Copyright (c) 2024, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Probation", {
	onload(frm) {
        frm.set_query("employee", function () {
            return {
                filters: {
                    'employment_type': "Probation",
                    'status' : "Active"
                }
            };
        });
        if(!frm.doc.transfer){
            frm.set_value('new_company', "");
            frm.refresh_field('new_company');
        }
	},
    refresh(frm){
        frm.fields_dict['probation_duration'].grid.get_field('appraisal').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                filters: {
                    'employee': frm.doc.employee,
                    'docstatus' : 1
                }
            };
        };
        if(!frm.doc.transfer){
            frm.set_value('new_company', "");
            frm.refresh_field('new_company');
        }
    }
});
