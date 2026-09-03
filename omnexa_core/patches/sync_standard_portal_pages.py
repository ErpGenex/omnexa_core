# Copyright (c) 2026, ErpGenEx
"""Sync all vertical role portal + workcenter pages to Trading-style JS bootstrap."""

from __future__ import annotations

import frappe


def execute():
	frappe.reload_doc("omnexa_core", "module", "vertical_workcenter")
	from omnexa_core.vertical_workcenter.portal_page_bootstrap import sync_all_standard_portal_pages

	sync_all_standard_portal_pages(import_db=True)
