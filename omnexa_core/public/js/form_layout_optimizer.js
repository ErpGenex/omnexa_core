// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt
// Adaptive, non-destructive form layout optimizer for Frappe Desk forms.

(function () {
	"use strict";

	const FORM_CLASS = "omnexa-form-optimized";
	const APPLIED_CLASS = "omnexa-grid-applied";
	const LEVEL_CLASS_PREFIX = "omnexa-layout-";
	const SECTION_CAP = 8;
	let glAccountUiHooksBound = false;
	let itemUiHooksBound = false;
	let universalItemGridSyncBound = false;

	function get_layout_level(frm) {
		const meta = frm && frm.meta ? frm.meta : {};
		if (meta.istable) return "single";
		if (meta.issingle) return "single";
		if (meta.is_submittable) return "complex";
		if ((meta.fields || []).length > 60) return "complex";
		if ((meta.fields || []).length > 32) return "dense";
		return "normal";
	}

	function mark_required_fields(wrapper) {
		wrapper.querySelectorAll(".frappe-control").forEach((control) => {
			const req = control.querySelector(".reqd-star, .has-error .control-label");
			control.classList.toggle("omnexa-required-control", Boolean(req));
		});
	}

	function optimize_numeric_alignment(wrapper) {
		wrapper.querySelectorAll(".frappe-control[data-fieldtype='Currency'], .frappe-control[data-fieldtype='Float'], .frappe-control[data-fieldtype='Int']").forEach((control) => {
			control.classList.add("omnexa-numeric-control");
			control.querySelectorAll("input, .control-value, .like-disabled-input").forEach((el) => {
				el.classList.add("omnexa-align-end");
			});
		});
	}

	function optimize_date_controls(wrapper) {
		wrapper.querySelectorAll(".frappe-control[data-fieldtype='Date'] input, .frappe-control[data-fieldtype='Datetime'] input").forEach((input) => {
			input.classList.add("omnexa-compact-input");
		});
	}

	function mark_currency_sections(wrapper) {
		// Add a stable class for sections that contain currency controls,
		// so CSS can enforce a 2-column sub-layout (Currency vs Default Tax Rule).
		const currency = wrapper.querySelector(".frappe-control[data-fieldname='currency']");
		if (!currency) return;
		const section = currency.closest(".form-section");
		if (!section) return;
		section.classList.add("omnexa-currency-section");
	}

	function place_supporting_attachment_in_currency_section(wrapper) {
		const currencyControl = wrapper.querySelector(".frappe-control[data-fieldname='currency']");
		const attachmentControl = wrapper.querySelector(".frappe-control[data-fieldname='supporting_attachment']");
		if (!currencyControl || !attachmentControl) return;

		const currencySection = currencyControl.closest(".form-section");
		if (!currencySection) return;
		const currencyBody = currencySection.querySelector(".section-body");
		if (!currencyBody) return;

		// If attachment is not already in currency section, move it visually there.
		if (!currencySection.contains(attachmentControl)) {
			currencyBody.appendChild(attachmentControl);
		}
		currencySection.classList.add("omnexa-currency-section");
	}

	function mark_table_sections(wrapper) {
		// Force full-width table sections regardless of legacy nested wrappers.
		wrapper.querySelectorAll(".form-section").forEach((section) => {
			const hasTable = section.querySelector(".frappe-control[data-fieldtype='Table']");
			section.classList.toggle("omnexa-has-table-section", Boolean(hasTable));
		});
	}

	function mark_important_fields(frm, wrapper) {
		const important = new Set();
		(frm.meta.fields || []).forEach((df) => {
			if (!df || !df.fieldname) return;
			if (
				df.reqd ||
				df.bold ||
				[
					"status",
					"company",
					"customer",
					"supplier",
					"posting_date",
					"transaction_date",
					"bill_date",
					"delivery_date",
					"due_date",
				].includes(df.fieldname)
			) {
				important.add(df.fieldname);
			}
		});
		important.forEach((fieldname) => {
			const node = wrapper.querySelector(`.frappe-control[data-fieldname='${fieldname}']`);
			if (node) node.classList.add("omnexa-important-control");
		});
	}

	function enforce_section_density(wrapper) {
		wrapper.querySelectorAll(".form-section, .section-body").forEach((section) => {
			const controls = section.querySelectorAll(":scope > .frappe-control, .section-body > .frappe-control");
			if (!controls.length) return;
			if (controls.length > SECTION_CAP) {
				section.classList.add("omnexa-section-dense");
			}
		});
	}

	function ensure_accessibility(wrapper) {
		wrapper.querySelectorAll(".form-section .section-head").forEach((head) => {
			if (!head.getAttribute("role")) head.setAttribute("role", "heading");
			if (!head.getAttribute("aria-level")) head.setAttribute("aria-level", "3");
		});
		wrapper.querySelectorAll(".frappe-control input, .frappe-control select, .frappe-control textarea").forEach((el) => {
			if (!el.getAttribute("tabindex")) el.setAttribute("tabindex", "0");
		});
	}

	function apply_company_branch_user_defaults(frm) {
		if (!frm || !frm.doc) return;
		const fields = (frm.meta && frm.meta.fields) || [];
		const hasCompany = fields.some((df) => df && df.fieldname === "company");
		const hasBranch = fields.some((df) => df && df.fieldname === "branch");
		if (!hasCompany && !hasBranch) return;

		try {
			const userCompany = frappe.defaults.get_user_default("Company");
			const userBranch = frappe.defaults.get_user_default("Branch");
			if (hasCompany && !frm.doc.company && userCompany) {
				frm.set_value("company", userCompany);
			}
			if (hasBranch && !frm.doc.branch && userBranch) {
				frm.set_value("branch", userBranch);
			}
		} catch (e) {
			// Non-blocking: defaults enhancement should never break form render.
		}
	}

	function apply_transaction_form_density(frm, wrapper) {
		if (!frm || !frm.meta) return;
		// Same vertical rhythm as Journal Entry reference, on every main form (not child rows / singles).
		if (!frm.meta.istable && !frm.meta.issingle) {
			wrapper.classList.add("omnexa-transaction-density");
		}
		// Remarks row compaction: Journal Entry only (other doctypes may need tall remarks).
		if (frm.doctype === "Journal Entry") {
			const remarks = wrapper.querySelector(".frappe-control[data-fieldname='remarks']");
			if (remarks) remarks.classList.add("omnexa-je-remarks");
		}
	}

	function setup_gl_account_link_formatter() {
		if (!frappe || !frappe.form) return;
		frappe.form.link_formatters = frappe.form.link_formatters || {};
		if (frappe.form.link_formatters["GL Account"]) return;
		frappe.form.link_formatters["GL Account"] = function (value, doc) {
			const accountName = (doc && doc.account_name) || "";
			const accountNumber = (doc && doc.account_number) || "";
			if (accountName && accountNumber) return `${accountName} (${accountNumber})`;
			if (accountName) return accountName;
			return value;
		};
	}

	function setup_item_link_formatter() {
		if (!frappe || !frappe.form) return;
		frappe.form.link_formatters = frappe.form.link_formatters || {};
		if (frappe.form.link_formatters["Item"]) return;
		frappe.form.link_formatters["Item"] = function (value, doc) {
			const itemName = (doc && doc.item_name) || "";
			const itemCode = (doc && doc.item_code) || value || "";
			if (itemName && itemCode) return `${itemName} (${itemCode})`;
			return itemName || itemCode;
		};
	}

	function setup_party_link_formatters() {
		if (!frappe || !frappe.form) return;
		frappe.form.link_formatters = frappe.form.link_formatters || {};

		if (!frappe.form.link_formatters["Customer"]) {
			frappe.form.link_formatters["Customer"] = function (value, doc) {
				const code = (doc && doc.customer_code) || "";
				const name = (doc && doc.customer_name) || value || "";
				if (code && name) return `${code} - ${name}`;
				return name || value || "";
			};
		}

		if (!frappe.form.link_formatters["Supplier"]) {
			frappe.form.link_formatters["Supplier"] = function (value, doc) {
				const code = (doc && doc.supplier_code) || "";
				const name = (doc && doc.supplier_name) || value || "";
				if (code && name) return `${code} - ${name}`;
				return name || value || "";
			};
		}

		if (!frappe.form.link_formatters["Account"]) {
			frappe.form.link_formatters["Account"] = function (value, doc) {
				const number = (doc && doc.account_number) || "";
				const name = (doc && doc.account_name) || value || "";
				if (number && name) return `${number} - ${name}`;
				return name || value || "";
			};
		}
	}

	function get_grid_row_value(row, fieldname) {
		const control = row.querySelector(`.frappe-control[data-fieldname='${fieldname}'] input`);
		return control ? (control.value || "").trim() : "";
	}

	function set_grid_row_value(row, fieldname, value) {
		const control = row.querySelector(`.frappe-control[data-fieldname='${fieldname}'] input`);
		if (!control) return;
		if ((control.value || "") === (value || "")) return;
		control.value = value || "";
		control.dispatchEvent(new Event("change", { bubbles: true }));
	}

	async function resolve_item_by_code(itemCode) {
		if (!itemCode) return null;
		try {
			const matches = await frappe.db.get_list("Item", {
				fields: ["name", "item_code", "item_name"],
				filters: {
					item_code: itemCode,
					disabled: 0,
				},
				limit: 2,
			});
			if (matches && matches.length === 1) {
				return matches[0];
			}
		} catch (e) {
			// Non-blocking UX enhancement.
		}
		return null;
	}

	async function resolve_item_by_name(itemName) {
		if (!itemName) return null;
		try {
			const itemData = await frappe.db.get_value("Item", itemName, ["item_code", "item_name"]);
			if (itemData && itemData.message && itemData.message.item_code) {
				return {
					name: itemName,
					item_code: itemData.message.item_code,
					item_name: itemData.message.item_name || "",
				};
			}
		} catch (e) {
			// Non-blocking UX enhancement.
		}
		return null;
	}

	function bind_universal_item_grid_sync() {
		if (universalItemGridSyncBound) return;
		universalItemGridSyncBound = true;

		document.addEventListener("change", async (evt) => {
			const target = evt.target;
			if (!target || !(target instanceof HTMLInputElement)) return;
			const control = target.closest(".frappe-control");
			const row = target.closest(".grid-row");
			if (!control || !row) return;

			const fieldname = control.getAttribute("data-fieldname");
			if (!fieldname || (fieldname !== "item" && fieldname !== "item_code")) return;

			const hasItemField = Boolean(row.querySelector(".frappe-control[data-fieldname='item']"));
			const hasItemCodeField = Boolean(row.querySelector(".frappe-control[data-fieldname='item_code']"));
			if (!hasItemField || !hasItemCodeField) return;

			if (fieldname === "item") {
				const itemName = get_grid_row_value(row, "item");
				const resolved = await resolve_item_by_name(itemName);
				if (!resolved) return;
				set_grid_row_value(row, "item_code", resolved.item_code || "");
				if (row.querySelector(".frappe-control[data-fieldname='item_name']")) {
					set_grid_row_value(row, "item_name", resolved.item_name || "");
				}
				return;
			}

			if (fieldname === "item_code") {
				const itemCode = get_grid_row_value(row, "item_code");
				const resolved = await resolve_item_by_code(itemCode);
				if (!resolved) return;
				set_grid_row_value(row, "item", resolved.name || "");
				set_grid_row_value(row, "item_code", resolved.item_code || "");
				if (row.querySelector(".frappe-control[data-fieldname='item_name']")) {
					set_grid_row_value(row, "item_name", resolved.item_name || "");
				}
			}
		});
	}

	function bind_item_ui_hooks() {
		if (itemUiHooksBound) return;
		itemUiHooksBound = true;

		document.addEventListener("focusin", (evt) => {
			const target = evt.target;
			if (!target) return;
			const control = target.closest && target.closest(".frappe-control");
			if (!control) return;
			const options = control.getAttribute("data-options");
			if (options !== "Item") return;

			// If the control has a sibling/row `item_code` field, autofill it on selection.
			const input = control.querySelector("input[data-fieldname='item'], input");
			if (!input) return;
			input.addEventListener(
				"change",
				() => {
					const row = control.closest(".grid-row");
					if (!row) return;
					const itemCodeInput = row.querySelector(".frappe-control[data-fieldname='item_code'] input");
					if (!itemCodeInput || itemCodeInput.value) return;
					// In many setups link value is item code/name already. Fill directly first.
					itemCodeInput.value = input.value || "";
					itemCodeInput.dispatchEvent(new Event("change", { bubbles: true }));
				},
				{ once: true }
			);
		});
	}

	function normalize_gl_account_dropdown_rows() {
		if (!document.body.classList.contains("omnexa-gl-link-focus")) return;
		document.querySelectorAll(".awesomplete ul li .small").forEach((el) => {
			const txt = (el.textContent || "").trim();
			if (!txt) return;
			// Strip internal hash-like id prefix: "<id>, <account_number>" -> "<account_number>"
			const cleaned = txt.replace(/^[^\s,]+\s*,\s*/, "");
			if (cleaned !== txt) el.textContent = cleaned;
		});
	}

	function bind_gl_account_ui_hooks() {
		if (glAccountUiHooksBound) return;
		glAccountUiHooksBound = true;

		document.addEventListener("focusin", (evt) => {
			const target = evt.target;
			if (!target) return;
			const control = target.closest && target.closest(".frappe-control");
			if (!control) return;
			const options = control.getAttribute("data-options");
			const fieldname = control.getAttribute("data-fieldname");
			if (options === "GL Account" || fieldname === "account") {
				document.body.classList.add("omnexa-gl-link-focus");
				window.requestAnimationFrame(normalize_gl_account_dropdown_rows);
			}
		});

		document.addEventListener("focusout", () => {
			window.requestAnimationFrame(() => {
				const active = document.activeElement;
				const control = active && active.closest ? active.closest(".frappe-control") : null;
				if (!control) {
					document.body.classList.remove("omnexa-gl-link-focus");
					return;
				}
				const options = control.getAttribute("data-options");
				const fieldname = control.getAttribute("data-fieldname");
				if (!(options === "GL Account" || fieldname === "account")) {
					document.body.classList.remove("omnexa-gl-link-focus");
				}
			});
		});

		const observer = new MutationObserver(() => {
			window.requestAnimationFrame(normalize_gl_account_dropdown_rows);
		});
		observer.observe(document.body, { childList: true, subtree: true });
	}

	function apply_form_layout(frm) {
		if (!frm || !frm.wrapper || !frm.meta) return;
		const wrapper = frm.wrapper;
		// Frappe renders the actual form under a `.form-layout` node inside wrapper.
		// Some themes/customizations style `.form-layout` directly; apply classes to both.
		const formLayout = wrapper.querySelector(".form-layout") || wrapper;

		wrapper.classList.add(FORM_CLASS, APPLIED_CLASS);
		if (formLayout !== wrapper) formLayout.classList.add(FORM_CLASS, APPLIED_CLASS);

		[...wrapper.classList]
			.filter((c) => c.startsWith(LEVEL_CLASS_PREFIX))
			.forEach((c) => wrapper.classList.remove(c));
		wrapper.classList.add(`${LEVEL_CLASS_PREFIX}${get_layout_level(frm)}`);
		if (formLayout !== wrapper) {
			[...formLayout.classList]
				.filter((c) => c.startsWith(LEVEL_CLASS_PREFIX))
				.forEach((c) => formLayout.classList.remove(c));
			formLayout.classList.add(`${LEVEL_CLASS_PREFIX}${get_layout_level(frm)}`);
		}

		mark_required_fields(wrapper);
		mark_important_fields(frm, wrapper);
		optimize_numeric_alignment(wrapper);
		optimize_date_controls(wrapper);
		mark_currency_sections(wrapper);
		place_supporting_attachment_in_currency_section(wrapper);
		mark_table_sections(wrapper);
		enforce_section_density(wrapper);
		ensure_accessibility(wrapper);
		apply_transaction_form_density(frm, wrapper);
		setup_gl_account_link_formatter();
		setup_item_link_formatter();
		setup_party_link_formatters();
		bind_gl_account_ui_hooks();
		bind_item_ui_hooks();
		bind_universal_item_grid_sync();
		apply_company_branch_user_defaults(frm);
	}

	function setup_lazy_reflow(frm) {
		if (!frm || !frm.wrapper || frm.__omnexa_layout_observer) return;
		const observer = new MutationObserver(() => {
			window.requestAnimationFrame(() => apply_form_layout(frm));
		});
		observer.observe(frm.wrapper, { childList: true, subtree: true });
		frm.__omnexa_layout_observer = observer;
	}

	frappe.ui.form.on("*", {
		onload_post_render(frm) {
			apply_form_layout(frm);
			setup_lazy_reflow(frm);
		},
		refresh(frm) {
			apply_form_layout(frm);
		},
	});
})();
