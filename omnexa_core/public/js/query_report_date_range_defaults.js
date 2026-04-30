/* global frappe */

// Ensure every Query Report has from_date/to_date filters
// and defaults them to Today if empty.
(function () {
	function today() {
		// Frappe date format: YYYY-MM-DD
		return frappe.datetime.get_today();
	}

	function ensureDateFilter(report, fieldname, label) {
		const existing = (report.filters || []).find((f) => (f && f.df && f.df.fieldname) === fieldname);
		if (existing) return existing;
		return report.add_filter({
			fieldname,
			label: __(label),
			fieldtype: "Date",
			default: today(),
		});
	}

	function applyDefaults(report) {
		if (!report || !report.filters || !report.add_filter) return;

		const from = ensureDateFilter(report, "from_date", "From Date");
		const to = ensureDateFilter(report, "to_date", "To Date");

		// Only set default if user hasn't provided a value.
		if (from && !from.get_value()) from.set_value(today());
		if (to && !to.get_value()) to.set_value(today());
	}

	// Monkey-patch QueryReport.setup_filters once.
	const proto = frappe.views?.QueryReport?.prototype;
	if (!proto || proto.__omnexa_date_range_patched) return;
	proto.__omnexa_date_range_patched = true;

	const original = proto.setup_filters;
	proto.setup_filters = function () {
		const out = original.apply(this, arguments);
		try {
			applyDefaults(this);
		} catch (e) {
			// Safe no-op: never break report rendering.
		}
		return out;
	};
})();

