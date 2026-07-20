frappe.pages["finance-control-center"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Finance Control Center"),
		single_column: true,
	});

	const $body = $(`
		<div class="finance-control-center">
			<div class="mb-3 text-muted">${__("Central controls for GL, banking, and reconciliation oversight.")}</div>
			<div class="row mb-3">
				<div class="col-md-4" data-field="company"></div>
				<div class="col-md-4" data-field="bank_account"></div>
				<div class="col-md-4 d-flex align-items-end">
					<button class="btn btn-primary w-100" data-action="open-rec-suggestions">${__("Open Reconciliation Suggestions")}</button>
				</div>
			</div>
			<div class="row mb-3">
				<div class="col-md-8" data-field="bank_statement_import"></div>
				<div class="col-md-4 d-flex align-items-end">
					<button class="btn btn-warning w-100" data-action="auto-match-import">${__("Auto-Match Statement Import")}</button>
				</div>
			</div>
			<div class="mb-2">
				<button class="btn btn-default" data-action="open-trial">${__("Open Trial Balance")}</button>
				<button class="btn btn-default ms-2" data-action="open-gl">${__("Open General Ledger")}</button>
				<button class="btn btn-default ms-2" data-action="open-bank-balance">${__("Open Bank Balance Summary")}</button>
			</div>
		</div>
	`);
	$(page.body).append($body);

	const companyField = frappe.ui.form.make_control({
		parent: $body.find('[data-field="company"]'),
		df: {
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company") || "",
		},
		render_input: true,
	});

	const bankField = frappe.ui.form.make_control({
		parent: $body.find('[data-field="bank_account"]'),
		df: {
			fieldname: "bank_account",
			label: __("Bank Account"),
			fieldtype: "Link",
			options: "Bank Account",
		},
		render_input: true,
	});
	const importField = frappe.ui.form.make_control({
		parent: $body.find('[data-field="bank_statement_import"]'),
		df: {
			fieldname: "bank_statement_import",
			label: __("Bank Statement Import"),
			fieldtype: "Link",
			options: "Bank Statement Import",
		},
		render_input: true,
	});

	$body.on("click", '[data-action="open-rec-suggestions"]', () => {
		frappe.set_route("query-report", "Bank Reconciliation Suggestions", {
			company: companyField.get_value(),
			bank_account: bankField.get_value(),
		});
	});
	$body.on("click", '[data-action="open-trial"]', () => {
		frappe.set_route("query-report", "Trial Balance", { company: companyField.get_value() });
	});
	$body.on("click", '[data-action="open-gl"]', () => {
		frappe.set_route("query-report", "General Ledger", { company: companyField.get_value() });
	});
	$body.on("click", '[data-action="open-bank-balance"]', () => {
		frappe.set_route("query-report", "Bank Balance Summary", { company: companyField.get_value() });
	});
	$body.on("click", '[data-action="auto-match-import"]', async () => {
		const name = importField.get_value();
		if (!name) {
			frappe.msgprint(__("Select Bank Statement Import first."));
			return;
		}
		const r = await frappe.call({
			method: "omnexa_core.omnexa_core.finance.api.auto_match_bank_statement_import",
			args: { bank_statement_import: name },
			freeze: true,
			freeze_message: __("Auto-matching bank statement lines..."),
		});
		const msg = r?.message || {};
		frappe.msgprint(__("Matched {0} of {1} lines.", [msg.matched || 0, msg.total || 0]));
	});
};

