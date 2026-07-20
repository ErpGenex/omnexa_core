/**
 * ErpGenEx Multi-Portal Loader
 * Loads role portals dynamically without interfering with existing Desk boot.
 */
/* global frappe */
frappe.provide("omnexa_core.multi_portal");

(function () {
	"use strict";

	class PortalLoader {
		constructor() {
			this.config = null;
			this.application = null;
			this.role = null;
		}

		async loadPortal(application, role) {
			const response = await frappe.call({
				method: "omnexa_core.api.multi_portal.load_portal",
				args: { application, role },
			});
			this.config = response.message || {};
			this.application = application;
			this.role = role;
			this.applyTheme(application);
			return this.config;
		}

		async routeCurrentUser(application) {
			const response = await frappe.call({
				method: "omnexa_core.api.multi_portal.route_user_portal",
				args: { application },
			});
			const payload = response.message || {};
			if (payload.success && payload.portal) {
				this.config = payload.portal;
				this.application = payload.application;
				this.role = payload.role;
				this.applyTheme(payload.application);
			}
			return payload;
		}

		applyTheme(application) {
			const boot = frappe.boot.multi_portal || {};
			const apps = boot.applications || [];
			if (!apps.includes(application)) {
				return;
			}
			document.documentElement.classList.add("omnexa-multi-portal", application);
			const theme = (this.config && this.config.config && this.config.config.theme) || {};
			const root = document.documentElement;
			if (theme.primary) {
				root.style.setProperty("--app-primary", theme.primary);
				root.style.setProperty("--primary-color", theme.primary);
			}
			if (theme.secondary) {
				root.style.setProperty("--app-secondary", theme.secondary);
				root.style.setProperty("--secondary-color", theme.secondary);
			}
			if (theme.accent) {
				root.style.setProperty("--app-accent", theme.accent);
				root.style.setProperty("--accent-color", theme.accent);
			}
		}

		renderSidebar(container, sidebar) {
			if (!container || !sidebar || !sidebar.sections) {
				return;
			}
			const $root = $(container);
			$root.empty().addClass("omnexa-portal-sidebar");
			sidebar.sections.forEach((section) => {
				$root.append(`<div class="omnexa-portal-section-title">${frappe.utils.escape_html(section.title)}</div>`);
				(section.items || []).forEach((item) => {
					const $link = $(`
						<a class="omnexa-portal-sidebar-link" href="${frappe.utils.escape_html(item.route)}">
							<span class="omnexa-portal-icon">${item.icon || "🌐"}</span>
							<span>${frappe.utils.escape_html(item.title)}</span>
						</a>`);
					$link.on("click", (event) => {
						event.preventDefault();
						if (item.route.startsWith("/app/")) {
							window.location.href = item.route;
						} else {
							frappe.set_route(item.route);
						}
					});
					$root.append($link);
				});
			});
		}

		renderDashboard(container, dashboard) {
			if (!container || !dashboard) {
				return;
			}
			const $root = $(container);
			$root.empty().addClass("omnexa-portal-dashboard");
			const $grid = $('<div class="omnexa-portal-kpi-grid"></div>');
			(dashboard.kpis || []).forEach((kpi) => {
				$grid.append(`
					<div class="omnexa-portal-kpi-card">
						<div class="omnexa-portal-kpi-title">${frappe.utils.escape_html(kpi.title)}</div>
						<div class="omnexa-portal-kpi-value">${frappe.utils.escape_html(String(kpi.value ?? 0))}</div>
					</div>`);
			});
			$root.append($grid);

			const $actions = $('<div class="omnexa-portal-quick-actions"></div>');
			(dashboard.quick_actions || []).forEach((action) => {
				const $btn = $(`<button class="btn btn-primary btn-sm">${frappe.utils.escape_html(action.title)}</button>`);
				$btn.on("click", () => {
					if (action.doctype && action.action === "create") {
						frappe.new_doc(action.doctype.replace(/_/g, " "));
					}
				});
				$actions.append($btn);
			});
			$root.append($actions);
		}
	}

	omnexa_core.multi_portal.PortalLoader = PortalLoader;
	omnexa_core.multi_portal.loader = new PortalLoader();

	$(document).on("app_ready", function () {
		const boot = frappe.boot.multi_portal;
		if (!boot || !boot.enabled) {
			return;
		}
		const route = frappe.get_route() || [];
		const application = (boot.primary_application || "").toLowerCase();
		if (!application) {
			return;
		}
		const routeApp = (route[0] || "").toLowerCase();
		if (Array.isArray(boot.applications) && boot.applications.includes(routeApp)) {
			omnexa_core.multi_portal.loader.applyTheme(routeApp);
		}
	});
})();
