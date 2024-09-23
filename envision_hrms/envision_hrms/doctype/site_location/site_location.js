// Copyright (c) 2024, Pooja Vadher and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Site Location", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Site Location', {
    // Triggered when the location_code field value changes
    location_code: function(frm) {
        let field_value = frm.doc.location_code || '';
        
        // Set of allowed digits
        let allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        
        // Check if the input contains only allowed digits
        if (field_value.split('').every(char => allowed_characters.includes(char))) {
            // Input is valid
            return;
        } else {
            // Invalid input
            frappe.msgprint(__('Location Code field value must only contain digits.'));
            // frm.set_value('location_code', ''); // Clear the field
        }
    },

    // Triggered before saving the form
    validate: function(frm) {
        let field_value = frm.doc.location_code || '';
        
        // Set of allowed digits
        let allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        
        // Check if the input contains only allowed digits
        if (!field_value.split('').every(char => allowed_characters.includes(char))) {
            frappe.msgprint(__('Location Code field value must only contain digits.'));
            frappe.validated = false; // Prevent the form from being saved
        }
    }
});