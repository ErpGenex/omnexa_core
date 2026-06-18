frappe.provide("omnexa_core.retail_pos");

omnexa_core.retail_pos = {
	API: "omnexa_core.omnexa_core.retail_pos_api",

	init(wrapper, options) {
		this.wrapper = wrapper;
		this.options = options || {};
		if (this.options.embedded) {
			this.page = { page_container: wrapper, body: wrapper };
			$(wrapper).addClass("retail-pos-page retail-pos-embedded");
		} else {
			this.page = frappe.ui.make_app_page({
				parent: wrapper,
				title: __("Retail POS"),
				single_column: true,
			});
			$(this.page.page_container).addClass("retail-pos-page");
		}
		this.state = {
			catalog: { categories: [], items: [], items_by_category: {} },
			activeCategory: "الكل",
			search: "",
			invoiceName: null,
			invoiceDetail: null,
			customer: null,
			qty: 1,
			selectedItem: null,
			showCategories: localStorage.getItem("retail_pos_show_categories") !== "0",
			canEditPrice: false,
		};
		this.render_shell();
		this.bind_events();
		this.bind_shortcuts();
		omnexa_core.retail_product_manager.init(this);
		this.bootstrap();
		return this;
	},

	render_shell() {
		const cashier = frappe.session.user_fullname || frappe.session.user;
		const initial = (cashier || "أ").trim()[0] || "أ";
		const company = frappe.defaults.get_user_default("Company") || __("Store");
		const hideSidebar = !!this.options.hideSidebar;
		const $root = $(`
			<div class="retail-pos${hideSidebar ? " retail-pos--no-sidebar" : ""}" dir="rtl">
				<aside class="retail-pos__sidebar">
					<div class="retail-pos__brand">
						<div class="retail-pos__brand-icon">🛒</div>
						<div class="retail-pos__brand-title">${frappe.utils.escape_html(company)}</div>
					</div>
					<nav class="retail-pos__nav">
						<button class="retail-pos__nav-item is-active" data-nav="pos"><span>🧾</span><span>${__("Point of Sale")}</span></button>
						<button class="retail-pos__nav-item" data-nav="products"><span>📦</span><span>${__("Products")}</span></button>
						<button class="retail-pos__nav-item" data-nav="customers"><span>👤</span><span>${__("Customers")}</span></button>
						<button class="retail-pos__nav-item" data-nav="suppliers"><span>🚚</span><span>${__("Suppliers")}</span></button>
						<button class="retail-pos__nav-item" data-nav="purchases"><span>🛍️</span><span>${__("Purchases")}</span></button>
						<button class="retail-pos__nav-item" data-nav="inventory"><span>📊</span><span>${__("Inventory")}</span></button>
						<button class="retail-pos__nav-item" data-nav="reports"><span>📈</span><span>${__("Reports")}</span></button>
						<button class="retail-pos__nav-item" data-nav="offers"><span>🏷️</span><span>${__("Offers and Discounts")}</span></button>
						<button class="retail-pos__nav-item" data-nav="expenses"><span>💸</span><span>${__("Expenses")}</span></button>
						<button class="retail-pos__nav-item" data-nav="settings"><span>⚙️</span><span>${__("Settings")}</span></button>
					</nav>
					<div class="retail-pos__sidebar-foot">
						<button class="retail-pos__nav-item" id="retail-pos-logout"><span>⏻</span><span>${__("Logout")}</span></button>
						<div id="retail-pos-datetime"></div>
						<div class="retail-pos__online">● ${__("Online")}</div>
					</div>
				</aside>
				<div class="retail-pos__main">
					<div class="retail-pos__topbar">
						<input class="retail-pos__search" id="retail-pos-search" placeholder="${__("Search product (F3)")} BarCode">
						<div class="retail-pos__quick">
							<button class="retail-pos__quick-btn" id="retail-pos-return" title="F7">${__("Return")} (F7)</button>
							<button class="retail-pos__quick-btn" id="retail-pos-hold" title="F6">${__("Hold")} (F6)</button>
							<button class="retail-pos__quick-btn" id="retail-pos-customer" title="F8">${__("Customer")} (F8)</button>
						</div>
						<div class="retail-pos__user">
							<span>${__("Cashier")} ${frappe.utils.escape_html(cashier)}</span>
							<div class="retail-pos__avatar">${frappe.utils.escape_html(initial)}</div>
						</div>
					</div>
					<div class="retail-pos__body">
						<section class="retail-pos__catalog">
							<div class="retail-pos__catalog-toolbar">
								<div class="retail-pos__categories${this.state.showCategories ? "" : " is-hidden"}" id="retail-pos-categories"></div>
								<button type="button" class="retail-pos__toggle-cats" id="retail-pos-toggle-cats" title="${__("Show/Hide Categories")}">
									${this.state.showCategories ? __("Hide Categories") : __("Show Categories")}
								</button>
							</div>
							<div class="retail-pos__grid-wrap">
								<div class="retail-pos__grid" id="retail-pos-grid"></div>
							</div>
						</section>
						<aside class="retail-pos__cart">
							<div class="retail-pos__cart-head">
								<span>${__("Shopping List")}</span>
								<span class="retail-pos__cart-badge" id="retail-pos-cart-count">0</span>
							</div>
							<div class="retail-pos__cart-items" id="retail-pos-cart-items"></div>
							<div class="retail-pos__totals" id="retail-pos-totals"></div>
							<button class="retail-pos__pay" id="retail-pos-pay" disabled>${__("Pay")} (F9) — <span id="retail-pos-pay-amount">0.00</span></button>
							<div class="retail-pos__cart-actions">
								<button id="retail-pos-discount">${__("Discount")}</button>
								<button id="retail-pos-line-discount">${__("Product Discount")}</button>
								<button class="danger" id="retail-pos-void">${__("Void")}</button>
							</div>
						</aside>
					</div>
					<div class="retail-pos__footer">
						<div class="retail-pos__barcode-wrap">
							<label>${__("Barcode")}</label>
							<input class="retail-pos__barcode" id="retail-pos-barcode" placeholder="${__("Scan barcode here")}">
						</div>
						<div class="retail-pos__qty-wrap">
							<label>${__("Qty")}</label>
							<button class="retail-pos__qty-btn" id="retail-pos-qty-minus">−</button>
							<input class="retail-pos__qty-input" id="retail-pos-qty" type="number" min="1" value="1">
							<button class="retail-pos__qty-btn" id="retail-pos-qty-plus">+</button>
						</div>
						<div class="retail-pos__footer-actions">
							<button class="retail-pos__btn-add" id="retail-pos-add">${__("Add")} (Enter)</button>
							<button class="retail-pos__btn-clear" id="retail-pos-clear-input">${__("Clear")} (Delete)</button>
							<button class="retail-pos__btn-util" id="retail-pos-print" title="F12">${__("Print Receipt")} (F12)</button>
							<button class="retail-pos__btn-util" id="retail-pos-tax-inv" title="F11">${__("Tax Invoice")} (F11)</button>
							<button class="retail-pos__btn-util" id="retail-pos-drawer" title="F10">${__("Open Cash Drawer")} (F10)</button>
						</div>
					</div>
				</div>
			</div>
		`);
		const $mount = this.options.embedded ? $(this.page.page_container) : $(this.page.body);
		$mount.empty().append($root);
		this.$root = $root;
		this.tick_clock();
	},

	bind_events() {
		const self = this;
		this.$root.on("input", "#retail-pos-search", function () {
			self.state.search = $(this).val() || "";
			self.render_products();
		});
		this.$root.on("click", ".retail-pos__cat", function () {
			self.state.activeCategory = $(this).data("category");
			self.$root.find(".retail-pos__cat").removeClass("is-active");
			$(this).addClass("is-active");
			self.render_products();
		});
		this.$root.on("click", ".retail-pos__card", function () {
			const code = $(this).data("item");
			const rate = flt($(this).data("rate"));
			self.state.selectedItem = code;
			self.prompt_add_item(code, rate);
		});
		this.$root.on("click", "#retail-pos-toggle-cats", () => self.toggle_categories());
		this.$root.on("click", ".retail-pos__cart-rate", function (e) {
			e.stopPropagation();
			if (!self.state.canEditPrice) return;
			self.prompt_line_rate($(this).data("row"), flt($(this).data("rate")));
		});
		this.$root.on("click", ".retail-pos__cart-remove", function (e) {
			e.stopPropagation();
			self.remove_line($(this).data("row"));
		});
		this.$root.on("click", "#retail-pos-pay", () => self.complete_sale());
		this.$root.on("click", "#retail-pos-add", () => self.add_from_barcode());
		this.$root.on("keydown", "#retail-pos-barcode", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				self.add_from_barcode();
			}
		});
		this.$root.on("click", "#retail-pos-qty-minus", () => self.adjust_qty(-1));
		this.$root.on("click", "#retail-pos-qty-plus", () => self.adjust_qty(1));
		this.$root.on("input", "#retail-pos-qty", function () {
			self.state.qty = Math.max(1, cint($(this).val()) || 1);
			$(this).val(self.state.qty);
		});
		this.$root.on("click", "#retail-pos-clear-input", () => {
			self.$root.find("#retail-pos-barcode").val("");
			self.$root.find("#retail-pos-search").val("");
			self.state.search = "";
			self.state.qty = 1;
			self.$root.find("#retail-pos-qty").val(1);
			self.render_products();
		});
		this.$root.on("click", "#retail-pos-discount", () => self.prompt_discount());
		this.$root.on("click", "#retail-pos-line-discount", () => self.prompt_discount());
		this.$root.on("click", "#retail-pos-void", () => self.void_cart());
		this.$root.on("click", "#retail-pos-hold", () => self.hold_sale());
		this.$root.on("click", "#retail-pos-customer", () => self.open_customer_picker());
		this.$root.on("click", "#retail-pos-return", () => frappe.set_route("List", "Sales Invoice", { is_return: 1 }));
		this.$root.on("click", "#retail-pos-print", () => self.print_last_receipt());
		this.$root.on("click", "#retail-pos-tax-inv", () => self.open_tax_invoice());
		this.$root.on("click", "#retail-pos-drawer", () => frappe.show_alert({ message: __("Cash drawer command sent"), indicator: "blue" }));
		this.$root.on("click", "#retail-pos-logout", () => frappe.app.logout());
		this.$root.on("click", ".retail-pos__nav-item", function () {
			const nav = $(this).data("nav");
			if (!nav) return;
			self.$root.find(".retail-pos__nav-item").removeClass("is-active");
			$(this).addClass("is-active");
			if (nav === "pos") return;
			if (nav === "products") {
				omnexa_core.retail_product_manager.open();
				return;
			}
			if (nav === "customers") {
				frappe.set_route("List", "Customer");
				return;
			}
			if (nav === "suppliers") {
				frappe.set_route("List", "Supplier");
				return;
			}
			if (nav === "purchases") {
				frappe.set_route("List", "Purchase Order");
				return;
			}
			if (nav === "inventory") {
				frappe.set_route("query-report", "Item Stock Balance");
				return;
			}
			if (nav === "reports") {
				frappe.set_route("query-report", "Sales Register");
				return;
			}
			if (nav === "offers") {
				self.open_offers_panel();
				return;
			}
			if (nav === "expenses") {
				frappe.set_route("List", "Payment Entry");
				return;
			}
			if (nav === "settings") {
				frappe.set_route("List", "Product Type");
			}
		});
	},

	bind_shortcuts() {
		const self = this;
		$(document).on("keydown.retail_pos", (e) => {
			if (!$(self.wrapper).is(":visible")) return;
			const tag = (e.target.tagName || "").toLowerCase();
			const typing = tag === "input" || tag === "textarea" || e.target.isContentEditable;
			if (e.key === "F3") {
				e.preventDefault();
				self.$root.find("#retail-pos-search").focus().select();
			} else if (e.key === "F6") {
				e.preventDefault();
				self.hold_sale();
			} else if (e.key === "F7") {
				e.preventDefault();
				frappe.set_route("List", "Sales Invoice", { is_return: 1 });
			} else if (e.key === "F8") {
				e.preventDefault();
				self.open_customer_picker();
			} else if (e.key === "F9") {
				e.preventDefault();
				self.complete_sale();
			} else if (e.key === "F10") {
				e.preventDefault();
				frappe.show_alert({ message: __("Cash drawer command sent"), indicator: "blue" });
			} else if (e.key === "F11") {
				e.preventDefault();
				self.open_tax_invoice();
			} else if (e.key === "F12") {
				e.preventDefault();
				self.print_last_receipt();
			} else if (e.key === "Enter" && !typing) {
				e.preventDefault();
				self.add_from_barcode();
			} else if (e.key === "Delete" && !typing) {
				e.preventDefault();
				self.$root.find("#retail-pos-barcode").val("");
			}
		});
	},

	tick_clock() {
		const update = () => {
			const now = new Date();
			const opts = { weekday: "long", year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" };
			this.$root.find("#retail-pos-datetime").text(now.toLocaleString("ar-EG", opts));
		};
		update();
		this._clockTimer = setInterval(update, 30000);
	},

	bootstrap() {
		frappe.call({
			method: `${this.API}.get_retail_pos_session`,
			callback: (r) => {
				this.state.canEditPrice = !!(r.message && r.message.can_edit_price);
				this.load_catalog();
			},
		});
	},

	load_catalog() {
		frappe.call({
			method: `${this.API}.get_retail_catalog`,
			callback: (r) => {
				this.state.catalog = r.message || { categories: [], items: [], items_by_category: {} };
				this.render_categories();
				this.render_products();
				this.ensure_invoice();
			},
		});
	},

	ensure_invoice() {
		frappe.call({
			method: `${this.API}.get_open_retail_pos_invoices`,
			callback: (r) => {
				const rows = r.message || [];
				if (rows.length) {
					this.state.invoiceName = rows[0].name;
					this.load_invoice();
					return;
				}
				this.create_invoice();
			},
			error: (r) => this.show_api_error(__("Could not load open invoices."), r),
		});
	},

	show_api_error(title, r) {
		const message =
			(r && r.message) ||
			(r && r.exc_type) ||
			__("An error occurred. Please refresh the page or contact your administrator.");
		frappe.msgprint({ title: title || __("Retail POS"), message, indicator: "red" });
	},

	create_invoice(customer) {
		frappe.call({
			method: `${this.API}.create_retail_pos_invoice`,
			args: { customer: customer || null },
			callback: (r) => {
				if (!r.message) {
					this.show_api_error(__("Could not create invoice."), r);
					return;
				}
				this.state.invoiceDetail = r.message;
				this.state.invoiceName = r.message.invoice_name;
				this.render_cart();
			},
			error: (r) => this.show_api_error(__("Could not create invoice."), r),
		});
	},

	load_invoice() {
		if (!this.state.invoiceName) return;
		frappe.call({
			method: `${this.API}.get_retail_pos_invoice_detail`,
			args: { invoice_name: this.state.invoiceName },
			callback: (r) => {
				this.state.invoiceDetail = r.message;
				this.render_cart();
			},
		});
	},

	render_categories() {
		const cats = this.state.catalog.categories || ["الكل"];
		const html = cats
			.map(
				(cat, idx) =>
					`<button class="retail-pos__cat${idx === 0 ? " is-active" : ""}" data-category="${frappe.utils.escape_html(cat)}">${frappe.utils.escape_html(cat)}</button>`
			)
			.join("");
		this.$root.find("#retail-pos-categories").html(html);
		this.$root.find("#retail-pos-categories").toggleClass("is-hidden", !this.state.showCategories);
		this.$root
			.find("#retail-pos-toggle-cats")
			.text(this.state.showCategories ? __("Hide Categories") : __("Show Categories"));
		this.state.activeCategory = cats[0] || "الكل";
	},

	toggle_categories() {
		this.state.showCategories = !this.state.showCategories;
		localStorage.setItem("retail_pos_show_categories", this.state.showCategories ? "1" : "0");
		this.render_categories();
	},

	filtered_items() {
		const map = this.state.catalog.items_by_category || {};
		const all = this.state.catalog.items || Object.values(map).flat();
		const search = (this.state.search || "").trim().toLowerCase();
		let items = all;
		if (this.state.activeCategory && this.state.activeCategory !== "الكل") {
			items = map[this.state.activeCategory] || [];
		}
		if (search) {
			items = items.filter(
				(i) =>
					(i.item_name || "").toLowerCase().includes(search) ||
					(i.item_code || "").toLowerCase().includes(search) ||
					(i.barcode || "").toLowerCase().includes(search)
			);
		}
		return items;
	},

	render_products() {
		const items = this.filtered_items();
		if (!items.length) {
			this.$root.find("#retail-pos-grid").html(`<div style="padding:20px;color:#6b7280">${__("No products found.")}</div>`);
			return;
		}
		const currency = frappe.defaults.get_default("currency");
		const html = items
			.map((item) => {
				const price = format_currency(item.rate || 0, currency, 2);
				const bg = item.image_style || "linear-gradient(135deg,#d4fc79,#96e6a1)";
				const barcode = item.barcode ? frappe.utils.escape_html(item.barcode) : "—";
				return `
					<div class="retail-pos__card" data-item="${frappe.utils.escape_html(item.item_code)}" data-rate="${item.rate || 0}">
						<div class="retail-pos__card-img" style="background-image:${bg}"></div>
						<div class="retail-pos__card-body">
							<div class="retail-pos__card-name">${frappe.utils.escape_html(item.item_name)}</div>
							<div class="retail-pos__card-price">${price}</div>
							<div class="retail-pos__card-barcode" title="${__("Barcode")}">▮ ${barcode}</div>
							<div class="retail-pos__card-code">${frappe.utils.escape_html(item.item_code)}</div>
						</div>
					</div>`;
			})
			.join("");
		this.$root.find("#retail-pos-grid").html(html);
	},

	render_cart() {
		const detail = this.state.invoiceDetail;
		const currency = frappe.defaults.get_default("currency");
		if (!detail) {
			this.$root.find("#retail-pos-cart-items").html(`<div style="padding:12px;color:#9ca3af">${__("Cart is empty")}</div>`);
			this.$root.find("#retail-pos-totals").empty();
			this.$root.find("#retail-pos-cart-count").text("0");
			this.$root.find("#retail-pos-pay").prop("disabled", true);
			this.$root.find("#retail-pos-pay-amount").text(format_currency(0, currency, 2));
			return;
		}
		const count = detail.items_count || 0;
		this.$root.find("#retail-pos-cart-count").text(count);
		if (!detail.items || !detail.items.length) {
			this.$root.find("#retail-pos-cart-items").html(`<div style="padding:12px;color:#9ca3af">${__("Cart is empty")}</div>`);
		} else {
			const rows = detail.items
				.map(
					(row) => `
				<div class="retail-pos__cart-row">
					<div>${frappe.utils.escape_html(row.item_name)}</div>
					<div>${row.qty}</div>
					<div class="retail-pos__cart-rate${this.state.canEditPrice ? " is-editable" : ""}" data-row="${row.row_name}" data-rate="${row.rate}">${format_currency(row.rate, currency, 2)}</div>
					<div>${format_currency(row.amount, currency, 2)}</div>
					<button class="retail-pos__cart-remove" data-row="${row.row_name}">×</button>
				</div>`
				)
				.join("");
			this.$root.find("#retail-pos-cart-items").html(rows);
		}
		this.$root.find("#retail-pos-totals").html(`
			<div class="retail-pos__total-row"><span>${__("Total before discount")}</span><span>${format_currency(detail.subtotal, currency, 2)}</span></div>
			<div class="retail-pos__total-row"><span>${__("Discount")}</span><span>${format_currency(detail.discount, currency, 2)}</span></div>
			<div class="retail-pos__total-row"><span>${__("VAT included")}</span><span>${format_currency(detail.tax, currency, 2)}</span></div>
			<div class="retail-pos__total-row retail-pos__total-row--grand"><span>${__("Invoice Total")}</span><span>${format_currency(detail.grand_total, currency, 2)}</span></div>
		`);
		this.$root.find("#retail-pos-pay-amount").text(format_currency(detail.grand_total, currency, 2));
		this.$root.find("#retail-pos-pay").prop("disabled", !(detail.items && detail.items.length));
	},

	add_from_barcode() {
		const code = (this.$root.find("#retail-pos-barcode").val() || "").trim();
		if (!code) {
			this.$root.find("#retail-pos-barcode").focus();
			return;
		}
		const item = (this.state.catalog.items || []).find(
			(i) =>
				i.item_code === code ||
				(i.barcode || "").toLowerCase() === code.toLowerCase()
		);
		this.prompt_add_item(code, item ? item.rate : 0, () => {
			this.$root.find("#retail-pos-barcode").val("").focus();
		});
	},

	prompt_add_item(item_code, default_rate, done) {
		const self = this;
		const qty = this.state.qty || 1;
		if (!this.state.canEditPrice) {
			this.add_item(item_code, qty, null, done);
			return;
		}
		frappe.prompt(
			[
				{ fieldname: "qty", label: __("Qty"), fieldtype: "Float", default: qty, reqd: 1 },
				{ fieldname: "rate", label: __("Price"), fieldtype: "Currency", default: default_rate || 0, reqd: 1 },
			],
			(values) => {
				self.add_item(item_code, values.qty, values.rate, done);
			},
			__("Add to Cart"),
			__("Add")
		);
	},

	prompt_line_rate(row_name, current_rate) {
		const self = this;
		frappe.prompt(
			[{ fieldname: "rate", label: __("Price"), fieldtype: "Currency", default: current_rate || 0, reqd: 1 }],
			(values) => {
				frappe.call({
					method: `${self.API}.update_retail_pos_line_rate`,
					args: { invoice_name: self.state.invoiceName, row_name, rate: values.rate },
					callback: (r) => {
						self.state.invoiceDetail = r.message;
						self.render_cart();
					},
				});
			},
			__("Edit Line Price")
		);
	},

	add_item(item_code, qty, rate, done) {
		if (!this.state.invoiceName) {
			frappe.call({
				method: `${this.API}.create_retail_pos_invoice`,
				args: { customer: null },
				callback: (r) => {
					if (!r.message) {
						this.show_api_error(__("Could not create invoice."), r);
						return;
					}
					this.state.invoiceDetail = r.message;
					this.state.invoiceName = r.message.invoice_name;
					this.add_item(item_code, qty, rate, done);
				},
				error: (r) => this.show_api_error(__("Could not create invoice."), r),
			});
			return;
		}
		const args = { invoice_name: this.state.invoiceName, item_code, qty: qty || 1 };
		if (rate !== null && rate !== undefined && this.state.canEditPrice) {
			args.rate = rate;
		}
		frappe.call({
			method: `${this.API}.add_item_to_retail_pos`,
			args,
			callback: (r) => {
				if (!r.message) {
					this.show_api_error(__("Could not add item to cart."), r);
					return;
				}
				this.state.invoiceDetail = r.message;
				this.render_cart();
				done && done();
			},
			error: (r) => this.show_api_error(__("Could not add item to cart."), r),
		});
	},

	remove_line(row_name) {
		if (!this.state.invoiceName) return;
		frappe.call({
			method: `${this.API}.remove_item_from_retail_pos`,
			args: { invoice_name: this.state.invoiceName, row_name },
			callback: (r) => {
				this.state.invoiceDetail = r.message;
				this.render_cart();
			},
		});
	},

	prompt_discount() {
		const self = this;
		frappe.prompt(
			[{ fieldname: "discount_amount", label: __("Discount Amount"), fieldtype: "Currency", default: 0 }],
			(values) => {
				frappe.call({
					method: `${self.API}.apply_retail_pos_discount`,
					args: { invoice_name: self.state.invoiceName, discount_amount: values.discount_amount },
					callback: (r) => {
						self.state.invoiceDetail = r.message;
						self.render_cart();
					},
				});
			},
			__("Apply Discount")
		);
	},

	open_offers_panel() {
		const self = this;
		const d = new frappe.ui.Dialog({
			title: __("Offers and Discounts"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "help",
					options: `<p class="text-muted">${__(
						"Apply a discount on the current cart, or open tax rules for pricing configuration."
					)}</p>`,
				},
			],
			primary_action_label: __("Apply Cart Discount"),
			primary_action() {
				d.hide();
				self.prompt_discount();
			},
			secondary_action_label: __("Tax Rules"),
			secondary_action() {
				d.hide();
				frappe.set_route("tax-rule");
			},
		});
		d.show();
	},

	void_cart() {
		const detail = this.state.invoiceDetail;
		if (!detail || !detail.items || !detail.items.length) return;
		const rows = [...detail.items];
		const remove_next = () => {
			const row = rows.pop();
			if (!row) {
				frappe.call({
					method: `${this.API}.apply_retail_pos_discount`,
					args: { invoice_name: this.state.invoiceName, discount_amount: 0 },
					callback: (r) => {
						this.state.invoiceDetail = r.message;
						this.render_cart();
						frappe.show_alert({ message: __("Cart cleared"), indicator: "orange" });
					},
				});
				return;
			}
			frappe.call({
				method: `${this.API}.remove_item_from_retail_pos`,
				args: { invoice_name: this.state.invoiceName, row_name: row.row_name },
				callback: () => remove_next(),
			});
		};
		remove_next();
	},

	hold_sale() {
		if (!this.state.invoiceDetail || !this.state.invoiceDetail.items || !this.state.invoiceDetail.items.length) {
			frappe.show_alert({ message: __("Nothing to hold"), indicator: "orange" });
			return;
		}
		const held = this.state.invoiceName;
		this.state.invoiceName = null;
		this.state.invoiceDetail = null;
		this.create_invoice();
		frappe.show_alert({ message: `${__("Sale on hold")}: ${held}`, indicator: "blue" });
	},

	open_customer_picker() {
		const self = this;
		frappe.prompt(
			[{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" }],
			(values) => {
				frappe.call({
					method: `${self.API}.set_retail_pos_customer`,
					args: { invoice_name: self.state.invoiceName, customer: values.customer },
					callback: (r) => {
						self.state.invoiceDetail = r.message;
						self.state.customer = values.customer;
						frappe.show_alert({ message: __("Customer selected"), indicator: "blue" });
					},
				});
			},
			__("Select Customer")
		);
	},

	complete_sale() {
		if (!this.state.invoiceName) return;
		const self = this;
		frappe.call({
			method: `${this.API}.complete_retail_pos_sale`,
			args: { invoice_name: this.state.invoiceName },
			freeze: true,
			callback: (r) => {
				const msg = r.message || {};
				const invoiceName = msg.invoice || "";
				const openReceipt = (html) => {
					self._lastReceiptHtml = html || "";
					self._lastInvoice = invoiceName;
					self.print_receipt(self._lastReceiptHtml);
					frappe.show_alert({
						message: `${__("Sale completed")}${invoiceName ? ` · ${invoiceName}` : ""}`,
						indicator: "green",
					});
					self.state.invoiceName = null;
					self.state.invoiceDetail = null;
					self.state.customer = null;
					self.create_invoice();
				};
				if (msg.receipt_html) {
					openReceipt(msg.receipt_html);
					return;
				}
				if (!invoiceName) {
					self.show_api_error(__("Could not complete sale."), r);
					return;
				}
				frappe.call({
					method: `${self.API}.get_retail_receipt_html`,
					args: { invoice_name: invoiceName },
					callback: (receipt) => openReceipt(receipt.message || ""),
					error: (err) => {
						openReceipt("");
						self.show_api_error(__("Sale completed but receipt could not be loaded."), err);
					},
				});
			},
			error: (r) => self.show_api_error(__("Could not complete sale."), r),
		});
	},

	open_tax_invoice() {
		if (this._lastInvoice) {
			frappe.set_route("Form", "Sales Invoice", this._lastInvoice);
			return;
		}
		if (this.state.invoiceName) {
			frappe.set_route("Form", "Sales Invoice", this.state.invoiceName);
		}
	},

	print_last_receipt() {
		if (this._lastReceiptHtml) {
			this.print_receipt(this._lastReceiptHtml);
			return;
		}
		const invoiceName = this._lastInvoice || this.state.invoiceName;
		if (!invoiceName) return;
		frappe.call({
			method: `${this.API}.get_retail_receipt_html`,
			args: { invoice_name: invoiceName },
			callback: (r) => {
				this._lastReceiptHtml = r.message || "";
				this.print_receipt(this._lastReceiptHtml);
			},
			error: (r) => this.show_api_error(__("Could not load receipt."), r),
		});
	},

	print_receipt(html) {
		if (!html) {
			frappe.show_alert({ message: __("No receipt to print"), indicator: "orange" });
			return;
		}
		const win = window.open("", "_blank", "width=320,height=720");
		if (!win) {
			frappe.msgprint(__("Allow pop-ups to print the receipt."));
			return;
		}
		win.document.write(html);
		win.document.close();
		win.focus();
		setTimeout(() => win.print(), 400);
	},

	adjust_qty(delta) {
		this.state.qty = Math.max(1, (this.state.qty || 1) + delta);
		this.$root.find("#retail-pos-qty").val(this.state.qty);
	},
};

function cint(v) {
	return parseInt(v, 10) || 0;
}

function flt(v) {
	return parseFloat(v) || 0;
}
