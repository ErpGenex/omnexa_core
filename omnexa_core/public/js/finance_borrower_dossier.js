/**
 * Finance Group — Borrower Complete File (PDF / Excel / Report)
 */
frappe.provide("omnexa_finance.dossier");

omnexa_finance.dossier.REPORT = "Finance Borrower Complete File";

omnexa_finance.dossier.isFinanceCaseDoctype = function (doctype) {
	const list = (frappe.boot && frappe.boot.finance_case_doctypes) || [];
	return list.some((r) => r.doctype === doctype);
};

omnexa_finance.dossier.openReport = function (doctype, name) {
	frappe.route_options = { case_doctype: doctype, case_name: name };
	frappe.set_route("query-report", omnexa_finance.dossier.REPORT);
};

omnexa_finance.dossier.downloadPdf = function (doctype, name) {
	const url =
		"/api/method/omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier.download_borrower_dossier_pdf" +
		"?doctype=" +
		encodeURIComponent(doctype) +
		"&name=" +
		encodeURIComponent(name);
	window.open(url, "_blank");
};

omnexa_finance.dossier.downloadExcel = function (doctype, name) {
	const url =
		"/api/method/omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier.download_borrower_dossier_excel" +
		"?doctype=" +
		encodeURIComponent(doctype) +
		"&name=" +
		encodeURIComponent(name);
	window.open(url, "_blank");
};

omnexa_finance.dossier.addFormButtons = function (frm) {
	if (!frm.doc.name || frm.is_new()) return;
	if (!omnexa_finance.dossier.isFinanceCaseDoctype(frm.doctype)) return;
	frm.add_custom_button(__("ملف المقترض — PDF"), () => {
		omnexa_finance.dossier.downloadPdf(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("ملف المقترض — Excel"), () => {
		omnexa_finance.dossier.downloadExcel(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("ملف المقترض — تقرير"), () => {
		omnexa_finance.dossier.openReport(frm.doctype, frm.docname);
	}, __("Borrower File"));
};

(function registerFinanceCaseForms() {
	const list = (frappe.boot && frappe.boot.finance_case_doctypes) || [];
	const registered = omnexa_finance.dossier._registered || new Set();
	omnexa_finance.dossier._registered = registered;
	list.forEach((row) => {
		if (!row.doctype || registered.has(row.doctype)) return;
		registered.add(row.doctype);
		frappe.ui.form.on(row.doctype, {
			refresh(frm) {
				omnexa_finance.dossier.addFormButtons(frm);
			},
		});
	});
})();
