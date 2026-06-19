# Copyright (c) 2026, ErpGenEx
"""Shared desk permission for Finance Group vertical apps."""

from __future__ import annotations

import frappe


def has_app_permission() -> bool:
	if frappe.session.user == "Administrator":
		return True
	if "System Manager" in (frappe.get_roles() or []):
		return True
	finance_roles = {r.strip() for r in (frappe.get_roles() or []) if r.strip().startswith("Finance ")}
	return bool(finance_roles)
