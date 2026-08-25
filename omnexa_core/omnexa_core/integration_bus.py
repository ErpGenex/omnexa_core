# Copyright (c) 2026, ErpGenEx
"""Wave 8 — Contract-based integration bus for financial core, inventory, sales, purchases, reports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

import frappe
from frappe import _

from omnexa_core.omnexa_core.activity_registry import INTEGRATION_COMMANDS

Handler = Callable[[dict[str, Any]], dict[str, Any]]


class IntegrationBusError(frappe.ValidationError):
	pass


@dataclass
class IntegrationCommandResult:
	ok: bool
	command: str
	source_app: str
	reference_doctype: str | None = None
	reference_name: str | None = None
	message: str = ""
	data: dict[str, Any] = field(default_factory=dict)
	idempotent_hit: bool = False

	def as_dict(self) -> dict[str, Any]:
		return {
			"ok": self.ok,
			"command": self.command,
			"source_app": self.source_app,
			"reference_doctype": self.reference_doctype,
			"reference_name": self.reference_name,
			"message": self.message,
			"data": self.data,
			"idempotent_hit": self.idempotent_hit,
		}


_HANDLERS: dict[str, Handler] = {}
_IDEMPOTENCY_CACHE: dict[str, dict[str, Any]] = {}


def register_command(command: str, handler: Handler) -> None:
	if command not in INTEGRATION_COMMANDS:
		frappe.log_error(f"Registering non-standard command: {command}", "Integration Bus")
	_HANDLERS[command] = handler


def _require(payload: dict[str, Any], *keys: str) -> None:
	for key in keys:
		if not payload.get(key):
			raise IntegrationBusError(_("Missing required field: {0}").format(key))


def _idempotency_key(command: str, source_app: str, payload: dict[str, Any], key: str | None) -> str:
	if key:
		return f"{command}:{source_app}:{key}"
	raw = json.dumps({"command": command, "source_app": source_app, "payload": payload}, sort_keys=True, default=str)
	return hashlib.sha256(raw.encode()).hexdigest()


def _ensure_accounting():
	if not frappe.db.exists("DocType", "Sales Invoice"):
		raise IntegrationBusError(_("omnexa_accounting is required for this command."))


def _apply_si_header(doc, payload: dict[str, Any]) -> None:
	if payload.get("due_date") and doc.meta.has_field("due_date"):
		doc.due_date = payload["due_date"]
	if payload.get("currency") and doc.meta.has_field("currency"):
		doc.currency = payload["currency"]
	if payload.get("conversion_rate") is not None and doc.meta.has_field("conversion_rate"):
		doc.conversion_rate = payload["conversion_rate"]
	if payload.get("remarks") and doc.meta.has_field("remarks"):
		doc.remarks = payload["remarks"]
	if payload.get("default_tax_rule") and doc.meta.has_field("default_tax_rule"):
		doc.default_tax_rule = payload["default_tax_rule"]
	if payload.get("is_pos") is not None and doc.meta.has_field("is_pos"):
		doc.is_pos = payload["is_pos"]
	if payload.get("update_stock") is not None and doc.meta.has_field("update_stock"):
		doc.update_stock = payload["update_stock"]
	if payload.get("taxes_and_charges") and doc.meta.has_field("taxes_and_charges"):
		doc.taxes_and_charges = payload["taxes_and_charges"]
	if payload.get("reference") and doc.meta.has_field("reference"):
		doc.reference = payload["reference"]
	if payload.get("external_reference") and doc.meta.has_field("external_reference"):
		doc.external_reference = payload["external_reference"]


def _append_si_item(doc, row: dict[str, Any]) -> None:
	item_row: dict[str, Any] = {
		"item_code": row.get("item_code"),
		"item_name": row.get("item_name") or row.get("description") or row.get("item_code"),
		"qty": row.get("qty") or 1,
		"rate": row.get("rate") or 0,
		"description": row.get("description"),
	}
	if row.get("item") and doc.meta.has_field("items"):
		item_row["item"] = row["item"]
	if row.get("income_account"):
		item_row["income_account"] = row["income_account"]
	if row.get("tax_rule") and doc.meta.has_field("items"):
		item_row["tax_rule"] = row["tax_rule"]
	if row.get("uom"):
		item_row["uom"] = row["uom"]
	if row.get("conversion_factor") is not None:
		item_row["conversion_factor"] = row["conversion_factor"]
	if row.get("amount") is not None:
		item_row["amount"] = row["amount"]
	doc.append("items", item_row)


def _finalize_doc(doc, payload: dict[str, Any]) -> dict[str, Any]:
	doc.insert(ignore_permissions=True)
	if payload.get("submit"):
		doc.submit()
	return {"reference_doctype": doc.doctype, "reference_name": doc.name, "docstatus": doc.docstatus}


def _handler_create_sales_invoice(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company", "customer")
	_ensure_accounting()
	doc = frappe.new_doc("Sales Invoice")
	doc.company = payload["company"]
	doc.customer = payload["customer"]
	if payload.get("branch") and doc.meta.has_field("branch"):
		doc.branch = payload["branch"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	_apply_si_header(doc, payload)
	for row in payload.get("items") or []:
		_append_si_item(doc, row)
	if payload.get("reference_doctype") and payload.get("reference_name"):
		if doc.meta.has_field("omnexa_source_doctype"):
			doc.omnexa_source_doctype = payload["reference_doctype"]
			doc.omnexa_source_name = payload["reference_name"]
	return _finalize_doc(doc, payload)


def _handler_create_purchase_invoice(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company", "supplier")
	_ensure_accounting()
	doc = frappe.new_doc("Purchase Invoice")
	doc.company = payload["company"]
	doc.supplier = payload["supplier"]
	if payload.get("branch") and frappe.get_meta("Purchase Invoice").has_field("branch"):
		doc.branch = payload["branch"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	for row in payload.get("items") or []:
		doc.append(
			"items",
			{
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name") or row.get("item_code"),
				"qty": row.get("qty") or 1,
				"rate": row.get("rate") or 0,
			},
		)
	doc.insert(ignore_permissions=True)
	if payload.get("submit"):
		doc.submit()
	return {"reference_doctype": "Purchase Invoice", "reference_name": doc.name, "docstatus": doc.docstatus}


def _handler_create_journal_entry(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company")
	_ensure_accounting()
	doc = frappe.new_doc("Journal Entry")
	doc.company = payload["company"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	doc.voucher_type = payload.get("voucher_type") or "Journal Entry"
	if payload.get("branch") and doc.meta.has_field("branch"):
		doc.branch = payload["branch"]
	if payload.get("reference") and doc.meta.has_field("reference"):
		doc.reference = payload["reference"]
	if payload.get("remarks") and doc.meta.has_field("remarks"):
		doc.remarks = payload["remarks"]
	for row in payload.get("accounts") or []:
		doc.append(
			"accounts",
			{
				"account": row.get("account"),
				"debit_in_account_currency": row.get("debit") or 0,
				"credit_in_account_currency": row.get("credit") or 0,
				"party_type": row.get("party_type"),
				"party": row.get("party"),
			},
		)
	return _finalize_doc(doc, payload)


def _append_stock_entry_item(doc, row: dict[str, Any]) -> None:
	item_row: dict[str, Any] = {
		"item_code": row.get("item_code"),
		"qty": row.get("qty") or 1,
		"s_warehouse": row.get("s_warehouse"),
		"t_warehouse": row.get("t_warehouse"),
	}
	if row.get("item") and doc.meta.has_field("items"):
		item_row["item"] = row["item"]
	if row.get("uom"):
		item_row["uom"] = row["uom"]
	if row.get("rate") is not None:
		if doc.meta.has_field("items") and frappe.get_meta("Stock Entry Item").has_field("rate"):
			item_row["rate"] = row["rate"]
		elif frappe.get_meta("Stock Entry Item").has_field("basic_rate"):
			item_row["basic_rate"] = row["rate"]
	if row.get("batch_no") and frappe.get_meta("Stock Entry Item").has_field("batch_no"):
		item_row["batch_no"] = row["batch_no"]
	if row.get("serial_no") and frappe.get_meta("Stock Entry Item").has_field("serial_no"):
		item_row["serial_no"] = row["serial_no"]
	doc.append("items", item_row)


def _handler_create_stock_entry(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company")
	if not frappe.db.exists("DocType", "Stock Entry"):
		raise IntegrationBusError(_("Stock Entry DocType not available."))
	doc = frappe.new_doc("Stock Entry")
	doc.company = payload["company"]
	purpose = payload.get("purpose") or payload.get("stock_entry_type") or "Material Issue"
	if doc.meta.has_field("purpose"):
		doc.purpose = purpose
	elif doc.meta.has_field("stock_entry_type"):
		doc.stock_entry_type = purpose
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	if payload.get("branch") and doc.meta.has_field("branch"):
		doc.branch = payload["branch"]
	if payload.get("from_warehouse") and doc.meta.has_field("from_warehouse"):
		doc.from_warehouse = payload["from_warehouse"]
	if payload.get("to_warehouse") and doc.meta.has_field("to_warehouse"):
		doc.to_warehouse = payload["to_warehouse"]
	if payload.get("remarks") and doc.meta.has_field("remarks"):
		doc.remarks = payload["remarks"]
	for row in payload.get("items") or []:
		_append_stock_entry_item(doc, row)
	return _finalize_doc(doc, payload)


def _handler_create_payment_entry(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company", "party_type", "party")
	_ensure_accounting()
	doc = frappe.new_doc("Payment Entry")
	doc.company = payload["company"]
	doc.party_type = payload["party_type"]
	doc.party = payload["party"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	doc.paid_amount = payload.get("paid_amount") or 0
	doc.received_amount = payload.get("received_amount") or payload.get("paid_amount") or 0
	doc.payment_type = payload.get("payment_type") or "Receive"
	return _finalize_doc(doc, payload)


def _handler_create_delivery_note(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company", "customer")
	if not frappe.db.exists("DocType", "Delivery Note"):
		raise IntegrationBusError(_("Delivery Note DocType not available."))
	doc = frappe.new_doc("Delivery Note")
	doc.company = payload["company"]
	doc.customer = payload["customer"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	for row in payload.get("items") or []:
		doc.append("items", {"item_code": row.get("item_code"), "qty": row.get("qty") or 1})
	return _finalize_doc(doc, payload)


def _handler_create_purchase_receipt(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company", "supplier")
	if not frappe.db.exists("DocType", "Purchase Receipt"):
		raise IntegrationBusError(_("Purchase Receipt DocType not available."))
	doc = frappe.new_doc("Purchase Receipt")
	doc.company = payload["company"]
	doc.supplier = payload["supplier"]
	doc.posting_date = payload.get("posting_date") or frappe.utils.today()
	for row in payload.get("items") or []:
		doc.append("items", {"item_code": row.get("item_code"), "qty": row.get("qty") or 1})
	doc.insert(ignore_permissions=True)
	return {"reference_doctype": "Purchase Receipt", "reference_name": doc.name, "docstatus": doc.docstatus}


def _handler_financial_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company")
	company = payload["company"]
	out: dict[str, Any] = {"company": company}
	if frappe.db.exists("DocType", "Sales Invoice"):
		out["sales_invoices"] = frappe.db.count("Sales Invoice", {"company": company, "docstatus": 1})
	if frappe.db.exists("DocType", "Purchase Invoice"):
		out["purchase_invoices"] = frappe.db.count("Purchase Invoice", {"company": company, "docstatus": 1})
	if frappe.db.exists("DocType", "Journal Entry"):
		out["journal_entries"] = frappe.db.count("Journal Entry", {"company": company, "docstatus": 1})
	return out


def _handler_inventory_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
	_require(payload, "company")
	company = payload["company"]
	out: dict[str, Any] = {"company": company}
	for dt in ("Stock Entry", "Delivery Note", "Purchase Receipt"):
		if frappe.db.exists("DocType", dt):
			out[dt.lower().replace(" ", "_")] = frappe.db.count(dt, {"company": company, "docstatus": 1})
	return out


def _register_builtin_handlers() -> None:
	register_command("accounting.create_sales_invoice", _handler_create_sales_invoice)
	register_command("accounting.create_purchase_invoice", _handler_create_purchase_invoice)
	register_command("accounting.create_journal_entry", _handler_create_journal_entry)
	register_command("accounting.create_payment_entry", _handler_create_payment_entry)
	register_command("inventory.create_stock_entry", _handler_create_stock_entry)
	register_command("inventory.create_delivery_note", _handler_create_delivery_note)
	register_command("inventory.create_purchase_receipt", _handler_create_purchase_receipt)
	register_command("reporting.get_financial_snapshot", _handler_financial_snapshot)
	register_command("reporting.get_inventory_snapshot", _handler_inventory_snapshot)


_register_builtin_handlers()


def dispatch_command(
	command: str,
	payload: dict[str, Any] | None = None,
	*,
	source_app: str,
	idempotency_key: str | None = None,
) -> IntegrationCommandResult:
	"""Dispatch a versioned integration command through the bus."""
	payload = dict(payload or {})
	if command not in _HANDLERS:
		raise IntegrationBusError(_("Unknown integration command: {0}").format(command))

	cache_key = _idempotency_key(command, source_app, payload, idempotency_key)
	cached = _IDEMPOTENCY_CACHE.get(cache_key)
	if cached:
		return IntegrationCommandResult(idempotent_hit=True, **cached)

	try:
		result_data = _HANDLERS[command](payload)
		out = IntegrationCommandResult(
			ok=True,
			command=command,
			source_app=source_app,
			reference_doctype=result_data.get("reference_doctype"),
			reference_name=result_data.get("reference_name"),
			message=_("Command completed."),
			data=result_data,
		)
	except Exception as exc:
		out = IntegrationCommandResult(
			ok=False,
			command=command,
			source_app=source_app,
			message=str(exc),
		)

	_IDEMPOTENCY_CACHE[cache_key] = {
		"ok": out.ok,
		"command": out.command,
		"source_app": out.source_app,
		"reference_doctype": out.reference_doctype,
		"reference_name": out.reference_name,
		"message": out.message,
		"data": out.data,
	}
	return out


@frappe.whitelist()
def execute_integration_command(
	command: str,
	payload: str | dict | None = None,
	source_app: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	frappe.only_for("System Manager")
	if isinstance(payload, str):
		payload = frappe.parse_json(payload) or {}
	source = (source_app or "").strip() or frappe.local.form_dict.get("app") or "unknown"
	return dispatch_command(command, payload, source_app=source, idempotency_key=idempotency_key).as_dict()


def list_integration_commands() -> list[str]:
	return sorted(_HANDLERS.keys())
