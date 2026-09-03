# Copyright (c) 2026, ErpGenEx
"""Sync all vertical role portal + workcenter pages to Trading-style JS bootstrap."""

from __future__ import annotations

import frappe


def _reconnect_db_if_needed() -> None:
	"""Recover from stale MySQL connections after long migrate runs."""
	try:
		frappe.db.sql("SELECT 1")
	except Exception:
		site = frappe.local.site
		frappe.destroy()
		frappe.init(site)
		frappe.connect()


def execute():
	from omnexa_core.vertical_workcenter.portal_page_bootstrap import sync_all_standard_portal_pages

	# Pages are created by ensure_vertical_journey_portals; this patch only rewrites JS.
	sync_all_standard_portal_pages(import_db=False, files_only=True)
	_reconnect_db_if_needed()
