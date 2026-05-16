# Copyright (c) 2026, Omnexa
# License: MIT

"""Central daily registry for Erpgenex vertical scheduled jobs (GAP-X-01)."""

from __future__ import annotations

import frappe


def run_erpgenex_daily_jobs() -> None:
	"""Invoke optional cross-app daily maintenance (each job is best-effort)."""
	_run("erpgenex_realestate_sales.tasks.expire_unit_reservations")
	_run("erpgenex_property_mgmt.escalation.apply_due_escalations")
	_run("erpgenex_realestate_dev.tasks.flag_overdue_permit_milestones")


def _run(dotted_path: str) -> None:
	try:
		frappe.get_attr(dotted_path)()
	except Exception:
		frappe.log_error(title=f"Erpgenex scheduler: {dotted_path}")
