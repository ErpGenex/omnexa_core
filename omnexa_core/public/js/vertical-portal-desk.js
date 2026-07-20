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

	function renderOperationalMenu(sections) {
		const $menu = $('<div class="oj-pharma-ops-menu"></div>');
		(sections || []).forEach((section) => {
			const title = t(section.title_ar, section.title_en);
			$menu.append(`<div class="oj-sidebar-section">${frappe.utils.escape_html(title)}</div>`);
			(section.items || []).forEach((item) => {
				const label = t(item.label_ar, item.label_en);
				const $btn = $(`
					<a class="oj-pharma-ops-link" href="${frappe.utils.escape_html(item.route)}">
						<span class="oj-sidebar-icon">${item.icon || "📄"}</span>
						<span>${frappe.utils.escape_html(label)}</span>
					</a>`);
				$btn.on("click", (e) => {
					e.preventDefault();
					navigateRoute(item.route);
				});
				$menu.append($btn);
			});
		});
		return $menu;
	}

	function renderPharmaPortalNav(portals, activeRoute) {
		const $nav = $('<nav class="oj-vertical-portal-sidebar"></nav>');
		(portals || []).forEach((p) => {
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
		return $nav;
	}

	function renderQuickActions(actions) {
		const $row = $('<div class="omnexa-portal-quick-actions"></div>');
		(actions || []).forEach((act) => {
			const label = t(act.label_ar, act.label_en);
			const $btn = $(`
				<a class="btn btn-sm btn-default omnexa-portal-quick-btn" href="${frappe.utils.escape_html(act.route)}">
					${act.icon || "⚡"} ${frappe.utils.escape_html(label)}
				</a>`);
			$btn.on("click", (e) => {
				e.preventDefault();
				navigateRoute(act.route);
			});
			$row.append($btn);
		});
		return $row;
	}

	function renderListPanel(titleAr, titleEn, rows, labelField) {
		const title = t(titleAr, titleEn);
		const $panel = $(`<div class="omnexa-portal-panel"><h5>${frappe.utils.escape_html(title)}</h5></div>`);
		const $list = $('<ul class="omnexa-portal-list"></ul>');
		if (!rows || !rows.length) {
			$list.append(`<li class="text-muted">${t("لا توجد عناصر", "No items")}</li>`);
		} else {
			rows.forEach((row) => {
				const label = row[labelField] || row.name || row.description || row.subject || "-";
				$list.append(`<li>${frappe.utils.escape_html(String(label))}</li>`);
			});
		}
		$panel.append($list);
		return $panel;
	}

	function renderPharmaDashboard(dashboard) {
		const $dash = $('<div class="omnexa-pharma-dashboard"></div>');
		if (!dashboard) return $dash;

		const kpis = dashboard.kpis || [];
		if (kpis.length) {
			const $kpis = $('<div class="omnexa-portal-kpi-grid"></div>');
			kpis.forEach((kpi) => {
				const title = t(kpi.title_ar, kpi.title_en || kpi.title);
				$kpis.append(`
					<div class="omnexa-portal-kpi-card">
						<div class="omnexa-portal-kpi-title">${kpi.icon || "📊"} ${frappe.utils.escape_html(title)}</div>
						<div class="omnexa-portal-kpi-value">${frappe.utils.escape_html(String(kpi.value ?? 0))}</div>
					</div>`);
			});
			$dash.append($kpis);
		}

		if (dashboard.quick_actions && dashboard.quick_actions.length) {
			$dash.append(`<h5 class="oj-section-title">${t("إجراءات سريعة", "Quick Actions")}</h5>`);
			$dash.append(renderQuickActions(dashboard.quick_actions));
		}

		const $panels = $('<div class="omnexa-portal-panels"></div>');
		$panels.append(renderListPanel("قائمة العمل", "Work Queue", dashboard.work_queue, "name"));
		$panels.append(renderListPanel("مهام معلقة", "Pending Tasks", dashboard.pending_tasks, "description"));
		$panels.append(renderListPanel("موافقات", "Approvals", dashboard.approvals, "name"));
		$dash.append($panels);

		if (dashboard.charts && dashboard.charts.length) {
			const $charts = $('<div class="omnexa-portal-charts"></div>');
			dashboard.charts.forEach((ch) => {
				const title = t(ch.title_ar, ch.title_en);
				$charts.append(`<div class="omnexa-portal-chart-placeholder">${frappe.utils.escape_html(title)} (${ch.type || "chart"})</div>`);
			});
			$dash.append($charts);
		}

		return $dash;
	}

	omnexa_core.vertical_portal.mountPharmaDesk = function (wrapper, roleKey) {
		const currentRoute = `/app/${frappe.get_route_str().replace(/ /g, "-")}`;
		let $mount;
		let pageTitle = __("Pharma Portal");

		const page = frappe.ui.make_app_page({ parent: wrapper, title: pageTitle, single_column: true });
		$mount = $(page.body);

		frappe.call({
			method: "omnexa_trading.pharma_portal_catalog.get_role_portal_context",
			args: { role_key: roleKey },
			callback(r) {
				const ctx = r.message || {};
				const portal = ctx.portal || {};
				const title = t(portal.label_ar, portal.label_en) || pageTitle;
				const roleLabel = t(portal.role_ar, portal.role_en) || roleKey;

				const $layout = $('<div class="oj-vertical-portal-layout"></div>');
				const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
				$sidebar.append(
					`<div class="oj-vertical-portal-brand">
						${ctx.logo_url ? `<img src="${ctx.logo_url}" alt="" />` : ""}
						<strong>${frappe.utils.escape_html(t(ctx.title_ar, ctx.title_en))}</strong>
					</div>`
				);

				frappe.call({
					method: "omnexa_trading.pharma_portal_catalog.get_grouped_pharma_portal_catalog",
					callback(navRes) {
						const groups = navRes.message || [];
						const allPortals = [];
						groups.forEach((g) => allPortals.push(...(g.portals || [])));
						$sidebar.append(renderPharmaPortalNav(allPortals, currentRoute));
						$sidebar.append(
							`<a class="oj-sidebar-link oj-sidebar-back" href="${ctx.workcenter_route || "#"}">${t(
								"← مركز العمل",
								"← Workcenter"
							)}</a>`
						);

						const $main = $('<div class="oj-vertical-portal-main"></div>');
						$main.append(`<h3 class="oj-section-title">${frappe.utils.escape_html(title)}</h3>`);
						$main.append(
							`<p class="oj-muted">${frappe.utils.escape_html(t("بوابة دور", "Role portal"))}: <strong>${frappe.utils.escape_html(roleLabel)}</strong></p>`
						);

						const dashboard = ctx.dashboard || {};
						if (dashboard.kpis || dashboard.work_queue) {
							$main.append(renderPharmaDashboard(dashboard));
						} else if (ctx.multi_portal && ctx.multi_portal.dashboard && ctx.multi_portal.dashboard.kpis) {
							const $kpis = $('<div class="omnexa-portal-kpi-grid"></div>');
							(ctx.multi_portal.dashboard.kpis || []).forEach((kpi) => {
								$kpis.append(`
									<div class="omnexa-portal-kpi-card">
										<div class="omnexa-portal-kpi-title">${frappe.utils.escape_html(kpi.title)}</div>
										<div class="omnexa-portal-kpi-value">${frappe.utils.escape_html(String(kpi.value ?? 0))}</div>
									</div>`);
							});
							$main.append($kpis);
						}

						$main.append(`<h5 class="oj-section-title">${t("القوائم التشغيلية", "Operational Menus")}</h5>`);
						$main.append(renderOperationalMenu(ctx.menu_sections || []));

						$layout.append($sidebar).append($main);
						$mount.empty().append($layout);

						if (wrapper && wrapper.page && wrapper.page.set_title) {
							wrapper.page.set_title(title);
						}
					},
				});
			},
		});
	};

	omnexa_core.vertical_portal.mountRoleDesk = function (wrapper, appName, roleKey) {
		if (appName === "omnexa_trading" && omnexa_core.vertical_portal.mountPharmaDesk) {
			omnexa_core.vertical_portal.mountPharmaDesk(wrapper, roleKey);
			return;
		}
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
