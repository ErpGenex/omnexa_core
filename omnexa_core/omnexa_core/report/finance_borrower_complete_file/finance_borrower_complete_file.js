frappe.query_reports["Finance Borrower Complete File"] = {
	filters: [
		{
			fieldname: "case_doctype",
			label: __("Case DocType"),
			fieldtype: "Select",
			reqd: 1,
			options: [],
		},
		{
			fieldname: "case_name",
			label: __("Case / Borrower File"),
			fieldtype: "Dynamic Link",
			options: "case_doctype",
			reqd: 1,
		},
	],
	onload(report) {
		const bootList = (frappe.boot && frappe.boot.finance_case_doctypes) || [];
		const options = bootList.map((r) => r.doctype).join("\n");
		const df = report.get_filter("case_doctype");
		if (df) {
			df.df.options = options || df.df.options;
			df.refresh();
		}
		const ro = frappe.route_options || {};
		if (ro.case_doctype) {
			report.set_filter_value("case_doctype", ro.case_doctype);
		}
		if (ro.case_name) {
			report.set_filter_value("case_name", ro.case_name);
		}
		if (ro.case_doctype && ro.case_name) {
			setTimeout(() => report.refresh(), 300);
		}
	},
};
