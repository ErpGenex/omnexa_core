/**
 * ErpGenEx — Generic Vertical Workcenter (Education / Healthcare / Trading parity)
 */
/* global frappe */
frappe.provide("omnexa_core.vertical_workcenter");

(function () {
	"use strict";

	const VW = omnexa_core.vertical_workcenter;

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

	function portalGrid(groups) {
		const $root = $('<div class="oj-portal-catalog oj-education-portals"></div>');
		(groups || []).forEach((g) => {
			const title = t(g.label_ar, g.label_en);
			const $sec = $(`<div class="oj-portal-section"><h4 class="oj-portal-cat-title">${frappe.utils.escape_html(title)}</h4></div>`);
			const $grid = $('<div class="oj-clinic-grid"></div>');
			(g.portals || []).forEach((p) => {
				const $card = $(`
					<div class="oj-clinic-card">
						<div class="oj-clinic-icon">${p.icon || "🌐"}</div>
						<h4>${frappe.utils.escape_html(t(p.label_ar, p.label_en))}</h4>
					</div>`);
				$card.on("click", () => navigateRoute(p.route));
				$grid.append($card);
			});
			$sec.append($grid);
			$root.append($sec);
		});
		return $root;
	}

	/** Healthcare-parity portal grid using OmnexaJourney clinicGrid */
	VW.renderJourneyPortals = function ($container, groups, OJ, opts) {
		opts = opts || {};
		const subtitleAr = opts.portalSubtitleAr || "بوابة خارجية";
		const subtitleEn = opts.portalSubtitleEn || "Outpatient portal";
		const defaultIcon = opts.defaultIcon || "🌐";
		(groups || []).forEach((g) => {
			const title = OJ.lang() === "ar" ? g.label_ar : g.label_en;
			$container.append(`<h4 class="oj-portal-cat-title" style="margin-top:20px">${OJ.esc(title)}</h4>`);
			const clinics = (g.portals || []).map((p) => ({
				id: p.id,
				name: OJ.lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: OJ.t(subtitleAr, subtitleEn),
				icon: p.icon || defaultIcon,
				doctor_count: 1,
				waiting_count: 0,
				route: p.route,
				exists: p.exists,
			}));
			if (OJ.clinicGrid) {
				$container.append(
					OJ.clinicGrid(
						clinics.filter((c) => c.exists !== false && c.route),
						(c) => OJ.navigateRoute(c.route)
					)
				);
			}
		});
	};

	VW.renderDemoAccountsPanel = function ($body, creds, OJ, opts) {
		opts = opts || {};
		if (!creds || !(creds.users || []).length) return;
		const $panel = $(`<div class="oj-panel" style="margin-top:16px"></div>`);
		$panel.append(`<h4>${OJ.t("حسابات الديمو", "Demo Accounts")}</h4>`);
		if (creds.password) {
			$panel.append(
				`<p class="oj-muted">${OJ.t("كلمة المرور", "Password")}: <code>${OJ.esc(creds.password)}</code></p>`
			);
		}
		if (opts.actionsHtml) {
			$panel.append(`<div class="oj-filter-bar">${opts.actionsHtml}</div>`);
		}
		const tableHtml =
			typeof OJ.dataTable === "function"
				? OJ.dataTable(
						opts.columns || [
							{ field: "role", label: OJ.t("الدور", "Role") },
							{ field: "email", label: OJ.t("البريد", "Email") },
							{ field: "name", label: OJ.t("الاسم", "Name") },
							{ field: "route", label: OJ.t("البوابة", "Portal") },
						],
						(creds.users || []).map((u) => ({ ...u, route: u.route || "—" }))
					)
				: "";
		if (typeof tableHtml === "string") {
			$panel.append(tableHtml);
		} else {
			$panel.append(tableHtml);
		}
		$body.append($panel);
	};

	/**
	 * Mount healthcare-parity journey workcenter shell.
	 * config: { pageTitle, shellTitle, shellSubtitle, shellRole, homeRoute, sidebarRole,
	 *           brandLogoUrl, currentPage, portalOpts, load, renderExtra, bindActions }
	 */
	VW.mountJourney = function (wrapper, config) {
		const OJ = window.OmnexaJourney;
		const cfg = config || {};
		if (!OJ || !OJ.mountDeskPage) {
			frappe.ui.make_app_page({
				parent: wrapper,
				title: cfg.pageTitle || __("Workcenter"),
				single_column: true,
			});
			return;
		}
		const $mount = OJ.mountDeskPage(wrapper, cfg.pageTitle || __("Workcenter"));

		async function render() {
			const data = (await cfg.load()) || {};
			const groups = data.groups || data.grouped_portals || [];
			const creds = data.credentials || data.creds || null;
			const kpis = (data.kpis || []).map((k) => ({
				value: k.value ?? "—",
				label: OJ.t(k.label_ar, k.label_en),
			}));

			const $body = $('<div class="oj-demo-hub"></div>');
			if (cfg.renderIntro) {
				cfg.renderIntro($body, data, OJ);
			}
			if (cfg.renderExtra) {
				await cfg.renderExtra($body, data, OJ);
			}
			if (cfg.showDemoAccounts !== false && creds && (creds.users || []).length) {
				VW.renderDemoAccountsPanel($body, creds, OJ, cfg.demoPanelOpts || {});
			}
			if (groups.length) {
				const portalTitle = cfg.portalPanelTitle || OJ.t("بوابات الأدوار", "Role Portals");
				$body.append(
					`<div class="oj-panel oj-demo-portals-panel" style="margin-top:16px"><h4>${portalTitle}</h4></div>`
				);
				VW.renderJourneyPortals($body.find(".oj-demo-portals-panel"), groups, OJ, cfg.portalOpts || {});
			}
			if (cfg.renderFooter) {
				cfg.renderFooter($body, data, OJ);
			}
			if (cfg.bindActions) {
				cfg.bindActions($body, data, render);
			}

			const shellOpts = {
				title: cfg.shellTitle,
				subtitle: cfg.shellSubtitle,
				role: cfg.shellRole || OJ.t("مدير النظام", "System Manager"),
				sidebar: cfg.sidebar || (OJ.defaultSidebar ? OJ.defaultSidebar(cfg.sidebarRole || "admin", cfg.currentPage) : []),
				bodyEl: $body,
				homeRoute: cfg.homeRoute,
				brandLogoUrl: data.logo_url || cfg.brandLogoUrl,
				kpis: kpis.length ? kpis : undefined,
				sidebarRole: cfg.sidebarRole,
				currentPage: cfg.currentPage,
			};
			const $shell = OJ.shell(shellOpts);
			$mount.empty().append($shell);
		}

		render().catch((e) => (OJ.showCallError ? OJ.showCallError(e) : frappe.msgprint(e.message || String(e))));
	};

	VW.mount = function (wrapper, appName) {
		const OJ = window.OmnexaJourney;
		if (OJ && OJ.mountDeskPage && OJ.shell && OJ.clinicGrid) {
			VW.mountJourney(wrapper, {
				pageTitle: __("Workcenter"),
				shellTitle: t("مركز عمل ErpGenEx", "ErpGenEx Workcenter"),
				shellSubtitle: t("بوابات الأدوار · محاكاة من الفرع", "Role portals · branch simulation"),
				shellRole: t("مدير النظام", "System Manager"),
				homeRoute: `/app/${appName.replace("omnexa_", "")}-workcenter`,
				sidebarRole: "admin",
				currentPage: `${appName.replace("omnexa_", "")}-workcenter`,
				portalOpts: { defaultIcon: "🌐" },
				showDemoAccounts: false,
				async load() {
					return new Promise((resolve, reject) => {
						frappe.call({
							method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
							args: { app: appName },
							callback(r) {
								const ctx = r.message || {};
								resolve({
									groups: ctx.grouped_portals || [],
									logo_url: ctx.logo_url,
									kpis: ctx.kpis || [],
								});
							},
							error: reject,
						});
					});
				},
				renderIntro($body, data, OJ) {
					$body.append(`<div class="oj-panel oj-phase-panel-intro">
						<h4>${OJ.t("مركز العمل", "Workcenter")}</h4>
						<p class="oj-muted">${OJ.t(
							"بوابات الأدوار · محاكاة من الفرع",
							"Role portals · branch simulation"
						)}</p>
					</div>`);
				},
			});
			return;
		}

		const title = __("Workcenter");
		let $mount;
		if (OJ && OJ.mountDeskPage) {
			$mount = OJ.mountDeskPage(wrapper, title);
		} else {
			const page = frappe.ui.make_app_page({ parent: wrapper, title, single_column: true });
			$mount = $(page.body);
		}

		frappe.call({
			method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
			args: { app: appName },
			callback(r) {
				const ctx = r.message || {};
				const groups = ctx.grouped_portals || [];
				const $layout = $('<div class="oj-vertical-portal-layout"></div>');
				const $sidebar = $('<aside class="oj-vertical-portal-aside"></aside>');
				$sidebar.append(
					`<div class="oj-vertical-portal-brand">
						${ctx.logo_url ? `<img src="${ctx.logo_url}" alt="" />` : ""}
						<strong>${frappe.utils.escape_html(t(ctx.title_ar, ctx.title_en))}</strong>
					</div>`
				);
				(groups || []).forEach((g) => {
					const gtitle = t(g.label_ar, g.label_en);
					$sidebar.append(`<div class="oj-sidebar-section">${frappe.utils.escape_html(gtitle)}</div>`);
					(g.portals || []).forEach((p) => {
						const $link = $(`
							<a class="oj-sidebar-link" href="${frappe.utils.escape_html(p.route)}">
								<span class="oj-sidebar-icon">${p.icon || "🌐"}</span>
								<span>${frappe.utils.escape_html(t(p.label_ar, p.label_en))}</span>
							</a>`);
						$link.on("click", (e) => {
							e.preventDefault();
							navigateRoute(p.route);
						});
						$sidebar.append($link);
					});
				});

				const $main = $('<div class="oj-vertical-portal-main vertical-workcenter-journey"></div>');
				$main.append(
					`<p class="oj-muted">${t(
						"مركز العمل — بوابات الأدوار · محاكاة من الفرع",
						"Workcenter — role portals · branch simulation"
					)}</p>`
				);
				if (ctx.can_simulate) {
					$main.append(`<p class="oj-muted">${frappe.utils.escape_html(ctx.branch_demo_hint || "")}</p>`);
				}
				$main.append(portalGrid(groups));

				$layout.append($sidebar).append($main);
				$mount.empty().append($layout);
			},
		});
	};
})();
