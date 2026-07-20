/** Legacy route — redirect bookmarks from demo hub to Workcenter */
frappe.pages["finance-demo-hub"].on_page_load = function () {
	frappe.set_route("finance-workcenter");
};
