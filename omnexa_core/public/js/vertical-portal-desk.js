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
		if (appName === "omnexa_hr" && window.egx && egx.desk && egx.desk.mountRoleLauncher) {
			omnexa_core.vertical_portal.mountHrRoleDesk(wrapper, roleKey);
			return;
		}
		const OJ = window.OmnexaJourney;
		const VW = window.omnexa_core && omnexa_core.vertical_workcenter;
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
			method: "omnexa_core.vertical_workcenter.role_portal_context.get_role_portal_context",
			args: { app: appName, role_key: roleKey },
			callback(r) {
				const ctx = r.message || {};
				const portal = ctx.portal || {};
				const groups = ctx.grouped_portals || [];
				const title = t(portal.label_ar || ctx.title_ar, portal.label_en || ctx.title_en) || pageTitle;
				const roleLabel = t(portal.role_ar || ctx.role_ar, portal.role_en || ctx.role_en) || roleKey;
				const brandName = t(ctx.brand_name_ar, ctx.brand_name_en) || t(ctx.title_ar, ctx.title_en);

				const $layout = $('<div class="oj-vertical-portal-layout"></div>');
				const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
				$sidebar.append(
					`<div class="oj-vertical-portal-brand">
						${ctx.logo_url ? `<img src="${ctx.logo_url}" alt="" />` : `<span class="oj-portal-role-icon">${portal.icon || ctx.icon || "🌐"}</span>`}
						<strong>${frappe.utils.escape_html(brandName)}</strong>
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
				$main.append(`<h3 class="oj-section-title">${frappe.utils.escape_html(title)} <span class="oj-muted">${portal.icon || ctx.icon || ""}</span></h3>`);
				$main.append(
					`<p class="oj-muted">${frappe.utils.escape_html(t("بوابة دور", "Role portal"))}: <strong>${frappe.utils.escape_html(roleLabel)}</strong></p>`
				);

				if ((ctx.kpis || []).length) {
					const $kpis = $('<div class="omnexa-portal-kpi-grid"></div>');
					ctx.kpis.forEach((kpi) => {
						$kpis.append(`
							<div class="omnexa-portal-kpi-card">
								<div class="omnexa-portal-kpi-title">${frappe.utils.escape_html(t(kpi.label_ar, kpi.label_en))}</div>
								<div class="omnexa-portal-kpi-value">${frappe.utils.escape_html(String(kpi.value ?? 0))}</div>
							</div>`);
					});
					$main.append($kpis);
				}

				if ((ctx.menu_sections || []).length) {
					$main.append(`<h5 class="oj-section-title">${t("القوائم التشغيلية", "Operational Menus")}</h5>`);
					$main.append(renderOperationalMenu(ctx.menu_sections));
				} else if ((ctx.quick_links || []).length) {
					$main.append(`<h5 class="oj-section-title">${t("اختصارات", "Quick Links")}</h5>`);
					$main.append(renderQuickActions(ctx.quick_links));
				}

				if (ctx.is_admin && (ctx.sibling_portals || []).length) {
					const $portalGrid = $('<div class="oj-portal-role-grid"></div>');
					ctx.sibling_portals.forEach((p) => {
						if (!p.route) return;
						const $card = $(`
							<div class="oj-portal-role-card">
								<div class="oj-portal-role-icon">${p.icon || "🌐"}</div>
								<h4>${frappe.utils.escape_html(t(p.label_ar, p.label_en))}</h4>
								<p class="oj-muted">${frappe.utils.escape_html(t(p.role_ar, p.role_en))}</p>
								<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${t("فتح", "Open")}</button>
							</div>`);
						$card.on("click", () => navigateRoute(p.route));
						$portalGrid.append($card);
					});
					$main.append(`<h5 class="oj-section-title" style="margin-top:20px">${t("جميع بوابات الأدوار", "All Role Portals")}</h5>`);
					$main.append($portalGrid);
				}

				if (!ctx.menu_sections?.length && !ctx.quick_links?.length && !ctx.sibling_portals?.length) {
					$main.append(
						`<div class="oj-card oj-vertical-portal-card">
							<p>${t("لا توجد قوائم مرتبطة بعد — راجع مساحة عمل القطاع.", "No linked menus yet — check the sector workspace.")}</p>
						</div>`
					);
				}

				$layout.append($sidebar).append($main);

				if (OJ && OJ.shell && VW && VW.buildAppSidebar) {
					const $body = $('<div class="oj-role-portal-hub"></div>').append($layout);
					const $shell = OJ.shell({
						title,
						subtitle: t("بوابات الأدوار · قائمة حسب الدور", "Role portals · role-scoped menus"),
						role: roleLabel,
						brandName,
						app: appName,
						sidebar: VW.buildAppSidebar(ctx, currentRoute.split("/app/")[1], OJ),
						bodyEl: $body,
						homeRoute: ctx.workcenter_route,
					});
					$mount.empty().append($shell);
				} else {
					$mount.empty().append($layout);
				}

				if (wrapper && wrapper.page && wrapper.page.set_title) {
					wrapper.page.set_title(title);
				}
			},
		});
	};

	const HR_ROLE_META = {
		"executive-dashboard": {
			title: __("Executive Dashboard"),
			description: __("Executive HR overview — same catalog as HR Dashboard."),
		},
		"operations-desk": {
			title: __("HR Operations Desk"),
			description: __("Day-to-day HR operations — attendance, leave, workforce management."),
		},
		"finance-desk": {
			title: __("HR Finance Desk"),
			description: __("Payroll, compensation, and HR finance workflows."),
		},
		"customer-portal": {
			title: __("HR Customer Portal"),
			description: __("External HR services portal for employees and stakeholders."),
		},
	};

	omnexa_core.vertical_portal.mountHrRoleDesk = function (wrapper, roleKey) {
		const meta = HR_ROLE_META[roleKey] || { title: __("HR Role Desk"), description: "" };
		const pageRoute = `hr-${roleKey}`;

		egx.desk.boot_modern_page(
			{
				pageRoute: pageRoute,
				wrapper: wrapper,
				css: ["/assets/omnexa_hr/css/hr_desk.css"],
				js: ["/assets/omnexa_core/js/egx_desk_dashboard.js"],
			},
			() => {
				const page = frappe.ui.make_app_page({
					parent: wrapper,
					title: meta.title,
					single_column: true,
				});
				page.set_primary_action(__("Refresh"), () => load($(page.main)));

				function load($main) {
					$main.html(`<div class="egx-skeleton-grid" style="padding:16px">${Array(4).fill('<div class="ed-skeleton-card" style="height:64px"></div>').join("")}</div>`);

					if (roleKey === "executive-dashboard") {
						frappe.call({
							method: "omnexa_hr.omnexa_hr.api.hr_dashboard.get_hr_dashboard_catalog",
							callback(r) {
								egx.desk.mountDashboard($main, r.message || {}, { onRefresh: () => load($main) });
							},
						});
						return;
					}

					const pageId = `hr-${roleKey}`;
					frappe.call({
						method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
						args: { app: "omnexa_hr" },
						callback(ctxRes) {
							const ctx = ctxRes.message || {};
							const all = (ctx.grouped_portals || []).flatMap((g) => g.portals || []);
							const links = all
								.filter((p) => p.exists !== false)
								.map((p) => ({
									label: t(p.label_ar, p.label_en),
									href: p.route,
									external: !String(p.route || "").startsWith("/hr"),
								}));

							frappe.call({
								method: "omnexa_hr.omnexa_hr.api.hr_workspace_catalog.get_hr_workspace_catalog",
								callback(catRes) {
									const cat = catRes.message || {};
									const seen = new Set(links.map((l) => l.href));
									(cat.sections || []).forEach((section) => {
										(section.links || []).forEach((l) => {
											const href = l.href || l.next_href;
											if (href && !seen.has(href)) {
												links.push({ label: l.label, href: href, external: l.external });
												seen.add(href);
											}
										});
									});
									const match = all.find((p) => p.id === pageId);
									if (match) {
										links.unshift({
											label: t(match.label_ar, match.label_en),
											href: match.route,
											external: !String(match.route || "").startsWith("/hr"),
										});
									}
									egx.desk.mountRoleLauncher($main, {
										title: meta.title,
										description: meta.description,
										links: links.slice(0, 16),
									});
								},
							});
						},
					});
				}

				load($(page.main));
			}
		);
	};
})();
