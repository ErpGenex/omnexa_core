/**
 * ErpGenEx — Generic Vertical Workcenter (Education / Healthcare / Finance parity)
 */
/* global frappe */
frappe.provide("omnexa_core.vertical_workcenter");

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

	omnexa_core.vertical_workcenter.mount = function (wrapper, appName) {
		const OJ = window.OmnexaJourney;
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
					$main.append(
						`<p class="oj-muted">${frappe.utils.escape_html(ctx.branch_demo_hint || "")}</p>`
					);
				}
				$main.append(portalGrid(groups));

				$layout.append($sidebar).append($main);
				$mount.empty().append($layout);
			},
		});
	};
})();
