frappe.ui.form.on('Expense Claim', {
    // before_submit: function(frm) {
    //     // Check if the approval status is 'Approved'
    //     if (frm.doc.approval_status === 'Approved') {
    //         // Clear logged errors to ensure fresh validation
    //         loggedErrors.clear();
    
    //         // Trigger the validation for all rows in the child table
    //         let hasErrors = validate_all_expense_details(frm);
    //         if (hasErrors) {
    //             frappe.validated = false; // Prevent form submission
    //         }
    //     }
    // },
    before_save: async function(frm) {
        if (frm.doc.company) {
            let company_limit = await frappe.db.get_value("Company", frm.doc.company, 'custom_validate_limit');
            if (company_limit.message && company_limit.message.custom_validate_limit == 1) {
                // console.log("Maximum Limit Validate");
    
                let max_limit_res = await frappe.db.get_value("Company", frm.doc.company, 'custom_maximum_limit_');
                let max_limit = max_limit_res.message.custom_maximum_limit_;
    
                if (frm.doc.total_claimed_amount > max_limit) {
                    frappe.throw({
                        title: __("Amount Validation"), // Custom error title
                        message: __("Maximum expense claim limit is <b>{0}</b>. Please raise another request for remaining amount", [max_limit])
                    });
                    frappe.validated = false; // Prevent form save
                }
            }
        }
    },
    refresh: function(frm) {
        frm.fields_dict['expenses'].grid.get_field('purchase_invoice').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            if (child.is_purchase_invoice_included && frm.doc.company) {
                return {
                    filters: {
                        company: frm.doc.company
                    }
                };
            }
        };
    }
});


let loggedErrors = new Set(); // Reset this in the approval_status function
function validate_expense_detail(frm, cdt, cdn, totalAmount) {
    let row = locals[cdt][cdn];
    let custom_category = row.custom_category;
    let expense_type = row.expense_type;
    let custom_grade = frm.doc.custom_grade;
    let custom_annexure_type = frm.doc.custom_annexure_type;
    let limit_expenses = row.limit_expenses

    if (limit_expenses) {
        // Fetch all records from the 'Expense Claim Type' doctype
        return frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Expense Claim Type',
                fields: ['name'],
                limit_page_length: 0
            },
            callback: function(response) {
                if (response.message) {
                    let valid = false;
                    let rowsToReset = [];

                    let expenseClaimTypeRequests = response.message.map(function(expense_claim_type) {
                        return frappe.call({
                            method: 'frappe.client.get',
                            args: {
                                doctype: 'Expense Claim Type',
                                name: expense_claim_type.name
                            }
                        });
                    });

                    return Promise.all(expenseClaimTypeRequests).then(results => {
                        results.forEach(function(expense_claim_type_response) {
                            if (expense_claim_type_response.message) {
                                let expense_claim_type_doc = expense_claim_type_response.message;

                                expense_claim_type_doc.custom_annexure.forEach(function(annexure_row) {
                                    if (annexure_row.annexure_type === custom_annexure_type &&
                                        annexure_row.grade === custom_grade &&
                                        annexure_row.category === custom_category &&
                                        expense_claim_type_doc.name === expense_type) {
                                        valid = true;

                                        let errorKey = `${custom_annexure_type}-${custom_grade}-${custom_category}-${expense_type}`;
                                        if (!loggedErrors.has(errorKey)) {
                                            if (totalAmount > annexure_row.amount) {
                                                let matchingRows = frm.doc.expenses
                                                    .map((otherRow, index) => {
                                                        return (otherRow.custom_category === custom_category && otherRow.expense_type === expense_type) ? index + 1 : null;
                                                    })
                                                    .filter(rowNumber => rowNumber !== null);

                                                frappe.msgprint(__('<b>Row: {2}</b>, Expense Type: {3}, Category: {4}. The requested total amount is {0} but Maximum allowed is {1}.',
                                                    [totalAmount, annexure_row.amount, matchingRows.join(', '), expense_type, custom_category]));

                                                frm.doc.expenses.forEach(function(otherRow) {
                                                    if (otherRow.custom_category === custom_category &&
                                                        otherRow.expense_type === expense_type) {
                                                        rowsToReset.push(otherRow.name);
                                                    }
                                                });

                                                loggedErrors.add(errorKey);
                                            } else {
                                                console.log('Allowed Amount:', annexure_row.amount);
                                            }
                                        }
                                    }
                                });
                            }
                        });

                        if (!valid) {
                            let errorKey = `${custom_annexure_type}-${custom_grade}-${custom_category}-${expense_type}`;
                            if (!loggedErrors.has(errorKey)) {
                                let currentRowNumber = frm.doc.expenses.findIndex(row => row.name === cdn) + 1;
                                frappe.msgprint(__('<b>Row: {0}</b>, Please Set Limit For Expense Type: {1}, Category: {2}',
                                    [currentRowNumber, expense_type, custom_category]));
                                rowsToReset.push(cdn);
                                loggedErrors.add(errorKey);
                            }
                        }

                        // Set All value 0
                        // rowsToReset.forEach(function(rowName) {
                        //     frappe.model.set_value(cdt, rowName, 'amount', 0);
                        // });

                        return rowsToReset.length > 0; // Return if any rows were reset
                    });
                }
            }
        });
    } else {
        console.log('Please ensure all required fields are filled.');
    }

    return false; // Default to no errors found if not validated
}

function validate_all_expense_details(frm) {
    let expenseSums = {};

    frm.doc.expenses.forEach(function(row) {
        let key = `${row.expense_type}-${row.custom_category}`;
        if (!expenseSums[key]) {
            expenseSums[key] = 0;
        }
        expenseSums[key] += row.amount;
    });

    let hasErrors = false;
    frm.doc.expenses.forEach(function(row) {
        let key = `${row.expense_type}-${row.custom_category}`;
        let result = validate_expense_detail(frm, row.doctype, row.name, expenseSums[key]);
        if (result) {
            hasErrors = true;
        }
    });

    return hasErrors;
}

