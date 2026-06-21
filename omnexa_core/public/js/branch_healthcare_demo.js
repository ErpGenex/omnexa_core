// Copyright (c) 2026, Omnexa and contributors
// License: MIT

function omnexa_installed(app) {
	const apps = frappe.boot.erpgenex_installed_apps || frappe.boot.installed_apps || [];
	return apps.indexOf(app) >= 0;
}

function omnexa_healthcare_demo_installed() {
	return omnexa_installed("omnexa_healthcare");
}

function omnexa_finance_group_installed() {
	return omnexa_installed("omnexa_finance_engine") && omnexa_installed("omnexa_sme_retail_finance");
}

frappe.ui.form.on("Branch", {
	refresh(frm) {
		if (frm.is_new() || !(frappe.session.user === "Administrator" || frappe.user.has_role("System Manager"))) {
			return;
		}
		if (omnexa_healthcare_demo_installed() && !frm.doc.branch_demo_activity) {
			frm.set_value("branch_demo_activity", "Healthcare");
		}
		if (omnexa_finance_group_installed() && frm.doc.branch_demo_activity === "Financial Services") {
			frm.set_df_property("branch_demo_finance_customers", "description", __("Clients/cases per finance vertical app (default 50)."));
		}
	},
	branch_demo_activity(frm) {
		if (frm.doc.branch_demo_activity === "Financial Services" && omnexa_finance_group_installed()) {
			if (!frm.doc.branch_demo_finance_customers) {
				frm.set_value("branch_demo_finance_customers", 50);
			}
		}
	},
});
