# Copyright (c) 2026, ErpGenEx
"""Whitelist APIs for SAP parity wave A (tenant license + audit trail)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.omnexa_license import verify_app_license
from omnexa_core.omnexa_core.platform_audit import get_audit_trail_summary, log_platform_event


@frappe.whitelist()
def get_tenant_license_snapshot(apps: str | None = None) -> dict:
	"""Return license status per app slug (multi-tenant / marketplace parity)."""
	raw = (apps or "").strip()
	slugs = [s.strip() for s in raw.split(",") if s.strip()] if raw else ["omnexa_core"]
	out = {}
	for slug in slugs:
		try:
			result = verify_app_license(slug)
			out[slug] = {
				"status": result.status,
				"message": getattr(result, "message", "") or "",
				"expires_at": getattr(result, "expires_at", None)}
		except Exception as exc:
			out[slug] = {"status": "error", "message": str(exc)
	}
	return {"apps": out, "site": frappe.local.site
	}


@frappe.whitelist()
def get_platform_audit_summary(company: str | None = None, limit: int = 50) -> dict:
	"""Read-only audit trail summary (Event Audit Log)."""
	return {
		"company": company,
		"rows": get_audit_trail_summary(company=company, limit=limit)}


@frappe.whitelist()
def record_platform_audit_event(
	event_name: str,
	source_doctype: str,
	source_docname: str,
	action: str = "",
	company: str | None = None,
	branch: str | None = None,
	ledger_domain: str = "General",
) -> dict:
	"""Explicit audit hook for integrations (append-only)."""
	event_hash = log_platform_event(
		event_name,
		source_doctype,
		source_docname,
		action=action,
		company=company,
		branch=branch,
		ledger_domain=ledger_domain,
	)
	return {"event_hash": event_hash, "recorded": bool(event_hash)
	}
