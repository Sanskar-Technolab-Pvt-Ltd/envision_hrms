// Copyright (c) 2025, Pooja Vadher and contributors
// For license information, please see license.txt

frappe.query_reports["PF ECR"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		}
	],
	"onload": function (report) {
		report.page.add_inner_button(__('PF-ECR'), function () {
			let d = new frappe.ui.Dialog({
				title: 'Select Date for PF-ECR',
				fields: [
					{
						label: 'Date',
						fieldname: 'date',
						fieldtype: 'Date',
						reqd: 1
					}
				],
				size: 'small',
				primary_action_label: 'Submit',
				primary_action(values) {
					frappe.call({
						method: 'envision_hrms.envision_hrms.report.pf_ecr.pf_ecr_api.generate_txt',
						args: {
							selected_date: values.date,
						},
						callback: function (response) {
							console.log(response);
							if (response.message) {
								var link = document.createElement('a');
								link.href = '/files/' + response.message;
								link.download = 'PF_ECR.txt';
								link.click();
							}
						}
					});
					d.hide();
				}
			});

			d.show();
		});
	}
};
