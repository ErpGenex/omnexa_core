// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

frappe.provide("erpgenex.company_demo");

erpgenex.company_demo.DEMO_TAB = "tab_break_demo_data";
erpgenex.company_demo._handlers = erpgenex.company_demo._handlers || [];
erpgenex.company_demo._refresh_timer = null;

erpgenex.company_demo.register = function register_demo_handler(fn) {
	if (typeof fn === "function" && !erpgenex.company_demo._handlers.includes(fn)) {
		erpgenex.company_demo._handlers.push(fn);
	}
	if (cur_frm && cur_frm.doctype === "Company") {
		erpgenex.company_demo.schedule_refresh(cur_frm);
	}
};

/** Same signature as frm.add_custom_button — renders inside Demo data tab panel. */
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

erpgenex.company_demo.is_active = function is_demo_tab_active(frm) {
	const active = frm.get_active_tab?.();
	if (active?.df?.fieldname === erpgenex.company_demo.DEMO_TAB) {
		return true;
	}
	const $active = frm.wrapper.find(
		'.form-tabs [data-fieldname].active, .form-tabs .nav-link.active[data-fieldname]',
	);
	return ($active.attr("data-fieldname") || "") === erpgenex.company_demo.DEMO_TAB;
};

erpgenex.company_demo.can_manage = function can_manage_demo(frm) {
	return (
		!frm.is_new() &&
		(frappe.user.has_role("System Manager") || frappe.session.user === "Administrator")
	);
};

erpgenex.company_demo.schedule_refresh = function schedule_refresh(frm) {
	clearTimeout(erpgenex.company_demo._refresh_timer);
	erpgenex.company_demo._refresh_timer = setTimeout(() => {
		erpgenex.company_demo.refresh_panel(frm);
	}, 50);
};

erpgenex.company_demo.refresh_panel = function refresh_panel(frm) {
	const field = frm.fields_dict?.demo_data_help;
	if (!field?.$wrapper) {
		return;
	}

	let $host = field.$wrapper.find(".erpgenex-demo-action-panel");
	if (!$host.length) {
		$host = $('<div class="erpgenex-demo-action-panel"></div>');
		field.$wrapper.append($host);
	}

	$host.empty();

	if (!erpgenex.company_demo.is_active(frm)) {
		$host.addClass("hide");
		return;
	}
	$host.removeClass("hide");

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
	if (!groupNames.length) {
		$host.html(
			`<p class="text-muted small">${__(
				"No demo apps loaded. Install omnexa_accounting, omnexa_construction, or omnexa_fixed_assets.",
			)}</p>`,
		);
		return;
	}

	for (const group of groupNames) {
		const $section = $(`
			<div class="erpgenex-demo-group">
				<div class="erpgenex-demo-group-title">${frappe.utils.escape_html(group)}</div>
				<div class="erpgenex-demo-btns"></div>
			</div>
		`);
		const $btns = $section.find(".erpgenex-demo-btns");
		for (const row of groups[group]) {
			const btnClass = row.danger ? "btn-danger" : "btn-primary";
			const $btn = $(
				`<button type="button" class="btn ${btnClass} btn-sm erpgenex-demo-btn">${frappe.utils.escape_html(
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

erpgenex.company_demo.bind_tab_listener = function bind_tab_listener(frm) {
	if (frm.__erpgenex_demo_tab_listener) {
		return;
	}
	frm.__erpgenex_demo_tab_listener = true;
	frm.wrapper.on(
		"shown.bs.tab",
		'button[data-toggle="tab"], a[data-toggle="tab"]',
		() => erpgenex.company_demo.schedule_refresh(frm),
	);
	frm.wrapper.on("click", ".form-tabs .nav-link", () => {
		setTimeout(() => erpgenex.company_demo.schedule_refresh(frm), 80);
	});
};

frappe.ui.form.on("Company", {
	refresh(frm) {
		erpgenex.company_demo.bind_tab_listener(frm);
		erpgenex.company_demo.schedule_refresh(frm);
	},
});
