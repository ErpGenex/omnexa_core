/**
 * Finance portal factory — Journey shell for all finance role desks
 */
frappe.provide("omnexa_finance");
frappe.provide("omnexa_finance.portal");

const FINANCE_JOURNEY_JS = [
	"/assets/omnexa_core/js/omnexa-finance-journey.js",
	"/assets/omnexa_core/js/finance-portal-registry.js",
	"/assets/omnexa_core/js/finance_borrower_dossier.js",
];

omnexa_finance.PORTAL_UI_VERSION = "20260621-dossier-v1";

omnexa_finance._hydrateRegistryFromBoot = function () {
	if (omnexa_finance.PORTAL_REGISTRY) return;
	if (frappe.boot && frappe.boot.finance_portal_registry) {
		omnexa_finance.PORTAL_REGISTRY = frappe.boot.finance_portal_registry;
	}
};

function financeJourneyReady() {
	return (
		window.OmnexaFinanceJourney &&
		typeof window.OmnexaFinanceJourney.defaultSidebar === "function" &&
		window.omnexa_finance &&
		window.omnexa_finance.PORTAL_REGISTRY
	);
}

omnexa_finance.dismissOnboardingDialog = function () {
	try {
		$(".msgprint-dialog:visible").closest(".modal.show").modal("hide");
	} catch (e) {
		/* ignore */
	}
};

omnexa_finance.ensureJourneyAssets = function (callback, attempt) {
	omnexa_finance._hydrateRegistryFromBoot();
	const tries = attempt || 0;
	if (financeJourneyReady()) {
		omnexa_finance.dismissOnboardingDialog();
		callback();
		return;
	}
	if (tries >= 120) {
		frappe.msgprint({
			title: __("Finance portals"),
			indicator: "red",
			message: __(
				"Finance Journey assets did not load. Press Ctrl+Shift+R to hard-refresh, or ask your admin to run: bench build --app omnexa_core && bench clear-cache"
			),
		});
		return;
	}
	if (!omnexa_finance._journeyLoading) {
		omnexa_finance._journeyLoading = true;
		frappe
			.require(FINANCE_JOURNEY_JS)
			.then(() => {
				omnexa_finance._journeyLoading = false;
				omnexa_finance.ensureJourneyAssets(callback, tries + 1);
			})
			.catch(() => {
				omnexa_finance._journeyLoading = false;
				setTimeout(() => omnexa_finance.ensureJourneyAssets(callback, tries + 1), 100);
			});
		return;
	}
	setTimeout(() => omnexa_finance.ensureJourneyAssets(callback, tries + 1), 50);
};

omnexa_finance.portal.mountPage = function (wrapper, pageName) {
	omnexa_finance.ensureJourneyAssets(() => {
		const cfg =
			(window.omnexa_finance && omnexa_finance.PORTAL_REGISTRY && omnexa_finance.PORTAL_REGISTRY[pageName]) || null;
		if (!cfg) {
			frappe.msgprint(__("Finance portal not registered: {0}", [pageName]));
			return;
		}
		omnexa_finance.portal.mount(wrapper, cfg);
	});
};

omnexa_finance.portal._financePortalPages = function () {
	const reg = (omnexa_finance.PORTAL_REGISTRY || {});
	return new Set(Object.keys(reg));
};

omnexa_finance.portal._navigateRoute = function (route, currentPage) {
	if (!route) return;
	if (route === "#wizard") {
		$(document).trigger("finance-portal-open-wizard");
		return;
	}
	if (route.startsWith("#step-")) {
		const key = route.replace("#step-", "");
		$(document).trigger("finance-portal-focus-step", [key]);
		return;
	}
	if (route.startsWith("/app/")) {
		const page = route.replace(/^\/app\//, "").split(/[?#]/)[0];
		const allowed = omnexa_finance.portal._financePortalPages();
		const extras = new Set(["finance-workcenter", "finance-demo-hub", "finance-control-center"]);
		if (!allowed.has(page) && !extras.has(page)) {
			frappe.show_alert({
				message: __("This link is not a finance portal page. Use servicing/executive links inside the portal."),
				indicator: "orange",
			});
			return;
		}
		if (page === (currentPage || "").replace(/^\/app\//, "")) return;
		window.location.href = route;
		return;
	}
	if (route.startsWith("List/")) frappe.set_route("List", route.slice(5));
	else if (route.startsWith("Form/")) {
		const p = route.split("/");
		frappe.set_route("Form", p[1], p[2] || "");
	} else if (route.startsWith("Report/")) frappe.set_route("query-report", route.slice(7));
	else if (route.startsWith("query-report/")) frappe.set_route("query-report", route.slice(14));
};

omnexa_finance.portal.mount = function (wrapper, config) {
	const OJ = window.OmnexaFinanceJourney;
	if (!OJ || typeof OJ.defaultSidebar !== "function") {
		omnexa_finance.ensureJourneyAssets(() => omnexa_finance.portal.mount(wrapper, config));
		return;
	}
	const company = frappe.defaults.get_user_default("Company") || "";
	const branch = frappe.defaults.get_user_default("Branch") || "";
	const $mount = OJ.mountDeskPage(wrapper, config.deskTitle || OJ.t(config.titleAr, config.titleEn));

	async function render() {
		const data = await OJ.call("omnexa_core.omnexa_core.finance_demo.finance_portal_desk.get_portal_dashboard", {
			page: config.page,
			company,
			branch,
		});
		const kpis = (data.kpis || []).map((k) => ({
			value: k.value ?? "—",
			label: OJ.t(k.label_ar, k.label_en),
		}));
		const $body = $("<div class='oj-finance-portal-body'></div>");
		const workflowSteps = data.workflow_steps || [];
		const caseDoctype = data.case_doctype;
		const isExec = (config.page || "").includes("executive");
		const portalState = { selectedCaseName: null, activeStepKey: "registration" };

		function stepByKey(key) {
			return (workflowSteps || []).find((s) => s.key === key);
		}

		function nextStepKey(currentKey) {
			const idx = workflowSteps.findIndex((s) => s.key === currentKey);
			if (idx >= 0 && idx < workflowSteps.length - 1) return workflowSteps[idx + 1].key;
			return null;
		}

		function runDossierAction(fn) {
			if (!caseDoctype || !portalState.selectedCaseName) {
				frappe.show_alert({
					message: OJ.t("اختر حالة من الجدول أولاً", "Select a case from the table first"),
					indicator: "orange",
				});
				return;
			}
			const dossier = window.omnexa_finance && omnexa_finance.dossier;
			if (dossier && typeof dossier[fn] === "function") {
				dossier[fn](caseDoctype, portalState.selectedCaseName);
				return;
			}
			frappe.require(["/assets/omnexa_core/js/finance_borrower_dossier.js"], () => {
				if (omnexa_finance.dossier && typeof omnexa_finance.dossier[fn] === "function") {
					omnexa_finance.dossier[fn](caseDoctype, portalState.selectedCaseName);
				} else {
					frappe.msgprint(__("Borrower export module failed to load. Hard-refresh (Ctrl+Shift+R)."));
				}
			});
		}

		async function openStage(stepKey) {
			if (!stepKey || !data.app) return;
			portalState.activeStepKey = stepKey;
			const $slot = $body.find(".oj-step-info");
			$slot.html(OJ.loading());
			$body.find(".oj-workflow-card").removeClass("selected");
			$body.find(`.oj-workflow-card[data-step="${stepKey}"]`).addClass("selected");
			try {
				const screen = await OJ.call(
					"omnexa_core.omnexa_core.finance_demo.finance_workflow_journey.get_workflow_stage_screen",
					{
						app: data.app,
						step_key: stepKey,
						case_name: portalState.selectedCaseName,
					}
				);
				$slot.empty().append(
					OJ.workflowStageScreen({
						screen,
						workflowSteps,
						onStepSelect: (key) => openStage(key),
						onAction: (actionKey) => {
							if (actionKey === "wizard") {
								$body.find(".btn-new-application").trigger("click");
								return;
							}
							if (actionKey === "open_case" && caseDoctype && portalState.selectedCaseName) {
								frappe.set_route("Form", caseDoctype, portalState.selectedCaseName);
								return;
							}
							if (actionKey === "open_list" && caseDoctype) {
								frappe.set_route("List", caseDoctype);
								return;
							}
							if (actionKey === "print_dossier") {
								runDossierAction("downloadPdf");
								return;
							}
							if (actionKey === "print_dossier_preview") {
								runDossierAction("printPreview");
								return;
							}
							if (actionKey === "export_dossier_excel") {
								runDossierAction("downloadExcel");
								return;
							}
							if (actionKey === "open_dossier_report") {
								runDossierAction("openReport");
								return;
							}
							if (actionKey === "next" || actionKey === "approve_step" || actionKey === "disburse" || actionKey === "collect") {
								const nk = nextStepKey(stepKey);
								if (nk) {
									frappe.show_alert({
										message: OJ.t("تم — الانتقال للمرحلة التالية", "Done — moving to next stage"),
										indicator: "green",
									});
									openStage(nk);
								}
								return;
							}
						},
					})
				);
				const top = $slot.offset() && $slot.offset().top;
				if (top) $("html, body").animate({ scrollTop: top - 70 }, 250);
			} catch (err) {
				$slot.html(`<p class="text-danger">${OJ.esc(err.message || String(err))}</p>`);
			}
		}

		if (!isExec && caseDoctype) {
			const $actions = $(`<div class="oj-portal-actions mb-3"></div>`);
			$actions.append(
				`<button type="button" class="btn btn-primary btn-new-application">${OJ.t("➕ تسجيل طلب تمويل", "➕ New Application")}</button>`
			);
			$body.append($actions);
		}

		if (workflowSteps.length) {
			$body.append(`<h4 class="oj-section-title">${OJ.t("مسار التمويل — 12 مرحلة", "Financing Journey — 12 Stages")}</h4>`);
			const $journey = OJ.workflowJourneyGrid(workflowSteps, (step) => openStage(step.key));
			$body.append($journey);
			$body.append(`<div class="oj-step-info oj-stage-screen-slot mt-2"></div>`);
		}

		const $trackerSlot = $(`<div class="oj-case-tracker-slot mt-3"></div>`);
		$body.append($trackerSlot);

		if (data.columns && data.rows) {
			$body.append(
				`<h4 class="oj-section-title mt-4">${OJ.t(data.table_title_ar || "الحالات الأخيرة", data.table_title_en || "Recent Cases")}</h4>`
			);
			const tableResult = OJ.dataTable(
				data.columns.map((c) => ({ field: c.field, label: OJ.t(c.label_ar, c.label_en) })),
				data.rows
			);
			const $tableWrap =
				tableResult && tableResult.jquery ? tableResult : $(typeof tableResult === "string" ? tableResult : "");
			$body.append($tableWrap);
			if (caseDoctype && $tableWrap.length) {
				$tableWrap.find("tbody tr").css("cursor", "pointer");
				$tableWrap.on("click", "tbody tr", function () {
					const idx = $(this).index();
					const row = (data.rows || [])[idx];
					if (!row || !row.name) return;
					portalState.selectedCaseName = row.name;
					$trackerSlot.empty().append(OJ.caseTrackerPanel(caseDoctype, row.name));
					openStage(portalState.activeStepKey || "registration");
					const top = $trackerSlot.offset() && $trackerSlot.offset().top;
					if (top) $("html, body").animate({ scrollTop: top - 80 }, 300);
				});
			}
		}

		const sidebarNav =
			(data.sidebar_nav || []).length > 0
				? OJ.appSidebar(data.sidebar_nav, `/app/${config.page}`, data.logo_url)
				: OJ.defaultSidebar(config.sidebarRole || "executive", `/app/${config.page}`);

		const $shell = OJ.shell({
			title: OJ.t(config.titleAr, config.titleEn),
			subtitle: OJ.t(config.subtitleAr || "ErpGenex — Finance Group", config.subtitleEn || "ErpGenex — Finance Group"),
			role: OJ.t(config.roleAr, config.roleEn),
			brandLogoUrl: config.app ? OJ.logoUrl(config.app) : "",
			kpis,
			sidebar: sidebarNav,
			bodyEl: $body,
			currentPage: config.page,
		});

		$shell.find(".oj-topbar-meta").prepend(
			`<span class="oj-pill oj-version-pill" title="Portal UI">${omnexa_finance.PORTAL_UI_VERSION || "v2"}</span>`
		);

		$shell.find(".oj-sidebar-item[data-nav-route]").off("click").on("click", function (e) {
			e.preventDefault();
			omnexa_finance.portal._navigateRoute($(this).attr("data-nav-route"), config.page);
		});

		$mount.empty().append($shell);
		omnexa_finance.dismissOnboardingDialog();

		$body.find(".btn-new-application").on("click", () => {
			$body.find(".oj-wizard-panel").remove();
			$body.prepend(
				OJ.registrationWizard({
					app: data.app,
					fields: data.wizard_fields || [],
					onSuccess: () => render(),
				})
			);
		});

		$(document).off("finance-portal-open-wizard").on("finance-portal-open-wizard", () => {
			$body.find(".btn-new-application").trigger("click");
		});

		$(document).off("finance-portal-focus-step").on("finance-portal-focus-step", (_e, key) => {
			if (key) openStage(key);
		});

		if (workflowSteps.length) {
			openStage(portalState.activeStepKey);
		}
	}

	render().catch((e) => {
		frappe.msgprint({ title: OJ.t("خطأ", "Error"), indicator: "red", message: e.message || String(e) });
	});
};
