// Copyright (c) 2026, Omnexa and contributors
// License: MIT. Desk navigation guard when an omnexa_* / erpgenex_* commercial app license is not OK.
(function () {
	"use strict";

	function hasBootLicenseData() {
		return frappe.boot && frappe.boot.omnexa_license_by_app;
	}

	function appFromModule(moduleName) {
		if (!moduleName || !frappe.boot.module_app) {
			return null;
		}
		const scrub = frappe.scrub(moduleName);
		const app = frappe.boot.module_app[scrub];
		return app && (String(app).startsWith("omnexa_") || String(app).startsWith("erpgenex_"))
			? app
			: null;
	}

	function isAppOk(app) {
		if (!app || !hasBootLicenseData()) {
			return true;
		}
		const row = frappe.boot.omnexa_license_by_app[app];
		return row && row.ok === true;
	}

	function isRouteStrSafe(routeStr) {
		if (!routeStr) {
			return true;
		}
		const hints = frappe.boot.omnexa_license_safe_route_hints || [];
		for (let i = 0; i < hints.length; i++) {
			if (routeStr.indexOf(hints[i]) !== -1) {
				return true;
			}
		}
		return false;
	}

	function blockWithMessage(app) {
		const row = (hasBootLicenseData() && frappe.boot.omnexa_license_by_app[app]) || {};
		const st = row.status || "unknown";
		const lockAt = row.lock_at ? String(row.lock_at) : "";
		const warnings = Array.isArray(row.warnings) ? row.warnings.join(", ") : "";
		const mp = frappe.boot.omnexa_marketplace_route || "/app/erpgenex-marketplace";
		frappe.msgprint({
			title: __("License required"),
			indicator: "red",
			message: __(
				"The application {0} is not licensed (status: {1}). {2}{3}Open ErpGenEx Marketplace and enter a valid license or developer key."
			).format(
				app,
				st,
				warnings ? __("Warnings: {0}. ", [warnings]) : "",
				lockAt ? __("Lock at (UTC ts): {0}. ", [lockAt]) : ""
			),
		});
		frappe.msgprint({
			title: __("Action"),
			indicator: "blue",
			message: __('<a href="{0}">Open Marketplace</a>').format(mp),
		});
	}

	function redirectWelcome() {
		frappe.set_route("Workspaces", "Welcome Workspace");
	}

	function guardWorkspace(route) {
		const pages = frappe.boot.allowed_workspaces || [];
		if (!route || !route.length) {
			return;
		}
		let ws = null;
		if (route[0] === "Workspaces" && route[1]) {
			const name = route[1];
			ws = pages.find((p) => p.name === name);
		} else if (route.length === 1) {
			// Modern workspace route is usually /app/<workspace-slug>
			const slug = String(route[0] || "").toLowerCase();
			ws = pages.find((p) => {
				const n = String(p.name || "");
				const t = String(p.title || "");
				return (
					frappe.router.slug(n).toLowerCase() === slug ||
					(t && frappe.router.slug(t).toLowerCase() === slug)
				);
			});
		}
		if (!ws || !ws.module) {
			return;
		}
		const app = appFromModule(ws.module);
		if (!app || isAppOk(app)) {
			return;
		}
		blockWithMessage(app);
		redirectWelcome();
	}

	function guardDoctype(doctype) {
		if (!doctype) {
			return;
		}
		frappe.model.with_doctype(
			doctype,
			function () {
				const meta = frappe.get_meta(doctype);
				if (!meta || !meta.module) {
					return;
				}
				const app = appFromModule(meta.module);
				if (!app || isAppOk(app)) {
					return;
				}
				blockWithMessage(app);
				redirectWelcome();
			},
			true
		);
	}

	function guardRoute() {
		if (frappe.session.user === "Guest" || !hasBootLicenseData()) {
			return;
		}
		const routeStr = frappe.get_route_str();
		if (isRouteStrSafe(routeStr)) {
			return;
		}
		const route = frappe.get_route() || [];
		if (route[0] === "Workspaces" || route.length === 1) {
			guardWorkspace(route);
			return;
		}
		const v0 = (route[0] || "").toLowerCase();
		if (v0 === "list" && route[1]) {
			guardDoctype(route[1]);
			return;
		}
		if (v0 === "form" && route[1]) {
			guardDoctype(route[1]);
		}
	}

	frappe.router.on("change", () => {
		setTimeout(guardRoute, 0);
	});

	frappe.refresh_omnexa_license_boot = function () {
		return frappe.call({
			method: "omnexa_core.desk_license_boot.get_omnexa_license_snapshot_for_desk",
			callback: function (r) {
				const m = r.message || {};
				if (m.omnexa_license_by_app) {
					frappe.boot.omnexa_license_by_app = m.omnexa_license_by_app;
				}
				if (typeof m.omnexa_license_enforce === "boolean") {
					frappe.boot.omnexa_license_enforce = m.omnexa_license_enforce;
				}
			},
		});
	};
})();
