/**
 * Omnexa Finance Journey — desk UI kit (healthcare-parity for banking group)
 */
/* global frappe */
(function (window) {
	"use strict";

	function lang() {
		return frappe.boot && frappe.boot.lang === "ar" ? "ar" : "en";
	}

	function t(ar, en) {
		return lang() === "ar" ? ar : en;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function call(method, args) {
		return new Promise((resolve, reject) => {
			frappe.call({ method, args: args || {}, callback: (r) => resolve(r.message), error: reject });
		});
	}

	function mountDeskPage(wrapper, title) {
		frappe.ui.make_app_page({ parent: wrapper, title: title || "", single_column: true });
		$(wrapper).find(".page-head").hide();
		return $(wrapper).find(".layout-main-section");
	}

	function sidebarIconHtml(item) {
		if (item.logoUrl) {
			return `<img class="oj-sidebar-logo-img" src="${esc(item.logoUrl)}" alt="" />`;
		}
		return `<span class="oj-sidebar-emoji">${item.icon || "•"}</span>`;
	}

	function shell(options) {
		const opts = options || {};
		const sidebar = opts.sidebar || [];
		const isRtl = lang() === "ar";
		const navHtml = sidebar
			.map(
				(n) =>
					`<a class="oj-sidebar-item ${n.active ? "active" : ""}" href="#" data-nav-route="${esc(n.route || "")}">${sidebarIconHtml(n)}<span class="oj-sidebar-label">${esc(n.label)}</span></a>`
			)
			.join("");
		const kpiHtml = (opts.kpis || [])
			.map((k) => `<div class="oj-kpi-card"><div class="oj-kpi-value">${esc(k.value)}</div><div class="oj-kpi-label">${esc(k.label)}</div></div>`)
			.join("");
		const brandLogo = opts.brandLogoUrl
			? `<img class="oj-brand-logo" src="${esc(opts.brandLogoUrl)}" alt="" />`
			: `<span class="oj-logo">+</span>`;
		const $root = $(`<div class="oj-shell oj-finance-shell ${isRtl ? "oj-rtl" : "oj-ltr"}" dir="${isRtl ? "rtl" : "ltr"}"></div>`);
		$root.html(`
			<aside class="oj-sidebar oj-finance-sidebar">${navHtml}<div class="oj-sidebar-spacer"></div>
				<a class="oj-sidebar-item" href="#" data-nav-route="/app/finance-workcenter" aria-label="${t("مركز العمل", "Workcenter")}"><span class="oj-sidebar-emoji">🏢</span><span class="oj-sidebar-label">${t("مركز العمل", "Workcenter")}</span></a>
				<a class="oj-sidebar-item oj-logout" href="/app"><span class="oj-sidebar-emoji">⏻</span><span class="oj-sidebar-label">${t("خروج", "Logout")}</span></a>
			</aside>
			<div class="oj-main">
				<header class="oj-topbar">
					<div class="oj-topbar-brand">${brandLogo}<div><strong>ErpGenEx Finance</strong><small>${esc(opts.subtitle || "")}</small></div></div>
					<div class="oj-topbar-meta"><span class="oj-pill">${esc(opts.role || "")}</span><span class="oj-user">${esc(frappe.session.user_fullname || frappe.session.user)}</span></div>
				</header>
				<div class="oj-title-row"><h1>${esc(opts.title || "")}</h1></div>
				${kpiHtml ? `<div class="oj-kpi-row">${kpiHtml}</div>` : ""}
				<div class="oj-body"></div>
			</div>`);
		const $body = $root.find(".oj-body");
		if (opts.bodyEl) $body.append(opts.bodyEl);
		else if (opts.body) $body.html(opts.body);
		$root.find(".oj-sidebar-item[data-nav-route]").on("click", function (e) {
			e.preventDefault();
			const route = $(this).attr("data-nav-route");
			if (!route) return;
			if (window.omnexa_finance && omnexa_finance.portal && omnexa_finance.portal._navigateRoute) {
				omnexa_finance.portal._navigateRoute(route, (opts.currentPage || ""));
				return;
			}
			if (route.startsWith("/app/")) window.location.href = route;
			else if (route.startsWith("List/")) frappe.set_route("List", route.slice(5));
			else if (route.startsWith("Form/")) {
				const p = route.split("/");
				frappe.set_route("Form", p[1], p[2] || "");
			} else if (route.startsWith("Report/")) frappe.set_route("query-report", route.slice(7));
		});
		return $root;
	}

	function dataTable(columns, rows) {
		const cols = columns || [];
		const head = cols.map((c) => `<th>${esc(c.label)}</th>`).join("");
		const body = (rows || [])
			.map((row) => `<tr>${cols.map((c) => `<td>${esc(row[c.field] ?? "—")}</td>`).join("")}</tr>`)
			.join("");
		const html = `<div class="oj-table-wrap"><table class="oj-data-table"><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${cols.length || 1}" class="oj-muted">${t("لا بيانات", "No data")}</td></tr>`}</tbody></table></div>`;
		return $(html);
	}

	function linkGrid(links) {
		const $g = $('<div class="oj-link-grid"></div>');
		(links || []).forEach((link) => {
			const icon = link.logoUrl
				? `<img class="oj-link-logo" src="${esc(link.logoUrl)}" alt="" />`
				: `<div class="oj-link-icon">${link.icon || "•"}</div>`;
			const $card = $(`<div class="oj-link-card">${icon}<div class="oj-link-label">${esc(link.label)}</div></div>`);
			$card.on("click", () => {
				const r = link.route || "";
				if (r.startsWith("/app/")) window.location.href = r;
				else if (r.startsWith("List/")) frappe.set_route("List", r.slice(5));
				else if (r.startsWith("Form/")) {
					const p = r.split("/");
					frappe.set_route("Form", p[1], p[2] || "");
				} else frappe.set_route(r);
			});
			$g.append($card);
		});
		return $g;
	}

	function portalCardGrid(portals, onSelect) {
		const $g = $('<div class="oj-clinic-grid oj-finance-portal-grid"></div>');
		(portals || []).forEach((p) => {
			const icon = p.logoUrl
				? `<img class="oj-portal-logo" src="${esc(p.logoUrl)}" alt="" />`
				: `<div class="oj-clinic-icon">${p.icon || "🏦"}</div>`;
			const $card = $(`
				<div class="oj-clinic-card ${p.disabled ? "oj-muted-card" : ""}">
					${icon}
					<h4>${esc(p.name)}</h4>
					<p class="oj-muted">${esc(p.subtitle || "")}</p>
					<button type="button" class="oj-btn oj-btn-primary oj-btn-sm">${t("فتح", "Open")}</button>
				</div>`);
			if (!p.disabled) $card.on("click", () => (onSelect ? onSelect(p) : null));
			$g.append($card);
		});
		return $g;
	}

	function loading() {
		return `<div class="oj-loading">${t("جاري التحميل...", "Loading...")}</div>`;
	}

	function logoUrl(app) {
		return app ? `/assets/${app}/logo.png` : "";
	}

	const SIDEBARS = {
		executive: [
			{ label: t("تنفيذي", "Executive"), route: "/app/fe-executive-dashboard", logoUrl: logoUrl("omnexa_finance_engine") },
			{ label: t("محرك", "Engine"), route: "/app/fe-servicing-portal", logoUrl: logoUrl("omnexa_finance_engine") },
			{ label: t("مركز العمل", "Workcenter"), route: "/app/finance-workcenter", icon: "🏢" },
		],
		credit: [
			{ label: t("منشأة", "Origination"), route: "/app/ce-servicing-portal", logoUrl: logoUrl("omnexa_credit_engine") },
			{ label: t("قرارات", "Decisions"), route: "List/Credit Decision Case", icon: "📋" },
			{ label: t("تنفيذي", "Executive"), route: "/app/ce-executive-dashboard", logoUrl: logoUrl("omnexa_credit_engine") },
		],
		risk: [
			{ label: t("مخاطر", "Risk"), route: "/app/rk-servicing-portal", logoUrl: logoUrl("omnexa_credit_risk") },
			{ label: t("تنفيذي", "Executive"), route: "/app/rk-executive-dashboard", logoUrl: logoUrl("omnexa_credit_risk") },
		],
		treasury: [
			{ label: t("خزينة", "Treasury"), route: "/app/al-servicing-portal", logoUrl: logoUrl("omnexa_alm") },
			{ label: t("تنفيذي", "Executive"), route: "/app/al-executive-dashboard", logoUrl: logoUrl("omnexa_alm") },
		],
		consumer: [
			{ label: t("استهلاكي", "Consumer"), route: "/app/cf-servicing-portal", logoUrl: logoUrl("omnexa_consumer_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/cf-executive-dashboard", logoUrl: logoUrl("omnexa_consumer_finance") },
		],
		auto: [
			{ label: t("مركبات", "Auto"), route: "/app/vf-servicing-portal", logoUrl: logoUrl("omnexa_vehicle_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/vf-executive-dashboard", logoUrl: logoUrl("omnexa_vehicle_finance") },
		],
		mortgage: [
			{ label: t("رهن", "Mortgage"), route: "/app/mg-servicing-portal", logoUrl: logoUrl("omnexa_mortgage_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/mg-executive-dashboard", logoUrl: logoUrl("omnexa_mortgage_finance") },
		],
		factoring: [
			{ label: t("تخصيم", "Factoring"), route: "/app/fc-servicing-portal", logoUrl: logoUrl("omnexa_factoring") },
			{ label: t("تنفيذي", "Executive"), route: "/app/fc-executive-dashboard", logoUrl: logoUrl("omnexa_factoring") },
		],
		sme: [
			{ label: t("منشآت", "SME"), route: "/app/sr-servicing-portal", logoUrl: logoUrl("omnexa_sme_retail_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/sr-executive-dashboard", logoUrl: logoUrl("omnexa_sme_retail_finance") },
		],
		micro: [
			{ label: t("ميداني", "Field"), route: "/app/mf-servicing-portal", logoUrl: logoUrl("omnexa_sme_microfinance") },
			{ label: t("حالات", "Cases"), route: "List/Microfinance Case", icon: "📋" },
			{ label: t("تنفيذي", "Executive"), route: "/app/mf-executive-dashboard", logoUrl: logoUrl("omnexa_sme_microfinance") },
		],
		leasing: [
			{ label: t("تأجير", "Leasing"), route: "/app/lf-servicing-portal", logoUrl: logoUrl("omnexa_leasing_finance") },
			{ label: t("تنفيذي", "Executive"), route: "/app/lf-executive-dashboard", logoUrl: logoUrl("omnexa_leasing_finance") },
		],
		grc: [
			{ label: t("GRC", "GRC"), route: "/app/or-grc-portal", logoUrl: logoUrl("omnexa_operational_risk") },
			{ label: t("تنفيذي", "Executive"), route: "/app/or-executive-dashboard", logoUrl: logoUrl("omnexa_operational_risk") },
		],
		accounting: [
			{ label: t("محاسبة", "GL"), route: "/app/acct-executive-dashboard", logoUrl: logoUrl("omnexa_accounting") },
			{ label: t("إغلاق", "Close"), route: "/app/accounting-close-dashboard", logoUrl: logoUrl("omnexa_accounting") },
		],
	};

	function defaultSidebar(role, activeRoute) {
		const route = activeRoute || "";
		return (SIDEBARS[role] || SIDEBARS.executive).map((item) => ({
			...item,
			active:
				route &&
				(item.route === route ||
					item.route === `/app/${route.replace(/^\/app\//, "")}` ||
					item.route.replace(/^\/app\//, "") === route.replace(/^\/app\//, "")),
		}));
	}

	function appSidebar(navItems, activeRoute, brandLogo) {
		const route = activeRoute || "";
		return (navItems || []).map((item) => ({
			label: t(item.label_ar, item.label_en),
			route: item.route,
			icon: item.icon || "•",
			logoUrl: item.logo_url || brandLogo || "",
			active:
				route &&
				(item.route === route ||
					item.route === `/app/${route.replace(/^\/app\//, "")}` ||
					(item.route.startsWith("/app/") && route.includes(item.route.replace("/app/", "")))),
		}));
	}

	function progressStepper(steps) {
		let html = `<div class="oj-stepper oj-finance-stepper">`;
		(steps || []).forEach((s, idx) => {
			const st = (s.status || "").toLowerCase();
			const cls =
				st === "completed" || st === "done"
					? "done"
					: st === "in progress" || st === "active"
						? "active"
						: st === "rejected" || st === "returned"
							? "rejected"
							: "";
			const ring =
				cls === "done"
					? "✓"
					: cls === "rejected"
						? "!"
						: s.step || idx + 1;
			html += `<div class="oj-step ${cls}" data-step-key="${esc(s.key || "")}"><div class="oj-step-ring">${ring}</div><div class="oj-step-label">${esc(t(s.label_ar, s.label_en))}</div></div>`;
		});
		html += `</div>`;
		return html;
	}

	function timelinePanel(events) {
		const $panel = $('<div class="oj-timeline"></div>');
		if (!events || !events.length) {
			$panel.append(`<p class="oj-muted">${t("لا سجل زمني", "No timeline yet")}</p>`);
			return $panel;
		}
		events.forEach((ev) => {
			const when = ev.date ? frappe.datetime.str_to_user(ev.date) : "";
			$panel.append(`
				<div class="oj-timeline-item">
					<div class="oj-timeline-dot"></div>
					<div class="oj-timeline-body">
						<strong>${esc(ev.action || t("تحديث", "Update"))}</strong>
						<span class="oj-muted"> — ${esc(ev.user || "")}</span>
						<div class="oj-muted small">${esc(when)}</div>
						${ev.comments ? `<div class="oj-timeline-comment">${esc(ev.comments)}</div>` : ""}
					</div>
				</div>`);
		});
		return $panel;
	}

	function workflowJourneyGrid(steps, onSelect) {
		const $g = $('<div class="oj-workflow-grid"></div>');
		(steps || []).forEach((s) => {
			const $card = $(`
				<div class="oj-workflow-card" data-step="${esc(s.key || "")}">
					<div class="oj-workflow-icon">${esc(s.icon || "•")}</div>
					<div class="oj-workflow-title">${esc(t(s.label_ar, s.label_en))}</div>
					<div class="oj-workflow-role oj-muted">${esc(t(s.role_ar, s.role_en))}</div>
				</div>`);
			$card.on("click", () => onSelect && onSelect(s));
			$g.append($card);
		});
		return $g;
	}

	function registrationWizard({ app, fields, onSuccess }) {
		const $dlg = $(`
			<div class="oj-wizard-panel">
				<h4>${t("تسجيل طلب تمويل جديد", "New Finance Application")}</h4>
				<p class="oj-muted">${t("معالج التسجيل — المرحلة 1 من 12", "Registration wizard — step 1 of 12")}</p>
				<form class="oj-wizard-form"></form>
				<div class="oj-wizard-actions mt-3">
					<button type="button" class="btn btn-primary btn-submit-wizard">${t("تسجيل وإرسال", "Register & Submit")}</button>
					<button type="button" class="btn btn-default btn-cancel-wizard ml-2">${t("إلغاء", "Cancel")}</button>
				</div>
			</div>`);
		const $form = $dlg.find(".oj-wizard-form");
		(fields || []).forEach((f) => {
			$form.append(`
				<div class="form-group">
					<label class="small">${esc(t(f.label_ar, f.label_en))}${f.reqd ? " *" : ""}</label>
					<input class="form-control" name="${esc(f.fieldname)}" type="${f.fieldtype === "Int" ? "number" : "text"}" ${f.reqd ? "required" : ""} />
				</div>`);
		});
		$dlg.find(".btn-cancel-wizard").on("click", () => $dlg.remove());
		$dlg.find(".btn-submit-wizard").on("click", async () => {
			const data = {};
			$form.find("input[name]").each(function () {
				data[$(this).attr("name")] = $(this).val();
			});
			try {
				const out = await call(
					"omnexa_core.omnexa_core.finance_demo.finance_workflow_journey.create_case_from_wizard",
					{ app, data: JSON.stringify(data) }
				);
				frappe.show_alert({ message: t("تم تسجيل الطلب", "Application registered"), indicator: "green" });
				$dlg.remove();
				if (onSuccess) onSuccess(out);
				else if (out.route) frappe.set_route(...out.route.split("/"));
			} catch (e) {
				frappe.msgprint({ title: t("خطأ", "Error"), indicator: "red", message: e.message || String(e) });
			}
		});
		return $dlg;
	}

	function statusBadgeClass(status) {
		const s = (status || "").toLowerCase();
		if (s.includes("approved")) return "oj-badge-green";
		if (s === "rejected") return "oj-badge-red";
		if (s === "pending review" || s === "uploaded") return "oj-badge-blue";
		return "oj-badge-gray";
	}

	function borrowerDocumentsPanel({ caseDoctype, caseName, financeApp }) {
		const $wrap = $(`<div class="oj-borrower-documents"></div>`);
		if (!caseDoctype || !caseName) {
			$wrap.append(
				`<div class="oj-alert oj-alert-info">${t("اختر حالة من الجدول لرفع المستندات.", "Select a case from the table to upload documents.")}</div>`
			);
			return $wrap;
		}

		function renderDocCard(doc) {
			const cap = doc.capture || {};
			const $card = $(`<div class="oj-doc-card" data-doc-name="${esc(doc.name || "")}"></div>`);
			const mandatory = doc.is_mandatory
				? `<span class="oj-badge oj-badge-red">${t("إلزامي", "Mandatory")}</span>`
				: `<span class="oj-badge oj-badge-gray">${t("اختياري", "Optional")}</span>`;
			$card.append(`
				<div class="oj-doc-card-head">
					<div>
						<strong>${esc(t(doc.label_ar, doc.label_en))}</strong>
						<div class="oj-muted small">${esc(doc.document_code || "")}</div>
					</div>
					<div>${mandatory} <span class="oj-badge ${statusBadgeClass(doc.verification_status)}">${esc(doc.verification_status || "")}</span></div>
				</div>`);

			const $meta = $('<div class="oj-doc-meta row"></div>');
			const fields = [];
			if (cap.capture_national_id)
				fields.push(["national_id", t("الرقم القومي", "National ID"), doc.national_id]);
			if (cap.capture_commercial_registration)
				fields.push(["commercial_registration", t("السجل التجاري", "CR"), doc.commercial_registration]);
			if (cap.capture_tax_card) fields.push(["tax_card_number", t("البطاقة الضريبية", "Tax Card"), doc.tax_card_number]);
			if (cap.capture_bank_account) fields.push(["bank_account", t("حساب بنكي", "Bank Account"), doc.bank_account]);
			if (cap.capture_iban) fields.push(["iban", "IBAN", doc.iban]);
			if (cap.capture_issue_date) fields.push(["issue_date", t("تاريخ الإصدار", "Issue Date"), doc.issue_date]);
			if (cap.capture_expiry_date) fields.push(["expiry_date", t("تاريخ الانتهاء", "Expiry"), doc.expiry_date]);

			fields.forEach(([fn, label, val]) => {
				const type = fn.includes("date") ? "date" : "text";
				$meta.append(`
					<div class="col-md-6 form-group">
						<label class="small">${esc(label)}</label>
						<input class="form-control oj-doc-field" data-field="${fn}" type="${type}" value="${esc(val || "")}" />
					</div>`);
			});
			if (fields.length) $card.append($meta);

			const $fileRow = $('<div class="oj-doc-file-row mt-2"></div>');
			if (doc.attachment) {
				$fileRow.append(
					`<a class="btn btn-sm btn-default" href="${esc(doc.attachment_url || doc.attachment)}" target="_blank">${t("عرض الملف", "View File")}</a>`
				);
			} else {
				$fileRow.append(`<span class="oj-muted small">${t("لم يُرفع بعد", "Not uploaded yet")}</span>`);
			}
			$card.append($fileRow);

			const $btns = $('<div class="oj-doc-actions mt-2"></div>');
			const $upload = $(`<button type="button" class="btn btn-sm btn-primary">${t("رفع", "Upload")}</button>`);
			$upload.on("click", () => {
				new frappe.ui.FileUploader({
					doctype: "Finance Borrower Case Document",
					docname: doc.name,
					fieldname: "attachment",
					folder: "Home/Attachments",
					on_success(file) {
						const payload = { name: doc.name, attachment: file.file_url };
						$card.find(".oj-doc-field").each(function () {
							payload[$(this).data("field")] = $(this).val();
						});
						call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.save_case_document", {
							data: JSON.stringify(payload),
						}).then(() => {
							frappe.show_alert({ message: t("تم رفع المستند", "Document uploaded"), indicator: "green" });
							load();
						});
					},
				});
			});
			$btns.append($upload);

			const $save = $(`<button type="button" class="btn btn-sm btn-default ml-1">${t("حفظ البيانات", "Save Metadata")}</button>`);
			$save.on("click", () => {
				const payload = { name: doc.name, attachment: doc.attachment || undefined };
				$card.find(".oj-doc-field").each(function () {
					payload[$(this).data("field")] = $(this).val();
				});
				call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.save_case_document", {
					data: JSON.stringify(payload),
				}).then(() => frappe.show_alert({ message: t("تم الحفظ", "Saved"), indicator: "green" }));
			});
			$btns.append($save);

			if (doc.name) {
				const dossier = window.omnexa_finance && omnexa_finance.dossier;
				const $printPdf = $(
					`<button type="button" class="btn btn-sm btn-default ml-1 btn-print-doc-pdf" aria-label="${t("PDF", "PDF")}">${t("PDF", "PDF")}</button>`
				);
				$printPdf.on("click", () => {
					if (dossier && dossier.printDocument) dossier.printDocument(doc.name);
				});
				const $print = $(
					`<button type="button" class="btn btn-sm btn-default ml-1 btn-print-doc" aria-label="${t("طباعة", "Print")}">${t("طباعة", "Print")}</button>`
				);
				$print.on("click", () => {
					if (dossier && dossier.printDocumentPreview) dossier.printDocumentPreview(doc.name);
					else if (dossier && dossier.printDocument) dossier.printDocument(doc.name);
				});
				$btns.append($printPdf, $print);
			}
			if (doc.name && doc.attachment) {
				const $eap = $(`<button type="button" class="btn btn-sm btn-success ml-1">${t("اعتماد إلكتروني", "E-Approve")}</button>`);
				$eap.on("click", () =>
					call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.approve_document_electronic", {
						name: doc.name,
					}).then(() => load())
				);
				const $pap = $(`<button type="button" class="btn btn-sm btn-success ml-1">${t("اعتماد ورقي", "Paper Approve")}</button>`);
				$pap.on("click", () =>
					call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.approve_document_paper", {
						name: doc.name,
					}).then(() => load())
				);
				const $rej = $(`<button type="button" class="btn btn-sm btn-danger ml-1">${t("رفض", "Reject")}</button>`);
				$rej.on("click", () => {
					frappe.prompt(
						{ fieldname: "reason", label: t("سبب الرفض", "Rejection Reason"), fieldtype: "Small Text", reqd: 1 },
						(v) =>
							call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.reject_case_document", {
								name: doc.name,
								reason: v.reason,
							}).then(() => load())
					);
				});
				$btns.append($eap, $pap, $rej);
			}
			$card.append($btns);
			return $card;
		}

		function load() {
			$wrap.html(loading());
			call("omnexa_core.omnexa_core.finance_demo.finance_borrower_documents.get_case_documents", {
				case_doctype: caseDoctype,
				case_name: caseName,
				finance_app: financeApp,
			})
				.then((payload) => {
					$wrap.empty();
					const s = payload.summary || {};
					$wrap.append(`
						<div class="oj-doc-summary mb-3">
							<span class="oj-badge oj-badge-blue">${t("إجمالي", "Total")}: ${s.total || 0}</span>
							<span class="oj-badge oj-badge-red ml-1">${t("إلزامي", "Mandatory")}: ${s.mandatory_uploaded || 0}/${s.mandatory_total || 0}</span>
							<span class="oj-badge oj-badge-green ml-1">${t("معتمد", "Approved")}: ${s.approved || 0}</span>
						</div>`);
					const $list = $('<div class="oj-doc-list"></div>');
					(payload.documents || []).forEach((doc) => $list.append(renderDocCard(doc)));
					$wrap.append($list);
					$wrap.append(
						`<p class="oj-muted small mt-2">${t("إضافة أنواع مستندات من: Finance Borrower Document Settings", "Add document types via Finance Borrower Document Settings")}</p>`
					);
				})
				.catch((e) => $wrap.html(`<p class="text-danger">${esc(e.message || String(e))}</p>`));
		}

		load();
		return $wrap;
	}

	function workflowStageScreen({ screen, workflowSteps, onAction, onStepSelect }) {
		const step = screen.step || {};
		const $panel = $(`<div class="oj-stage-screen"></div>`);
		$panel.append(`<h4 class="oj-section-title">${esc(t(step.label_ar, step.label_en))}</h4>`);
		$panel.append(`<p class="oj-muted oj-stage-desc">${esc(t(screen.desc_ar, screen.desc_en))}</p>`);
		$panel.append(
			`<div class="oj-stage-role oj-muted">${t("المسؤول", "Responsible")}: <strong>${esc(t(step.role_ar, step.role_en))}</strong></div>`
		);

		if (screen.case && screen.case.name) {
			$panel.append(
				`<div class="oj-stage-case-badge">${t("الحالة", "Case")}: <strong>${esc(screen.case.name)}</strong> · ${esc(screen.case.workflow_state || "")}</div>`
			);
		} else if (screen.case_doctype) {
			$panel.append(
				`<div class="oj-alert oj-alert-info">${t("اختر حالة من الجدول أدناه أو أنشئ طلباً جديداً.", "Select a case from the table below or create a new application.")}</div>`
			);
		}

		if (screen.screen_type === "documents") {
			$panel.append(
				borrowerDocumentsPanel({
					caseDoctype: screen.case_doctype,
					caseName: screen.case && screen.case.name,
					financeApp: screen.app,
				})
			);
		}

		if (screen.case && screen.case.name && screen.case_doctype) {
			const $c360 = $(`<div class="oj-customer-360-slot mt-2" role="region" aria-label="${t("عميل 360", "Customer 360")}"></div>`);
			$panel.append($c360);
			call("omnexa_core.omnexa_core.finance_demo.finance_wave6_global_leader.get_finance_customer_360", {
				case_doctype: screen.case_doctype,
				case_name: screen.case.name,
			})
				.then((payload) => {
					const cust = (payload && payload.customer) || {};
					const docs = (payload && payload.documents_summary) || {};
					let html = `<div class="oj-alert oj-alert-info oj-customer-360"><strong>${t("عميل 360", "Customer 360")}</strong>`;
					if (cust.customer_link) {
						html += ` · <a href="${esc(cust.customer_link)}">${esc(cust.customer || "")}</a>`;
					} else {
						html += ` · ${esc(cust.customer || t("—", "—"))}`;
					}
					html += `<br/><small>${t("مستندات", "Documents")}: ${docs.approved || 0}/${docs.total || 0} ${t("معتمد", "approved")}</small></div>`;
					$c360.html(html);
				})
				.catch(() => $c360.remove());
		}

		if (screen.metrics && screen.metrics.length) {
			const $m = $('<div class="oj-kpi-row oj-stage-metrics"></div>');
			screen.metrics.forEach((m) => {
				$m.append(
					`<div class="oj-kpi-card"><div class="oj-kpi-value">${esc(m.value ?? "—")}</div><div class="oj-kpi-label">${esc(t(m.label_ar, m.label_en))}</div></div>`
				);
			});
			$panel.append($m);
		}

		if (screen.checklist && screen.checklist.length) {
			const $cl = $('<div class="oj-stage-checklist"></div>');
			screen.checklist.forEach((item, idx) => {
				$cl.append(`
					<label class="oj-check-item">
						<input type="checkbox" checked data-check-id="${esc(item.id || idx)}" />
						<span>${esc(t(item.label_ar, item.label_en))}</span>
						<span class="oj-badge oj-badge-green">${t("مكتمل", "Complete")}</span>
					</label>`);
			});
			$panel.append($cl);
		}

		if (screen.fields && screen.fields.length) {
			const $form = $('<div class="oj-stage-form row"></div>');
			screen.fields.forEach((f) => {
				const val =
					(screen.case && screen.case[f.fieldname]) ||
					(f.fieldname === "amount" && screen.case && screen.case.principal) ||
					"";
				$form.append(`
					<div class="col-md-6 form-group">
						<label class="small">${esc(t(f.label_ar, f.label_en))}</label>
						<input class="form-control" name="${esc(f.fieldname)}" value="${esc(val)}" />
					</div>`);
			});
			$panel.append($form);
		}

		if (screen.decisions && screen.decisions.length) {
			const $d = $('<div class="oj-stage-decisions"></div>');
			screen.decisions.forEach((d, idx) => {
				$d.append(`
					<label class="oj-radio-item">
						<input type="radio" name="oj-stage-decision" value="${esc(d.value)}" ${idx === 0 ? "checked" : ""} />
						<span>${esc(t(d.label_ar, d.label_en))}</span>
					</label>`);
			});
			$panel.append($d);
		}

		if (screen.table_cols && screen.table_rows) {
			const cols = screen.table_cols.map(([field, ar, en]) => ({ field, label: t(ar, en) }));
			$panel.append(dataTable(cols, screen.table_rows));
		}

		const $actions = $('<div class="oj-stage-actions mt-3"></div>');
		(screen.actions || []).forEach((act) => {
			const cls = act.primary ? "btn btn-primary" : "btn btn-default ml-2";
			const $btn = $(`<button type="button" class="${cls}" data-action="${esc(act.key)}">${esc(t(act.label_ar, act.label_en))}</button>`);
			$btn.on("click", () => onAction && onAction(act.key, screen));
			$actions.append($btn);
		});
		$panel.append($actions);

		return $panel;
	}

	function caseTrackerPanel(doctype, name) {
		const $wrap = $(`<div class="oj-case-tracker">${loading()}</div>`);
		call("omnexa_core.omnexa_core.finance_demo.finance_workflow_journey.get_case_journey_detail", {
			doctype,
			name,
		})
			.then((tracker) => {
				$wrap.empty();
				$wrap.append(`<h4 class="oj-section-title">${t("تتبع الحالة", "Case Tracking")}: ${esc(name)}</h4>`);
				$wrap.append(
					`<div class="oj-case-meta oj-muted mb-2">${t("المرحلة", "Stage")}: <strong>${esc(tracker.current_stage || "")}</strong> · ${t("الحالة", "Status")}: ${esc(tracker.approval_status || "")}</div>`
				);
				$wrap.append(`<h5 class="oj-section-title">${t("السجل الزمني", "Audit Timeline")}</h5>`);
				$wrap.append(timelinePanel(tracker.timeline || []));
				$wrap.append(
					`<button type="button" class="btn btn-sm btn-default mt-2 btn-open-case">${t("فتح السجل", "Open Record")}</button>`
				);
				const $row = $('<div class="mt-2 oj-case-export-btns"></div>');
				const $pdf = $(`<button type="button" class="btn btn-sm btn-primary mr-1">${t("PDF", "PDF")}</button>`);
				const $print = $(`<button type="button" class="btn btn-sm btn-default mr-1">${t("طباعة", "Print")}</button>`);
				function bindDossier() {
					const d = window.omnexa_finance && omnexa_finance.dossier;
					if (!d) return false;
					$pdf.off("click").on("click", () => d.downloadPdf(doctype, name));
					$print.off("click").on("click", () => d.printPreview(doctype, name));
					return true;
				}
				$row.append($pdf, $print);
				$wrap.append($row);
				if (!bindDossier()) {
					frappe.require(["/assets/omnexa_core/js/finance_borrower_dossier.js"], bindDossier);
				}
				$wrap.find(".btn-open-case").on("click", () => frappe.set_route("Form", doctype, name));
			})
			.catch((e) => {
				$wrap.html(`<p class="text-danger">${esc(e.message || String(e))}</p>`);
			});
		return $wrap;
	}

	function portalCategoryGrid(groups) {
		const $root = $('<div class="oj-portal-catalog oj-finance-workcenter-portals"></div>');
		(groups || []).forEach((g) => {
			const title = lang() === "ar" ? g.label_ar : g.label_en;
			const $sec = $(`<div class="oj-portal-section"><h4 class="oj-portal-cat-title">${esc(title)}</h4></div>`);
			const portals = (g.portals || []).map((p) => ({
				id: p.id,
				name: lang() === "ar" ? p.label_ar : p.label_en,
				subtitle: p.page || "",
				logoUrl: p.logo_url || (p.app ? logoUrl(p.app) : ""),
				route: p.route,
				disabled: p.exists === false,
			}));
			const $grid = portalCardGrid(portals, (c) => {
				if (c.route) window.location.href = c.route;
			});
			$sec.append($grid);
			$root.append($sec);
		});
		return $root;
	}

	window.OmnexaFinanceJourney = {
		lang,
		t,
		esc,
		call,
		mountDeskPage,
		shell,
		dataTable,
		linkGrid,
		portalCardGrid,
		loading,
		logoUrl,
		defaultSidebar,
		appSidebar,
		progressStepper,
		timelinePanel,
		workflowJourneyGrid,
		workflowStageScreen,
		borrowerDocumentsPanel,
		registrationWizard,
		caseTrackerPanel,
		portalCategoryGrid,
	};
})(window);
