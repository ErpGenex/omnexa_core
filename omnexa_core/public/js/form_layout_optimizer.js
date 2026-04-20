// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt
// Adaptive, non-destructive form layout optimizer for Frappe Desk forms.

(function () {
	"use strict";

	const FORM_CLASS = "omnexa-form-optimized";
	const APPLIED_CLASS = "omnexa-grid-applied";
	const LEVEL_CLASS_PREFIX = "omnexa-layout-";
	const SECTION_CAP = 8;

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

	function apply_form_layout(frm) {
		if (!frm || !frm.wrapper || !frm.meta) return;
		const wrapper = frm.wrapper;
		wrapper.classList.add(FORM_CLASS, APPLIED_CLASS);

		[...wrapper.classList]
			.filter((c) => c.startsWith(LEVEL_CLASS_PREFIX))
			.forEach((c) => wrapper.classList.remove(c));
		wrapper.classList.add(`${LEVEL_CLASS_PREFIX}${get_layout_level(frm)}`);

		mark_required_fields(wrapper);
		mark_important_fields(frm, wrapper);
		optimize_numeric_alignment(wrapper);
		optimize_date_controls(wrapper);
		enforce_section_density(wrapper);
		ensure_accessibility(wrapper);
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
