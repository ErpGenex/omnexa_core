/* global frappe */
// Universal Query Report filters: Company → Branch → From Date → To Date (when missing).
// Defaults from user/session context; dates default to Today. Server-side reinforcement in report_defaults.py.

(function () {
	function today_str() {
		return frappe.datetime.get_today();
	}

	function default_company() {
		return (
			frappe.defaults.get_user_default("company") ||
			frappe.defaults.get_user_default("Company") ||
			(frappe.boot?.user?.defaults?.company || "")
		);
	}

	function default_branch() {
		return (
			frappe.defaults.get_user_default("branch") ||
			frappe.defaults.get_user_default("Branch") ||
			(frappe.boot?.user?.defaults?.branch || "")
		);
	}

	function has_field(filters, fieldname) {
		return !!(filters || []).some((df) => df && df.fieldname === fieldname);
	}

	// Map ambiguous filter definitions to DocType-backed Link filters (dropdown picker UX).
	const _FIELD_TO_LINK_DT = {
		company: "Company",
		branch: "Branch",
		warehouse: "Warehouse",
		warehouse_from: "Warehouse",
		warehouse_to: "Warehouse",
		from_warehouse: "Warehouse",
		to_warehouse: "Warehouse",
		cost_center: "Cost Center",
		project: "Project",
		customer: "Customer",
		supplier: "Supplier",
		employee: "Employee",
		department: "Department",
		designation: "Designation",
		item: "Item",
		item_code: "Item",
		batch: "Batch",
		serial_no: "Serial No",
		item_group: "Item Group",
		brand: "Brand",
		territory: "Territory",
		customer_group: "Customer Group",
		supplier_group: "Supplier Group",
		mode_of_payment: "Mode of Payment",
		payment_mode: "Mode of Payment",
		bank_account: "Bank Account",
		fiscal_year: "Fiscal Year",
		party_type: "Party Type",
		gl_account: "GL Account",
	};

	function _ensure_branch_get_query(report, df) {
		if (!df || df.fieldname !== "branch" || df.fieldtype !== "Link" || df.get_query) return;
		df.get_query = () => {
			const c =
				report.get_filter_value?.("company", false) ||
				frappe.defaults.get_user_default("company") ||
				frappe.defaults.get_user_default("Company") ||
				"";
			return c ? { filters: { company: c } } : {};
		};
	}

	function normalize_filters_for_link_dropdowns(report, filter_defs) {
		for (const df of filter_defs || []) {
			if (!df || !df.fieldname || df.fieldtype === "Break") continue;

			const dt = _FIELD_TO_LINK_DT[df.fieldname];
			if (dt) {
				if (df.fieldtype === "Link" && !df.options) {
					df.options = dt;
				} else if (df.fieldtype === "Data" || df.fieldtype === "Autocomplete") {
					df.fieldtype = "Link";
					df.options = dt;
				}
			}

			if (df.fieldtype === "Link") {
				_ensure_branch_get_query(report, df);
			}
		}
	}

	function build_std_filter_defs(report, existing_filters) {
		const t = today_str();
		const defs = [];

		const comp = default_company();

		if (!has_field(existing_filters, "company")) {
			defs.push({
				fieldname: "company",
				fieldtype: "Link",
				options: "Company",
				label: __("Company"),
				default: comp || undefined,
				width: "80px",
			});
		}

		const branchDf = has_field(existing_filters, "branch")
			? null
			: {
					fieldname: "branch",
					fieldtype: "Link",
					options: "Branch",
					label: __("Branch"),
					default: default_branch() || undefined,
					width: "80px",
					get_query: () => {
						const c =
							report.get_filter_value?.("company", false) || default_company();
						return c ? { filters: { company: c } } : {};
					},
				};
		if (branchDf) {
			defs.push(branchDf);
		}

		if (!has_field(existing_filters, "from_date")) {
			defs.push({
				fieldname: "from_date",
				fieldtype: "Date",
				label: __("From Date"),
				default: t,
				width: "80px",
			});
		}
		if (!has_field(existing_filters, "to_date")) {
			defs.push({
				fieldname: "to_date",
				fieldtype: "Date",
				label: __("To Date"),
				default: t,
				width: "80px",
			});
		}
		return defs;
	}

	function inject_standard_filters(report) {
		const rs = report.report_settings;
		if (!rs) return;
		const base = rs.filters ? [...rs.filters] : [];
		const extra = build_std_filter_defs(report, base);
		rs.filters = [...extra, ...base];
		try {
			normalize_filters_for_link_dropdowns(report, rs.filters);
		} catch (e) {
			/* ignore */
		}
	}

	function _set_values_if_empty(report) {
		if (!report || !Array.isArray(report.filters)) return;

		const t = today_str();
		const comp = default_company();
		const br = default_branch();

		const byName = {};
		report.filters.forEach((f) => {
			if (f?.df?.fieldname) byName[f.df.fieldname] = f;
		});

		function set_if_empty(fn, val) {
			if (val === undefined || val === null || val === "") return;
			if (!byName[fn]) return;
			const cur = typeof byName[fn].get_value === "function" ? byName[fn].get_value() : null;
			if (cur !== undefined && cur !== null && cur !== "") return;
			if (report.set_filter_value) {
				report.set_filter_value(fn, val);
			}
		}

		set_if_empty("company", comp);
		set_if_empty("branch", br);
		set_if_empty("from_date", t);
		set_if_empty("to_date", t);

		report.filters.forEach((f) => {
			const df = f?.df || {};
			if (df.fieldtype !== "Date") return;
			const fieldname = (df.fieldname || "").toLowerCase();
			const label = (df.label || "").toLowerCase();
			const isFrom =
				fieldname.includes("from") ||
				label.includes("from") ||
				fieldname === "start_date";
			const isTo =
				fieldname.includes("to") ||
				label.includes("to") ||
				fieldname === "end_date";

			if (!isFrom && !isTo) return;
			const current = typeof f.get_value === "function" ? f.get_value() : "";
			if (current !== undefined && current !== null && current !== "") return;
			report.set_filter_value?.(df.fieldname, t);
		});
	}

	const proto = frappe.views?.QueryReport?.prototype;
	if (!proto || proto.__omnexa_report_filters_patched) return;
	proto.__omnexa_report_filters_patched = true;

	const originalSetupFilters = proto.setup_filters;
	proto.setup_filters = function () {
		try {
			inject_standard_filters(this);
		} catch (e) {
			/* never break desk */
		}
		const out = originalSetupFilters.apply(this, arguments);
		try {
			_set_values_if_empty(this);
			frappe.after_ajax(() => _set_values_if_empty(this));
		} catch (e) {
			/* ignore */
		}
		return out;
	};

	const originalRefresh = proto.refresh;
	if (typeof originalRefresh === "function") {
		proto.refresh = function () {
			try {
				_set_values_if_empty(this);
			} catch (e) {
				/* ignore */
			}
			return originalRefresh.apply(this, arguments);
		};
	}
})();
