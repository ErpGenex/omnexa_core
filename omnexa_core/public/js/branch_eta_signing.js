// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

frappe.ui.form.on("Branch", {
	refresh(frm) {
		if (!frm.doc.eta_einvoice_enabled) {
			return;
		}
		if (frm.doc.eta_signer_mode === "signing_agent" || frm.doc.eta_signer_mode === "windows_app") {
			frm.set_df_property(
				"eta_usb_signing_pin",
				"description",
				__(
					"Required. Same as Temp-ETR USB PIN. Used for E-Invoice only (not E-Receipt). Re-enter and Save when changing."
				)
			);
			if (!frm.is_new()) {
				frappe.call({
					method:
						"omnexa_einvoice.omnexa_einvoice.doctype.e_invoice_submission.e_invoice_submission.get_branch_usb_signing_status",
					args: { branch: frm.doc.name },
					callback(r) {
						const d = r.message || {};
						if (d.has_pin) {
							frm.dashboard.add_indicator(__("USB PIN configured on branch"), "green");
						} else if (d.signer_mode === "signing_agent" || d.signer_mode === "windows_app") {
							frm.dashboard.add_indicator(__("USB PIN missing — enter and Save"), "red");
						}
					},
				});
			}
		}
		if (frm.doc.eta_signer_mode !== "signing_agent") {
			return;
		}
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(
			__("Test USB Signing"),
			async () => {
				try {
					const r = await frappe.call({
						method:
							"omnexa_einvoice.eta_signing_agent.run_branch_usb_signing_test_on_server",
						args: { branch: frm.doc.name },
						freeze: true,
						freeze_message: __("Running signing tests on ERP server…"),
					});
					const d = r.message || {};
					await frappe.require("/assets/omnexa_einvoice/js/einvoice_usb_agent.js");
					const show = omnexa.einvoice?.showSigningTestResult;
					if (show) {
						show({
							title: d.ok
								? __("USB Signing Test — server OK")
								: __("USB Signing Test — failed"),
							indicator: d.ok ? "green" : "red",
							checks: d.checks,
							extra: frappe.utils.escape_html(d.summary || ""),
						});
					} else {
						frappe.msgprint({
							title: __("USB Signing Test"),
							indicator: d.ok ? "green" : "red",
							message: (d.summary || "") + "<br>" + JSON.stringify(d.checks || []),
						});
					}
					if (!d.ok) {
						return;
					}
					const onWindows =
						(navigator.platform || "").toLowerCase().includes("win") ||
						(navigator.userAgent || "").toLowerCase().includes("windows");
					const localAgent = /127\.0\.0\.1|localhost/i.test(
						frm.doc.eta_signing_agent_url || ""
					);
					if (d.browser_sign_required && onWindows && localAgent && omnexa.einvoice?.testBranchUsbSigning) {
						await omnexa.einvoice.testBranchUsbSigning(frm.doc.name);
					} else if (d.browser_sign_required) {
						frappe.show_alert({
							message: __(
								"Server checks OK. Open ERP on the Windows PC with the USB token to test signing with the agent."
							),
							indicator: "blue",
						});
					}
				} catch (e) {
					frappe.msgprint({
						title: __("USB Signing Test"),
						indicator: "red",
						message: e.message || String(e),
					});
				}
			},
			__("Egypt ETA")
		);
	},
});
