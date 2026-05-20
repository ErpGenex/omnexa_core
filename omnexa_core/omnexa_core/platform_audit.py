# Copyright (c) 2026, ErpGenEx
"""Central platform audit API (SAP BC-LOG / SLCA parity) — append-only, sidecar-only."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


def log_platform_event(
	event_name: str,
	source_doctype: str,
	source_docname: str,
	*,
	action: str = "",
	company: str | None = None,
	branch: str | None = None,
	ledger_domain: str = "General",
	payload: dict[str, Any] | None = None,
	amount: float | None = None,
	currency: str | None = None,
) -> str | None:
	"""Record a platform-level audit row. No-op unless ``platform_audit_api`` flag is enabled."""
	if not is_feature_enabled("platform_audit_api", default=True):
		return None

	serialized = json.dumps(payload or {}, sort_keys=True, default=str)
	event_hash = hashlib.sha256(
		f"{event_name}|{source_doctype}|{source_docname}|{serialized}".encode()
	).hexdigest()
	if frappe.db.get_value("Event Audit Log", {"event_hash": event_hash}, "name"):
		return event_hash

	log = frappe.new_doc("Event Audit Log")
	log.event_name = event_name
	log.source_doctype = source_doctype
	log.source_docname = source_docname
	log.action = action or ""
	log.ledger_domain = ledger_domain or "General"
	log.company = company
	log.branch = branch
	log.currency = currency or ""
	log.amount = float(amount or 0)
	log.event_payload = serialized
	log.event_hash = event_hash
	log.processing_status = "Projected"
	log.insert(ignore_permissions=True)
	return event_hash


def get_audit_trail_summary(company: str | None = None, limit: int = 50) -> list[dict]:
	"""Recent Event Audit Log rows for desk / integration (read-only)."""
	limit = max(1, min(int(limit or 50), 500))
	filters: dict[str, Any] = {}
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Event Audit Log",
		filters=filters,
		fields=[
			"name",
			"creation",
			"event_name",
			"source_doctype",
			"source_docname",
			"action",
			"ledger_domain",
			"company",
			"branch",
			"processing_status",
		],
		order_by="creation desc",
		limit=limit,
	)
