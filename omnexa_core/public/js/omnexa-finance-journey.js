/**
 * Omnexa Finance Journey — desk UI kit (healthcare-parity for banking group)
 */
/* global frappe */
(function (window) {
	"use strict";

	function lang() {
		return frappe.boot && frappe.boot.lang === "ar" ? "ar" : "en";
	}

	function t(ar, en) {
		return lang() === "ar" ? ar : en;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function call(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({ method, args: args || {}, callback: (r) => resolve(r.message), error: reject });
		});
	}

	function mountDeskPage(wrapper, title) {
		frappe.ui.make_app_page({ parent: wrapper, title: title || "", single_column: true });
		$(wrapper).find(".page-head").hide();
		return $(wrapper).find(".layout-main-section");
	}

	function sidebarIconHtml(item) {
		if (item.logoUrl) {
			return `<img class="oj-sidebar-logo-img" src="${esc(item.logoUrl)}" alt="" />`;
		}
		return `<span class="oj-sidebar-emoji">${item.icon || "•"}</span>`;
	}

	function shell(options) {
		const opts = options || {};
		const sidebar = opts.sidebar || [];
		const isRtl = lang() === "ar";
		const navHtml = sidebar
			.map(
				(n) =>
					`<a class="oj-sidebar-item ${n.active ? "active" : ""}" href="#" data-nav-route="${esc(n.route || "")}">${sidebarIconHtml(n)}<span class="oj-sidebar-label">${esc(n.label)}</span></a>`
			)
			.join("");
		const kpiHtml = (opts.kpis || [])
			.map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${esc(k.value)}</div><div class="oj-kpi-label">${esc(k.label)}</div></div>`)
			.join("");
		const brandLogo = opts.brandLogoUrl
			? `<img class="oj-brand-logo" src="${esc(opts.brandLogoUrl)}" alt="" />`
			: `<span class="oj-logo">+</span>`;
		const $root = $(`<div class="oj-shell oj-finance-shell ${isRtl ? "oj-rtl" : "oj-ltr"}" dir="${isRtl ? "rtl" : "ltr"}"></div>`);
		$root.html(`
			<aside class="oj-sidebar oj-finance-sidebar">${navHtml}<div class="oj-sidebar-spacer"></div>
				<a class="oj-sidebar-item" href="#" data-nav-route="/app/finance-demo-hub"><span class="oj-sidebar-emoji">🎯</span><span class="oj-sidebar-label">${t("الديمو", "Demo")}</span></a>
				<a class="oj-sidebar-item oj-logout" href="/app"><span class="oj-sidebar-emoji">⏻</span><span class="oj-sidebar-label">${t("خروج", "Logout")}</span></a>
			</aside>
			<div class="oj-main">
				<header class="oj-topbar">
					<div class="oj-topbar-brand">${brandLogo}<div><strong>ErpGenEx Finance</strong><small>${esc(opts.subtitle || "")}</small></div></div>
					<div class="oj-topbar-meta"><span class="oj-pill">${esc(opts.role || "")}</span><span class="oj-user">${esc(frappe.session.user_fullname || frappe.session.user)}</span></div>
				</header>
				<div class="oj-title-row"><h1>${esc(opts.title || "")}</h1></div>
				${kpiHtml ? `<div class="oj-kpi-row">${kpiHtml}</div>` : ""}
				<div class="oj-body"></div>
			</div>`);
		const $body = $root.find(".oj-body");
		if (opts.bodyEl) $body.append(opts.bodyEl);
		else if (opts.body) $body.html(opts.body);
		$root.find(".oj-sidebar-item[data-nav-route]").on("click", function (e) {
			e.preventDefault();
			const route = $(this).attr("data-nav-route");
			if (route) window.location.href = route.startsWith("/") ? route : `/app/${route}`;
		});
		return $root;
	}

	function dataTable(columns, rows) {
		const cols = columns || [];
		const head = cols.map((c) => `<th>${esc(c.label)}</th>`).join("");
		const body = (rows || [])
			.map((row) => `<tr>${cols.map((c) => `<td>${esc(row[c.field] ?? "—")}</td>`).join("")}</tr>`)
			.join("");
		return `<div class="oj-table-wrap"><table class="oj-data-table"><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${cols.length || 1}" class="oj-muted">${t("لا بيانات", "No data")}</td></tr>`}</tbody></table></div>`;
	}

	function linkGrid(links) {
		const $g = $('<div class="oj-link-grid"></div>');
		(links || []).forEach((link) => {
			const icon = link.logoUrl
				? `<img class="oj-link-logo" src="${esc(link.logoUrl)}" alt="" />`
				: `<div class="oj-link-icon">${link.icon || "•"}</div>`;
			const $card = $(`<div class="oj-link-card">${icon}<div class="oj-link-label">${esc(link.label)}</div></div>`);
			$card.on("click", () => {
				const r = link.route || "";
				if (r.startsWith("/app/")) window.location.href = r;
				else if (r.startsWith("List/")) frappe.set_route("List", r.slice(5));
				else if (r.startsWith("Form/")) {
					const p = r.split("/");
					frappe.set_route("Form", p[1], p[2] || "");
				} else frappe.set_route(r);
			});
			$g.append($card);
		});
		return $g;
	}

	function portalCardGrid(portals, onSelect) {
		const $g = $('<div class="oj-clinic-grid oj-finance-portal-grid"></div>');
		(portals || []).forEach((p) => {
			const icon = p.logoUrl
				? `<img class="oj-portal-logo" src="${esc(p.logoUrl)}" alt="" />`
				: `<div class="oj-clinic-icon">${p.icon || "🏦"}</div>`;
			const $card = $(`
				<div class="oj-clinic-card ${p.disabled ? "oj-muted-card" : ""}">
					${icon}
					<h4>${esc(p.name)}</h4>
					<p class="oj-muted">${esc(p.subtitle || "")}</p>
					<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${t("فتح", "Open")}</button>
				</div>`);
			if (!p.disabled) $card.on("click", () => (onSelect ? onSelect(p) : null));
			$g.append($card);
		});
		return $g;
	}

	function loading() {
		return `<div class="oj-loading">${t("جاري التحميل...", "Loading...")}</div>`;
	}

	function logoUrl(app) {
		return app ? `/assets/${app}/logo.png` : "";
	}

	const SIDEBARS = {
		executive: [
			{ label: t("تنفيذي", "Executive"), route: "/app/fe-executive-dashboard", logoUrl: logoUrl("omnexa_finance_engine") },
			{ label: t("محرك", "Engine"), route: "/app/fe-servicing-portal", logoUrl: logoUrl("omnexa_finance_engine") },
			{ label: t("ديمو", "Demo Hub"), route: "/app/finance-demo-hub", icon: "🎯" },
		],
		credit: [
			{ label: t("منشأة", "Origination"), route: "/app/ce-servicing-portal", logoUrl: logoUrl("omnexa_credit_engine") },
			{ label: t("قرارات", "Decisions"), route: "List/Credit Decision Case", icon: "📋" },
			{ label: t("تنفيذي", "Executive"), route: "/app/ce-executive-dashboard", logoUrl: logoUrl("omnexa_credit_engine") },
		],
		risk: [
			{ label: t("مخاطر", "Risk"), route: "/app/rk-servicing-portal", logoUrl: logoUrl("omnexa_credit_risk") },
			{ label: t("تنفيذي", "Executive"), route: "/app/rk-executive-dashboard", logoUrl: logoUrl("omnexa_credit_risk") },
		],
		treasury: [
			{ label: t("خزينة", "Treasury"), route: "/app/al-servicing-portal", logoUrl: logoUrl("omnexa_alm") },
			{ label: t("تنفيذي", "Executive"), route: "/app/al-executive-dashboard", logoUrl: logoUrl("omnexa_alm") },
		],
		consumer: [
			{ label: t("استهلاكي", "Consumer"), route: "/app/cf-servicing-portal", logoUrl: logoUrl("omnexa_consumer_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/cf-executive-dashboard", logoUrl: logoUrl("omnexa_consumer_finance") },
		],
		auto: [
			{ label: t("مركبات", "Auto"), route: "/app/vf-servicing-portal", logoUrl: logoUrl("omnexa_vehicle_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/vf-executive-dashboard", logoUrl: logoUrl("omnexa_vehicle_finance") },
		],
		mortgage: [
			{ label: t("رهن", "Mortgage"), route: "/app/mg-servicing-portal", logoUrl: logoUrl("omnexa_mortgage_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/mg-executive-dashboard", logoUrl: logoUrl("omnexa_mortgage_finance") },
		],
		factoring: [
			{ label: t("تخصيم", "Factoring"), route: "/app/fc-servicing-portal", logoUrl: logoUrl("omnexa_factoring") },
			{ label: t("تنفيذي", "Executive"), route: "/app/fc-executive-dashboard", logoUrl: logoUrl("omnexa_factoring") },
		],
		sme: [
			{ label: t("منشآت", "SME"), route: "/app/sr-servicing-portal", logoUrl: logoUrl("omnexa_sme_retail_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/sr-executive-dashboard", logoUrl: logoUrl("omnexa_sme_retail_finance") },
		],
		micro: [
			{ label: t("ميداني", "Field"), route: "/app/mf-servicing-portal", logoUrl: logoUrl("omnexa_sme_microfinance") },
			{ label: t("حالات", "Cases"), route: "List/Microfinance Case", icon: "📋" },
			{ label: t("تنفيذي", "Executive"), route: "/app/mf-executive-dashboard", logoUrl: logoUrl("omnexa_sme_microfinance") },
		],
		leasing: [
			{ label: t("تأجير", "Leasing"), route: "/app/lf-servicing-portal", logoUrl: logoUrl("omnexa_leasing_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/lf-executive-dashboard", logoUrl: logoUrl("omnexa_leasing_finance") },
		],
		grc: [
			{ label: t("GRC", "GRC"), route: "/app/or-grc-portal", logoUrl: logoUrl("omnexa_operational_risk") },
			{ label: t("تنفيذي", "Executive"), route: "/app/or-executive-dashboard", logoUrl: logoUrl("omnexa_operational_risk") },
		],
		accounting: [
			{ label: t("محاسبة", "GL"), route: "/app/acct-executive-dashboard", logoUrl: logoUrl("omnexa_accounting") },
			{ label: t("إغلاق", "Close"), route: "/app/accounting-close-dashboard", logoUrl: logoUrl("omnexa_accounting") },
		],
	};

	function defaultSidebar(role, activeRoute) {
		const route = activeRoute || "";
		return (SIDEBARS[role] || SIDEBARS.executive).map((item) => ({
			...item,
			active:
				route &&
				(item.route === route ||
					item.route === `/app/${route.replace(/^\/app\//, "")}` ||
					item.route.replace(/^\/app\//, "") === route.replace(/^\/app\//, "")),
		}));
	}

	function portalCategoryGrid(groups) {
		const $root = $('<div class="oj-portal-catalog oj-finance-demo-portals"></div>');
		(groups || []).forEach((g) => {
			const title = lang() === "ar" ? g.label_ar : g.label_en;
			const $sec = $(`<div class="oj-portal-section"><h4 class="oj-portal-cat-title">${esc(title)}</h4></div>`);
			const portals = (g.portals || []).map((p) => ({
				id: p.id,
				name: lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: p.page || "",
				logoUrl: p.logo_url || (p.app ? logoUrl(p.app) : ""),
				route: p.route,
				disabled: p.exists === false,
			}));
			const $grid = portalCardGrid(portals, (c) => {
				if (c.route) window.location.href = c.route;
			});
			$sec.append($grid);
			$root.append($sec);
		});
		return $root;
	}

	window.OmnexaFinanceJourney = {
		lang,
		t,
		esc,
		call,
		mountDeskPage,
		shell,
		dataTable,
		linkGrid,
		portalCardGrid,
		loading,
		logoUrl,
		defaultSidebar,
		portalCategoryGrid,
	};
})(window);
