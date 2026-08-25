# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.utils import cint


_DEFAULT_SHARED_MASTERS = frozenset({"Customer", "Item", "Supplier", "Warehouse"})

_SKIP_BRANCH_FIELD_DOCTYPES = frozenset(
	{
		"Branch",
		"Company",
		"User",
		"Role",
		"Module Def",
		"DocType",
		"Custom Field",
		"Property Setter",
		"Patch Log",
		"Version",
		"Error Log",
		"File",
	}
)


def get_isolation_settings() -> dict:
	if not frappe.db.exists("DocType", "Omnexa Core Settings"):
		return {
			"allow_shared_null_branch_masters": True,
			"shared_master_doctypes": sorted(_DEFAULT_SHARED_MASTERS),
			"auto_branch_field_sweep": True,
		}
	row = frappe.get_single("Omnexa Core Settings")
	shared = [
		line.strip()
		for line in (row.shared_master_doctypes or "").splitlines()
		if line.strip()
	]
	if not shared:
		shared = sorted(_DEFAULT_SHARED_MASTERS)
	return {
		"allow_shared_null_branch_masters": cint(row.allow_shared_null_branch_masters),
		"shared_master_doctypes": shared,
		"auto_branch_field_sweep": cint(getattr(row, "auto_branch_field_sweep", 1)),
	}


def is_shared_master_doctype(doctype: str) -> bool:
	settings = get_isolation_settings()
	if not settings["allow_shared_null_branch_masters"]:
		return False
	return doctype in set(settings["shared_master_doctypes"])


def should_skip_branch_sweep(doctype: str) -> bool:
	if doctype in _SKIP_BRANCH_FIELD_DOCTYPES:
		return True
	meta = frappe.get_meta(doctype)
	if meta.issingle or meta.istable:
		return True
	if is_shared_master_doctype(doctype):
		return True
	return False
