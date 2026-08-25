/* global frappe */
// All desk screens: company/branch come from navbar context; hide those fields everywhere.

(function () {
	"use strict";

	const SKIP_DOCTYPES = new Set([
		"Company",
		"Branch",
		"User",
		"User Branch Access",
		"Global Defaults",
		"System Settings",
		"Navbar Settings",
	]);

	const SCOPE_FIELDS = ["company", "branch"];

	function activate_scope_body_class() {
		document.body.classList.add("omnexa-navbar-scope-active");
	}

	function fetch_navbar_defaults(callback) {
		frappe.call({
			method: "omnexa_core.omnexa_core.user_context.get_navbar_form_defaults",
			callback(r) {
				callback((r && r.message) || {});
			},
		});
	}

	function resolve_scope_values(defaults) {
		const scope = frappe.omnexa_core?.view_scope?.get?.() || {};
		return {
			company: defaults?.company || scope.company || "",
			branch:
				defaults?.branch ||
				(scope.view_all_branches ? defaults?.branch || "" : scope.branch || defaults?.branch || ""),
			view_all_branches: Boolean(scope.view_all_branches),
		};
	}

	function hide_control(control) {
		if (!control) return;
		try {
			control.df.hidden = 1;
			control.df.read_only = 1;
			if (control.$wrapper) control.$wrapper.hide();
			if (control.wrapper) control.wrapper.classList.add("hidden");
		} catch (e) {
			/* ignore */
		}
	}

	function hide_scope_field(frm, fieldname) {
		if (!frm?.fields_dict?.[fieldname]) return;
		try {
			frm.set_df_property(fieldname, "hidden", 1);
			frm.set_df_property(fieldname, "read_only", 1);
			hide_control(frm.fields_dict[fieldname]);
		} catch (e) {
			/* ignore */
		}
	}

	function set_scope_values(frm, values) {
		if (!frm || !values?.company) return;
		if (frm.fields_dict.company && frm.doc.company !== values.company) {
			frm.set_value("company", values.company);
		}
		if (frm.fields_dict.branch) {
			const branch = values.branch || "";
			if (frm.doc.branch !== branch) {
				frm.set_value("branch", branch);
			}
		}
	}

	function hide_grid_scope_columns(frm) {
		if (!frm?.meta?.fields) return;
		frm.meta.fields.forEach((df) => {
			if (df.fieldtype !== "Table" || !df.fieldname) return;
			const grid = frm.fields_dict[df.fieldname]?.grid;
			if (!grid) return;
			SCOPE_FIELDS.forEach((fieldname) => {
				const has_field = (grid.docfields || []).some((row) => row.fieldname === fieldname);
				if (!has_field) return;
				try {
					grid.update_docfield_property(fieldname, "hidden", 1);
					grid.update_docfield_property(fieldname, "read_only", 1);
					grid.set_column_disp(fieldname, false);
				} catch (e) {
					/* ignore */
				}
			});
		});
	}

	function hide_all_scope_fields(frm) {
		SCOPE_FIELDS.forEach((fieldname) => hide_scope_field(frm, fieldname));
		hide_grid_scope_columns(frm);
	}

	function form_has_scope_fields(frm) {
		if (!frm?.meta) return false;
		const fields = frm.meta.fields || [];
		if (fields.some((df) => df && SCOPE_FIELDS.includes(df.fieldname))) return true;
		return fields.some((df) => {
			if (df.fieldtype !== "Table" || !df.options) return false;
			try {
				const child_meta = frappe.get_meta(df.options);
				return SCOPE_FIELDS.some((fn) => child_meta?.has_field?.(fn));
			} catch (e) {
				return false;
			}
		});
	}

	function should_scope_form(frm) {
		if (!frm || !frm.meta) return false;
		if (SKIP_DOCTYPES.has(frm.doctype)) return false;
		return form_has_scope_fields(frm);
	}

	function apply_navbar_scope_to_form(frm) {
		if (!should_scope_form(frm)) return;
		activate_scope_body_class();

		const scope = frappe.omnexa_core?.view_scope?.get?.() || {};
		const apply_values = (defaults) => {
			const values = resolve_scope_values(defaults);
			if (!values.company) return;
			set_scope_values(frm, values);
			hide_all_scope_fields(frm);
		};

		if (scope.company && !(scope.view_all_branches && frm.fields_dict.branch && !frm.doc.branch)) {
			apply_values({});
			return;
		}

		fetch_navbar_defaults(apply_values);
	}

	function hide_list_scope_field(listview, fieldname, value) {
		const field = listview.page?.fields_dict?.[fieldname];
		if (!field) return;
		if (value !== undefined && value !== null) field.set_value(value);
		hide_control(field);
	}

	function apply_navbar_scope_to_listview(listview) {
		if (!listview?.meta) return;
		const fields = listview.meta.fields || [];
		const hasCompany = fields.some((df) => df && df.fieldname === "company");
		const hasBranch = fields.some((df) => df && df.fieldname === "branch");
		if (!hasCompany && !hasBranch) return;

		activate_scope_body_class();
		const apply_values = (defaults) => {
			const values = resolve_scope_values(defaults);
			if (!values.company) return;
			hide_list_scope_field(listview, "company", values.company);
			if (hasBranch) hide_list_scope_field(listview, "branch", values.branch || "");
		};

		const scope = frappe.omnexa_core?.view_scope?.get?.() || {};
		if (scope.company && !scope.view_all_branches) {
			apply_values({});
			return;
		}
		fetch_navbar_defaults(apply_values);
	}

	function apply_navbar_scope_to_report(report) {
		if (!report || !Array.isArray(report.filters)) return;
		activate_scope_body_class();
		frappe.omnexa_core?.view_scope?.apply_to_report?.(report);
	}

	frappe.ui.form.on("*", {
		onload(frm) {
			apply_navbar_scope_to_form(frm);
		},
		refresh(frm) {
			apply_navbar_scope_to_form(frm);
		},
	});

	if (frappe.views?.ListView?.prototype?.setup_main_section) {
		const _setup_main_section = frappe.views.ListView.prototype.setup_main_section;
		frappe.views.ListView.prototype.setup_main_section = function () {
			return _setup_main_section.apply(this, arguments).then(() => {
				apply_navbar_scope_to_listview(this);
			});
		};
	}

	const report_proto = frappe.views?.QueryReport?.prototype;
	if (report_proto && !report_proto.__omnexa_navbar_scope_patched) {
		report_proto.__omnexa_navbar_scope_patched = true;
		const _setup_filters = report_proto.setup_filters;
		report_proto.setup_filters = function () {
			const out = _setup_filters.apply(this, arguments);
			frappe.after_ajax(() => apply_navbar_scope_to_report(this));
			apply_navbar_scope_to_report(this);
			return out;
		};
	}

	activate_scope_body_class();
})();
