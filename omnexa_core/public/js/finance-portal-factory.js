/**
 * Finance portal factory — Journey shell for all finance role desks
 */
frappe.provide("omnexa_finance");
frappe.provide("omnexa_finance.portal");

const FINANCE_JOURNEY_JS = [
	"/assets/omnexa_core/js/omnexa-finance-journey.js",
	"/assets/omnexa_core/js/finance-portal-registry.js",
];

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
		const $body = $("<div></div>");
		if (config.links || data.links) {
			const links = (data.links || config.links || []).map((l) => ({
				label: OJ.t(l.label_ar, l.label_en),
				route: l.route,
				logoUrl: l.logo_url || (l.app ? OJ.logoUrl(l.app) : ""),
				icon: l.icon,
			}));
			$body.append(`<h4 class="oj-section-title">${OJ.t("سيناريوهات العمل", "Work scenarios")}</h4>`);
			$body.append(OJ.linkGrid(links));
		}
		if (data.columns && data.rows) {
			$body.append(`<h4 class="oj-section-title mt-4">${OJ.t(data.table_title_ar || "السجلات", data.table_title_en || "Records")}</h4>`);
			$body.append(
				OJ.dataTable(
					data.columns.map((c) => ({ field: c.field, label: OJ.t(c.label_ar, c.label_en) })),
					data.rows
				)
			);
		}
		const $shell = OJ.shell({
			title: OJ.t(config.titleAr, config.titleEn),
			subtitle: OJ.t(config.subtitleAr || "ErpGenEx — Finance Group", config.subtitleEn || "ErpGenEx — Finance Group"),
			role: OJ.t(config.roleAr, config.roleEn),
			brandLogoUrl: config.app ? OJ.logoUrl(config.app) : "",
			kpis,
			sidebar: OJ.defaultSidebar(config.sidebarRole || "executive", `/app/${config.page}`),
			bodyEl: $body,
		});
		$mount.empty().append($shell);
		omnexa_finance.dismissOnboardingDialog();
	}

	render().catch((e) => {
		frappe.msgprint({ title: OJ.t("خطأ", "Error"), indicator: "red", message: e.message || String(e) });
	});
};
