# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled
from omnexa_core.omnexa_core.procurement.three_way_match import validate_purchase_invoice_three_way_match
from omnexa_core.omnexa_core.procurement.budget import validate_budget_for_purchase
from omnexa_core.omnexa_core.procurement.approval import enforce_purchase_approval
from omnexa_core.omnexa_core.finance.api import validate_finance_submit_controls


_SKIP_DOCTYPES = {
	"DocType",
	"Custom Field",
	"Property Setter",
	"Patch Log",
	"Version",
	"Error Log",
	"File",
	"Module Def",
	"Event Audit Log",
}

# Master data uses default_currency on Company, not transaction currency.
_CURRENCY_EXEMPT_DOCTYPES = frozenset(
	{
		"Company",
		"Branch",
		"Customer",
		"Supplier",
		"Item",
		"Warehouse",
		"GL Account",
		"Cost Center",
	}
)


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


def _ifrs16_enabled() -> bool:
	return is_feature_enabled("global_ifrs16_lease_controls", default=True)


def _ias21_enabled() -> bool:
	return is_feature_enabled("global_ias21_fx_controls", default=True)


def _ifrs9_enabled() -> bool:
	return is_feature_enabled("global_ifrs9_ecl_controls", default=True)

def _purchase_three_way_enabled() -> bool:
	return is_feature_enabled("global_purchase_three_way_match", default=True)

def _purchase_budget_enabled() -> bool:
	return is_feature_enabled("global_purchase_budget_controls", default=False)

def _purchase_approval_enabled() -> bool:
	return is_feature_enabled("global_purchase_approval_matrix", default=False)

def _inventory_controls_enabled() -> bool:
	return is_feature_enabled("global_inventory_controls", default=True)

def _prevent_negative_stock() -> bool:
	return is_feature_enabled("global_inventory_prevent_negative_stock", default=True)

def _inventory_adjustment_approval_enabled() -> bool:
	return is_feature_enabled("global_inventory_adjustment_approval", default=True)


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


def _is_foreign_currency_doc(doc) -> bool:
	if not doc.meta.has_field("currency") or not doc.get("company"):
		return False
	company_currency = frappe.db.get_value("Company", doc.get("company"), "default_currency")
	return bool(company_currency and doc.get("currency") and doc.get("currency") != company_currency)


def _journal_has_lease_accounts(doc) -> tuple[bool, bool]:
	"""Return (has_rou_asset, has_lease_liability) by account_number lookup."""
	has_rou = False
	has_lease_liability = False
	for row in doc.get("accounts") or []:
		acc = row.get("account")
		if not acc:
			continue
		acc_no = frappe.db.get_value("GL Account", acc, "account_number") or ""
		if str(acc_no).startswith("1204"):
			has_rou = True
		if str(acc_no).startswith("2106") or str(acc_no).startswith("2202"):
			has_lease_liability = True
	return has_rou, has_lease_liability


def _compliance_fail(doc, rule_code: str, message: str):
	payload = {
		"rule_code": rule_code,
		"doctype": getattr(doc, "doctype", None),
		"name": getattr(doc, "name", None),
		"company": doc.get("company") if getattr(doc, "meta", None) and doc.meta.has_field("company") else None,
		"branch": doc.get("branch") if getattr(doc, "meta", None) and doc.meta.has_field("branch") else None,
		"message": message,
	}
	try:
		frappe.log_error(
			message=json.dumps(payload, ensure_ascii=False),
			title=f"Compliance: {rule_code}",
		)
	except Exception:
		pass
	frappe.throw(_(message), title=_("Compliance"))


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
				_compliance_fail(
					doc,
					"IFRS15_DELIVERY_LINK",
					"IFRS 15 control transfer check failed: stock sales invoice must reference Delivery Note, or be POS/update_stock flow.",
				)

	# VAT governance: invoice must have tax rule at header or line-level (or explicit manual tax rate).
	if doc.doctype in {"Sales Invoice", "Purchase Invoice"} and (doc.get("items") or []):
		header_tax = doc.get("default_tax_rule") if doc.meta.has_field("default_tax_rule") else None
		manual_rate = (
			doc.meta.has_field("tax_rate") and flt(doc.get("tax_rate")) > 0
		)
		if not header_tax and not _has_any_line_tax_rule(doc) and not manual_rate:
			_compliance_fail(
				doc,
				"TAX_RULE_REQUIRED",
				"Tax Rule is required at header or item row for invoice compliance. "
				"Create a Tax Rule for this company (Accounting → Tax Rule) or set Default Tax Rule on the invoice.",
			)

	# IFRS 9 / credit governance: credit invoices should have due date and coherent schedule.
	if doc.doctype in {"Sales Invoice", "Purchase Invoice"}:
		if doc.meta.has_field("due_date") and not doc.get("due_date"):
			_compliance_fail(doc, "DUE_DATE_REQUIRED", "Due Date is mandatory for invoice compliance.")
		if doc.meta.has_field("payment_schedule") and (doc.get("payment_schedule") or []):
			total_schedule = _sum_payment_schedule(doc)
			grand_total = flt(doc.get("grand_total"))
			if abs(total_schedule - grand_total) > 0.0001:
				_compliance_fail(
					doc,
					"PAYMENT_SCHEDULE_MISMATCH",
					"Payment Schedule total must equal Grand Total.",
				)

	# IAS 21: foreign-currency transactions require explicit conversion rate.
	if _ias21_enabled() and doc.doctype in {"Sales Invoice", "Purchase Invoice", "Payment Entry"}:
		if _is_foreign_currency_doc(doc):
			if not doc.meta.has_field("conversion_rate") or flt(doc.get("conversion_rate")) <= 0:
				_compliance_fail(
					doc,
					"IAS21_CONVERSION_RATE",
					"IAS 21 control failed: foreign-currency transaction requires valid conversion rate.",
				)

	# Procurement governance: three-way match for Purchase Invoice.
	if doc.doctype == "Purchase Invoice" and _purchase_three_way_enabled():
		try:
			validate_purchase_invoice_three_way_match(doc, tolerance_ratio=0.01)
		except frappe.ValidationError:
			# already thrown with a message
			raise
		except Exception:
			# never crash submit for unexpected schema issues; still enforce as strict posture
			_compliance_fail(doc, "PURCHASE_3WAY_MATCH", "3-way match validation failed due to an unexpected error.")

	# Optional: budget controls (non-breaking default OFF).
	if _purchase_budget_enabled() and doc.doctype in {"Purchase Order", "Purchase Invoice"}:
		try:
			validate_budget_for_purchase(doc)
		except frappe.ValidationError:
			raise
		except Exception:
			_compliance_fail(doc, "PURCHASE_BUDGET", "Budget control failed due to an unexpected error.")

	# Optional: approval matrix by role (non-breaking default OFF).
	if _purchase_approval_enabled() and doc.doctype in {"Purchase Order", "Purchase Invoice"}:
		try:
			enforce_purchase_approval(doc)
		except frappe.ValidationError:
			raise
		except Exception:
			_compliance_fail(doc, "PURCHASE_APPROVAL", "Approval matrix enforcement failed due to an unexpected error.")

	# Inventory governance on stock movements.
	if _inventory_controls_enabled() and doc.doctype == "Stock Entry":
		# Traceability for items marked as batch/serial tracked.
		for row in doc.get("items") or []:
			item = row.get("item")
			if not item:
				continue
			if cint(frappe.db.get_value("Item", item, "has_batch_no")):
				has_batch_or_serial = bool((row.get("batch_no") or "").strip() or (row.get("serial_no") or "").strip())
				if not has_batch_or_serial:
					_compliance_fail(
						doc,
						"IAS2_TRACEABILITY",
						_("Stock traceability control: tracked item requires batch or serial in row {0}.").format(row.idx),
					)

		# Prevent negative stock unless disabled by feature flag.
		if _prevent_negative_stock() and (doc.get("purpose") in {"Material Issue", "Material Transfer"}):
			for row in doc.get("items") or []:
				qty = flt(row.get("qty"))
				if qty <= 0:
					continue
				item = row.get("item")
				if not item:
					continue
				current_qty = flt(frappe.db.get_value("Item", item, "current_stock_qty") or 0)
				if qty - current_qty > 0.0001:
					_compliance_fail(
						doc,
						"NEGATIVE_STOCK_PREVENTED",
						_("Negative stock prevented for item {0}. Available={1}, Required={2}").format(item, current_qty, qty),
					)

		# Stock adjustment requires reason + manager-style approval.
		entry_type = (doc.get("entry_type") or "").strip() if doc.meta.has_field("entry_type") else ""
		if entry_type in {"Stock Adjustment", "Opening Stock"}:
			reason = (doc.get("adjustment_reason") or "").strip() if doc.meta.has_field("adjustment_reason") else ""
			if not reason:
				_compliance_fail(doc, "ADJUSTMENT_REASON_REQUIRED", "Stock adjustment requires adjustment reason.")
			if _inventory_adjustment_approval_enabled():
				roles = set(frappe.get_roles() or [])
				if "System Manager" not in roles and "Accounts Manager" not in roles:
					_compliance_fail(
						doc,
						"ADJUSTMENT_APPROVAL_REQUIRED",
						"Stock adjustment requires manager approval role (Accounts Manager/System Manager).",
					)

	# Finance governance (GL, payment, period-sensitive entries).
	if doc.doctype in {"Journal Entry", "Payment Entry"}:
		try:
			validate_finance_submit_controls(doc)
		except frappe.ValidationError:
			raise
		except Exception:
			_compliance_fail(doc, "FINANCE_SUBMIT_CONTROL", "Finance submit controls failed due to unexpected error.")

	# IFRS 9: high credit utilization needs explicit risk note/approval context.
	if _ifrs9_enabled() and doc.doctype == "Sales Invoice" and not cint(doc.get("is_return")):
		customer = doc.get("customer")
		if customer:
			limit = flt(frappe.db.get_value("Customer", customer, "credit_limit") or 0)
			if limit > 0 and flt(doc.get("grand_total")) >= (0.8 * limit):
				reason = (doc.get("credit_limit_override_reason") or "").strip() if doc.meta.has_field("credit_limit_override_reason") else ""
				if not reason:
					_compliance_fail(
						doc,
						"IFRS9_HIGH_UTILIZATION",
						"IFRS 9 control: high credit utilization invoice requires risk/override reason.",
					)

	# IFRS 16: lease journal entries should include both ROU asset and lease liability legs.
	if _ifrs16_enabled() and doc.doctype == "Journal Entry":
		remarks = (doc.get("remarks") or "").lower()
		is_lease_context = "lease" in remarks or "ifrs 16" in remarks or "ايجار" in remarks
		if is_lease_context:
			has_rou, has_lease_liability = _journal_has_lease_accounts(doc)
			if not (has_rou and has_lease_liability):
				_compliance_fail(
					doc,
					"IFRS16_LEASE_STRUCTURE",
					"IFRS 16 control failed: lease entry must include both Right-of-Use asset and Lease Liability accounts.",
				)

	# Payment governance: allocated references cannot exceed paid amount.
	if doc.doctype == "Payment Entry" and doc.meta.has_field("references"):
		allocated = 0.0
		for row in doc.get("references") or []:
			allocated += flt(row.get("allocated_amount"))
		if allocated - flt(doc.get("paid_amount")) > 0.0001:
			_compliance_fail(doc, "PAYMENT_ALLOCATION_EXCEEDED", "Allocated amount cannot exceed Paid Amount.")


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

	if has_field("currency") and doc.doctype not in _CURRENCY_EXEMPT_DOCTYPES:
		if not (doc.get("currency") or "").strip() and doc.get("company") and has_field("company"):
			comp_curr = frappe.db.get_value("Company", doc.get("company"), "default_currency")
			if comp_curr:
				doc.currency = comp_curr
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
