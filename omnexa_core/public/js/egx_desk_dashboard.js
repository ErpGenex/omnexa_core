/**
 * ErpGenEx Desk — shared dashboard renderers (Frappe desk ↔ Next.js catalog parity)
 */
/* global frappe */
frappe.provide("egx.desk");

(function () {
	"use strict";

	const CHART_COLORS = ["#2563eb", "#8b5cf6", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444"];
	const TONE_CLASS = {
		purple: "egx-kpi--purple",
		green: "egx-kpi--success",
		orange: "egx-kpi--warning",
		blue: "egx-kpi--blue",
		red: "egx-kpi--danger",
	};

	function esc(s) {
		return frappe.utils.escape_html(String(s ?? ""));
	}

	function toneClass(tone) {
		return TONE_CLASS[tone] || "";
	}

	function renderDonutChart($wrap, labels, values, title) {
		$wrap.empty();
		if (!labels || !labels.length) {
			$wrap.append(`<div class="egx-muted egx-dash-chart-empty">${esc(__("No chart data"))}</div>`);
			return;
		}
		const $canvas = $('<div class="egx-dash-chart-canvas"></div>');
		$wrap.append($canvas);
		if (typeof frappe.Chart !== "function") {
			$wrap.append(`<div class="egx-dash-legend">${labels.map((l, i) => `<span>${esc(l)}: <b>${values[i] || 0}</b></span>`).join(" · ")}</div>`);
			return;
		}
		try {
			new frappe.Chart($canvas[0], {
				title: title || "",
				type: "donut",
				height: 240,
				colors: CHART_COLORS,
				data: {
					labels: labels,
					datasets: [{ values: values }],
				},
			});
		} catch (e) {
			$wrap.append(`<div class="egx-muted">${esc(__("Chart unavailable"))}</div>`);
		}
	}

	function renderLineChart($wrap, labels, values, title) {
		$wrap.empty();
		const $canvas = $('<div class="egx-dash-chart-canvas"></div>');
		$wrap.append($canvas);
		if (typeof frappe.Chart !== "function") {
			return;
		}
		try {
			new frappe.Chart($canvas[0], {
				title: title || "",
				type: "line",
				height: 200,
				colors: ["#2563eb"],
				data: {
					labels: labels || [],
					datasets: [{ name: __("Attendance"), values: values || [] }],
				},
				lineOptions: { regionFill: 1 },
			});
		} catch (e) {
			$wrap.append(`<div class="egx-muted">${esc(__("Chart unavailable"))}</div>`);
		}
	}

	egx.desk.mountDashboard = function ($mount, catalog, opts) {
		opts = opts || {};
		catalog = catalog || {};
		const welcome = catalog.welcome || {};
		const kpis = catalog.kpis || [];
		const actions = catalog.quick_actions || [];
		const announcements = catalog.announcements || [];
		const charts = catalog.charts || {};
		const panels = catalog.panels || {};
		const empOverview = charts.employee_overview || {};
		const attendance = charts.attendance || {};

		const $shell = $(`<div class="egx-page-shell egx-hr-dashboard"></div>`);

		// Row 1: welcome + quick actions + announcements
		const $row1 = $('<div class="egx-dash-row egx-dash-row--hero"></div>');

		$row1.append(`
			<div class="egx-panel egx-dash-welcome">
				<h2 class="egx-page-title">${esc(welcome.title || __("HR Dashboard"))}</h2>
				<p class="egx-page-subtitle">${esc(welcome.subtitle || "")}</p>
				<div class="egx-dash-welcome-art" aria-hidden="true"></div>
			</div>`);

		const $actions = $(`<div class="egx-panel egx-dash-actions"><h3 class="egx-dash-section-title">${esc(__("Quick Actions"))}</h3><div class="egx-dash-action-grid"></div></div>`);
		actions.forEach((a) => {
			$actions.find(".egx-dash-action-grid").append(`
				<a class="egx-dash-action" href="${esc(a.route)}">
					<span class="egx-dash-action-icon egx-dash-action-icon--${esc(a.tone || "blue")}"></span>
					<span>${esc(a.label)}</span>
				</a>`);
		});
		$row1.append($actions);

		const $ann = $(`<div class="egx-panel egx-dash-announce"><div class="egx-dash-section-head"><h3 class="egx-dash-section-title">${esc(__("Announcements"))}</h3></div><ul class="egx-dash-announce-list"></ul></div>`);
		announcements.forEach((a) => {
			$ann.find(".egx-dash-announce-list").append(`
				<li>
					<span class="egx-dash-announce-dot"></span>
					<div>
						<div class="egx-dash-announce-title">${esc(a.title)}</div>
						<div class="egx-dash-announce-meta">${esc(a.date)} ${esc(a.time || "")}</div>
					</div>
				</li>`);
		});
		$row1.append($ann);
		$shell.append($row1);

		// KPIs
		const $kpiRow = $('<div class="egx-kpi-row egx-dash-kpi-row"></div>');
		kpis.forEach((k) => {
			const delta =
				k.delta && k.direction
					? `<span class="egx-kpi__delta egx-kpi__delta--${esc(k.direction)}">${esc(k.delta)}</span>`
					: "";
			$kpiRow.append(`
				<div class="egx-kpi ${toneClass(k.tone)}">
					<div class="egx-kpi__label">${esc(k.label)}</div>
					<div class="egx-kpi__value-row">
						<span class="egx-kpi__value">${esc(k.value)}</span>${delta}
					</div>
				</div>`);
		});
		$shell.append($kpiRow);

		// Charts
		const $charts = $('<div class="egx-dash-row egx-dash-row--charts"></div>');
		const $donutPanel = $(`
			<div class="egx-panel egx-dash-chart-panel">
				<h3 class="egx-dash-section-title">${esc(empOverview.title || __("Employee Overview"))}</h3>
				<div class="egx-dash-tabs"></div>
				<div class="egx-dash-chart-host egx-dash-donut"></div>
			</div>`);
		(empOverview.tabs || []).forEach((tab, i) => {
			$donutPanel.find(".egx-dash-tabs").append(
				`<button type="button" class="egx-dash-tab${i === 0 ? " active" : ""}">${esc(tab)}</button>`
			);
		});
		$charts.append($donutPanel);

		const $linePanel = $(`
			<div class="egx-panel egx-dash-chart-panel">
				<h3 class="egx-dash-section-title">${esc(attendance.title || __("Attendance Overview"))}</h3>
				<p class="egx-page-subtitle">${esc(attendance.subtitle || "")}</p>
				<div class="egx-dash-chart-host egx-dash-line"></div>
				<div class="egx-dash-att-stats"></div>
			</div>`);
		(attendance.stats || []).forEach((s) => {
			$linePanel.find(".egx-dash-att-stats").append(`
				<div class="egx-dash-att-stat">
					<div class="egx-kpi__value">${esc(s.value)}</div>
					<div class="egx-kpi__label">${esc(s.label)}</div>
				</div>`);
		});
		$charts.append($linePanel);
		$shell.append($charts);

		// Panels
		const $panels = $('<div class="egx-dash-row egx-dash-row--panels"></div>');

		const $leave = $(`<div class="egx-panel"><h3 class="egx-dash-section-title">${esc(__("Leave Summary"))}</h3><div class="egx-dash-progress-list"></div></div>`);
		(panels.leave_summary || []).forEach((item) => {
			const pct = item.total ? Math.round((item.used / item.total) * 100) : 0;
			$leave.find(".egx-dash-progress-list").append(`
				<div class="egx-dash-progress">
					<div class="egx-dash-progress-head">
						<span>${esc(item.label)}</span>
						<span class="egx-muted">${item.used}/${item.total}</span>
					</div>
					<div class="egx-dash-progress-bar"><span style="width:${pct}%"></span></div>
				</div>`);
		});
		$panels.append($leave);

		const $training = $(`<div class="egx-panel"><h3 class="egx-dash-section-title">${esc(__("Training Summary"))}</h3><ul class="egx-dash-simple-list"></ul></div>`);
		(panels.training_summary || []).forEach((t) => {
			$training.find(".egx-dash-simple-list").append(
				`<li><span>${esc(t.label)}</span><strong>${esc(t.count)}</strong></li>`
			);
		});
		$panels.append($training);

		$panels.append(`
			<div class="egx-panel">
				<h3 class="egx-dash-section-title">${esc(__("Recent Activities"))}</h3>
				<p class="egx-muted">${esc(__("Activity feed will appear here."))}</p>
			</div>`);
		$shell.append($panels);

		$mount.empty().append($shell);

		try {
			renderDonutChart($donutPanel.find(".egx-dash-donut"), empOverview.labels, empOverview.values, empOverview.title);
			renderLineChart($linePanel.find(".egx-dash-line"), attendance.labels, attendance.values, attendance.title);
		} catch (chartErr) {
			console.warn("[egx.desk.mountDashboard] charts", chartErr);
		}
	};

	egx.desk.mountAnalytics = function ($mount, data, opts) {
		data = data || {};
		const s = data.summary || {};
		const areas = data.areas || {};
		const $shell = $(`<div class="egx-page-shell egx-hr-analytics"></div>`);

		$shell.append(`
			<div class="egx-dash-analytics-head">
				<div>
					<h2 class="egx-page-title">${esc(__("HR Analytics — ISO 30414"))}</h2>
					<p class="egx-page-subtitle">${esc(data.standard || "ISO 30414")}${data.company ? " · " + esc(data.company) : ""}${data.branch ? " · " + esc(data.branch) : ""}</p>
				</div>
			</div>`);

		const $kpiRow = $('<div class="egx-kpi-row"></div>');
		[
			{ label: __("Headcount"), value: s.headcount || 0, tone: "purple" },
			{ label: __("Attendance Rate (30d)"), value: (s.attendance_rate_30d || 0) + "%", tone: "green" },
			{ label: __("Pending Leave"), value: s.open_leave_approvals || 0, tone: "orange" },
			{ label: __("Active Applicants"), value: s.active_applicants || 0, tone: "blue" },
		].forEach((k) => {
			$kpiRow.append(`
				<div class="egx-kpi ${toneClass(k.tone)}">
					<div class="egx-kpi__label">${esc(k.label)}</div>
					<div class="egx-kpi__value">${esc(k.value)}</div>
				</div>`);
		});
		$shell.append($kpiRow);

		const $areas = $('<div class="egx-dash-area-grid"></div>');
		Object.keys(areas).forEach((key) => {
			const area = areas[key];
			const rows = (area.indicators || [])
				.map((ind) => `<tr><td>${esc(ind.kpi)}</td><td class="text-right"><b>${esc(ind.value)}</b></td></tr>`)
				.join("");
			$areas.append(`
				<div class="egx-panel">
					<h3 class="egx-dash-section-title">${esc(area.label || key)}</h3>
					<div class="egx-table-wrap">
						<table class="egx-table"><tbody>${rows}</tbody></table>
					</div>
				</div>`);
		});
		$shell.append($areas);
		$mount.empty().append($shell);
	};

	egx.desk.mountESS = function ($mount, data, opts) {
		data = data || {};
		opts = opts || {};
		const $shell = $(`<div class="egx-page-shell egx-hr-ess"></div>`);

		if (!data.employee) {
			$shell.append(`
				<div class="egx-panel">
					<h2 class="egx-page-title">${esc(__("Employee Self-Service"))}</h2>
					<p class="egx-muted">${esc(data.message || __("No employee profile linked."))}</p>
					<a class="egx-btn egx-btn--primary" href="/app/employee-directory">${esc(__("Open Employee Directory"))} →</a>
				</div>`);
			$mount.empty().append($shell);
			return;
		}

		const emp = data.employee;
		const photo = emp.employee_photo ? frappe.utils.get_file_link(emp.employee_photo) : "/assets/omnexa_hr/images/default-avatar.svg";
		const meta = [emp.employee_code, emp.department, emp.designation].filter(Boolean).join(" · ");

		$shell.append(`
			<h2 class="egx-page-title">${esc(__("Employee Self-Service"))}</h2>
			<div class="egx-panel egx-ess-profile">
				<img class="egx-ess-avatar" src="${esc(photo)}" alt="">
				<div>
					<h3 class="egx-ess-name">${esc(emp.employee_name)}</h3>
					<p class="egx-page-subtitle">${esc(meta)}</p>
				</div>
			</div>`);

		const $kpiRow = $('<div class="egx-kpi-row egx-ess-kpis"></div>');
		$kpiRow.append(`
			<div class="egx-kpi egx-kpi--warning"><div class="egx-kpi__label">${esc(__("Pending Leave"))}</div><div class="egx-kpi__value">${data.pending_leave || 0}</div></div>
			<div class="egx-kpi egx-kpi--success"><div class="egx-kpi__label">${esc(__("Approved Leave"))}</div><div class="egx-kpi__value">${data.approved_leave || 0}</div></div>
			<div class="egx-ess-actions">
				<button type="button" class="egx-btn egx-btn--primary" id="egx-ess-new-leave">${esc(__("New Leave Application"))}</button>
				<button type="button" class="egx-btn" id="egx-ess-attendance">${esc(__("My Attendance"))}</button>
			</div>`);
		$shell.append($kpiRow);

		const balances = (data.leave_balances || [])
			.map((b) => `<li>${esc(b.leave_type)}: <strong>${b.balance_days}</strong> (${esc(b.fiscal_year)})</li>`)
			.join("");
		$shell.append(`
			<div class="egx-panel">
				<h3 class="egx-dash-section-title">${esc(__("Leave Balances"))}</h3>
				<ul class="egx-dash-simple-list egx-ess-balances">${balances || `<li class="egx-muted">${esc(__("No balances yet"))}</li>`}</ul>
			</div>`);

		const attendance = (data.recent_attendance || [])
			.map(
				(a) =>
					`<tr><td>${esc(a.attendance_date)}</td><td>${esc(a.status)}</td><td>${esc(a.check_in || "—")}</td><td>${esc(a.check_out || "—")}</td><td>${esc(a.working_hours ?? "—")}</td></tr>`
			)
			.join("");
		$shell.append(`
			<div class="egx-panel egx-ess-attendance">
				<h3 class="egx-dash-section-title">${esc(__("Recent Attendance"))}</h3>
				<div class="egx-table-wrap">
					<table class="egx-table">
						<thead><tr><th>${esc(__("Date"))}</th><th>${esc(__("Status"))}</th><th>${esc(__("In"))}</th><th>${esc(__("Out"))}</th><th>${esc(__("Hours"))}</th></tr></thead>
						<tbody>${attendance}</tbody>
					</table>
				</div>
			</div>`);

		$mount.empty().append($shell);
		$shell.find("#egx-ess-new-leave").on("click", () => frappe.new_doc("HR Leave Application"));
		$shell.find("#egx-ess-attendance").on("click", () => frappe.set_route("List", "HR Attendance", { employee: emp.name }));
	};

	egx.desk.mountRoleLauncher = function ($mount, opts) {
		opts = opts || {};
		const links = opts.links || [];
		const $shell = $(`<div class="egx-page-shell egx-hr-role-desk"></div>`);
		$shell.append(`
			<h2 class="egx-page-title">${esc(opts.title || __("Role Desk"))}</h2>
			<p class="egx-page-subtitle">${esc(opts.description || "")}</p>`);
		const $grid = $('<div class="egx-dash-link-grid"></div>');
		links.forEach((l) => {
			$grid.append(`
				<a class="egx-panel egx-dash-link-card" href="${esc(l.href)}">
					<span>${esc(l.label)}</span>
					${l.external ? '<span class="egx-dash-link-ext">↗</span>' : '<span class="egx-dash-link-arrow">→</span>'}
				</a>`);
		});
		$shell.append($grid);
		$mount.empty().append($shell);
	};

	egx.desk.mountWorkspaceHub = function ($mount, catalog) {
		catalog = catalog || {};
		const $shell = $(`<div class="egx-page-shell egx-hr-workspace"></div>`);
		$shell.append(`
			<h2 class="egx-page-title">${esc(catalog.title || "HR")}</h2>
			<p class="egx-page-subtitle">${esc(__("Human Resources workspace — same catalog as Next.js desk."))}</p>`);

		if ((catalog.kpis || []).length) {
			const $kpiRow = $('<div class="egx-kpi-row"></div>');
			catalog.kpis.forEach((k) => {
				$kpiRow.append(`
					<div class="egx-kpi">
						<div class="egx-kpi__label">${esc(k.label)}</div>
						<div class="egx-kpi__value">${esc(k.value)}</div>
					</div>`);
			});
			$shell.append($kpiRow);
		}

		(catalog.sections || []).forEach((section) => {
			$shell.append(`<h3 class="egx-dash-section-title egx-ws-section">${esc(section.title)}</h3>`);
			const $grid = $('<div class="egx-dash-link-grid"></div>');
			(section.links || []).forEach((link) => {
				$grid.append(`
					<a class="egx-panel egx-dash-link-card" href="${esc(link.href)}">
						<span>${esc(link.label)}</span>
						${link.external ? '<span class="egx-dash-link-ext">↗</span>' : '<span class="egx-dash-link-arrow">→</span>'}
					</a>`);
			});
			$shell.append($grid);
		});
		$mount.empty().append($shell);
	};
})();
