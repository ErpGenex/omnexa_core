// Block Desk routes outside the active company's business activity when strict filtering is on.
(function () {
	"use strict";

	function filterState() {
		return (frappe.boot && frappe.boot.omnexa_activity_filter) || {};
	}

	function shouldGuard() {
		const f = filterState();
		if (!f.active) return false;
		if (f.can_set_activity_menu_scope && f.activity_menu_scope === "all") return false;
		return Boolean(f.strict_company_filtering !== 0);
	}

	function hiddenApps() {
		return new Set((filterState().hidden_apps || []).map(String));
	}

	function moduleToApp(moduleName) {
		if (!moduleName) return null;
		const map = frappe.boot.module_app || {};
		const scrubbed = frappe.router.slug(moduleName);
		return map[scrubbed] || map[moduleName] || null;
	}

	function appHidden(appSlug) {
		if (!appSlug) return false;
		return hiddenApps().has(appSlug);
	}

	function workspaceModule(name) {
		const pages = frappe.boot.allowed_workspaces || [];
		const row = pages.find((p) => p.name === name || p.title === name);
		if (row) return row.module || row.module_name;
		const all = frappe.boot.workspaces || [];
		const alt = all.find((p) => p.name === name || p.title === name);
		return alt ? alt.module || alt.module_name : null;
	}

	function routeTargetApp(route) {
		if (!route || !route.length) return null;
		const r0 = String(route[0] || "").toLowerCase();

		if (r0 === "workspaces" && route[1]) {
			return moduleToApp(workspaceModule(route[1]));
		}
		if (route.length === 1 && r0 !== "list" && r0 !== "form" && r0 !== "query-report") {
			const slug = route[0];
			const mod = workspaceModule(slug);
			if (mod) return moduleToApp(mod);
			const pageMeta = (frappe.boot.page_info || {})[slug];
			if (pageMeta && pageMeta.module) return moduleToApp(pageMeta.module);
		}
		if (r0 === "list" && route[1]) {
			return frappe.model.with_doctype(route[1], () => {
				const meta = frappe.get_meta(route[1]);
				return meta && meta.module ? moduleToApp(meta.module) : null;
			});
		}
		if (r0 === "form" && route[1]) {
			const meta = frappe.get_meta(route[1]);
			return meta && meta.module ? moduleToApp(meta.module) : null;
		}
		if (r0 === "query-report" && route[1]) {
			return frappe.model.with_doctype("Report", () => null);
		}
		return null;
	}

	function isRouteBlocked(route) {
		if (!shouldGuard()) return false;
		const hidden = hiddenApps();
		if (!hidden.size) return false;

		if (!route || !route.length) return false;
		const r0 = String(route[0] || "").toLowerCase();

		if (r0 === "workspaces" && route[1]) {
			const app = moduleToApp(workspaceModule(route[1]));
			return appHidden(app);
		}
		if (route.length === 1 && r0 !== "list" && r0 !== "form" && r0 !== "query-report") {
			const slug = route[0];
			if ((frappe.boot.page_info || {})[slug] === undefined && !workspaceModule(slug)) {
				return false;
			}
			const mod = workspaceModule(slug) || ((frappe.boot.page_info || {})[slug] || {}).module;
			return appHidden(moduleToApp(mod));
		}
		if ((r0 === "list" || r0 === "form") && route[1] && frappe.get_meta(route[1])) {
			const meta = frappe.get_meta(route[1]);
			return appHidden(moduleToApp(meta.module));
		}
		return false;
	}

	function redirectSafe() {
		const workspaces = frappe.boot.allowed_workspaces || [];
		const first = workspaces[0];
		if (first && first.name) {
			frappe.set_route("Workspaces", first.name);
			return;
		}
		frappe.set_route("apps");
	}

	function guardRoute() {
		if (!window.frappe || frappe.session.user === "Guest") return;
		if (!shouldGuard()) return;
		const route = frappe.get_route() || [];
		if (!isRouteBlocked(route)) return;
		frappe.show_alert({
			message: __("This screen belongs to another business activity and is hidden for your company."),
			indicator: "orange",
		});
		redirectSafe();
	}

	function init() {
		if (!window.frappe || !frappe.router) return;
		frappe.router.on("change", () => setTimeout(guardRoute, 0));
	}

	if (window.frappe && frappe.router) {
		init();
	} else {
		$(document).on("app_ready", init);
	}
})();
