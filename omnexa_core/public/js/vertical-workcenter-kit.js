/**
 * ErpGenEx — Generic Vertical Workcenter (isolated per app · dynamic role portals)
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

	function labelFor(OJ, ar, en) {
		return OJ ? OJ.t(ar, en) : t(ar, en);
	}

	function escFor(OJ, value) {
		return OJ ? OJ.esc(value) : frappe.utils.escape_html(value == null ? "" : String(value));
	}

	/** Build sidebar from the active vertical's portal catalog — never healthcare defaults. */
	VW.buildAppSidebar = function (ctx, currentPage, OJ) {
		ctx = ctx || {};
		const homeRoute = ctx.workcenter_route || (currentPage ? `/app/${currentPage}` : "/app");
		const items = [
			{
				id: "workcenter",
				label: labelFor(OJ, "مركز العمل", "Workcenter"),
				icon: "🎯",
				route: homeRoute,
				active: !currentPage || currentPage === ctx.workcenter_page,
			},
		];
		const seen = new Set([homeRoute]);
		(ctx.grouped_portals || []).forEach((g) => {
			(g.portals || []).forEach((p) => {
				if (!p.route || p.exists === false || seen.has(p.route)) return;
				seen.add(p.route);
				const pageSlug = (p.route || "").split("/app/")[1] || "";
				items.push({
					id: p.id || pageSlug,
					label: labelFor(OJ, p.label_ar, p.label_en),
					icon: p.icon || "🌐",
					route: p.route,
					active: currentPage && (currentPage === pageSlug || p.route.indexOf(currentPage) >= 0),
				});
			});
		});
		return items.slice(0, 12);
	};

	function portalGrid(groups, OJ) {
		const $root = $('<div class="oj-portal-catalog oj-vertical-portals"></div>');
		(groups || []).forEach((g) => {
			const title = labelFor(OJ, g.label_ar, g.label_en);
			const $sec = $(`<div class="oj-portal-section"><h4 class="oj-portal-cat-title">${escFor(OJ, title)}</h4></div>`);
			const $grid = $('<div class="oj-portal-role-grid"></div>');
			(g.portals || []).forEach((p) => {
				if (p.exists === false || !p.route) return;
				const roleLabel = labelFor(OJ, p.role_ar || p.label_ar, p.role_en || p.label_en);
				const portalLabel = labelFor(OJ, p.label_ar, p.label_en);
				const $card = $(`
					<div class="oj-portal-role-card">
						<div class="oj-portal-role-icon">${p.icon || "🌐"}</div>
						<h4>${escFor(OJ, portalLabel)}</h4>
						<p class="oj-muted">${escFor(OJ, roleLabel)}</p>
						<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${labelFor(OJ, "فتح", "Open")}</button>
					</div>`);
				$card.on("click", () => navigateRoute(p.route));
				$card.find("button").on("click", (e) => {
					e.stopPropagation();
					navigateRoute(p.route);
				});
				$grid.append($card);
			});
			$sec.append($grid);
			$root.append($sec);
		});
		return $root;
	}

	/** Healthcare-only clinic grid (doctors / waiting). */
	VW.renderJourneyPortals = function ($container, groups, OJ, opts) {
		opts = opts || {};
		const useClinicGrid = opts.useClinicGrid === true;
		if (!useClinicGrid) {
			$container.append(portalGrid(groups, OJ));
			return;
		}
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
				doctor_count: p.doctor_count || 0,
				waiting_count: p.waiting_count || 0,
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
		$panel.append(tableHtml);
		$body.append($panel);
	};

	VW.resolveBrandName = function (data, cfg, OJ) {
		if (cfg.brandName) return cfg.brandName;
		if (data.brand_name_ar || data.brand_name_en) {
			return OJ ? OJ.t(data.brand_name_ar, data.brand_name_en) : t(data.brand_name_ar, data.brand_name_en);
		}
		return OJ ? OJ.t(data.title_ar, data.title_en) : t(data.title_ar, data.title_en);
	};

	VW.resolvePortalOpts = function (data, cfg) {
		const base = cfg.portalOpts || {};
		return {
			useClinicGrid: base.useClinicGrid === true || data.use_clinic_portal_grid === true || data.use_clinic_portal_grid === 1,
			portalSubtitleAr: base.portalSubtitleAr || data.portal_subtitle_ar || "بوابة دور",
			portalSubtitleEn: base.portalSubtitleEn || data.portal_subtitle_en || "Role portal",
			defaultIcon: base.defaultIcon || "🌐",
		};
	};

	/**
	 * Mount journey workcenter shell — app-isolated branding and sidebar.
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
			const currentPage = cfg.currentPage || data.workcenter_page || "";
			const portalOpts = VW.resolvePortalOpts(data, cfg);
			const brandName = VW.resolveBrandName(data, cfg, OJ);
			const isHealthcare = (cfg.app || data.app) === "omnexa_healthcare";
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
				VW.renderJourneyPortals($body.find(".oj-demo-portals-panel"), groups, OJ, portalOpts);
			}
			if (cfg.renderFooter) {
				cfg.renderFooter($body, data, OJ);
			}
			if (cfg.bindActions) {
				cfg.bindActions($body, data, render);
			}

			let sidebar = cfg.sidebar;
			if (!sidebar) {
				if (isHealthcare && cfg.sidebarRole && OJ.defaultSidebar) {
					sidebar = OJ.defaultSidebar(cfg.sidebarRole, currentPage);
				} else {
					sidebar = VW.buildAppSidebar(data, currentPage, OJ);
				}
			}

			const shellOpts = {
				title:
					cfg.shellTitle ||
					`${OJ.t(data.title_ar, data.title_en)} — ${OJ.t("مركز العمل", "Workcenter")}`,
				subtitle:
					cfg.shellSubtitle ||
					OJ.t("بوابات الأدوار · بدون تداخل", "Role portals · fully isolated"),
				role: cfg.shellRole || OJ.t("مدير النظام", "System Manager"),
				sidebar,
				bodyEl: $body,
				homeRoute: cfg.homeRoute || data.workcenter_route,
				brandName,
				brandLogoUrl: data.logo_url || cfg.brandLogoUrl,
				app: cfg.app || data.app,
				kpis: kpis.length ? kpis : undefined,
			};
			const $shell = OJ.shell(shellOpts);
			$mount.empty().append($shell);
		}

		render().catch((e) => (OJ.showCallError ? OJ.showCallError(e) : frappe.msgprint(e.message || String(e))));
	};

	VW.mount = function (wrapper, appName) {
		const isHealthcare = appName === "omnexa_healthcare";
		VW.mountJourney(wrapper, {
			app: appName,
			pageTitle: __("Workcenter"),
			showDemoAccounts: false,
			sidebarRole: isHealthcare ? "admin" : null,
			async load() {
				return new Promise((resolve, reject) => {
					frappe.call({
						method: "omnexa_core.vertical_workcenter.context.get_workcenter_context",
						args: { app: appName },
						callback(r) {
							resolve(r.message || {});
						},
						error: reject,
					});
				});
			},
			renderIntro($body, data, OJ) {
				$body.append(`<div class="oj-panel oj-phase-panel-intro">
					<h4>${OJ.esc(OJ.t(data.title_ar, data.title_en))} — ${OJ.t("مركز العمل", "Workcenter")}</h4>
					<p class="oj-muted">${OJ.t(
						"بوابات الأدوار الديناميكية · معزولة عن باقي القطاعات",
						"Dynamic role portals · isolated from other verticals"
					)}</p>
				</div>`);
			},
		});
	};
})();
