/* global frappe */
// Extended export actions: Excel, CSV, JSON, HTML snapshot for Query Reports.

(function () {
	function report_rows(report) {
		const dt = report.datatable;
		if (!dt || !dt.datamanager) return [];
		return dt.datamanager.data || [];
	}

	function report_columns(report) {
		const dt = report.datatable;
		if (!dt || !dt.options) return [];
		return (dt.options.columns || []).filter((c) => c.fieldname && c.fieldname !== "_check");
	}

	function cell_value(row, col) {
		const val = row[col.fieldname];
		if (val === undefined || val === null) return "";
		return val;
	}

	function download_blob(filename, mime, content) {
		const blob = new Blob([content], { type: mime });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		a.remove();
		URL.revokeObjectURL(url);
	}

	function slug(name) {
		return (name || "report").replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_").toLowerCase();
	}

	function export_csv(report) {
		const cols = report_columns(report);
		const rows = report_rows(report);
		const header = cols.map((c) => c.name || c.fieldname).join(",");
		const body = rows
			.map((row) =>
				cols
					.map((c) => {
						const v = cell_value(row, c);
						const s = String(v).replace(/"/g, '""');
						return `"${s}"`;
					})
					.join(",")
			)
			.join("\n");
		download_blob(`${slug(report.report_name)}.csv`, "text/csv;charset=utf-8", header + "\n" + body);
	}

	function export_json(report) {
		const cols = report_columns(report);
		const rows = report_rows(report).map((row) => {
			const out = {};
			cols.forEach((c) => {
				out[c.fieldname] = cell_value(row, c);
			});
			return out;
		});
		const payload = {
			report: report.report_name,
			filters: report.get_filter_values ? report.get_filter_values() : {},
			generated_at: frappe.datetime.now_datetime(),
			rows,
		};
		download_blob(
			`${slug(report.report_name)}.json`,
			"application/json;charset=utf-8",
			JSON.stringify(payload, null, 2)
		);
	}

	function export_html_snapshot(report) {
		const table = report.$report?.find("table")?.[0];
		if (!table) {
			frappe.msgprint(__("Run the report first, then export HTML."));
			return;
		}
		const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${report.report_name}</title></head><body>${table.outerHTML}</body></html>`;
		download_blob(`${slug(report.report_name)}.html`, "text/html;charset=utf-8", html);
	}

	function export_word_doc(report) {
		const table = report.$report?.find("table")?.[0];
		if (!table) {
			frappe.msgprint(__("Run the report first, then export Word."));
			return;
		}
		// Word can open HTML when saved as .doc. This is court-friendly for Arabic prints.
		const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${report.report_name}</title></head><body>${table.outerHTML}</body></html>`;
		download_blob(`${slug(report.report_name)}.doc`, "application/msword", html);
	}

	function omnexaEnsureExportToolbar(report) {
		if (!report.page || report._omnexa_export_toolbar_installed) return;
		report._omnexa_export_toolbar_installed = true;
		const group = __("Export");
		const ref = report.report_doc?.ref_doctype;
		const mayExport = () => !ref || frappe.model.can_export(ref);

		if (!mayExport()) return;

		report.page.add_inner_button(__("Excel"), () => {
			if (!frappe.views?.QueryReport?.prototype?.export_report) {
				frappe.msgprint(__("Excel export unavailable."));
				return;
			}
			report.export_report();
		}, group);
		report.page.add_inner_button(__("CSV"), () => export_csv(report), group);
		report.page.add_inner_button(__("JSON"), () => export_json(report), group);
		report.page.add_inner_button(__("HTML"), () => export_html_snapshot(report), group);
		report.page.add_inner_button(__("Word"), () => export_word_doc(report), group);
	}

	const proto = frappe.views?.QueryReport?.prototype;
	if (!proto || proto.__omnexa_export_patched) return;
	proto.__omnexa_export_patched = true;

	const origAddChart = proto.add_chart_buttons_to_toolbar;
	proto.add_chart_buttons_to_toolbar = function (show) {
		const ret = origAddChart.apply(this, arguments);
		try {
			omnexaEnsureExportToolbar(this);
		} catch (e) {
			/* ignore */
		}
		return ret;
	};
})();
