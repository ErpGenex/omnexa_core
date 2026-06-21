/**
 * Finance Group — Borrower Complete File (PDF / Excel / Report / Print)
 */
frappe.provide("omnexa_finance.dossier");

omnexa_finance.dossier.REPORT = "Finance Borrower Complete File";
omnexa_finance.dossier.DOSSIER_PDF =
	"omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier.download_borrower_dossier_pdf";
omnexa_finance.dossier.DOSSIER_EXCEL =
	"omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier.download_borrower_dossier_excel";
omnexa_finance.dossier.DOSSIER_HTML =
	"omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier.get_borrower_dossier_html";
omnexa_finance.dossier.DOC_PRINT =
	"omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.print_case_document";
omnexa_finance.dossier.DOC_HTML =
	"omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.get_document_print_html";

omnexa_finance.dossier.isFinanceCaseDoctype = function (doctype) {
	const list = (frappe.boot && frappe.boot.finance_case_doctypes) || [];
	return list.some((r) => r.doctype === doctype);
};

/** Frappe-standard POST download (same tab — triggers file save). */
omnexa_finance.dossier.apiDownload = function (method, args) {
	if (!method) return;
	const cmd = method.startsWith("/api/method/") ? method.replace("/api/method/", "") : method;
	const params = Object.assign({ cmd: cmd }, args || {});
	const postUrl = (frappe.request && frappe.request.url) || frappe.urllib.get_full_url("/");
	if (typeof open_url_post === "function") {
		open_url_post(postUrl, params, false);
		return;
	}
	const qs = new URLSearchParams(params).toString();
	window.location.href = frappe.urllib.get_full_url(`/api/method/${cmd}?${qs}`);
};

omnexa_finance.dossier._openHtmlPrintWindow = function (html, title) {
	if (!html) {
		frappe.msgprint({ title: __("Print"), indicator: "red", message: __("Empty print preview.") });
		return;
	}
	const w = window.open("", "_blank");
	if (!w) {
		frappe.msgprint({
			title: __("Print"),
			indicator: "orange",
			message: __("Allow pop-ups for this site, then try Print again."),
		});
		return;
	}
	w.document.open();
	w.document.write(html);
	w.document.close();
	w.document.title = title || __("Borrower File");
	w.focus();
	setTimeout(() => {
		try {
			w.print();
		} catch (e) {
			/* user may cancel */
		}
	}, 400);
};

omnexa_finance.dossier._requireCase = function (doctype, name) {
	if (doctype && name) return true;
	frappe.show_alert({ message: __("Select a case from the table first."), indicator: "orange" });
	return false;
};

omnexa_finance.dossier.openReport = function (doctype, name) {
	if (!omnexa_finance.dossier._requireCase(doctype, name)) return;
	frappe.route_options = { case_doctype: doctype, case_name: name };
	frappe.set_route("query-report", omnexa_finance.dossier.REPORT);
};

omnexa_finance.dossier.downloadPdf = function (doctype, name) {
	if (!omnexa_finance.dossier._requireCase(doctype, name)) return;
	omnexa_finance.dossier.apiDownload(omnexa_finance.dossier.DOSSIER_PDF, { doctype, name });
	frappe.show_alert({ message: __("Downloading borrower PDF…"), indicator: "blue" });
};

omnexa_finance.dossier.downloadExcel = function (doctype, name) {
	if (!omnexa_finance.dossier._requireCase(doctype, name)) return;
	omnexa_finance.dossier.apiDownload(omnexa_finance.dossier.DOSSIER_EXCEL, { doctype, name });
	frappe.show_alert({ message: __("Downloading Excel…"), indicator: "blue" });
};

omnexa_finance.dossier.printPreview = function (doctype, name) {
	if (!omnexa_finance.dossier._requireCase(doctype, name)) return;
	const run = frappe.xcall
		? frappe.xcall(omnexa_finance.dossier.DOSSIER_HTML, { doctype, name })
		: frappe.call({ method: omnexa_finance.dossier.DOSSIER_HTML, args: { doctype, name } }).then((r) => r.message);
	run
		.then((html) => {
			omnexa_finance.dossier._openHtmlPrintWindow(html, __("Borrower Complete File"));
		})
		.catch((err) => {
			frappe.msgprint({
				title: __("Print"),
				indicator: "red",
				message: err || __("Print preview failed."),
			});
		});
};

omnexa_finance.dossier.printDocument = function (docName) {
	if (!docName) return;
	omnexa_finance.dossier.apiDownload(omnexa_finance.dossier.DOC_PRINT, { name: docName });
	frappe.show_alert({ message: __("Downloading document PDF…"), indicator: "blue" });
};

omnexa_finance.dossier.printDocumentPreview = function (docName) {
	if (!docName) return;
	const run = frappe.xcall
		? frappe.xcall(omnexa_finance.dossier.DOC_HTML, { name: docName })
		: frappe.call({ method: omnexa_finance.dossier.DOC_HTML, args: { name: docName } }).then((r) => r.message);
	run.then((html) => omnexa_finance.dossier._openHtmlPrintWindow(html, __("Borrower Document")));
};

omnexa_finance.dossier.ensureLoaded = function (callback) {
	if (omnexa_finance.dossier.downloadPdf) {
		callback();
		return;
	}
	frappe.require(["/assets/omnexa_core/js/finance_borrower_dossier.js"], callback);
};

omnexa_finance.dossier.addFormButtons = function (frm) {
	if (!frm.doc.name || frm.is_new()) return;
	if (!omnexa_finance.dossier.isFinanceCaseDoctype(frm.doctype)) return;
	frm.add_custom_button(__("ملف المقترض — PDF"), () => {
		omnexa_finance.dossier.downloadPdf(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("ملف المقترض — طباعة"), () => {
		omnexa_finance.dossier.printPreview(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("ملف المقترض — Excel"), () => {
		omnexa_finance.dossier.downloadExcel(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("ملف المقترض — تقرير"), () => {
		omnexa_finance.dossier.openReport(frm.doctype, frm.docname);
	}, __("Borrower File"));
	frm.add_custom_button(__("مستندات المقترض"), () => {
		frappe.route_options = { case_doctype: frm.doctype, case_name: frm.docname };
		frappe.set_route("List", "Finance Borrower Case Document");
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
