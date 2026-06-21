/**
 * Finance Workcenter — redirect non-admin finance users to their role portal on desk landing.
 */
frappe.provide("omnexa_finance.workcenter");

omnexa_finance.workcenter.applyPortalEntry = function () {
	const wc = frappe.boot && frappe.boot.finance_workcenter;
	if (!wc || !wc.portal_entry_mode || !wc.primary_portal_route) return;

	const route = frappe.get_route() || [];
	const onGenericDesk =
		route.length === 0 ||
		route[0] === "Workspaces" ||
		(route[0] === "List" && route[1] === "Workflow") ||
		route.join("/") === "query-report";

	if (!onGenericDesk) return;
	if (sessionStorage.getItem("omnexa_finance_portal_home")) return;

	sessionStorage.setItem("omnexa_finance_portal_home", "1");
	window.location.href = wc.primary_portal_route;
};

$(document).on("app_ready", function () {
	omnexa_finance.workcenter.applyPortalEntry();
});
