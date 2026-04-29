# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


_SKIP_DOCTYPES = {
	"DocType",
	"Custom Field",
	"Property Setter",
	"Patch Log",
	"Version",
	"Error Log",
	"File",
	"Module Def",
}


def _is_runtime_safe() -> bool:
	return not any(
		[
			getattr(frappe.flags, "in_install", False),
			getattr(frappe.flags, "in_migrate", False),
			getattr(frappe.flags, "in_patch", False),
			getattr(frappe.flags, "in_import", False),
		]
	)


def _strict_enabled() -> bool:
	# Default ON to satisfy enterprise governance baseline.
	return is_feature_enabled("global_enterprise_compliance_strict", default=True)


def _require_cost_center() -> bool:
	# Optional hardening; can be enabled globally when teams are ready.
	return is_feature_enabled("global_require_cost_center", default=False)


def _ifrs_submit_enabled() -> bool:
	# User-requested strict enterprise posture.
	return is_feature_enabled("global_ifrs_submit_controls", default=True)


def _sum_payment_schedule(doc) -> float:
	total = 0.0
	for row in doc.get("payment_schedule") or []:
		total += flt(row.get("payment_amount"))
	return total


def _has_any_line_tax_rule(doc) -> bool:
	for row in doc.get("items") or []:
		if row.get("tax_rule"):
			return True
	return False


def _contains_stock_items(doc) -> bool:
	for row in doc.get("items") or []:
		item = row.get("item")
		if not item:
			continue
		if frappe.db.get_value("Item", item, "is_stock_item"):
			return True
	return False


def enforce_global_submit_compliance(doc, method=None):
	"""Submit-time controls for IFRS/enterprise governance."""
	if not _is_runtime_safe() or not _strict_enabled() or not _ifrs_submit_enabled():
		return
	if not getattr(doc, "doctype", None):
		return

	# IFRS 15: sales revenue recognition should not be detached from delivery for stock items.
	if doc.doctype == "Sales Invoice" and not cint(doc.get("is_return")):
		if _contains_stock_items(doc):
			has_delivery_link = bool(doc.get("delivery_note")) if doc.meta.has_field("delivery_note") else False
			update_stock = cint(doc.get("update_stock")) if doc.meta.has_field("update_stock") else 0
			is_pos = cint(doc.get("is_pos")) if doc.meta.has_field("is_pos") else 0
			if not has_delivery_link and not update_stock and not is_pos:
				frappe.throw(
					_(
						"IFRS 15 control transfer check failed: stock sales invoice must reference Delivery Note, "
						"or be POS/update_stock flow."
					),
					title=_("Compliance"),
				)

	# VAT governance: invoice must have tax rule at header or line-level (unless explicitly exempt process).
	if doc.doctype in {"Sales Invoice", "Purchase Invoice"} and (doc.get("items") or []):
		header_tax = doc.get("default_tax_rule") if doc.meta.has_field("default_tax_rule") else None
		if not header_tax and not _has_any_line_tax_rule(doc):
			frappe.throw(
				_("Tax Rule is required at header or item row for invoice compliance."),
				title=_("Compliance"),
			)

	# IFRS 9 / credit governance: credit invoices should have due date and coherent schedule.
	if doc.doctype in {"Sales Invoice", "Purchase Invoice"}:
		if doc.meta.has_field("due_date") and not doc.get("due_date"):
			frappe.throw(_("Due Date is mandatory for invoice compliance."), title=_("Compliance"))
		if doc.meta.has_field("payment_schedule") and (doc.get("payment_schedule") or []):
			total_schedule = _sum_payment_schedule(doc)
			grand_total = flt(doc.get("grand_total"))
			if abs(total_schedule - grand_total) > 0.0001:
				frappe.throw(
					_("Payment Schedule total must equal Grand Total."),
					title=_("Compliance"),
				)

	# Payment governance: allocated references cannot exceed paid amount.
	if doc.doctype == "Payment Entry" and doc.meta.has_field("references"):
		allocated = 0.0
		for row in doc.get("references") or []:
			allocated += flt(row.get("allocated_amount"))
		if allocated - flt(doc.get("paid_amount")) > 0.0001:
			frappe.throw(
				_("Allocated amount cannot exceed Paid Amount."),
				title=_("Compliance"),
			)


def enforce_global_enterprise_compliance(doc, method=None):
	"""Global non-destructive compliance guard for all business documents.

	Designed for cross-app usage without breaking framework internals:
	- Enforces company / branch / currency / FX coherence when fields exist.
	- Enforces due_date >= posting_date when both are present.
	- Optionally enforces cost_center on item rows via feature flag.
	"""
	if not _is_runtime_safe() or not _strict_enabled():
		return

	if not getattr(doc, "doctype", None) or doc.doctype in _SKIP_DOCTYPES:
		return

	meta = getattr(doc, "meta", None)
	if not meta:
		return

	has_field = meta.has_field

	if has_field("company") and not doc.get("company"):
		frappe.throw(_("Company is mandatory for compliance."), title=_("Compliance"))

	if has_field("branch") and not doc.get("branch"):
		frappe.throw(_("Branch is mandatory for compliance."), title=_("Compliance"))

	if has_field("currency"):
		currency = (doc.get("currency") or "").strip()
		if not currency:
			frappe.throw(_("Currency is mandatory for compliance."), title=_("Compliance"))
		if not frappe.db.exists("Currency", currency):
			frappe.throw(_("Currency {0} does not exist.").format(currency), title=_("Compliance"))

		if has_field("conversion_rate") and doc.get("company"):
			company_currency = frappe.db.get_value("Company", doc.get("company"), "default_currency")
			if company_currency and currency != company_currency and flt(doc.get("conversion_rate")) <= 0:
				frappe.throw(
					_("Conversion Rate must be greater than zero for foreign-currency transactions."),
					title=_("Compliance"),
				)

	if has_field("posting_date") and has_field("due_date") and doc.get("posting_date") and doc.get("due_date"):
		if getdate(doc.get("due_date")) < getdate(doc.get("posting_date")):
			frappe.throw(_("Due Date cannot be before Posting Date."), title=_("Compliance"))

	if not _require_cost_center():
		return

	# Optional strict dimensional governance on child rows.
	for table_field in ("items", "accounts"):
		if not has_field(table_field):
			continue
		for row in doc.get(table_field) or []:
			row_meta = getattr(row, "meta", None)
			if not row_meta:
				continue
			if row_meta.has_field("cost_center") and not row.get("cost_center"):
				frappe.throw(
					_("Row {0}: Cost Center is required by global policy.").format(row.idx),
					title=_("Compliance"),
				)
