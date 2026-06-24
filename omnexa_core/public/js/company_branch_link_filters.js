/* global frappe */
// Company → Branch coherence on every desk form: branch picker shows only branches of the selected company.

(function () {
	"use strict";

	const EMPTY_BRANCH_QUERY = { filters: { name: ["in", []] } };

	function resolve_company(frm, row) {
		return (row && row.company) || frm.doc.company || "";
	}

	function branch_query(company) {
		return company ? { filters: { company } } : EMPTY_BRANCH_QUERY;
	}

	function apply_branch_queries(frm) {
		if (!frm || !frm.meta) return;

		if (frm.meta.has_field("branch")) {
			frm.set_query("branch", () => branch_query(frm.doc.company));
		}

		if (frm.doctype === "Branch" && frm.meta.has_field("parent_branch")) {
			frm.set_query("parent_branch", () => branch_query(frm.doc.company));
		}

		(frm.meta.fields || []).forEach((df) => {
			if (df.fieldtype !== "Table" || !df.options) return;
			let child_meta;
			try {
				child_meta = frappe.get_meta(df.options);
			} catch (e) {
				return;
			}
			if (!child_meta || !child_meta.has_field("branch")) return;
			frm.set_query("branch", df.fieldname, (doc, cdt, cdn) => {
				const row = locals[cdt][cdn];
				return branch_query(resolve_company(frm, row));
			});
		});
	}

	function clear_mismatched_branch(frm) {
		if (!frm.doc.branch) return;
		if (!frm.doc.company) {
			frm.set_value("branch", "");
			return;
		}
		frappe.db.get_value("Branch", frm.doc.branch, "company").then((r) => {
			const branch_company = r && r.message;
			if (branch_company && branch_company !== frm.doc.company) {
				frm.set_value("branch", "");
			}
		});
	}

	function clear_mismatched_parent_branch(frm) {
		if (frm.doctype !== "Branch" || !frm.doc.parent_branch) return;
		if (!frm.doc.company) {
			frm.set_value("parent_branch", "");
			return;
		}
		frappe.db.get_value("Branch", frm.doc.parent_branch, "company").then((r) => {
			const branch_company = r && r.message;
			if (branch_company && branch_company !== frm.doc.company) {
				frm.set_value("parent_branch", "");
			}
		});
	}

	frappe.ui.form.on("*", {
		onload(frm) {
			apply_branch_queries(frm);
		},
		refresh(frm) {
			apply_branch_queries(frm);
		},
		company(frm) {
			clear_mismatched_branch(frm);
			apply_branch_queries(frm);
		},
		branch(frm) {
			if (!frm.doc.branch || !frm.doc.company) return;
			frappe.db.get_value("Branch", frm.doc.branch, "company").then((r) => {
				const branch_company = r && r.message;
				if (branch_company && branch_company !== frm.doc.company) {
					frappe.msgprint({
						title: __("Invalid Branch"),
						indicator: "red",
						message: __("Branch {0} does not belong to Company {1}.", [
							frm.doc.branch,
							frm.doc.company,
						]),
					});
					frm.set_value("branch", "");
				}
			});
		},
	});

	frappe.ui.form.on("Branch", {
		parent_branch(frm) {
			if (!frm.doc.parent_branch || !frm.doc.company) return;
			frappe.db.get_value("Branch", frm.doc.parent_branch, "company").then((r) => {
				const branch_company = r && r.message;
				if (branch_company && branch_company !== frm.doc.company) {
					frappe.msgprint({
						title: __("Invalid Branch"),
						indicator: "red",
						message: __("Parent Branch must belong to the same Company."),
					});
					frm.set_value("parent_branch", "");
				}
			});
		},
		company(frm) {
			clear_mismatched_parent_branch(frm);
		},
	});
})();
