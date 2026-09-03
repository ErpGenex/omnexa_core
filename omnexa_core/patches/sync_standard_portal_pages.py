# Copyright (c) 2026, ErpGenEx
"""Sync all vertical role portal + workcenter pages to Trading-style JS bootstrap."""

from __future__ import annotations

import frappe


def execute():
	from omnexa_core.vertical_workcenter.portal_page_bootstrap import sync_all_standard_portal_pages

	# Pages are created by ensure_vertical_journey_portals; this patch only rewrites JS.
	sync_all_standard_portal_pages(import_db=False, files_only=True)
