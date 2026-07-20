frappe.pages["retail-pos"].on_page_load = function (wrapper) {
	frappe.require(
		[
			"/assets/omnexa_core/css/retail_pos.css",
			"/assets/omnexa_core/css/retail_product_manager.css",
			"/assets/omnexa_core/js/retail_product_manager.js",
			"/assets/omnexa_core/js/retail_pos.js",
		],
		function () {
			omnexa_core.retail_pos.init(wrapper);
		}
	);
};
