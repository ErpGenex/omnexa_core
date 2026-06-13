# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Retail POS → Sales Invoice e-invoice bridge."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

WALKIN_CUSTOMER_NAME = "Retail Walk-in Customer"


def resolve_retail_pos_company_branch(user: str | None = None) -> tuple[str, str]:
	"""Resolve company/branch for POS using the same fallbacks as desk branch access."""
	from omnexa_core.omnexa_core.branch_access import get_default_branch, get_default_company

	user = user or frappe.session.user
	company = get_default_company(user)
	branch = get_default_branch(company, user) if company else None

	if not company:
		frappe.throw(
			_(
				"No company is available for your user. Set a default Company in Settings, "
				"or ask an administrator to configure User Branch Access."
			),
			title=_("Retail POS"),
		)
	if not branch:
		frappe.throw(
			_("No branch is available for company {0}. Create a Branch or assign User Branch Access.").format(
				frappe.bold(company)
			),
			title=_("Retail POS"),
		)

	if not frappe.defaults.get_user_default("Company", user):
		frappe.defaults.set_user_default("Company", company, user)
	if not frappe.defaults.get_user_default("Branch", user):
		frappe.defaults.set_user_default("Branch", branch, user)

	return company, branch


def resolve_pos_profile(company: str, branch: str | None = None) -> str | None:
	filters: dict[str, Any] = {"company": company, "is_active": 1}
	if branch:
		filters["branch"] = branch
	return frappe.db.get_value("POS Profile", filters, "name", order_by="modified desc")


def resolve_retail_pos_eta_billing_type(branch: str) -> str:
	"""Use E-Receipt or E-Invoice when the branch supports it; otherwise Regular."""
	if not frappe.get_meta("Sales Invoice").has_field("eta_billing_type"):
		return "Regular"
	try:
		from omnexa_einvoice.branch_eta import branch_einvoice_enabled, branch_ereceipt_enabled
		from omnexa_einvoice.sales_invoice_eta import (
			ETA_BILLING_EINVOICE,
			ETA_BILLING_ERECEIPT,
			ETA_BILLING_REGULAR,
		)

		if branch_ereceipt_enabled(branch):
			return ETA_BILLING_ERECEIPT
		if branch_einvoice_enabled(branch):
			return ETA_BILLING_EINVOICE
		return ETA_BILLING_REGULAR
	except ImportError:
		return "Regular"


def _default_customer_group() -> str:
	if frappe.db.exists("DocType", "Selling Settings"):
		val = frappe.db.get_single_value("Selling Settings", "customer_group")
		if val:
			return val
	return "Individual"


def _default_territory() -> str:
	if frappe.db.exists("DocType", "Selling Settings"):
		val = frappe.db.get_single_value("Selling Settings", "territory")
		if val:
			return val
	return "All Territories"


def ensure_walkin_customer(company: str) -> str:
	existing = frappe.db.get_value("Customer", {"customer_name": WALKIN_CUSTOMER_NAME, "company": company}, "name")
	if existing:
		return existing
	meta = frappe.get_meta("Customer")
	payload: dict[str, Any] = {
		"doctype": "Customer",
		"customer_name": WALKIN_CUSTOMER_NAME,
		"company": company,
	}
	if meta.has_field("status"):
		payload["status"] = "Active"
	if meta.has_field("customer_type"):
		payload["customer_type"] = "Individual"
	if meta.has_field("customer_group"):
		payload["customer_group"] = _default_customer_group()
	if meta.has_field("territory"):
		payload["territory"] = _default_territory()
	customer = frappe.get_doc(payload)
	customer.insert(ignore_permissions=True)
	return customer.name


def dispatch_einvoice_for_sales_invoice(invoice_name: str) -> dict[str, Any]:
	if "omnexa_einvoice" not in frappe.get_installed_apps():
		return {"status": "skipped", "reason": "omnexa_einvoice not installed"}
	try:
		from omnexa_einvoice.sales_invoice_eta import sales_invoice_is_eta_billing

		inv = frappe.get_doc("Sales Invoice", invoice_name)
		if not sales_invoice_is_eta_billing(inv):
			return {"status": "skipped", "reason": "regular_billing"}

		from omnexa_einvoice.tax_engine.dispatch import dispatch_tax_for_document

		return dispatch_tax_for_document("Sales Invoice", invoice_name, branch=getattr(inv, "branch", None))
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Retail POS e-invoice dispatch")
		return {"status": "error", "message": str(exc)}


def get_einvoice_receipt_context(invoice_name: str) -> dict[str, Any]:
	out: dict[str, Any] = {"qr_image_base64": "", "uuid": "", "sales_invoice": invoice_name}
	if "omnexa_einvoice" not in frappe.get_installed_apps():
		return out
	try:
		from omnexa_einvoice.einvoice_print.context import get_sales_invoice_print_context

		ctx = get_sales_invoice_print_context(invoice_name)
		tax = ctx.get("tax") or {}
		out["qr_image_base64"] = tax.get("qr_image_base64") or ""
		out["uuid"] = tax.get("uuid") or ""
		out["authority_status"] = tax.get("authority_status") or tax.get("status") or ""
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Retail receipt einvoice context")
	return out
