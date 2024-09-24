frappe.ui.form.on('Company', {
    onload: function(frm) {
        // Fetch the last custom_company_code
        if(frm.is_new()){
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Company',  // replace with your actual DocType
                    fields: ['custom_company_code'],
                    order_by: 'custom_company_code desc',
                    limit: 1
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        // Get the last custom_company_code and increment it
                        let last_code = parseInt(r.message[0].custom_company_code) || 0;
                        let next_code = last_code + 1;
                        
                        // Set the next custom_company_code
                        frm.set_value('custom_company_code', next_code);
                    } else {
                        // If no previous record found, set custom_company_code to 1
                        frm.set_value('custom_company_code', 1);
                    }
                }
            });
        }
    }
});
