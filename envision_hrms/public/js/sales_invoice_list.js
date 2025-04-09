frappe.provide("custom_project_formatter");

const doctypesWithProjectField = [
    'Stock Ledger Entry', 'Email Digest', 'Project Update', 'Subcontracting Receipt', 'Sales Order',
    'BOM Creator', 'Bank Guarantee', 'Asset Repair', 'Sales Invoice', 'Work Order', 'GL Entry',
    'Supplier Quotation', 'Issue', 'Stock Reservation Entry', 'Payment Entry', 'Production Plan',
    'Payment Request', 'Task', 'Job Card', 'Purchase Order', 'Delivery Note', 'Stock Entry',
    'Purchase Invoice', 'Account Closing Balance', 'POS Invoice', 'Subcontracting Order',
    'Purchase Receipt', 'Process Statement Of Accounts', 'BOM', 'Budget'
];

// Register formatter globally
doctypesWithProjectField.forEach(doctype => {
    frappe.listview_settings[doctype] = {
        onload: function(listview) {
            const project_column = listview.columns.find(col => col.df.fieldname === "project");
            if (project_column) {
                project_column.df.formatter = function(value, df, options, doc) {
                    if (!value || value.includes(":")) {
                        return value;
                    }

                    // Fetch project name once and cache
                    frappe.db.get_value('Project', value, 'project_name').then(r => {
                        if (r && r.message && r.message.project_name) {
                            const formatted = `${value}:${r.message.project_name}`;
                            // Replace displayed cell text
                            $(`[data-name="${doc.name}"] [data-fieldname="project"]`).text(formatted);
                        }
                    });

                    return value;
                };
            }
        }
    };
});
