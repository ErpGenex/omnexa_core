// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

frappe.provide("erpgenex.company_demo");

erpgenex.company_demo._esc = function (text) {
	const t = text == null ? "" : String(text);
	if (frappe.utils?.escape_html) {
		return frappe.utils.escape_html(t);
	}
	return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
};

erpgenex.company_demo._mount = function (frm) {
	let $host = frm.wrapper.find("#erpgenex-demo-action-mount").first();
	if ($host.length) {
		return $host;
	}
	const sec = frm.fields_dict?.production_readiness_section?.$wrapper;
	if (sec?.length) {
		$host = $('<div id="erpgenex-demo-action-mount" class="erpgenex-demo-action-panel"></div>');
		sec.before($host);
		return $host;
	}
	const help = frm.fields_dict?.demo_data_help?.$wrapper;
	if (help?.length) {
		$host = $('<div id="erpgenex-demo-action-mount" class="erpgenex-demo-action-panel"></div>');
		help.append($host);
		return $host;
	}
	return $();
};

erpgenex.company_demo._ctx = function (frm) {
	return {
		company: frm.doc.name,
		branch: (frm.doc.production_demo_branch || "").trim() || null,
		activity: (frm.doc.production_demo_activity || frm.doc.industry_sector || "").trim() || null,
	};
};

erpgenex.company_demo._run = function (frm, spec, extra = {}) {
	const ctx = erpgenex.company_demo._ctx(frm);
	return frappe.call({
		method: "omnexa_core.omnexa_core.company_demo_api.run_demo_action",
		args: {
			company: ctx.company,
			action_key: spec.key,
			branch: ctx.branch,
			activity: ctx.activity,
			...extra,
		},
		freeze: true,
		freeze_message: spec.label,
	});
};

erpgenex.company_demo._click = function (frm, spec) {
	const go = () => {
		if (spec.prompt_confirm_text) {
			frappe.prompt(
				[
					{
						fieldname: "confirm_text",
						fieldtype: "Data",
						label: __("Type DELETE ALL to confirm"),
						reqd: 1,
					},
				],
				(v) => {
					if (!v?.confirm_text) return;
					erpgenex.company_demo._run(frm, spec, { confirm_text: v.confirm_text }).then((r) => {
						frappe.show_alert({ message: spec.label + ": OK", indicator: "green" });
						if (r?.message?.message) {
							frappe.msgprint(r.message.message);
						}
					});
				},
				__("Full Company Wipe"),
				__("Execute"),
			);
			return;
		}
		if (spec.confirm) {
			frappe.confirm(spec.confirm, () => {
				erpgenex.company_demo._run(frm, spec).then((r) => {
					frappe.show_alert({ message: spec.label + ": OK", indicator: "green" });
					const m = r?.message || {};
					if (m.message) frappe.msgprint(m.message);
				});
			});
			return;
		}
		erpgenex.company_demo._run(frm, spec).then((r) => {
			frappe.show_alert({ message: spec.label + ": OK", indicator: "green" });
			const m = r?.message || {};
			if (m.message) frappe.msgprint(m.message);
		});
	};
	go();
};

erpgenex.company_demo.render = function (frm) {
	if (!frm || frm.doctype !== "Company" || frm.is_new()) {
		return;
	}
	const $host = erpgenex.company_demo._mount(frm);
	if (!$host.length) {
		return;
	}

	if (!frappe.user.has_role("System Manager") && frappe.session.user !== "Administrator") {
		$host.html(
			`<p class="text-muted small">${__(
				"Demo seeding requires the System Manager role.",
			)}</p>`,
		);
		return;
	}

	$host.html(`<p class="text-muted small">${__("Loading demo actions…")}</p>`);

	frappe.call({
		method: "omnexa_core.omnexa_core.company_demo_api.get_demo_action_specs",
		args: { company: frm.doc.name },
		callback(r) {
			const specs = r.message || [];
			$host.empty();
			if (!specs.length) {
				$host.html(
					`<p class="text-muted small">${__(
						"No demo actions available. Install omnexa_accounting / omnexa_construction and run bench migrate.",
					)}</p>`,
				);
				return;
			}
			const byGroup = {};
			specs.forEach((s) => {
				const g = s.group || __("Demo");
				(byGroup[g] = byGroup[g] || []).push(s);
			});
			Object.keys(byGroup).forEach((group) => {
				const $sec = $(`
					<div class="erpgenex-demo-group">
						<div class="erpgenex-demo-group-title">${erpgenex.company_demo._esc(group)}</div>
						<div class="erpgenex-demo-btns"></div>
					</div>
				`);
				const $btns = $sec.find(".erpgenex-demo-btns");
				byGroup[group].forEach((spec) => {
					const cls = cint(spec.danger) ? "btn-danger" : "btn-primary";
					const $btn = $(
						`<button type="button" class="btn ${cls} btn-sm erpgenex-demo-btn">${erpgenex.company_demo._esc(
							spec.label,
						)}</button>`,
					);
					$btn.on("click", (e) => {
						e.preventDefault();
						erpgenex.company_demo._click(frm, spec);
					});
					$btns.append($btn);
				});
				$host.append($sec);
			});
		},
	});
};

function erpgenex_company_demo_refresh(frm) {
	erpgenex.company_demo.render(frm);
	setTimeout(() => erpgenex.company_demo.render(frm), 300);
	setTimeout(() => erpgenex.company_demo.render(frm), 1200);
}

if (!erpgenex.company_demo._bound) {
	erpgenex.company_demo._bound = true;
	frappe.ui.form.on("Company", {
		refresh(frm) {
			if (!frm.is_new() && frappe.user.has_role("System Manager")) {
				frm.set_query("production_demo_branch", () => ({
					filters: { company: frm.doc.name },
				}));
			}
			erpgenex_company_demo_refresh(frm);
		},
	});
}
