// Compatibility shim for custom desk scripts expecting frappe.ready.
(function () {
	if (!window.frappe) {
		window.frappe = {};
	}
	if (typeof window.frappe.ready === "function") {
		return;
	}
	window.frappe.ready = function (fn) {
		if (typeof fn !== "function") return;
		if (document.readyState === "loading") {
			document.addEventListener("DOMContentLoaded", fn);
		} else {
			fn();
		}
	};
})();
