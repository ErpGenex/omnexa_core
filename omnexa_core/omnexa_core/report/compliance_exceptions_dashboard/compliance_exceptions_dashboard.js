frappe.query_reports["Compliance Exceptions Dashboard"] = {
	filters: [
		{
			fieldname: "hours",
			label: __("Window (Hours)"),
			fieldtype: "Int",
			default: 24,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "reference_doctype",
			label: __("DocType"),
			fieldtype: "Data",
		},
		{
			fieldname: "rule_code",
			label: __("Rule Code"),
			fieldtype: "Data",
		},
	],
};
