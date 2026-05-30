// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt
// All Company demo actions in one file (works even if sector app doctype_js fails to load).

frappe.provide("erpgenex.company_demo");

erpgenex.company_demo._esc = function _esc(text) {
		const t = text == null ? "" : String(text);
		if (frappe.utils && typeof frappe.utils.escape_html === "function") {
			return frappe.utils.escape_html(t);
		}
		return t
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	};

erpgenex.company_demo._has_app = function _has_app(app_name) {
	let apps = frappe.boot?.erpgenex_installed_apps;
	if (!apps || !apps.length) {
		apps = frappe.boot?.versions ? Object.keys(frappe.boot.versions) : [];
	}
	if (!apps || !apps.length) {
		// Before re-login after migrate: show actions; server validates on call.
		return true;
	}
	return apps.includes(app_name);
};

	erpgenex.company_demo.add_action = function add_action(frm, group, label, action, opts = {}) {
		if (!frm.__demo_action_groups) {
			frm.__demo_action_groups = {};
		}
		const key = group || __("Demo");
		if (!frm.__demo_action_groups[key]) {
			frm.__demo_action_groups[key] = [];
		}
		frm.__demo_action_groups[key].push({
			label,
			action: typeof action === "function" ? action : () => {},
			danger: !!opts.danger,
		});
	};

	erpgenex.company_demo.can_manage = function can_manage_demo(frm) {
		return (
			!frm.is_new() &&
			(frappe.user.has_role("System Manager") || frappe.session.user === "Administrator")
		);
	};

	erpgenex.company_demo._get_mount = function _get_mount(frm) {
		let $host = frm.wrapper.find("#erpgenex-demo-action-mount");
		if ($host.length) {
			return $host.first();
		}
		const field = frm.fields_dict?.demo_data_help;
		if (field?.$wrapper) {
			$host = field.$wrapper.find("#erpgenex-demo-action-mount");
			if ($host.length) {
				return $host.first();
			}
			$host = $('<div id="erpgenex-demo-action-mount" class="erpgenex-demo-action-panel"></div>');
			field.$wrapper.append($host);
			return $host;
		}
		return $();
	};

	erpgenex.company_demo._run = async function _run(method, args, freeze_message) {
		try {
			const r = await frappe.call({
				method,
				args,
				freeze: true,
				freeze_message,
			});
			const out = r.message || {};
			frappe.show_alert({
				indicator: out.ok !== false ? "green" : "orange",
				message: `${freeze_message}: ${out.log_id || __("OK")}`,
			});
			return out;
		} catch (e) {
			let serverMessage = null;
			try {
				const raw = e?._server_messages;
				if (raw) {
					const arr = JSON.parse(raw);
					if (Array.isArray(arr) && arr.length) {
						const first = JSON.parse(arr[0] || "{}");
						serverMessage = first.message || null;
					}
				}
			} catch {
				serverMessage = null;
			}
			frappe.msgprint({
				title: __("Error"),
				message: serverMessage || e?.message || __("Unexpected server error. Check Error Log."),
				indicator: "red",
			});
			throw e;
		}
	};

	erpgenex.company_demo.populate_actions = function populate_actions(frm) {
		const company = frm.doc.name;
		const branch = () => {
			const v = (frm.doc.production_demo_branch || "").trim();
			return v || null;
		};
		const activity = () => {
			const v = (frm.doc.production_demo_activity || frm.doc.industry_sector || "").trim();
			return v || null;
		};
		const add = (group, label, fn, opts) =>
			erpgenex.company_demo.add_action(frm, group, label, fn, opts);

		if (erpgenex.company_demo._has_app("omnexa_accounting")) {
			const prod = __("Production demo");
			const ifrs = __("IFRS defaults");

			add(
				prod,
				__("Generate professional COA"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.production_readiness.generate_professional_chart_of_accounts",
						{ company, branch: branch(), activity: activity() },
						__("Generate professional COA"),
					),
			);
			add(
				ifrs,
				__("Fill default GLs from CoA (by account number)"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.company_financial_defaults.fill_company_financial_defaults_from_coa",
						{ company, branch: branch(), overwrite: 0 },
						__("Fill default GLs from CoA"),
					),
			);
			add(
				prod,
				__("Resync COA labels (names from template)"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.production_readiness.resync_chart_of_accounts_labels",
						{ company, branch: branch(), activity: activity() },
						__("Resync COA labels"),
					),
			);
			add(
				prod,
				__("Seed demo data (masters)"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.production_readiness.seed_activity_demo_data",
						{
							company,
							branch: branch(),
							activity: activity(),
							include_transactions: 0,
						},
						__("Seed demo data"),
					),
			);
			add(
				prod,
				__("Seed demo data + transactions"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.production_readiness.seed_activity_demo_data",
						{
							company,
							branch: branch(),
							activity: activity(),
							include_transactions: 1,
						},
						__("Seed demo data + transactions"),
					),
			);
			add(
				prod,
				__("Reset transactions (dry run)"),
				() =>
					erpgenex.company_demo._run(
						"omnexa_accounting.utils.production_readiness.reset_transactions",
						{ company, branch: branch(), dry_run: 1 },
						__("Reset transactions (dry run)"),
					),
			);
			add(
				prod,
				__("Reset transactions (execute)"),
				() => {
					frappe.confirm(
						__(
							"This will cancel and delete matched transactions for this company (and branch if set). Continue?",
						),
						() =>
							erpgenex.company_demo._run(
								"omnexa_accounting.utils.production_readiness.enqueue_reset_transactions",
								{ company, branch: branch(), limit: 0, batch_size: 200 },
								__("Reset transactions queued"),
							),
						() => {},
					);
				},
			);

			if (frappe.session.user === "Administrator") {
				add(
					__("Danger Zone"),
					__("Delete ALL company data (DANGER)"),
					async () => {
						const values = await new Promise((resolve) => {
							frappe.prompt(
								[
									{
										fieldname: "confirm_text",
										fieldtype: "Data",
										label: __("Type DELETE ALL to confirm"),
										reqd: 1,
									},
								],
								(v) => resolve(v || null),
								__("Full Company Wipe"),
								__("Execute"),
							);
						});
						if (!values?.confirm_text) return;
						await erpgenex.company_demo._run(
							"omnexa_accounting.utils.production_readiness.wipe_company_all_data",
							{
								company,
								branch: branch(),
								confirm_text: values.confirm_text,
							},
							__("Full company wipe"),
						);
					},
					{ danger: true },
				);
			}
		}

		if (erpgenex.company_demo._has_app("omnexa_construction")) {
			add(
				__("Construction demo"),
				__("Seed 5 projects (owners, IPC, subcontractors, costs)"),
				() => {
					frappe.confirm(
						__(
							"Creates five demo project contracts with clients, subcontractors, BOQ, IPC certificates, site diaries, and WIP. Continue?",
						),
						() => {
							frappe.call({
								method: "omnexa_construction.api.seed_construction_demo_from_company",
								args: {
									company: frm.doc.name,
									branch: branch(),
									force: 0,
								},
								freeze: true,
								freeze_message: __("Seeding construction demo portfolio..."),
								callback(r) {
									const m = r.message || {};
									if (m.skipped) {
										frappe.msgprint({
											title: __("Already seeded"),
											indicator: "blue",
											message:
												m.message ||
												__("Construction demo data already exists for this company."),
										});
										return;
									}
									frappe.msgprint({
										title: __("Construction demo ready"),
										indicator: "green",
										message: m.message || __("Done."),
									});
								},
							});
						},
					);
				},
			);
		}

		if (erpgenex.company_demo._has_app("omnexa_fixed_assets")) {
			add(
				__("أصول الفنادق — تجريبي"),
				__("إنشاء 50 أصلًا (غرف + مناطق إدارية + حركات)"),
				() => {
					frappe.confirm(
						__(
							"سيتم إنشاء فندقًا تجريبيًا وغرفًا وعدد 50 أصلًا مع رسملة، وتحويلات فندقية، وسجلات RFID. المتابعة؟",
						),
						() => {
							frappe.call({
								method: "omnexa_fixed_assets.api.seed_hotel_demo_assets_from_company",
								args: {
									company: frm.doc.name,
									count: 50,
									with_transfer: 1,
									with_rfid: 1,
								},
								freeze: true,
								freeze_message: __("جاري إنشاء البيانات التجريبية..."),
								callback(r) {
									const m = r.message || {};
									frappe.msgprint({
										title: __("تم"),
										indicator: "green",
										message: `تم إنشاء ${m.created_count ?? 0} أصلًا تجريبيًا. الفندق: ${
											m.hotel_property || "—"
										}`,
									});
								},
							});
						},
					);
				},
			);
		}
	};

	erpgenex.company_demo.refresh_panel = function refresh_panel(frm) {
		if (!frm || frm.doctype !== "Company") {
			return;
		}

		const $host = erpgenex.company_demo._get_mount(frm);
		if (!$host.length) {
			return;
		}

		$host.removeClass("hide").show().css("display", "block");

		if (!erpgenex.company_demo.can_manage(frm)) {
			$host.html(
				`<p class="text-muted small">${__(
					"Save the company first. Demo seeding requires the System Manager role.",
				)}</p>`,
			);
			return;
		}

		frm.__demo_action_groups = {};
		erpgenex.company_demo.populate_actions(frm);

		const groups = frm.__demo_action_groups || {};
		const groupNames = Object.keys(groups);
		$host.empty();

		if (!groupNames.length) {
			const apps = (frappe.boot?.erpgenex_installed_apps || []).join(", ") || __("unknown");
			$host.html(
				`<p class="text-muted small">${__(
					"No demo apps detected on this site. Installed apps:",
				)} ${erpgenex.company_demo._esc(apps)}. ${__(
					"Install omnexa_accounting (and related apps), then bench build and clear-cache.",
				)}</p>`,
			);
			return;
		}

		for (const group of groupNames) {
			const $section = $(`
				<div class="erpgenex-demo-group">
					<div class="erpgenex-demo-group-title">${erpgenex.company_demo._esc(group)}</div>
					<div class="erpgenex-demo-btns"></div>
				</div>
			`);
			const $btns = $section.find(".erpgenex-demo-btns");
			for (const row of groups[group]) {
				const btnClass = row.danger ? "btn-danger" : "btn-primary";
				const $btn = $(
					`<button type="button" class="btn ${btnClass} btn-sm erpgenex-demo-btn">${erpgenex.company_demo._esc(
						row.label,
					)}</button>`,
				);
				$btn.on("click", (e) => {
					e.preventDefault();
					row.action();
				});
				$btns.append($btn);
			}
			$host.append($section);
		}
	};

	erpgenex.company_demo.schedule_refresh = function schedule_refresh(frm) {
		if (!frm) {
			return;
		}
		erpgenex.company_demo.refresh_panel(frm);
		setTimeout(() => erpgenex.company_demo.refresh_panel(frm), 200);
		setTimeout(() => erpgenex.company_demo.refresh_panel(frm), 800);
	};

	erpgenex.company_demo.setup_company_queries = function setup_company_queries(frm) {
		if (frm.is_new() || !frappe.user.has_role("System Manager")) {
			return;
		}
		frm.set_query("production_demo_branch", () => ({
			filters: { company: frm.doc.name },
		}));
		const companyGlDefaultFields = [
			"default_petty_cash_gl",
			"default_bank_operating_gl",
			"default_receivable_gl",
			"default_inventory_gl",
			"default_advance_to_supplier_gl",
			"default_input_vat_gl",
			"default_other_receivable_gl",
			"default_trade_payable_gl",
			"default_output_vat_gl",
			"default_customer_advances_gl",
			"default_share_capital_gl",
			"default_retained_earnings_gl",
			"default_sales_revenue_gl",
			"default_service_revenue_gl",
			"default_cogs_gl",
			"default_opex_gl",
			"default_finance_cost_gl",
		];
		companyGlDefaultFields.forEach((fieldname) => {
			frm.set_query(fieldname, () => ({ filters: { company: frm.doc.name } }));
		});
	};

if (!erpgenex.company_demo._form_bound) {
	erpgenex.company_demo._form_bound = true;
	frappe.ui.form.on("Company", {
		refresh(frm) {
			erpgenex.company_demo.setup_company_queries(frm);
			erpgenex.company_demo.schedule_refresh(frm);
		},
	});
}
