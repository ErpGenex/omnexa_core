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
			__("Test cloud ↔ PC signing"),
			async () => {
				try {
					if (omnexa.einvoice && omnexa.einvoice.showCloudSigningBridgeTest) {
						await omnexa.einvoice.showCloudSigningBridgeTest({
							branch: frm.doc.name,
							agentUrl: frm.doc.eta_signing_agent_url,
						});
						return;
					}
					frappe.throw(__("Reload ERP (Ctrl+Shift+R) after omnexa_einvoice update."));
				} catch (e) {
					frappe.msgprint({
						title: __("Cloud ↔ PC signing test"),
						indicator: "red",
						message: e.omnexa_html ? e.message : frappe.utils.escape_html(e.message || String(e)),
					});
				}
			},
			__("Egypt ETA")
		).addClass("btn-primary");
		frm.add_custom_button(
			__("ERP config only (no local agent)"),
			async () => {
				try {
					const r = await frappe.call({
						method:
							"omnexa_einvoice.eta_signing_agent.run_branch_usb_signing_test_on_server",
						args: { branch: frm.doc.name },
						freeze: true,
						freeze_message: __("Checking ERP / branch settings…"),
					});
					const d = r.message || {};
					const needsPc = !!d.browser_sign_required;
					const extraParts = [frappe.utils.escape_html(d.summary || "")];
					if (needsPc) {
						extraParts.push(
							`<p class="small mt-2 mb-0"><b>${__(
								"Linux/cloud server cannot reach 127.0.0.1"
							)}</b> — ${__(
								'Use the primary button <b>Test cloud ↔ PC signing</b> in Chrome on the Windows PC where the USB token and signing agent are running. "Failed to fetch" here is expected if you are not on that PC.'
							)}</p>`
						);
					}
					if (omnexa.einvoice && omnexa.einvoice.showSigningTestResult) {
						omnexa.einvoice.showSigningTestResult({
							title: needsPc
								? __("USB Signing — ERP config OK (test on Windows PC)")
								: d.ok
									? __("USB Signing Test — server OK")
									: __("USB Signing Test — failed"),
							indicator: d.ok ? (needsPc ? "orange" : "green") : "red",
							checks: d.checks,
							extra: extraParts.join(""),
						});
					}
				} catch (e) {
					frappe.msgprint({
						title: __("USB Signing Test"),
						indicator: "red",
						message: frappe.utils.escape_html(e.message || String(e)),
					});
				}
			},
			__("Egypt ETA")
		);
	},
});
