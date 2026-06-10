// Copyright (c) 2026, Omnexa and contributors
// License: MIT

function omnexa_healthcare_demo_installed() {
	const apps = frappe.boot.erpgenex_installed_apps || frappe.boot.installed_apps || [];
	return apps.indexOf("omnexa_healthcare") >= 0;
}

frappe.ui.form.on("Branch", {
	refresh(frm) {
		if (frm.is_new() || !(frappe.session.user === "Administrator" || frappe.user.has_role("System Manager"))) {
			return;
		}
		if (!omnexa_healthcare_demo_installed()) {
			return;
		}
		if (!frm.doc.branch_demo_activity) {
			frm.set_value("branch_demo_activity", "Healthcare");
		}
	},
});
