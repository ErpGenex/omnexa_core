# Copyright (c) 2026, ErpGenEx
"""Scaffold {slug}-workcenter pages for tier-1/2 vertical apps."""

from __future__ import annotations

import frappe

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY
from omnexa_core.vertical_workcenter.scaffold import scaffold_workcenter


def execute():
	installed = set(frappe.get_installed_apps() or [])
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("reference") or entry.get("status") == "finance_group":
			continue
		if entry.get("tier", 99) > 2:
			continue
		app = entry["app"]
		if app not in installed:
			continue
		wc = entry["workcenter"]
		try:
			scaffold_workcenter(app, sync_hooks=entry.get("tier") == 1)
		except Exception:
			frappe.log_error(title=f"Workcenter scaffold failed: {app}")
	frappe.db.commit()
