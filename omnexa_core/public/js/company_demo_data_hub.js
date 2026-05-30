// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

frappe.provide("erpgenex.company_demo");

erpgenex.company_demo.DEMO_TAB = "tab_break_demo_data";
erpgenex.company_demo._handlers = erpgenex.company_demo._handlers || [];
erpgenex.company_demo._refresh_timer = null;

erpgenex.company_demo._esc = function _esc(text) {
	const t = text == null ? "" : String(text);
	if (frappe.utils && typeof frappe.utils.escape_html === "function") {
		return frappe.utils.escape_html(t);
	}
	return t
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;");
};

erpgenex.company_demo.register = function register_demo_handler(fn) {
	if (typeof fn === "function" && !erpgenex.company_demo._handlers.includes(fn)) {
		erpgenex.company_demo._handlers.push(fn);
	}
};

erpgenex.company_demo.demo_btn = function demo_btn(frm, label, fn, group) {
	erpgenex.company_demo.add_action(frm, group || __("Demo"), label, fn);
};

erpgenex.company_demo.add_action = function add_action(frm, group, label, action, opts = {}) {
	if (!frm.__demo_action_groups) {
		frm.__demo_action_groups = {};
	}
	const key = group || __("Demo");
	if (!frm.__demo_action_groups[key]) {
		frm.__demo_action_groups[key] = [];
	}
	frm.__demo_action_groups[key].push({
		label,
		action: typeof action === "function" ? action : () => {},
		danger: !!opts.danger,
	});
};

erpgenex.company_demo.can_manage = function can_manage_demo(frm) {
	return (
		!frm.is_new() &&
		(frappe.user.has_role("System Manager") || frappe.session.user === "Administrator")
	);
};

erpgenex.company_demo._get_mount = function _get_mount(frm) {
	let $host = frm.wrapper.find("#erpgenex-demo-action-mount");
	if ($host.length) {
		return $host;
	}
	const field = frm.fields_dict?.demo_data_help;
	if (field?.$wrapper) {
		$host = field.$wrapper.find("#erpgenex-demo-action-mount");
		if ($host.length) {
			return $host;
		}
		$host = field.$wrapper.find(".erpgenex-demo-action-panel");
		if ($host.length) {
			return $host;
		}
		$host = $('<div id="erpgenex-demo-action-mount" class="erpgenex-demo-action-panel"></div>');
		field.$wrapper.append($host);
		return $host;
	}
	return $();
};

erpgenex.company_demo.refresh_panel = function refresh_panel(frm) {
	if (!frm || frm.doctype !== "Company") {
		return;
	}

	const $host = erpgenex.company_demo._get_mount(frm);
	if (!$host.length) {
		return;
	}

	$host.removeClass("hide").show();

	if (!erpgenex.company_demo.can_manage(frm)) {
		$host.html(
			`<p class="text-muted small">${__(
				"Save the company first. Demo seeding requires the System Manager role.",
			)}</p>`,
		);
		return;
	}

	frm.__demo_action_groups = {};
	for (const fn of erpgenex.company_demo._handlers) {
		try {
			fn(frm);
		} catch (e) {
			console.error("Company demo handler failed", e);
		}
	}

	const groups = frm.__demo_action_groups || {};
	const groupNames = Object.keys(groups);
	$host.empty();

	if (!groupNames.length) {
		$host.html(
			`<p class="text-muted small">${__(
				"No demo apps loaded. Update omnexa_accounting, omnexa_construction, and omnexa_fixed_assets, then run bench build and clear-cache.",
			)}</p>`,
		);
		return;
	}

	for (const group of groupNames) {
		const $section = $(`
			<div class="erpgenex-demo-group">
				<div class="erpgenex-demo-group-title">${erpgenex.company_demo._esc(group)}</div>
				<div class="erpgenex-demo-btns"></div>
			</div>
		`);
		const $btns = $section.find(".erpgenex-demo-btns");
		for (const row of groups[group]) {
			const btnClass = row.danger ? "btn-danger" : "btn-primary";
			const $btn = $(
				`<button type="button" class="btn ${btnClass} btn-sm erpgenex-demo-btn">${erpgenex.company_demo._esc(
					row.label,
				)}</button>`,
			);
			$btn.on("click", (e) => {
				e.preventDefault();
				row.action();
			});
			$btns.append($btn);
		}
		$host.append($section);
	}
};

erpgenex.company_demo.schedule_refresh = function schedule_refresh(frm) {
	if (!frm) {
		return;
	}
	clearTimeout(erpgenex.company_demo._refresh_timer);
	erpgenex.company_demo._refresh_timer = setTimeout(() => {
		erpgenex.company_demo.refresh_panel(frm);
	}, 80);
	// Late pass: other apps register handlers after first refresh tick
	setTimeout(() => erpgenex.company_demo.refresh_panel(frm), 350);
};

erpgenex.company_demo.bind_tab_listener = function bind_tab_listener(frm) {
	if (frm.__erpgenex_demo_tab_listener) {
		return;
	}
	frm.__erpgenex_demo_tab_listener = true;
	const rerender = () => erpgenex.company_demo.refresh_panel(frm);
	frm.wrapper.on("shown.bs.tab", 'button[data-toggle="tab"], a[data-toggle="tab"]', rerender);
	frm.wrapper.on("click", ".form-tabs .nav-link", () => setTimeout(rerender, 120));
	for (const tab of frm.layout?.tabs || []) {
		if (tab.df?.fieldname === erpgenex.company_demo.DEMO_TAB) {
			tab.tab_link.find(".nav-link").on("shown.bs.tab", rerender);
		}
	}
};

frappe.ui.form.on("Company", {
	refresh(frm) {
		erpgenex.company_demo.bind_tab_listener(frm);
		erpgenex.company_demo.schedule_refresh(frm);
	},
});
