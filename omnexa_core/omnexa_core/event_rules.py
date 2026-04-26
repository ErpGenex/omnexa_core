from __future__ import annotations

from typing import Any

import frappe

DEFAULT_EVENT_RULES: dict[str, dict[str, Any]] = {
	"SalesInvoice.Submitted": {"enabled": 1, "ledger_domain": "Accounting"},
	"SalesInvoice.Cancelled": {"enabled": 1, "ledger_domain": "Accounting"},
	"PurchaseInvoice.Submitted": {"enabled": 1, "ledger_domain": "Accounting"},
	"PurchaseInvoice.Cancelled": {"enabled": 1, "ledger_domain": "Accounting"},
	"PaymentEntry.Submitted": {"enabled": 1, "ledger_domain": "Accounting"},
	"PaymentEntry.Cancelled": {"enabled": 1, "ledger_domain": "Accounting"},
	"JournalEntry.Submitted": {"enabled": 1, "ledger_domain": "Accounting"},
	"JournalEntry.Cancelled": {"enabled": 1, "ledger_domain": "Accounting"},
	"StockEntry.Submitted": {"enabled": 1, "ledger_domain": "Inventory"},
	"StockEntry.Cancelled": {"enabled": 1, "ledger_domain": "Inventory"},
	"DeliveryNote.Submitted": {"enabled": 1, "ledger_domain": "Inventory"},
	"DeliveryNote.Cancelled": {"enabled": 1, "ledger_domain": "Inventory"},
	"PurchaseReceipt.Submitted": {"enabled": 1, "ledger_domain": "Inventory"},
	"PurchaseReceipt.Cancelled": {"enabled": 1, "ledger_domain": "Inventory"},
}


def resolve_rule(event_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
	"""
	Resolve effective event processing rule (overlay-safe).
	Order:
	1) built-in defaults
	2) site_config override: omnexa_event_rules (dict by event_name)
	"""
	base = dict(DEFAULT_EVENT_RULES.get(event_name, {"enabled": 1, "ledger_domain": "General"}))
	overrides = frappe.conf.get("omnexa_event_rules") or {}
	if isinstance(overrides, dict):
		custom = overrides.get(event_name)
		if isinstance(custom, dict):
			base.update(custom)

	base["enabled"] = bool(base.get("enabled", 1))
	base["ledger_domain"] = str(base.get("ledger_domain") or "General")
	base["event_name"] = event_name
	if payload and "company" in payload and payload.get("company"):
		base["company"] = str(payload.get("company"))
	return base

