// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

const EINV_SIGNING_DEPLOY_INFO =
	"omnexa_einvoice.omnexa_einvoice.doctype.e_invoice_submission.e_invoice_submission.get_signing_deploy_info";

function branch_country_iso(frm) {
	if (typeof omnexa !== "undefined" && omnexa.einvoice && omnexa.einvoice.getBranchCountryIso) {
		return omnexa.einvoice.getBranchCountryIso(frm);
	}
	return (frm.doc.country_iso || frm.doc.country_code || "EG")
		.split(" — ")[0]
		.trim()
		.toUpperCase();
}

frappe.ui.form.on("Branch", {
	refresh(frm) {
		const country = branch_country_iso(frm);
		if (
			typeof omnexa !== "undefined" &&
			omnexa.einvoice &&
			omnexa.einvoice.purgeForeignTaxToolbarGroups
		) {
			omnexa.einvoice.purgeForeignTaxToolbarGroups(frm);
		} else if (country !== "EG" && frm.page) {
			const $group = frm.page.get_inner_group_button(__("Egypt ETA"));
			if ($group && $group.length) {
				$group.remove();
			}
		}
		if (country !== "EG") {
			return;
		}
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
				frappe.call({
					method: EINV_SIGNING_DEPLOY_INFO,
					callback(r) {
						const d = r.message || {};
						const jsVer =
							(typeof omnexa !== "undefined" &&
								omnexa.einvoice &&
								omnexa.einvoice.AGENT_JS_VERSION) ||
							"—";
						if (jsVer === d.min_agent_js && d.release === d.min_agent_js) {
							frm.dashboard.add_indicator(
								__("Signing bridge {0} (server+browser OK)", [d.release]),
								"green"
							);
						} else {
							frm.dashboard.add_indicator(
								__("Signing update required — server {0}, browser {1}", [
									d.release || "?",
									jsVer,
								]),
								"red"
							);
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
		// Block legacy combined test (old JS called fetch → "Failed to fetch" on cloud).
		if (frm.custom_buttons) {
			Object.keys(frm.custom_buttons).forEach((group) => {
				(frm.custom_buttons[group] || []).forEach((btn) => {
					const label = (btn && btn.label) || "";
					if (/test usb signing/i.test(label) && !/cloud|config only/i.test(label)) {
						btn.remove();
					}
				});
			});
		}

		frm.add_custom_button(
			__("Test cloud ↔ PC signing"),
			async () => {
				try {
					if (!omnexa.einvoice || !omnexa.einvoice.showCloudSigningBridgeTest) {
						const dep = await frappe.call({ method: EINV_SIGNING_DEPLOY_INFO });
						const d = dep.message || {};
						frappe.msgprint({
							title: __("Signing not loaded"),
							indicator: "red",
							message: [
								`<p>${__(
									"Browser JS is missing cloud signing. On the server run:"
								)}</p>`,
								`<pre class="small">bench build --apps omnexa_einvoice,omnexa_core\nbench --site SITE clear-cache\nbench restart</pre>`,
								`<p>${__("Then Ctrl+Shift+R on the Windows PC.")}</p>`,
								`<p class="small">${__("Server release")}: <b>${frappe.utils.escape_html(
									d.release || "?"
								)}</b> · ${__("Your browser")}: <b>${frappe.utils.escape_html(
									(omnexa.einvoice && omnexa.einvoice.AGENT_JS_VERSION) || "—"
								)}</b></p>`,
							].join(""),
						});
						return;
					}
					await omnexa.einvoice.showCloudSigningBridgeTest({
						branch: frm.doc.name,
						agentUrl: frm.doc.eta_signing_agent_url,
					});
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
	},
});
