# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""JSON structured logging for ERPGenex operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import frappe


def log_event(event: str, **fields) -> None:
	"""Write a structured log line to Error Log (info-level operational events)."""
	payload = {
		"ts": datetime.now(timezone.utc).isoformat(),
		"event": event,
		"site": getattr(frappe.local, "site", None),
		"user": getattr(getattr(frappe.local, "session", None), "user", None),
		**fields}
	try:
		frappe.logger("omnexa").info(json.dumps(payload, ensure_ascii=False, default=str))
	except Exception:
		pass
	if frappe.conf.get("omnexa_structured_log_to_error_log"):
		frappe.log_error(json.dumps(payload, ensure_ascii=False, default=str), f"Omnexa: {event}")
