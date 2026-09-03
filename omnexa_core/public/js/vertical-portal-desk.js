/**
 * ErpGenEx — Standard role portal desk (Trading / Pharma layout for all verticals)
 */
/* global frappe */
frappe.provide("omnexa_core.vertical_portal");

(function () {
	"use strict";

	const APP_PORTAL_CONTEXT = {
		omnexa_trading: {
			method: "omnexa_trading.pharma_portal_catalog.get_role_portal_context",
			args: (roleKey) => ({ role_key: roleKey }),
		},
		erpgenex_legal: {
			method: "erpgenex_legal.api.legal_role_portal.get_role_portal_context",
			args: (roleKey) => ({ role_key: roleKey }),
		},
		omnexa_hr: {
			method: "omnexa_hr.omnexa_hr.api.hr_role_portal.get_role_portal_context",
			args: (roleKey) => ({ role_key: roleKey }),
		},
	};

	const APP_WORKCENTER_CONTEXT = {
		erpgenex_legal: {
			method: "erpgenex_legal.api.legal_workcenter.get_workcenter_context_api",
			args: () => ({}),
		},
		omnexa_trading: {
			method: "omnexa_trading.trading_portal_catalog.get_workcenter_context",
			args: () => ({}),
		},
		omnexa_education: {
			method: "omnexa_education.api.education_portal_catalog.get_workcenter_context",
			args: () => ({}),
		},
		omnexa_hr: {
			method: "omnexa_hr.omnexa_hr.api.hr_role_portal.get_workcenter_context_api",
			args: () => ({}),
		},
	};

	function t(ar, en) {
		return frappe.boot.lang === "ar" ? ar : en;
	}

	function isRtl() {
		return (frappe.boot.lang || "").startsWith("ar");
	}

	function applyPortalDirection($el) {
		if (!$el || !$el.length) return;
		const rtl = isRtl();
		$el.attr("dir", rtl ? "rtl" : "ltr");
		$el.toggleClass("oj-rtl", rtl).toggleClass("oj-ltr", !rtl);
	}

	function esc(v) {
		return frappe.utils.escape_html(String(v ?? ""));
	}

	function renderPortalIcon(item, cssClass) {
		cssClass = cssClass || "oj-pharma-ops-icon";
		const svg = item && item.icon_svg;
		const color = (item && item.icon_color) || "#6366f1";
		if (svg && frappe.utils && frappe.utils.icon) {
			return `<span class="${cssClass} oj-portal-icon-badge" style="--portal-icon-bg:${esc(color)}">${frappe.utils.icon(svg, "md")}</span>`;
		}
		return `<span class="${cssClass}">${(item && item.icon) || "▫️"}</span>`;
	}

	function navigateRoute(route) {
		if (!route) return;
		if (route.startsWith("/app/") || route.startsWith("/legal") || route.startsWith("/education/")) {
			window.location.href = route;
			return;
		}
		frappe.set_route(route);
	}

	function scrubLegacySidebars(wrapper) {
		document.body.classList.remove("legal-desk-active");
		document.body.classList.add("no-sidebar");
		document.body.setAttribute("data-sidebar", "0");
		const $scope = $(wrapper).closest(".page-container");
		$scope.find(".oj-shell > .oj-sidebar, aside.oj-sidebar").remove();
		$scope.find(".legal-desk-shell > .legal-desk-aside").remove();
		$(".desk-sidebar, .list-sidebar, .layout-side-section").hide();
	}

	function prepareMount(wrapper, title) {
		document.body.classList.add("omnexa-role-portal-active");
		$(wrapper).closest(".page-container").addClass("omnexa-role-portal-page");
		scrubLegacySidebars(wrapper);
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: title || __("Role Portal"),
			single_column: true,
		});
		$(wrapper).find(".page-head").hide();
		return $(page.main);
	}

	function renderSidebar(groups, activeRoute) {
		const $nav = $('<nav class="oj-vertical-portal-sidebar"></nav>');
		(groups || []).forEach((g) => {
			$nav.append(`<div class="oj-sidebar-section">${esc(t(g.label_ar, g.label_en))}</div>`);
			(g.portals || []).forEach((p) => {
				const label = t(p.label_ar, p.label_en);
				const active = p.route === activeRoute ? " active" : "";
				const $link = $(`
					<a class="oj-sidebar-link${active}" href="${esc(p.route)}">
						${renderPortalIcon(p, "oj-sidebar-icon")}
						<span>${esc(label)}</span>
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

	function collectFlatPortals(groups) {
		const allPortals = [];
		(groups || []).forEach((g) => {
			(g.portals || []).forEach((p) => {
				if (p.exists === false || !p.route) return;
				allPortals.push(p);
			});
		});
		return allPortals;
	}

	function sidebarNavForContext(ctx, currentRoute) {
		return renderSidebar(ctx.grouped_portals || [], currentRoute);
	}

	function renderFlatPortalNav(portals, activeRoute) {
		const $nav = $('<nav class="oj-vertical-portal-sidebar"></nav>');
		(portals || []).forEach((p) => {
			const label = t(p.label_ar, p.label_en);
			const active = p.route === activeRoute ? " active" : "";
			const $link = $(`
				<a class="oj-sidebar-link${active}" href="${esc(p.route)}">
					${renderPortalIcon(p, "oj-sidebar-icon")}
					<span>${esc(label)}</span>
				</a>`);
			$link.on("click", (e) => {
				e.preventDefault();
				navigateRoute(p.route);
			});
			$nav.append($link);
		});
		return $nav;
	}

	function renderOperationalMenu(sections) {
		const $root = $('<div class="oj-pharma-ops-sections"></div>');
		(sections || []).forEach((section) => {
			const $sec = $(`
				<section class="oj-pharma-ops-section">
					<h5 class="oj-pharma-ops-section-title">${esc(t(section.title_ar, section.title_en))}</h5>
					<div class="oj-pharma-ops-menu"></div>
				</section>`);
			(section.items || []).forEach((item) => {
				const label = t(item.label_ar, item.label_en);
				const $btn = $(`
					<a class="oj-pharma-ops-link" href="${esc(item.route)}">
						${renderPortalIcon(item)}
						<span class="oj-pharma-ops-label">${esc(label)}</span>
					</a>`);
				$btn.on("click", (e) => {
					e.preventDefault();
					navigateRoute(item.route);
				});
				$sec.find(".oj-pharma-ops-menu").append($btn);
			});
			if ($sec.find(".oj-pharma-ops-link").length) {
				$root.append($sec);
			}
		});
		return $root;
	}

	function renderQuickActions(actions) {
		const $row = $('<div class="omnexa-portal-quick-actions"></div>');
		(actions || []).forEach((act) => {
			const label = t(act.label_ar || act.label, act.label_en || act.label);
			const $btn = $(`
				<a class="btn btn-sm btn-default omnexa-portal-quick-btn" href="${esc(act.route)}">
					${act.icon || "⚡"} ${esc(label)}
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
		const $panel = $(`<div class="omnexa-portal-panel"><h5>${esc(t(titleAr, titleEn))}</h5></div>`);
		const $list = $('<ul class="omnexa-portal-list"></ul>');
		if (!rows || !rows.length) {
			$list.append(`<li class="text-muted">${t("لا توجد عناصر", "No items")}</li>`);
		} else {
			rows.forEach((row) => {
				const label =
					row[labelField] ||
					row.task_title ||
					row.legal_case ||
					row.applicant_name ||
					row.description ||
					row.name ||
					"-";
				$list.append(`<li>${esc(String(label))}</li>`);
			});
		}
		$panel.append($list);
		return $panel;
	}

	function normalizeDashboard(ctx) {
		const dash = ctx.dashboard || {};
		if (dash.kpis && (dash.work_queue || dash.pending_tasks || dash.approvals || dash.charts)) {
			return dash;
		}
		const kpis = (dash.kpis || ctx.kpis || []).map((kpi) => ({
			title_en: kpi.title_en || kpi.label_en,
			title_ar: kpi.title_ar || kpi.label_ar,
			value: kpi.value,
			icon: kpi.icon || "📊",
		}));
		const quick_actions = (dash.quick_actions || []).map((act) => ({
			label_en: act.label_en || act.label,
			label_ar: act.label_ar || act.label,
			route: act.route,
			icon: act.icon || "⚡",
		}));
		return {
			kpis,
			quick_actions,
			work_queue: dash.work_queue || dash.hearings || [],
			pending_tasks: dash.pending_tasks || dash.tasks || [],
			approvals: dash.approvals || dash.intake || [],
			charts: dash.charts || [],
		};
	}

	function renderPharmaDashboard(dashboard) {
		const $dash = $('<div class="omnexa-pharma-dashboard"></div>');
		if (!dashboard) return $dash;

		const kpis = dashboard.kpis || [];
		if (kpis.length) {
			const $kpis = $('<div class="omnexa-portal-kpi-grid"></div>');
			kpis.forEach((kpi) => {
				const title = t(kpi.title_ar || kpi.label_ar, kpi.title_en || kpi.label_en || kpi.title);
				$kpis.append(`
					<div class="omnexa-portal-kpi-card">
						<div class="omnexa-portal-kpi-title">${kpi.icon || "📊"} ${esc(title)}</div>
						<div class="omnexa-portal-kpi-value">${esc(String(kpi.value ?? 0))}</div>
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
				$charts.append(`<div class="omnexa-portal-chart-placeholder">${esc(title)} (${ch.type || "chart"})</div>`);
			});
			$dash.append($charts);
		}

		return $dash;
	}

	function renderStandardRolePortal($mount, wrapper, ctx, currentRoute, $sidebarNav) {
		const portal = ctx.portal || {};
		const title = t(portal.label_ar || ctx.title_ar, portal.label_en || ctx.title_en);
		const roleLabel = t(portal.role_ar || ctx.role_ar, portal.role_en || ctx.role_en);
		const brandName = t(ctx.brand_name_ar, ctx.brand_name_en) || title;
		const icon = portal.icon || ctx.icon || "🌐";

		const $layout = $('<div class="oj-vertical-portal-layout omnexa-standard-role-portal"></div>');
		applyPortalDirection($layout);
		const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
		$sidebar.append(`
			<div class="oj-vertical-portal-brand">
				${ctx.logo_url ? `<img src="${esc(ctx.logo_url)}" alt="" />` : `<span class="oj-portal-role-icon">${icon}</span>`}
				<strong>${esc(brandName)}</strong>
			</div>`);
		$sidebar.append($sidebarNav || renderSidebar(ctx.grouped_portals || [], currentRoute));
		$sidebar.append(
			`<a class="oj-sidebar-link oj-sidebar-back" href="${esc(ctx.workcenter_route || "#")}">${t("← مركز العمل", "← Workcenter")}</a>`
		);

		const $main = $('<div class="oj-vertical-portal-main"></div>');
		$main.append(`<h3 class="oj-section-title">${esc(title)}</h3>`);
		$main.append(
			`<p class="oj-muted omnexa-portal-role-line">${esc(t("بوابة دور", "Role portal"))}: <strong>${esc(roleLabel)}</strong></p>`
		);
		$main.append(renderPharmaDashboard(normalizeDashboard(ctx)));

		if ((ctx.menu_sections || []).length) {
			$main.append(`<h5 class="oj-section-title">${t("القوائم التشغيلية", "Operational Menus")}</h5>`);
			$main.append(renderOperationalMenu(ctx.menu_sections));
		} else if ((ctx.quick_links || []).length) {
			$main.append(`<h5 class="oj-section-title">${t("اختصارات", "Quick Links")}</h5>`);
			$main.append(renderQuickActions(ctx.quick_links));
		}

		$layout.append($sidebar).append($main);
		$mount.empty().append($layout);

		if (wrapper && wrapper.page && wrapper.page.set_title) {
			wrapper.page.set_title(title);
		}
	}

	function resolveContextCall(appName, roleKey) {
		const spec = APP_PORTAL_CONTEXT[appName];
		if (spec) {
			return { method: spec.method, args: spec.args(roleKey) };
		}
		return {
			method: "omnexa_core.vertical_workcenter.role_portal_context.get_role_portal_context",
			args: { app: appName, role_key: roleKey },
		};
	}

	function resolveWorkcenterCall(appName, opts) {
		if (opts && opts.method) {
			return { method: opts.method, args: opts.args || {} };
		}
		const spec = APP_WORKCENTER_CONTEXT[appName];
		if (spec) {
			return { method: spec.method, args: spec.args(appName) };
		}
		return {
			method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
			args: { app: appName },
		};
	}

	function renderStandardWorkcenter($mount, wrapper, ctx, appName, currentRoute, opts, refresh) {
		opts = opts || {};
		const title = t(opts.title_ar || ctx.title_ar, opts.title_en || ctx.title_en);
		const subtitle = t(opts.subtitle_ar, opts.subtitle_en);
		const roleLabel = t(ctx.role_label_ar || ctx.role_ar, ctx.role_label_en || ctx.role_en);
		const brandName = t(ctx.brand_name_ar, ctx.brand_name_en) || title;
		const icon = opts.icon || ctx.icon || "🎯";

		const $layout = $('<div class="oj-vertical-portal-layout omnexa-standard-role-portal"></div>');
		applyPortalDirection($layout);
		const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
		$sidebar.append(`
			<div class="oj-vertical-portal-brand">
				${ctx.logo_url ? `<img src="${esc(ctx.logo_url)}" alt="" />` : `<span class="oj-portal-role-icon">${icon}</span>`}
				<strong>${esc(brandName)}</strong>
			</div>`);
		$sidebar.append(sidebarNavForContext(ctx, currentRoute));
		$sidebar.append(
			`<a class="oj-sidebar-link oj-sidebar-back" href="${esc(ctx.workcenter_route || currentRoute)}">${t("← مركز العمل", "← Workcenter")}</a>`
		);

		const $main = $('<div class="oj-vertical-portal-main"></div>');
		const $header = $('<div class="omnexa-portal-workcenter-header"></div>');
		$header.append(`<h3 class="oj-section-title">${esc(title)}</h3>`);
		if (subtitle) {
			$header.append(`<p class="oj-muted omnexa-portal-role-line">${esc(subtitle)}</p>`);
		}
		if (roleLabel) {
			$header.append(
				`<p class="oj-muted omnexa-portal-role-line">${esc(t("بوابة دور", "Role portal"))}: <strong>${esc(roleLabel)}</strong></p>`
			);
		}
		const $actions = $('<div class="omnexa-portal-header-actions"></div>');
		if (refresh) {
			$actions.append(
				`<button type="button" class="btn btn-default btn-sm btn-wc-refresh">${t("تحديث", "Refresh")}</button>`
			);
		}
		if (opts.websiteRoute) {
			$actions.append(
				`<a class="btn btn-primary btn-sm" href="${esc(opts.websiteRoute)}">${t("الموقع", "Website")}</a>`
			);
		}
		if ($actions.children().length) {
			$header.append($actions);
		}
		$main.append($header);
		if ($actions.find(".btn-wc-refresh").length) {
			$actions.find(".btn-wc-refresh").on("click", refresh);
		}

		if (opts.renderExtra) {
			opts.renderExtra($main, ctx, refresh);
		}

		if (ctx.primary_portal && !ctx.is_admin) {
			const pp = ctx.primary_portal;
			const $hint = $(`
				<div class="omnexa-portal-primary-hint mb-3">
					<button type="button" class="btn btn-primary btn-sm btn-open-primary">${t("فتح بوابتي", "Open My Portal")}</button>
				</div>`);
			$hint.find(".btn-open-primary").on("click", () => navigateRoute(pp.route));
			$main.append($hint);
		}

		$main.append(renderPharmaDashboard(normalizeDashboard(ctx)));

		if ((ctx.menu_sections || []).length) {
			$main.append(`<h5 class="oj-section-title">${t("القوائم التشغيلية", "Operational Menus")}</h5>`);
			$main.append(renderOperationalMenu(ctx.menu_sections));
		}

		const groups = ctx.grouped_portals || [];
		if (groups.length) {
			$main.append(`<h5 class="oj-section-title">${t("بوابات الأدوار", "Role Portals")}</h5>`);
			$main.append(omnexa_core.vertical_portal.renderPortalCategoryGrid(groups));
		}

		$layout.append($sidebar).append($main);
		$mount.empty().append($layout);

		if (wrapper && wrapper.page && wrapper.page.set_title) {
			wrapper.page.set_title(title);
		}
	}

	omnexa_core.vertical_portal.renderPortalCategoryGrid = function (groups) {
		const $root = $('<div class="oj-portal-role-grid"></div>');
		(groups || []).forEach((group) => {
			(group.portals || []).forEach((portal) => {
				if (portal.exists === false || !portal.route) return;
				const $card = $(`
					<a class="oj-portal-role-card" href="${esc(portal.route)}">
						${renderPortalIcon(portal, "oj-portal-role-icon")}
						<h4>${esc(t(portal.label_ar, portal.label_en))}</h4>
						<p class="oj-muted">${esc(t(portal.role_ar, portal.role_en))}</p>
					</a>`);
				$card.on("click", (e) => {
					e.preventDefault();
					navigateRoute(portal.route);
				});
				$root.append($card);
			});
		});
		return $root;
	};

	omnexa_core.vertical_portal.mountPharmaDesk = function (wrapper, roleKey) {
		omnexa_core.vertical_portal.mountRoleDesk(wrapper, "omnexa_trading", roleKey);
	};

	omnexa_core.vertical_portal.mountWorkcenter = function (wrapper, appName, opts) {
		opts = opts || {};
		const currentRoute = `/app/${frappe.get_route_str().replace(/ /g, "-")}`;
		document.body.classList.add("omnexa-role-portal-active");
		$(wrapper).closest(".page-container").addClass("omnexa-role-portal-page");
		scrubLegacySidebars(wrapper);
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: opts.pageTitle || __("Workcenter"),
			single_column: true,
		});
		$(wrapper).find(".page-head").hide();
		const $mount = $(page.main);

		function load() {
			$mount.html(`<div class="omnexa-portal-loading text-muted">${t("جاري التحميل...", "Loading...")}</div>`);
			const callSpec = resolveWorkcenterCall(appName, opts);
			frappe.call({
				method: callSpec.method,
				args: callSpec.args,
				callback(r) {
					if (r.exc) {
						$mount.html(`<div class="text-muted">${t("تعذّر تحميل مركز العمل", "Failed to load workcenter")}</div>`);
						return;
					}
					renderStandardWorkcenter($mount, wrapper, r.message || {}, appName, currentRoute, opts, load);
				},
			});
		}

		load();
	};

	omnexa_core.vertical_portal.mountRoleDesk = function (wrapper, appName, roleKey) {
		const currentRoute = `/app/${frappe.get_route_str().replace(/ /g, "-")}`;
		const $mount = prepareMount(wrapper, __("Role Portal"));
		$mount.html(`<div class="omnexa-portal-loading text-muted">${t("جاري التحميل...", "Loading...")}</div>`);

		const callSpec = resolveContextCall(appName, roleKey);
		frappe.call({
			method: callSpec.method,
			args: callSpec.args,
			callback(r) {
				if (r.exc) {
					$mount.html(`<div class="text-muted">${t("تعذّر تحميل البوابة", "Failed to load portal")}</div>`);
					return;
				}
				const ctx = r.message || {};
				renderStandardRolePortal(
					$mount,
					wrapper,
					ctx,
					currentRoute,
					sidebarNavForContext(ctx, currentRoute)
				);
			},
		});
	};

	if (window.frappe && frappe.router) {
		frappe.router.on("change", () => {
			document.body.classList.remove("omnexa-role-portal-active", "no-sidebar");
			document.body.removeAttribute("data-sidebar");
			$(".page-container").removeClass("omnexa-role-portal-page");
		});
	}

	omnexa_core.vertical_portal.renderPortalIcon = renderPortalIcon;
})();
