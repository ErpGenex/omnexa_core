from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.event_rules import resolve_rule

ACCOUNTING_DOCTYPES = {
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
}

INVENTORY_DOCTYPES = {
	"Stock Entry",
	"Delivery Note",
	"Purchase Receipt",
}


def accounting_audit_handler(event_name: str, payload: dict[str, Any], doc) -> None:
	if getattr(doc, "doctype", "") not in ACCOUNTING_DOCTYPES:
		return
	rule = resolve_rule(event_name=event_name, payload=payload)
	if not rule.get("enabled", True):
		return
	ledger_domain = str(rule.get("ledger_domain") or "Accounting")
	_insert_event_audit_log(event_name=event_name, payload=payload, doc=doc, ledger_domain=ledger_domain)


def inventory_audit_handler(event_name: str, payload: dict[str, Any], doc) -> None:
	if getattr(doc, "doctype", "") not in INVENTORY_DOCTYPES:
		return
	rule = resolve_rule(event_name=event_name, payload=payload)
	if not rule.get("enabled", True):
		return
	ledger_domain = str(rule.get("ledger_domain") or "Inventory")
	_insert_event_audit_log(event_name=event_name, payload=payload, doc=doc, ledger_domain=ledger_domain)


def _insert_event_audit_log(event_name: str, payload: dict[str, Any], doc, ledger_domain: str) -> None:
	"""
	Append-only projection for event audit.
	This handler is intentionally sidecar-only and does not mutate business documents.
	"""
	serialized = json.dumps(payload or {}, sort_keys=True, default=str)
	event_hash = hashlib.sha256(f"{event_name}|{doc.doctype}|{doc.name}|{serialized}".encode()).hexdigest()
	exists = frappe.db.get_value("Event Audit Log", {"event_hash": event_hash}, "name")
	if exists:
		return

	log = frappe.new_doc("Event Audit Log")
	log.event_name = event_name
	log.source_doctype = doc.doctype
	log.source_docname = doc.name
	log.action = str((payload or {}).get("action") or "")
	log.ledger_domain = ledger_domain
	log.company = getattr(doc, "company", None)
	log.branch = getattr(doc, "branch", None)
	log.currency = _pick_first_attr(doc, ("currency", "party_account_currency", "account_currency"))
	log.amount = _pick_amount(doc)
	log.event_payload = serialized
	log.event_hash = event_hash
	log.processing_status = "Projected"
	log.insert(ignore_permissions=True)


def _pick_first_attr(doc, attrs: tuple[str, ...]) -> str:
	for key in attrs:
		value = getattr(doc, key, None)
		if value:
			return str(value)
	return ""


def _pick_amount(doc) -> float:
	for key in ("grand_total", "base_grand_total", "paid_amount", "total", "base_total"):
		value = getattr(doc, key, None)
		if value is None:
			continue
		try:
			return float(value)
		except Exception:
			continue
	return 0.0
