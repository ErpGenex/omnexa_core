// Replace residual "ERPNext" in the browser tab title after navigation.
frappe.ready(function () {
	function fixTitle() {
		if (!document.title) return;
		if (document.title.indexOf("ERPNext") === -1 && document.title.indexOf("ErpNext") === -1) return;
		document.title = document.title
			.replace(/ERPNext/g, "ERPGENEX")
			.replace(/ErpNext/g, "ERPGENEX");
	}
	fixTitle();
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", fixTitle);
	}
});
