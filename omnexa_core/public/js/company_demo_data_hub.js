// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt

frappe.provide("erpgenex.company_demo");

erpgenex.company_demo.DEMO_TAB = "tab_break_demo_data";
erpgenex.company_demo._handlers = erpgenex.company_demo._handlers || [];

erpgenex.company_demo.register = function register_demo_handler(fn) {
	if (typeof fn === "function" && !erpgenex.company_demo._handlers.includes(fn)) {
		erpgenex.company_demo._handlers.push(fn);
	}
};

erpgenex.company_demo.is_active = function is_demo_tab_active(frm) {
	const $active = frm.wrapper.find(".form-tabs .nav-link.active");
	const fieldname = $active.attr("data-fieldname") || "";
	return fieldname === erpgenex.company_demo.DEMO_TAB;
};

erpgenex.company_demo.can_manage = function can_manage_demo(frm) {
	return !frm.is_new() && frappe.user.has_role("System Manager");
};

erpgenex.company_demo.refresh_buttons = function refresh_demo_buttons(frm) {
	if (!erpgenex.company_demo.can_manage(frm)) {
		return;
	}
	if (!erpgenex.company_demo.is_active(frm)) {
		return;
	}
	frm.clear_custom_buttons();
	for (const fn of erpgenex.company_demo._handlers) {
		try {
			fn(frm);
		} catch (e) {
			console.error("Company demo handler failed", e);
		}
	}
};

erpgenex.company_demo.bind_tab_listener = function bind_tab_listener(frm) {
	if (frm.__erpgenex_demo_tab_listener) {
		return;
	}
	frm.__erpgenex_demo_tab_listener = true;
	frm.wrapper.on("shown.bs.tab", 'a[data-toggle="tab"]', () => {
		if (!erpgenex.company_demo.can_manage(frm)) {
			return;
		}
		frm.clear_custom_buttons();
		erpgenex.company_demo.refresh_buttons(frm);
	});
};

frappe.ui.form.on("Company", {
	refresh(frm) {
		erpgenex.company_demo.bind_tab_listener(frm);
		erpgenex.company_demo.refresh_buttons(frm);
	},
});
