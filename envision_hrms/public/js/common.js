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
                    frm.refresh_field('earnings');
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

frappe.ui.form.on('Retention Bonus', {
    bonus_wage : function(frm){
        frm.set_value("bonus_amount",0.00);
        frm.refresh_field("bonus_amount");
    },
    bonus_percentage : function(frm){
        frm.set_value("bonus_amount",0.00);
        frm.refresh_field("bonus_amount");
    },
    get_salary_slip : function(frm) {
        if (!frm.doc.from_date || !frm.doc.to_date){
            frappe.msgprint("Please select valid date range")
        }
        var yearly_bonus = frm.doc.yearly_bonus;
        var emp = frm.doc.employee;
        var from_date = frm.doc.from_date;
        var to_date = frm.doc.to_date;

        if (yearly_bonus === 1 && emp && from_date && to_date) {
            frappe.call({
                method: "envision_hrms.envision_hrms.custom_py.yearly_bonus.get_employee_bonus",
                args: {
                    employee: emp,
                    from_date: from_date,
                    to_date: to_date
                },
                async: false,
                callback: function (response) {
                    console.log(response.message);
                    if (response.message){
                        frm.clear_table("employee_bonus");

                        var salary_slips = response.message[0];
                        var get_salary_data = response.message[1];
                        var totalBonus = 0;
                        var totalAmount = 0.0;

                        for (var i = 0; i < salary_slips.length; i++) {
                            var row = frm.add_child("employee_bonus");
                            row.salary_slip = salary_slips[i].name;
                            row.basic_salary = salary_slips[i].base_gross_pay - get_salary_data[i].amount;
                            
                            var amount = salary_slips[i].base_gross_pay - get_salary_data[i].amount;
                            totalAmount += amount
                        }

                        frm.refresh_field("employee_bonus");
                        // frm.set_value("salary_component", "Bonus");
                        totalAmount = parseFloat(totalAmount.toFixed(0));
                        frm.set_value("bonus_wage", totalAmount);
                        frm.refresh_field("bonus_wage");
                    }
                    else{
                        frappe.msgprint("No Salary Slips Found between selected Dates")
                    }
                }
            });
        }
    },
    before_save:function(frm){
        if (frm.doc.yearly_bonus == 1 && frm.doc.bonus_percentage && frm.doc.bonus_wage) {
            if(frm.doc.bonus_amount == 0.00){
                var bp = frm.doc.bonus_percentage / 100 ;
                bp = parseFloat(bp.toFixed(4));
                console.log(bp)
                totalBonus = frm.doc.bonus_wage * bp;
                totalBonus = parseFloat(totalBonus.toFixed(0));
                console.log(totalBonus)
                frm.set_value("bonus_amount", totalBonus);
                frm.refresh_field("bonus_amount");
            }
        } 
    }
});

frappe.ui.form.on('Attendance Request', {
	before_save(frm) {
		if(frm.doc.reason == "Early Going" || frm.doc.reason == "Late Coming" || frm.doc.reason == "Missed Punch In" || frm.doc.reason == "Missed Punch Out"){
            if(frm.doc.from_date !== frm.doc.to_date){
                frappe.throw({
                    title: __('Validation'),
                    message: __('From Date and To Date must be the same for Early Going/Late Going'),
                    indicator: 'orange'
                });
            }
        }
	}
})