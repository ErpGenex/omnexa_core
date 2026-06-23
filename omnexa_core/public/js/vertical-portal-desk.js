/**
 * ErpGenEx — Generic vertical role portal desk (sidebar + main)
 */
/* global frappe */
frappe.provide("omnexa_core.vertical_portal");

(function () {
	"use strict";

	function t(ar, en) {
		return frappe.boot.lang === "ar" ? ar : en;
	}

	function navigateRoute(route) {
		if (!route) return;
		if (route.startsWith("/app/") || route.startsWith("/education/")) {
			window.location.href = route;
			return;
		}
		frappe.set_route(route);
	}

	function renderSidebar(groups, activeRoute) {
		const $nav = $('<nav class="oj-vertical-portal-sidebar"></nav>');
		(groups || []).forEach((g) => {
			const title = t(g.label_ar, g.label_en);
			$nav.append(`<div class="oj-sidebar-section">${frappe.utils.escape_html(title)}</div>`);
			(g.portals || []).forEach((p) => {
				const label = t(p.label_ar, p.label_en);
				const active = p.route === activeRoute ? " active" : "";
				const $link = $(`
					<a class="oj-sidebar-link${active}" href="${frappe.utils.escape_html(p.route)}">
						<span class="oj-sidebar-icon">${p.icon || "🌐"}</span>
						<span>${frappe.utils.escape_html(label)}</span>
					</a>`);
				$link.on("click", (e) => {
					e.preventDefault();
					navigateRoute(p.route);
				});
				$nav.append($link);
			});
		});
		return $nav;
	}

	omnexa_core.vertical_portal.mountRoleDesk = function (wrapper, appName, roleKey) {
		const OJ = window.OmnexaJourney;
		const currentRoute = `/app/${frappe.get_route_str().replace(/ /g, "-")}`;
		let $mount;
		let pageTitle = __("Role Portal");

		if (OJ && OJ.mountDeskPage) {
			$mount = OJ.mountDeskPage(wrapper, pageTitle);
		} else {
			const page = frappe.ui.make_app_page({ parent: wrapper, title: pageTitle, single_column: true });
			$mount = $(page.body);
		}

		frappe.call({
			method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
			args: { app: appName },
			callback(r) {
				const ctx = r.message || {};
				const groups = ctx.grouped_portals || [];
				let portal = null;
				groups.forEach((g) => {
					(g.portals || []).forEach((p) => {
						if (p.id && p.id.endsWith(roleKey)) portal = p;
					});
				});

				const title = portal ? t(portal.label_ar, portal.label_en) : pageTitle;
				const roleLabel = portal ? t(portal.role_ar, portal.role_en) : roleKey;

				const $layout = $('<div class="oj-vertical-portal-layout"></div>');
				const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
				$sidebar.append(
					`<div class="oj-vertical-portal-brand">
						${ctx.logo_url ? `<img src="${ctx.logo_url}" alt="" />` : ""}
						<strong>${frappe.utils.escape_html(t(ctx.title_ar, ctx.title_en))}</strong>
					</div>`
				);
				$sidebar.append(renderSidebar(groups, currentRoute));
				$sidebar.append(
					`<a class="oj-sidebar-link oj-sidebar-back" href="${ctx.workcenter_route || "#"}">${t(
						"← مركز العمل",
						"← Workcenter"
					)}</a>`
				);

				const $main = $('<div class="oj-vertical-portal-main"></div>');
				$main.append(`<h3 class="oj-section-title">${frappe.utils.escape_html(title)}</h3>`);
				$main.append(
					`<p class="oj-muted">${frappe.utils.escape_html(
						t("بوابة دور", "Role portal")
					)}: <strong>${frappe.utils.escape_html(roleLabel)}</strong></p>`
				);
				$main.append(
					`<div class="oj-card oj-vertical-portal-card">
						<p>${t(
							"هذه البوابة جاهزة للتخصيص — اربطها بمساحات العمل والتقارير الخاصة بالقطاع.",
							"This portal is ready for customization — link sector workspaces and reports."
						)}</p>
						<p class="oj-muted">${t(
							"استخدم مركز العمل للتنقل بين جميع بوابات الأدوار.",
							"Use the workcenter to navigate all role portals."
						)}</p>
					</div>`
				);

				$layout.append($sidebar).append($main);
				$mount.empty().append($layout);

				if (wrapper && wrapper.page && wrapper.page.set_title) {
					wrapper.page.set_title(title);
				}
			},
		});
	};
})();
