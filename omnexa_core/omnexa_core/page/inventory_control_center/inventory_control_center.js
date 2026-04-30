frappe.pages["inventory-control-center"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Inventory Control Center"),
		single_column: true,
	});

	const $body = $(`
		<div class="inventory-control-center">
			<div class="mb-3 text-muted">
				${__("Central inventory actions for reorder and stock analytics.")}
			</div>
			<div class="row mb-3">
				<div class="col-md-4" data-field="company"></div>
				<div class="col-md-4" data-field="branch"></div>
				<div class="col-md-2" data-field="limit"></div>
				<div class="col-md-2 d-flex align-items-end">
					<button class="btn btn-primary w-100" data-action="generate-pr">${__("Generate Reorder PR")}</button>
				</div>
			</div>
			<div class="mb-3">
				<button class="btn btn-default" data-action="open-kpi">${__("Open Inventory KPI Dashboard")}</button>
				<button class="btn btn-default ms-2" data-action="open-low-stock">${__("Open Low Stock Report")}</button>
			</div>
			<div class="small text-muted" data-section="status"></div>
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
	const branchField = frappe.ui.form.make_control({
		parent: $body.find('[data-field="branch"]'),
		df: {
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			default: frappe.defaults.get_user_default("Branch") || "",
		},
		render_input: true,
	});
	const limitField = frappe.ui.form.make_control({
		parent: $body.find('[data-field="limit"]'),
		df: {
			fieldname: "limit",
			label: __("Max Items"),
			fieldtype: "Int",
			default: 200,
		},
		render_input: true,
	});

	$body.on("click", '[data-action="generate-pr"]', async () => {
		const company = companyField.get_value();
		if (!company) {
			frappe.msgprint(__("Company is required."));
			return;
		}
		const branch = branchField.get_value();
		const limit = limitField.get_value() || 200;
		const r = await frappe.call({
			method: "omnexa_core.omnexa_core.inventory.api.create_purchase_request_from_reorder",
			args: { company, branch, limit, min_suggested_qty: 0.0001 },
			freeze: true,
			freeze_message: __("Generating Purchase Request from reorder suggestions..."),
		});
		const msg = r?.message || {};
		if (msg.created) {
			$body.find('[data-section="status"]').text(__("Purchase Request created: {0}", [msg.created]));
			frappe.show_alert({ message: __("Created: {0}", [msg.created]), indicator: "green" });
			return;
		}
		$body.find('[data-section="status"]').text(msg.skipped || __("No document created."));
		frappe.msgprint(__(msg.skipped || "No document created."));
	});

	$body.on("click", '[data-action="open-kpi"]', () => {
		frappe.set_route("query-report", "Inventory KPI Dashboard", {
			company: companyField.get_value(),
		});
	});
	$body.on("click", '[data-action="open-low-stock"]', () => {
		frappe.set_route("query-report", "Low Stock", {
			company: companyField.get_value(),
		});
	});
};

