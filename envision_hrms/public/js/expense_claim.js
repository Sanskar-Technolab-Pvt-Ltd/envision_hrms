frappe.ui.form.on('Expense Claim', {
    // onload: function(frm) {
    //     // Initially show the expenses table (if needed)
    //     frm.toggle_display('expenses', true);
    // },

    // custom_grade: function(frm) {
    //     // Trigger the validation for all rows in the child table when the grade is changed
    //     validate_all_expense_details(frm);
    // },
    validate: function(frm) {
        // Check if the approval status is 'Approved'
        if (frm.doc.approval_status === 'Approved') {
            // Clear logged errors to ensure fresh validation
            loggedErrors.clear();
    
            // Trigger the validation for all rows in the child table
            let hasErrors = validate_all_expense_details(frm);
            if (hasErrors) {
                frappe.validated = false; // Prevent form submission
            }
        }
    }
    
    
    // custom_annexure_type: function(frm) {
    //     // Trigger the validation for all rows in the child table when the annexure type is changed
    //     validate_all_expense_details(frm);
    // }
});

// frappe.ui.form.on('Expense Claim Detail', {
//     amount: function(frm, cdt, cdn) {
//         validate_expense_detail(frm, cdt, cdn);
//     },

//     expense_type: function(frm, cdt, cdn) {
//         validate_expense_detail(frm, cdt, cdn);
//     },

//     custom_category: function(frm, cdt, cdn) {
//         validate_expense_detail(frm, cdt, cdn);
//     }
// });
// Function to hide <hr> tags inside the modal
let loggedErrors = new Set(); // Reset this in the approval_status function
function validate_expense_detail(frm, cdt, cdn, totalAmount) {
    let row = locals[cdt][cdn];
    let custom_category = row.custom_category;
    let expense_type = row.expense_type;
    let custom_grade = frm.doc.custom_grade;
    let custom_annexure_type = frm.doc.custom_annexure_type;

    if (custom_grade && custom_annexure_type && custom_category && expense_type) {
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

                                                frappe.msgprint(__('<b>Row: {2}</b>, Expense Type: {3}, Category: {4} for applied Total amount is {0} but Maximum allowed is {1}.',
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
                                frappe.msgprint(__('<b>Row: {0}</b>, Expense Type: {1}, Category: {2} for amount Not Found.',
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