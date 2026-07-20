/* global frappe */
// Quick period presets for Query Report date filters.

(function () {
	const PRESETS = [
		{ key: "today", label: __("Today") },
		{ key: "yesterday", label: __("Yesterday") },
		{ key: "this_week", label: __("This Week") },
		{ key: "this_month", label: __("This Month") },
		{ key: "this_quarter", label: __("This Quarter") },
		{ key: "this_year", label: __("This Year") },
	];

	function period_range(key) {
		const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
		const y = today.getFullYear();
		const m = today.getMonth();
		const d = today.getDate();
		const fmt = (dt) => frappe.datetime.obj_to_str(dt);

		if (key === "today") {
			const t = fmt(today);
			return { from_date: t, to_date: t };
		}
		if (key === "yesterday") {
			const yd = new Date(today);
			yd.setDate(d - 1);
			const t = fmt(yd);
			return { from_date: t, to_date: t };
		}
		if (key === "this_week") {
			const start = new Date(today);
			start.setDate(d - start.getDay());
			return { from_date: fmt(start), to_date: fmt(today) };
		}
		if (key === "this_month") {
			return { from_date: fmt(new Date(y, m, 1)), to_date: fmt(today) };
		}
		if (key === "this_quarter") {
			const qm = m - (m % 3);
			return { from_date: fmt(new Date(y, qm, 1)), to_date: fmt(today) };
		}
		if (key === "this_year") {
			return { from_date: fmt(new Date(y, 0, 1)), to_date: fmt(today) };
		}
		return null;
	}

	function has_date_filters(report) {
		return (report.filters || []).some((f) => f?.df?.fieldtype === "Date");
	}

	function apply_preset(report, key) {
		const range = period_range(key);
		if (!range || !report.set_filter_value) return;
		if (report.get_filter_value?.("from_date", false) !== undefined) {
			report.set_filter_value("from_date", range.from_date);
		}
		if (report.get_filter_value?.("to_date", false) !== undefined) {
			report.set_filter_value("to_date", range.to_date);
		}
		report.refresh();
	}

	function omnexaEnsurePeriodToolbar(report) {
		if (!report.page || report._omnexa_period_toolbar_installed) return;
		if (!has_date_filters(report)) return;
		report._omnexa_period_toolbar_installed = true;
		const group = __("Period");
		PRESETS.forEach((p) => {
			report.page.add_inner_button(p.label, () => apply_preset(report, p.key), group);
		});
	}

	const proto = frappe.views?.QueryReport?.prototype;
	if (!proto || proto.__omnexa_period_patched) return;
	proto.__omnexa_period_patched = true;

	const origSetup = proto.setup_filters;
	proto.setup_filters = function () {
		const out = origSetup.apply(this, arguments);
		try {
			frappe.after_ajax(() => omnexaEnsurePeriodToolbar(this));
		} catch (e) {
			/* ignore */
		}
		return out;
	};
})();
