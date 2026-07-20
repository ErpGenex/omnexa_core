/**
 * ErpGenEx — Executive hub (Healthcare workcenter parity) for all verticals
 */
/* global frappe */
frappe.provide("omnexa_core.vertical_executive_hub");

(function () {
	"use strict";

	const VE = omnexa_core.vertical_executive_hub;
	const VW = omnexa_core.vertical_workcenter;

	function phaseLabel(phase, OJ) {
		return OJ.lang() === "ar" ? phase.label_ar : phase.label_en;
	}

	function phaseSummary(phase, OJ) {
		return OJ.lang() === "ar" ? phase.summary_ar : phase.summary_en;
	}

	VE.renderPhasePanels = function (phases, OJ, opts) {
		opts = opts || {};
		const statLabels = opts.statLabels || {
			customers: { ar: "عملاء", en: "Customers" },
			orders: { ar: "أوامر", en: "Orders" },
			batches: { ar: "دفعات", en: "Batches" },
			pos_sales: { ar: "نقاط البيع", en: "POS Sales" },
			patients: { ar: "مرضى", en: "Patients" },
			departments: { ar: "أقسام", en: "Depts" },
			beds: { ar: "أسرة", en: "Beds" },
		};
		const statKeys = opts.statKeys || ["customers", "orders", "batches"];

		const $row = $('<div class="oj-phase-dashboard"></div>');
		(phases || []).forEach((phase) => {
			const stats = phase.stats || {};
			const activeCls = phase.active ? " oj-phase-card-active" : "";
			const readyBadge = phase.ready
				? `<span class="oj-phase-badge oj-phase-badge-ready">${OJ.t("جاهز", "Ready")}</span>`
				: `<span class="oj-phase-badge">${OJ.t("غير مُفعّل", "Not provisioned")}</span>`;

			const statHtml = statKeys
				.map((key) => {
					const lbl = statLabels[key] || { ar: key, en: key };
					return `<div class="oj-phase-stat"><span>${stats[key] || 0}</span><small>${OJ.t(lbl.ar, lbl.en)}</small></div>`;
				})
				.join("");

			const extraLinks = [
				phase.pos_url
					? `<a class="oj-btn oj-btn-outline oj-phase-link" href="${OJ.esc(phase.pos_url)}">${OJ.t("نقطة البيع", "Point of Sale")}</a>`
					: "",
				phase.site_url
					? `<a class="oj-btn oj-btn-outline oj-phase-link" href="${OJ.esc(phase.site_url)}" target="_blank">${OJ.t("الموقع", "Website")}</a>`
					: "",
				phase.booking_url
					? `<a class="oj-btn oj-btn-outline oj-phase-link" href="${OJ.esc(phase.booking_url)}" target="_blank">${OJ.t("الحجز", "Booking")}</a>`
					: "",
			]
				.filter(Boolean)
				.join("");

			const $card = $(`
				<div class="oj-phase-card${activeCls}" data-phase="${OJ.esc(phase.id)}">
					<div class="oj-phase-card-head">
						<span class="oj-phase-icon">${phase.icon || "🏢"}</span>
						<div>
							<h4>${OJ.esc(phaseLabel(phase, OJ))}</h4>
							<p class="oj-muted">${OJ.esc(phaseSummary(phase, OJ))}</p>
						</div>
						${readyBadge}
					</div>
					<div class="oj-phase-meta">
						<div><strong>${OJ.t("الشركة", "Company")}:</strong> <code>${OJ.esc(phase.company || "—")}</code></div>
						<div><strong>${OJ.t("الفرع", "Branch")}:</strong> <code>${OJ.esc(phase.branch || "—")}</code></div>
						<div><strong>${OJ.t("البوابات", "Portals")}:</strong> ${phase.portal_count || 0}</div>
					</div>
					<div class="oj-phase-stats">${statHtml}</div>
					<div class="oj-phase-actions">
						<button type="button" class="oj-btn oj-btn-primary oj-phase-activate" data-phase="${OJ.esc(phase.id)}">
							${OJ.t("تفعيل وزرع", "Activate & Seed")}
						</button>
						<button type="button" class="oj-btn oj-btn-outline oj-phase-switch" data-phase="${OJ.esc(phase.id)}" ${phase.ready ? "" : "disabled"}>
							${OJ.t("التبديل", "Switch")}
						</button>
						${extraLinks}
					</div>
				</div>
			`);
			$row.append($card);
		});
		return $row;
	};

	VE.filterPortalGroups = function (groups, phases, activePhaseId) {
		const active = (phases || []).find((p) => p.id === activePhaseId);
		if (!active || !active.portal_ids) return groups;
		const allowed = new Set(active.portal_ids);
		return (groups || [])
			.map((g) => ({
				...g,
				portals: (g.portals || []).filter((p) => allowed.has(p.id) || allowed.has(p.key)),
			}))
			.filter((g) => (g.portals || []).length);
	};

	VE.bindPhaseActions = function ($body, OJ, opts, rerender) {
		opts = opts || {};
		$body.find(".oj-phase-activate").on("click", function () {
			const phaseId = $(this).data("phase");
			frappe.confirm(
				OJ.t("سيتم إنشاء/تحديث بيانات هذه المرحلة. هل تريد المتابعة؟", "This will provision demo data. Continue?"),
				() => {
					frappe.call({
						method: opts.activateMethod,
						args: { phase_id: phaseId, force: 1 },
						freeze: true,
						callback(r) {
							frappe.show_alert({ message: OJ.t("تم تفعيل المرحلة", "Phase activated"), indicator: "green" });
							if (r.message && r.message.message) frappe.msgprint(r.message.message);
							if (rerender) rerender();
						},
					});
				}
			);
		});
		$body.find(".oj-phase-switch").on("click", function () {
			const phaseId = $(this).data("phase");
			frappe.call({
				method: opts.switchMethod,
				args: { phase_id: phaseId },
				freeze: true,
				callback() {
					frappe.show_alert({ message: OJ.t("تم التبديل", "Context switched"), indicator: "green" });
					if (rerender) rerender();
				},
			});
		});
	};

	/**
	 * Mount executive hub — healthcare workcenter design parity.
	 * config: pageTitle, shellTitle, shellSubtitle, shellRole, homeRoute, sidebar,
	 *         brandLogoUrl, portalOpts, phaseOpts, loadDashboard, activateMethod, switchMethod
	 */
	VE.mountExecutiveHub = function (wrapper, config) {
		const OJ = window.OmnexaJourney;
		const cfg = config || {};
		if (!OJ || !OJ.mountDeskPage || !OJ.shell) {
			frappe.ui.make_app_page({ parent: wrapper, title: cfg.pageTitle || __("Executive Dashboard"), single_column: true });
			return;
		}

		const $mount = OJ.mountDeskPage(wrapper, cfg.pageTitle || __("Executive Dashboard"));
		let activePhaseId = "";

		async function render() {
			const data = (await cfg.load()) || {};
			const groups = data.groups || data.grouped_portals || [];
			const phases = data.phases || [];
			const creds = data.credentials || data.creds || null;
			activePhaseId = data.active_phase || "";

			const $body = $('<div class="oj-demo-hub oj-executive-hub"></div>');
			$body.append(`<div class="oj-panel oj-phase-panel-intro">
				<h4>${OJ.t("لوحات التشغيل على مراحل", "Deployment Phase Control Panels")}</h4>
				<p class="oj-muted">${OJ.esc(cfg.introText || OJ.t(
					"اختر سيناريو التشغيل · التفعيل يزرع البيانات ويضبط الشركة/الفرع.",
					"Pick an operating scenario · activation seeds data and sets Company/Branch."
				))}</p>
				${activePhaseId ? `<p><strong>${OJ.t("المرحلة النشطة", "Active phase")}:</strong> <code>${OJ.esc(activePhaseId)}</code></p>` : ""}
			</div>`);

			if (phases.length) {
				$body.append(VE.renderPhasePanels(phases, OJ, cfg.phaseOpts || {}));
				VE.bindPhaseActions($body, OJ, cfg, render);
			}

			if (cfg.renderExtra) {
				await cfg.renderExtra($body, data, OJ);
			}

			if (creds && (creds.users || []).length && VW && VW.renderDemoAccountsPanel) {
				VW.renderDemoAccountsPanel($body, creds, OJ, cfg.demoPanelOpts || {});
			}

			const filteredGroups = activePhaseId ? VE.filterPortalGroups(groups, phases, activePhaseId) : groups;
			const portalTitle = activePhaseId
				? OJ.t("بوابات المرحلة النشطة", "Active Phase Portals")
				: cfg.portalPanelTitle || OJ.t("بوابات الأدوار", "Role Portals");

			if ((filteredGroups || groups || []).length) {
				$body.append(`<div class="oj-panel oj-demo-portals-panel" style="margin-top:16px"><h4>${portalTitle}</h4></div>`);
				if (VW && VW.renderJourneyPortals) {
					VW.renderJourneyPortals($body.find(".oj-demo-portals-panel"), filteredGroups.length ? filteredGroups : groups, OJ, cfg.portalOpts || {});
				}
			}

			const kpis = (data.kpis || []).map((k) => ({
				value: k.value ?? "—",
				label: OJ.t(k.label_ar, k.label_en),
			}));

			const $shell = OJ.shell({
				title: cfg.shellTitle,
				subtitle: cfg.shellSubtitle,
				role: cfg.shellRole || OJ.t("الإدارة التنفيذية", "Executive"),
				sidebar: cfg.sidebar || (OJ.defaultSidebar ? OJ.defaultSidebar(cfg.sidebarRole || "workcenter", cfg.currentPage) : []),
				bodyEl: $body,
				homeRoute: cfg.homeRoute,
				brandLogoUrl: data.logo_url || cfg.brandLogoUrl,
				kpis: kpis.length ? kpis : undefined,
			});
			$mount.empty().append($shell);
		}

		render().catch((e) => (OJ.showCallError ? OJ.showCallError(e) : frappe.msgprint(e.message || String(e))));
	};
})();
