/**
 * ErpGenEx Desk — modern page bootstrap helper.
 * Usage: egx_boot_modern_page({ pageRoute: "employee-directory", css: [...] }, initFn)
 */
frappe.provide("egx.desk");

egx.desk.boot_modern_page = function (opts, initFn) {
	const css = (opts.css || []).concat(["/assets/omnexa_core/css/egx_desk_design_system.css"]);
	const js = opts.js || [];
	const bodyClass = opts.bodyClass || "egx-modern-desk";
	const assets = css.concat(js);

	frappe.require(assets, function () {
		$("body").addClass(bodyClass);
		if (opts.pageRoute) {
			$("body").addClass("egx-page-" + opts.pageRoute.replace(/\//g, "-"));
		}
		if (opts.wrapper) {
			$(opts.wrapper).closest(".page-container").find(".page-head").hide();
		}
		initFn();
	});
};
