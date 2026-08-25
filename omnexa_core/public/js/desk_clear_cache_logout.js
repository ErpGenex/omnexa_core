/* global frappe */
// After desk cache clear, force logout so boot (workspaces, routes) reloads on next login.

(function () {
	const orig = frappe.ui.toolbar && frappe.ui.toolbar.clear_cache;
	if (!orig || orig.__omnexa_logout_patched) return;

	frappe.ui.toolbar.clear_cache = frappe.utils.throttle(function () {
		frappe.assets.clear_local_storage();
		frappe.xcall("frappe.sessions.clear").then((message) => {
			frappe.show_alert({
				message: message || __("Cache cleared"),
				indicator: "info",
			});
			if (frappe.app && frappe.app.logout) {
				frappe.app.logout();
				return;
			}
			window.location.href = "/login";
		});
	}, 10000);
	frappe.ui.toolbar.clear_cache.__omnexa_logout_patched = true;
})();
