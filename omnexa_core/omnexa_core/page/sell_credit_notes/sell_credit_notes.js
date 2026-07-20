frappe.pages["sell-credit-notes"].on_page_load = function () {
	frappe.route_options = { is_return: 1 };
	frappe.set_route("List", "Sales Invoice");
};
