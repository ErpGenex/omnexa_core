/**
 * Safe boot for finance role portal pages (vertical app page bundles may load before desk globals).
 */
frappe.provide("omnexa_finance");

const FINANCE_PORTAL_ASSETS = [
	"/assets/omnexa_core/js/omnexa-finance-journey.js",
	"/assets/omnexa_core/js/finance-portal-registry.js",
	"/assets/omnexa_core/js/finance-portal-factory.js",
];

omnexa_finance._hydrateRegistryFromBoot = function () {
	if (window.omnexa_finance && omnexa_finance.PORTAL_REGISTRY) return;
	if (frappe.boot && frappe.boot.finance_portal_registry) {
		frappe.provide("omnexa_finance");
		omnexa_finance.PORTAL_REGISTRY = frappe.boot.finance_portal_registry;
	}
};

omnexa_finance.bootPortalPage = function (wrapper, pageName) {
	omnexa_finance._hydrateRegistryFromBoot();

	function mount() {
		omnexa_finance._hydrateRegistryFromBoot();
		if (window.omnexa_finance && omnexa_finance.portal && omnexa_finance.portal.mountPage) {
			omnexa_finance.portal.mountPage(wrapper, pageName);
			return;
		}
		frappe.require("/assets/omnexa_core/js/finance-portal-factory.js", mount);
	}

	if (
		window.OmnexaFinanceJourney &&
		typeof window.OmnexaFinanceJourney.defaultSidebar === "function" &&
		window.omnexa_finance &&
		omnexa_finance.PORTAL_REGISTRY
	) {
		mount();
		return;
	}

	frappe.require(FINANCE_PORTAL_ASSETS, mount);
};
