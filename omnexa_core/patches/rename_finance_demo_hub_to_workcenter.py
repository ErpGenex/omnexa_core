# Copyright (c) 2026, ErpGenEx
"""Rename Finance Demo Hub page → Finance Workcenter."""

from __future__ import annotations

import frappe


def execute():
	from omnexa_core.omnexa_core.finance_demo.finance_workcenter import (
		LEGACY_DEMO_PAGE,
		WORKCENTER_PAGE,
		ensure_workcenter_page,
		sync_workcenter_page_roles,
	)

	ensure_workcenter_page()

	if frappe.db.exists("Page", LEGACY_DEMO_PAGE) and not frappe.db.exists("Page", WORKCENTER_PAGE):
		try:
			frappe.rename_doc("Page", LEGACY_DEMO_PAGE, WORKCENTER_PAGE, force=True, merge=False)
		except Exception:
			frappe.db.set_value(
				"Page",
				LEGACY_DEMO_PAGE,
				{"name": WORKCENTER_PAGE, "page_name": WORKCENTER_PAGE, "title": "Finance Workcenter"
	},
			)

	if frappe.db.exists("Page", WORKCENTER_PAGE):
		frappe.db.set_value("Page", WORKCENTER_PAGE, "title", "Finance Workcenter", update_modified=False)

	sync_workcenter_page_roles()
	frappe.db.commit()
