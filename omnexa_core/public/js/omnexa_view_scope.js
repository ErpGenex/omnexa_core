/* global frappe */
// Shared desk view scope from navbar (company / branch / all branches).

(function () {
	function cint(v) {
		return parseInt(v, 10) || 0;
	}

	function read_default(keys) {
		for (const key of keys) {
			const val = frappe.defaults.get_user_default(key);
			if (val !== undefined && val !== null && val !== "") return val;
		}
		return "";
	}

	function get_navbar_view_scope() {
		const boot = (frappe.boot && frappe.boot.omnexa_view_context) || {};
		const company =
			boot.company ||
			read_default(["omnexa_view_company", "company", "Company"]) ||
			(frappe.boot?.user?.defaults?.company || "");

		const view_all_branches =
			Boolean(boot.view_all_branches) ||
			cint(read_default(["omnexa_view_all_branches"])) === 1;

		let branch = "";
		if (!view_all_branches) {
			branch =
				boot.branch ||
				read_default(["omnexa_view_branch", "branch", "Branch"]) ||
				(frappe.boot?.user?.defaults?.branch || "");
			if (branch === "__ALL__") branch = "";
		}

		return {
			company: company || "",
			branch: branch || "",
			view_all_branches,
			has_scope: Boolean(company),
			lock_filters: Boolean(company),
			label: boot.label || "",
		};
	}

	function default_company() {
		return get_navbar_view_scope().company;
	}

	function default_branch() {
		const scope = get_navbar_view_scope();
		return scope.view_all_branches ? "" : scope.branch;
	}

	function apply_scope_to_report_filters(report) {
		if (!report || !Array.isArray(report.filters)) return;

		const scope = get_navbar_view_scope();
		if (!scope.has_scope) return;

		if (scope.company && report.set_filter_value) {
			report.set_filter_value("company", scope.company);
		}
		if (scope.branch && !scope.view_all_branches) {
			report.set_filter_value("branch", scope.branch);
		} else if (scope.view_all_branches && report.set_filter_value) {
			report.set_filter_value("branch", "");
		}

		if (!scope.lock_filters) return;

		report.filters.forEach((f) => {
			const fn = f?.df?.fieldname;
			if (fn !== "company" && fn !== "branch") return;
			f.df.read_only = 1;
			f.df.hidden = 1;
			if (f.$wrapper) f.$wrapper.hide();
		});
	}

	frappe.provide("omnexa_core.view_scope");
	omnexa_core.view_scope.get = get_navbar_view_scope;
	omnexa_core.view_scope.default_company = default_company;
	omnexa_core.view_scope.default_branch = default_branch;
	omnexa_core.view_scope.apply_to_report = apply_scope_to_report_filters;
})();
