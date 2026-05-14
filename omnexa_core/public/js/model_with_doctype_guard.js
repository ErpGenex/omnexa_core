/**
 * Erpgenex / omnexa_core — desk patch only (do not modify frappe framework).
 *
 * Frappe Query Report chains: frappe.model.with_doctype(report_doc.ref_doctype).
 * When Report.ref_doctype is empty, GET frappe.desk.form.load.getdoctype is sent
 * without `doctype` → TypeError on the server.
 */
(function () {
	if (typeof frappe === "undefined" || !frappe.model || frappe.model.__erpgenex_with_doctype_guard) {
		return;
	}
	const original = frappe.model.with_doctype;
	frappe.model.with_doctype = function (doctype, callback, async) {
		if (!doctype) {
			if (callback) {
				callback();
			}
			return Promise.resolve();
		}
		return original.call(frappe.model, doctype, callback, async);
	};
	frappe.model.__erpgenex_with_doctype_guard = true;
})();
