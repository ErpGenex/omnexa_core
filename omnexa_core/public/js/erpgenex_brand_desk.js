// Replace residual "ERPNext" in the browser tab title after navigation.
function mount_erpgenex_brand_desk() {
	if (!window.frappe || !frappe.boot || frappe.session.user === "Guest") return;
	if (window.__erpgenex_brand_desk_mounted) return;
	window.__erpgenex_brand_desk_mounted = true;

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
}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", mount_erpgenex_brand_desk);
} else {
	mount_erpgenex_brand_desk();
}
$(window).on("load", mount_erpgenex_brand_desk);
