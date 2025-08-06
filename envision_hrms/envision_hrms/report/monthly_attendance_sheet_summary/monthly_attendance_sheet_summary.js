// Copyright (c) 2025, Pooja Vadher and contributors
// For license information, please see license.txt


frappe.query_reports["Monthly Attendance Sheet Summary"] = {
   filters: [
       {
           fieldname: "company",
           label: ("Company"),
           fieldtype: "Link",
           options: "Company",
           default: frappe.defaults.get_user_default("Company"),
           reqd: 1,
       },
       {
           fieldname: "month",
           label: ("Month"),
           fieldtype: "Select",
           reqd: 1,
           options: [
               { value: 1, label: ("Jan") },
               { value: 2, label: ("Feb") },
               { value: 3, label: ("Mar") },
               { value: 4, label: ("Apr") },
               { value: 5, label: ("May") },
               { value: 6, label: ("June") },
               { value: 7, label: ("July") },
               { value: 8, label: ("Aug") },
               { value: 9, label: ("Sep") },
               { value: 10, label: ("Oct") },
               { value: 11, label: ("Nov") },
               { value: 12, label: ("Dec") },
           ],
           default: frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
       },
       {
           fieldname: "year",
           label: ("Year"),
           fieldtype: "Select",
           reqd: 1,
       },
       {
           fieldname: "employee",
           label: ("Employee"),
           fieldtype: "Link",
           options: "Employee",
           get_query: () => {
               var company = frappe.query_report.get_filter_value("company");
               return {
                   filters: {
                       company: company,
                   },
               };
           },
       },
      
       {
           fieldname: "group_by",
           label: ("Group By"),
           fieldtype: "Select",
           options: [
               { value: "", label: ("") },
               { value: "department", label: ("Department") },
               { value: "designation", label: ("Designation") },
               { value: "branch", label: ("Branch") }
           ],
           default: "",
       },
   ],
  
   onload: function () {
       return frappe.call({
           method: "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
           callback: function (r) {
               var year_filter = frappe.query_report.get_filter("year");
               year_filter.df.options = r.message;
               year_filter.df.default = r.message.split("\n")[0];
               year_filter.refresh();
               year_filter.set_input(year_filter.df.default);
           },
       });
   },
  
   formatter: function (value, row, column, data, default_formatter) {
       // Handle group headers formatting
       if (data && data.is_group) {
           if (column.fieldname === "employee_name") {
               return `<span style="font-weight: bold;">${value}</span>`;
           }
           return "";
       }
       return default_formatter(value, row, column, data);
   },
  
   tree: true, // Enable tree view for grouping
  
   parent_field: "parent_account", // Field that identifies the parent
  
   initial_depth: 1, // Show groups expanded by default
}
