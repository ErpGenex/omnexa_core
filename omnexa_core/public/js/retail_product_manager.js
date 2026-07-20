frappe.provide("omnexa_core.retail_product_manager");

omnexa_core.retail_product_manager = {
	API: "omnexa_core.omnexa_core.retail_item_manager",
	TYPES: [
		{ key: "Product", label: __("Products") },
		{ key: "Service", label: __("Services") },
		{ key: "Raw Material", label: __("Raw Materials") },
		{ key: "Consumable", label: __("Consumables") },
		{ key: "Bundle", label: __("Bundles") },
	],
	FORM_TABS: [
		{ key: "basic", label: __("Basic") },
		{ key: "sales", label: __("Sales") },
		{ key: "purchase", label: __("Purchase") },
		{ key: "inventory", label: __("Inventory & Warehouses") },
		{ key: "accounts", label: __("Accounts & Costing") },
		{ key: "manufacturing", label: __("Manufacturing") },
	],

	init(pos) {
		this.pos = pos;
		this.state = { type: "Product", search: "", items: [], editing: null, formTab: "basic" };
		this.mount();
		this.bind();
	},

	mount() {
		const html = `
			<div class="retail-prod-panel" id="retail-prod-panel">
				<div class="retail-prod-panel__head">
					<div class="retail-prod-panel__title">${__("Product Management")}</div>
					<button class="btn btn-sm btn-default" id="retail-prod-close">${__("Back to POS")}</button>
				</div>
				<div class="retail-prod-panel__tabs" id="retail-prod-tabs"></div>
				<div class="retail-prod-panel__toolbar">
					<input class="retail-prod-panel__search" id="retail-prod-search" placeholder="${__("Search products...")}">
					<button class="retail-prod-panel__add" id="retail-prod-add">${__("Add New")}</button>
				</div>
				<div class="retail-prod-panel__body" id="retail-prod-body"></div>
			</div>
			<div class="retail-prod-modal-backdrop" id="retail-prod-modal">
				<div class="retail-prod-modal">
					<h4 id="retail-prod-modal-title">${__("Item")}</h4>
					<div class="retail-prod-form-tabs" id="retail-prod-form-tabs"></div>
					<div class="retail-prod-form-panels" id="retail-prod-form-panels"></div>
					<div class="retail-prod-modal__foot">
						<button class="retail-prod-modal__cancel" id="retail-prod-cancel">${__("Cancel")}</button>
						<button class="retail-prod-modal__save" id="retail-prod-save">${__("Save")}</button>
					</div>
				</div>
			</div>`;
		this.pos.$root.find(".retail-pos__main").append(html);
		this.$panel = this.pos.$root.find("#retail-prod-panel");
		this.$modal = this.pos.$root.find("#retail-prod-modal");
		this.render_type_tabs();
	},

	bind() {
		const self = this;
		this.pos.$root.on("click", "#retail-prod-close", () => this.close());
		this.pos.$root.on("click", ".retail-prod-tab", function () {
			self.state.type = $(this).data("type");
			self.render_type_tabs();
			self.load();
		});
		this.pos.$root.on("input", "#retail-prod-search", function () {
			self.state.search = $(this).val() || "";
			self.load();
		});
		this.pos.$root.on("click", "#retail-prod-add", () => self.open_form());
		this.pos.$root.on("click", "#retail-prod-cancel", () => self.$modal.removeClass("is-open"));
		this.pos.$root.on("click", "#retail-prod-save", () => self.save_form());
		this.pos.$root.on("click", ".retail-prod-edit", function () {
			self.open_form($(this).data("name"));
		});
		this.pos.$root.on("click", ".retail-prod-toggle", function () {
			frappe.call({
				method: `${self.API}.toggle_retail_item_active`,
				args: { name: $(this).data("name"), disabled: $(this).data("disabled") ? 0 : 1 },
				callback: () => {
					self.load();
					self.pos.bootstrap();
				},
			});
		});
		this.pos.$root.on("click", ".retail-prod-form-tab", function () {
			self.state.formTab = $(this).data("tab");
			self.render_form_tabs();
		});
	},

	open() {
		this.$panel.addClass("is-open");
		this.load();
	},

	close() {
		this.$panel.removeClass("is-open");
		this.pos.bootstrap();
	},

	render_type_tabs() {
		const html = this.TYPES.map(
			(t) =>
				`<button class="retail-prod-tab ${this.state.type === t.key ? "is-active" : ""}" data-type="${t.key}">${t.label}</button>`
		).join("");
		this.pos.$root.find("#retail-prod-tabs").html(html);
	},

	load() {
		frappe.call({
			method: `${this.API}.get_retail_items_for_manager`,
			args: { product_type: this.state.type, search: this.state.search || null },
			callback: (r) => {
				this.state.items = r.message || [];
				this.render_table();
			},
		});
	},

	render_table() {
		const currency = frappe.defaults.get_default("currency");
		const rows = (this.state.items || [])
			.map(
				(item) => `
			<tr>
				<td>${frappe.utils.escape_html(item.item_name || "")}</td>
				<td>${frappe.utils.escape_html(item.item_code || "")}</td>
				<td>${frappe.utils.escape_html(item.barcode || "—")}</td>
				<td>${format_currency(item.standard_selling_rate || 0, currency, 2)}</td>
				<td>${item.disabled ? __("Disabled") : __("Active")}</td>
				<td>
					<button class="btn btn-xs btn-default retail-prod-edit" data-name="${item.name}">${__("Edit")}</button>
					<button class="btn btn-xs ${item.disabled ? "btn-success" : "btn-danger"} retail-prod-toggle" data-name="${item.name}" data-disabled="${item.disabled ? 1 : 0}">${item.disabled ? __("Enable") : __("Disable")}</button>
				</td>
			</tr>`
			)
			.join("");
		this.pos.$root.find("#retail-prod-body").html(`
			<table class="retail-prod-table">
				<thead><tr><th>${__("Name")}</th><th>${__("Code")}</th><th>${__("Barcode")}</th><th>${__("Price")}</th><th>${__("Status")}</th><th></th></tr></thead>
				<tbody>${rows || `<tr><td colspan="6" class="text-center text-muted">${__("No products found.")}</td></tr>`}</tbody>
			</table>`);
	},

	open_form(name) {
		if (!name) {
			this.state.editing = { product_type: this._type_to_product(this.state.type) };
			this.state.formTab = "basic";
			this.render_item_form(this.state.editing);
			this.$modal.addClass("is-open");
			return;
		}
		frappe.call({
			method: `${this.API}.get_retail_item_detail`,
			args: { name },
			callback: (r) => {
				this.state.editing = r.message || {};
				this.state.formTab = "basic";
				this.render_item_form(this.state.editing);
				this.$modal.addClass("is-open");
			},
		});
	},

	_type_to_product(type) {
		const map = { Product: "Traditional Product", Service: "Service", "Raw Material": "Raw Material", Consumable: "Consumable", Bundle: "Kit" };
		return map[type] || "Traditional Product";
	},

	render_form_tabs() {
		const tabs = this.FORM_TABS.map(
			(t) =>
				`<button type="button" class="retail-prod-form-tab ${this.state.formTab === t.key ? "is-active" : ""}" data-tab="${t.key}">${t.label}</button>`
		).join("");
		this.pos.$root.find("#retail-prod-form-tabs").html(tabs);
		this.pos.$root.find(".retail-prod-form-panel").removeClass("is-active");
		this.pos.$root.find(`.retail-prod-form-panel[data-panel="${this.state.formTab}"]`).addClass("is-active");
	},

	render_item_form(data) {
		this.state.editing = data;
		this.pos.$root.find("#retail-prod-modal-title").text(data.name ? __("Edit Item") : __("New Item"));
		const pt = data.product_type || "Traditional Product";
		this.pos.$root.find("#retail-prod-form-panels").html(`
			<div class="retail-prod-form-panel is-active" data-panel="basic">
				<div class="retail-prod-form-grid">
					<div><label>${__("Item Code")}</label><input id="f-code" value="${frappe.utils.escape_html(data.item_code || "")}"></div>
					<div><label>${__("Item Name")}</label><input id="f-name" value="${frappe.utils.escape_html(data.item_name || "")}"></div>
					<div><label>${__("Item Name (Arabic)")}</label><input id="f-name-ar" value="${frappe.utils.escape_html(data.item_name_ar || "")}"></div>
					<div><label>${__("Barcode")}</label><input id="f-barcode" value="${frappe.utils.escape_html(data.barcode || "")}"></div>
					<div><label>${__("Product Type")}</label><select id="f-ptype">
						<option value="Traditional Product" ${pt === "Traditional Product" ? "selected" : ""}>${__("Product")}</option>
						<option value="Service" ${pt === "Service" ? "selected" : ""}>${__("Service")}</option>
						<option value="Raw Material" ${pt === "Raw Material" ? "selected" : ""}>${__("Raw Material")}</option>
						<option value="Consumable" ${pt === "Consumable" ? "selected" : ""}>${__("Consumable")}</option>
						<option value="Kit" ${pt === "Kit" ? "selected" : ""}>${__("Bundle")}</option>
					</select></div>
					<div><label>${__("Stock UOM")}</label><input id="f-uom" value="${frappe.utils.escape_html(data.stock_uom || "Nos")}"></div>
					<div><label>${__("Classification Code")}</label><input id="f-class" value="${frappe.utils.escape_html(data.classification_code || "")}"></div>
					<div class="full"><label>${__("Description")}</label><textarea id="f-desc" rows="2">${frappe.utils.escape_html(data.item_description || "")}</textarea></div>
				</div>
			</div>
			<div class="retail-prod-form-panel" data-panel="sales">
				<div class="retail-prod-form-grid">
					<div><label><input type="checkbox" id="f-is-sales" ${data.is_sales_item ? "checked" : ""}> ${__("Is Sales Item")}</label></div>
					<div><label><input type="checkbox" id="f-show-pos" ${data.show_in_retail_pos ? "checked" : ""}> ${__("Show in Retail POS")}</label></div>
					<div><label>${__("Standard Selling Rate")}</label><input type="number" step="0.01" id="f-sell-rate" value="${data.standard_selling_rate || 0}"></div>
					<div class="full"><label>${__("Default Sales Account")}</label><input id="f-sales-acc" value="${frappe.utils.escape_html(data.default_sales_account || "")}"></div>
				</div>
			</div>
			<div class="retail-prod-form-panel" data-panel="purchase">
				<div class="retail-prod-form-grid">
					<div><label><input type="checkbox" id="f-is-purchase" ${data.is_purchase_item !== 0 ? "checked" : ""}> ${__("Is Purchase Item")}</label></div>
					<div><label>${__("Standard Purchase Rate")}</label><input type="number" step="0.01" id="f-buy-rate" value="${data.standard_purchase_rate || 0}"></div>
					<div class="full"><label>${__("Default Purchase Account")}</label><input id="f-purchase-acc" value="${frappe.utils.escape_html(data.default_purchase_account || "")}"></div>
				</div>
			</div>
			<div class="retail-prod-form-panel" data-panel="inventory">
				<div class="retail-prod-form-grid">
					<div><label><input type="checkbox" id="f-is-stock" ${data.is_stock_item !== 0 ? "checked" : ""}> ${__("Is Stock Item")}</label></div>
					<div><label>${__("Default Warehouse")}</label><input id="f-warehouse" value="${frappe.utils.escape_html(data.default_warehouse || "")}"></div>
					<div><label>${__("Reorder Level")}</label><input type="number" step="0.01" id="f-reorder" value="${data.reorder_level || 0}"></div>
					<div><label>${__("Safety Stock")}</label><input type="number" step="0.01" id="f-safety" value="${data.safety_stock || 0}"></div>
					<div><label>${__("Valuation Method")}</label><select id="f-valuation"><option value="FIFO" ${(data.valuation_method || "FIFO") === "FIFO" ? "selected" : ""}>FIFO</option><option value="Weighted Average" ${data.valuation_method === "Weighted Average" ? "selected" : ""}>${__("Weighted Average")}</option></select></div>
					<div><label><input type="checkbox" id="f-batch" ${data.has_batch_no ? "checked" : ""}> ${__("Track Batch / Serial")}</label></div>
					<div><label><input type="checkbox" id="f-serial" ${data.has_serial_no ? "checked" : ""}> ${__("Track Serial Numbers")}</label></div>
					<div class="full"><label>${__("Inventory Control GL")}</label><input id="f-inv-gl" value="${frappe.utils.escape_html(data.inventory_control_account || "")}"></div>
				</div>
			</div>
			<div class="retail-prod-form-panel" data-panel="accounts">
				<div class="retail-prod-form-grid">
					<div class="full"><label>${__("Default Expense Account")}</label><input id="f-exp-acc" value="${frappe.utils.escape_html(data.default_expense_account || "")}"></div>
					<div class="full"><label>${__("Cost Center")}</label><input id="f-cost-center" value="${frappe.utils.escape_html(data.item_cost_center || "")}"></div>
				</div>
			</div>
			<div class="retail-prod-form-panel" data-panel="manufacturing">
				<div class="retail-prod-form-grid">
					<div><label>${__("Manufacturing Role")}</label><select id="f-mfg-role">
						<option value="Finished Good" ${(data.manufacturing_role || "Finished Good") === "Finished Good" ? "selected" : ""}>${__("Finished Good")}</option>
						<option value="Raw Material" ${data.manufacturing_role === "Raw Material" ? "selected" : ""}>${__("Raw Material")}</option>
						<option value="Consumable" ${data.manufacturing_role === "Consumable" ? "selected" : ""}>${__("Consumable")}</option>
						<option value="Sub Assembly" ${data.manufacturing_role === "Sub Assembly" ? "selected" : ""}>${__("Sub Assembly")}</option>
						<option value="Service" ${data.manufacturing_role === "Service" ? "selected" : ""}>${__("Service")}</option>
					</select></div>
					<div><label><input type="checkbox" id="f-can-mfg" ${data.can_be_manufactured ? "checked" : ""}> ${__("Can Be Manufactured")}</label></div>
					<div><label><input type="checkbox" id="f-dynamic" ${data.requires_dynamic_composition ? "checked" : ""}> ${__("Requires Dynamic Composition")}</label></div>
				</div>
			</div>
		`);
		this.render_form_tabs();
	},

	collect_form() {
		const d = this.state.editing || {};
		return {
			name: d.name,
			item_code: this.pos.$root.find("#f-code").val(),
			item_name: this.pos.$root.find("#f-name").val(),
			item_name_ar: this.pos.$root.find("#f-name-ar").val(),
			barcode: this.pos.$root.find("#f-barcode").val(),
			item_description: this.pos.$root.find("#f-desc").val(),
			product_type: this.pos.$root.find("#f-ptype").val(),
			stock_uom: this.pos.$root.find("#f-uom").val() || "Nos",
			classification_code: this.pos.$root.find("#f-class").val(),
			is_sales_item: this.pos.$root.find("#f-is-sales").is(":checked") ? 1 : 0,
			show_in_retail_pos: this.pos.$root.find("#f-show-pos").is(":checked") ? 1 : 0,
			standard_selling_rate: flt(this.pos.$root.find("#f-sell-rate").val()),
			default_sales_account: this.pos.$root.find("#f-sales-acc").val(),
			is_purchase_item: this.pos.$root.find("#f-is-purchase").is(":checked") ? 1 : 0,
			standard_purchase_rate: flt(this.pos.$root.find("#f-buy-rate").val()),
			default_purchase_account: this.pos.$root.find("#f-purchase-acc").val(),
			is_stock_item: this.pos.$root.find("#f-is-stock").is(":checked") ? 1 : 0,
			default_warehouse: this.pos.$root.find("#f-warehouse").val(),
			reorder_level: flt(this.pos.$root.find("#f-reorder").val()),
			safety_stock: flt(this.pos.$root.find("#f-safety").val()),
			valuation_method: this.pos.$root.find("#f-valuation").val(),
			has_batch_no: this.pos.$root.find("#f-batch").is(":checked") ? 1 : 0,
			has_serial_no: this.pos.$root.find("#f-serial").is(":checked") ? 1 : 0,
			inventory_control_account: this.pos.$root.find("#f-inv-gl").val(),
			default_expense_account: this.pos.$root.find("#f-exp-acc").val(),
			item_cost_center: this.pos.$root.find("#f-cost-center").val(),
			manufacturing_role: this.pos.$root.find("#f-mfg-role").val(),
			can_be_manufactured: this.pos.$root.find("#f-can-mfg").is(":checked") ? 1 : 0,
			requires_dynamic_composition: this.pos.$root.find("#f-dynamic").is(":checked") ? 1 : 0,
			company: frappe.defaults.get_user_default("Company"),
		};
	},

	save_form() {
		const self = this;
		const payload = this.collect_form();
		if (!payload.item_name) {
			frappe.show_alert({ message: __("Item Name is required"), indicator: "orange" });
			return;
		}
		frappe.call({
			method: `${this.API}.save_retail_item`,
			args: { data: payload },
			freeze: true,
			callback: () => {
				self.$modal.removeClass("is-open");
				self.load();
				self.pos.bootstrap();
				frappe.show_alert({ message: __("Item saved"), indicator: "green" });
			},
		});
	},
};

function flt(v) {
	return parseFloat(v) || 0;
}
