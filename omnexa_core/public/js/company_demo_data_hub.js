// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

function omnexa_sync_company_modified(frm) {
	if (frm.is_new() || !frm.doc.name || frm.is_dirty()) {
		return;
	}
	frappe.db.get_value("Company", frm.doc.name, "modified").then((row) => {
		if (row?.modified && frm.doc.modified !== row.modified) {
			frm.doc.modified = row.modified;
		}
	});
}

frappe.ui.form.on("Company", {
	refresh(frm) {
		omnexa_sync_company_modified(frm);

		if (frm.is_new() || !(frappe.session.user === "Administrator" || frappe.user.has_role("System Manager"))) {
			return;
		}
		const wipe_btn = frm.fields_dict.demo_btn_wipe_all;
		if (!wipe_btn || wipe_btn._omnexa_wipe_bound) {
			return;
		}
		wipe_btn._omnexa_wipe_bound = true;
		wipe_btn.$input.off("click").on("click", () => {
			const confirm = (frm.doc.demo_danger_confirm || "").trim().toUpperCase();
			if (!["DELETE ALL", "DELETEALL"].includes(confirm.replace(/\s+/g, ""))) {
				frappe.msgprint({
					title: __("Wipe company data"),
					message: __("Type <b>DELETE ALL</b> in the confirm field, then click the button again."),
					indicator: "orange",
				});
				return;
			}
			frappe.confirm(
				__(
					"This permanently deletes all transactions, masters, chart of accounts, construction demo data, and <b>all branches</b> for {0}. Continue?",
					[frm.doc.name]
				),
				() => {
					frappe.call({
						method: "omnexa_core.omnexa_core.company_demo_api.wipe_company_all",
						args: {
							company: frm.doc.name,
							confirm_text: frm.doc.demo_danger_confirm,
						},
						freeze: true,
						freeze_message: __("Queuing company wipe…"),
						callback(r) {
							if (!r.exc && r.message) {
								const job = r.message.job_id || "n/a";
								frappe.msgprint({
									title: __("Wipe company data"),
									message: __(
										"Company wipe queued. Job: {0}. The form will refresh when the job finishes.",
										[job]
									),
									indicator: "green",
								});
								omnexa_reload_company_after_wipe(frm);
							}
						},
					});
				}
			);
		});
	},
});

function omnexa_reload_company_after_wipe(frm) {
	if (!frm.doc?.name) {
		return;
	}
	frm.reload_doc();
	[8000, 25000, 60000].forEach((ms) => {
		setTimeout(() => {
			if (frm.doc?.name) {
				frm.reload_doc();
			}
		}, ms);
	});
}
