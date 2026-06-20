/**
 * Safe boot for finance role portal pages (vertical app page bundles may load before desk globals).
 * Always reloads journey assets so portal UI updates are not stuck on cached desk bundles.
 */
frappe.provide("omnexa_finance");

const FINANCE_PORTAL_ASSETS = [
	"/assets/omnexa_core/js/omnexa-finance-journey.js",
	"/assets/omnexa_core/js/finance-portal-registry.js",
	"/assets/omnexa_core/js/finance-portal-factory.js",
];

omnexa_finance.PORTAL_UI_VERSION = "20260620-workflow-v5";

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
		frappe.msgprint({
			title: __("Finance portals"),
			indicator: "red",
			message: __("Finance portal factory failed to load. Hard-refresh (Ctrl+Shift+R)."),
		});
	}

	// Always reload factory chain — desk global include may serve a stale cached bundle.
	frappe.require(FINANCE_PORTAL_ASSETS, mount);
};
