/* global frappe */

// Ensure every Query Report has from_date/to_date filters
// and defaults them to Today if empty.
(function () {
	function today() {
		// Frappe date format: YYYY-MM-DD
		return frappe.datetime.get_today();
	}

	function _set_filter_value(report, fieldname, value) {
		try {
			if (typeof report.set_filter_value === "function") {
				// Preferred: updates both filter UI + internal report state
				return report.set_filter_value(fieldname, value);
			}
		} catch (e) {
			// ignore
		}
		const f = (report.filters || []).find((x) => (x && x.df && x.df.fieldname) === fieldname);
		try {
			if (f && typeof f.set_value === "function") return f.set_value(value);
		} catch (e) {
			// ignore
		}
		return null;
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
		if (from && typeof from.get_value === "function" && !from.get_value()) _set_filter_value(report, "from_date", today());
		if (to && typeof to.get_value === "function" && !to.get_value()) _set_filter_value(report, "to_date", today());
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

	// Also patch refresh() to guarantee values exist before report runs.
	const originalRefresh = proto.refresh;
	if (typeof originalRefresh === "function") {
		proto.refresh = function () {
			try {
				applyDefaults(this);
				const from = (this.get_filter_value && this.get_filter_value("from_date")) || "";
				const to = (this.get_filter_value && this.get_filter_value("to_date")) || "";
				if ((!from || !to) && !this.__omnexa_refresh_defaulting) {
					this.__omnexa_refresh_defaulting = true;
					_set_filter_value(this, "from_date", from || today());
					_set_filter_value(this, "to_date", to || today());
					this.__omnexa_refresh_defaulting = false;
				}
			} catch (e) {
				// ignore
			}
			return originalRefresh.apply(this, arguments);
		};
	}
})();

