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
				const $body = $('<div class="vertical-workcenter-journey"></div>');
				$body.append(
					`<p class="oj-muted">${t(
						"مركز العمل — بوابات الأدوار · محاكاة من الفرع",
						"Workcenter — role portals · branch simulation"
					)}</p>`
				);
				if (ctx.logo_url) {
					$body.append(
						`<div style="margin-bottom:12px"><img src="${ctx.logo_url}" alt="" style="height:48px;border-radius:8px"/></div>`
					);
				}
				$body.append(
					`<h4 class="oj-section-title">${frappe.utils.escape_html(t(ctx.title_ar, ctx.title_en))}</h4>`
				);
				$body.append(portalGrid(ctx.grouped_portals));
				if (ctx.can_simulate) {
					$body.append(
						`<p class="oj-muted" style="margin-top:16px">${frappe.utils.escape_html(ctx.branch_demo_hint || "")}</p>`
					);
				}
				$mount.empty().append($body);
			},
		});
	};
})();
