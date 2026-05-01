/* global frappe */
// Full-width layout, clearer report actions (Print / PDF / Export / column tools), idempotent toolbar hooks.

(function () {
	function run_menu_item(report, labelEn) {
		const want = __(labelEn);
		const items = report.menu_items || [];
		for (let i = 0; i < items.length; i++) {
			const m = items[i];
			if (!m || m.label !== want) continue;
			if (m.condition && !m.condition()) continue;
			m.action();
			return true;
		}
		return false;
	}

	function open_print(report) {
		run_menu_item(report, "Print");
	}

	function open_pdf(report) {
		run_menu_item(report, "PDF");
	}

	function open_export(report) {
		run_menu_item(report, "Export");
	}

	function open_add_column(report) {
		run_menu_item(report, "Add Column");
	}

	function omnexaEnsureReportToolbar(report) {
		if (!report.page || !report.report_doc || report._omnexa_report_toolbar_installed) return;
		report._omnexa_report_toolbar_installed = true;

		const page = report.page;
		const group = __("Report");
		const ref = report.report_doc.ref_doctype;
		const mayPrint = () => !ref || frappe.model.can_print(ref);
		const mayExport = () => !ref || frappe.model.can_export(ref);

		if (mayPrint()) {
			page.add_inner_button(__("Print"), () => open_print(report), group);
			page.add_inner_button(__("PDF"), () => open_pdf(report), group);
		}
		if (mayExport()) {
			page.add_inner_button(__("Export"), () => open_export(report), group);
		}

		page.add_inner_button(__("Add Column"), () => open_add_column(report), group);
		page.add_inner_button(__("Report setup"), () => frappe.set_route("Form", "Report", report.report_name), group);
	}

	const proto = frappe.views?.QueryReport?.prototype;
	if (!proto || proto.__omnexa_qr_ux_patched) return;
	proto.__omnexa_qr_ux_patched = true;

	const origLoadReport = proto.load_report;
	proto.load_report = function (route_options) {
		this._omnexa_report_toolbar_installed = false;
		return origLoadReport.apply(this, arguments);
	};

	const origAddChart = proto.add_chart_buttons_to_toolbar;
	proto.add_chart_buttons_to_toolbar = function (show) {
		const ret = origAddChart.apply(this, arguments);
		try {
			omnexaEnsureReportToolbar(this);
		} catch (e) {
			/* ignore */
		}
		return ret;
	};
})();
