# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Rename legacy workspaces and align title/label to canonical English names."""

from __future__ import annotations

import frappe

# Arabic legacy -> final (Desk routes + sidebar slug are derived from Workspace title/name)
_FINAL = (
	("إدارة العقارات", "Property Management"),
	("تطوير العقارات", "RE Development"),
	("تسويق العقارات", "RE Marketing"),
)
# Older EG-prefixed -> final
_EG_LEGACY = (
	("EG Property Management", "Property Management"),
	("EG RE Development", "RE Development"),
	("EG RE Marketing", "RE Marketing"),
)


def execute() -> None:
	for old, canonical in (*_FINAL, *_EG_LEGACY):
		_normalize_workspace(old, canonical)
	frappe.clear_cache()


def _normalize_workspace(arabic_or_eg_name: str, canonical: str) -> None:
	if not arabic_or_eg_name or not canonical:
		return
	has_old = frappe.db.exists("Workspace", arabic_or_eg_name)
	has_new = frappe.db.exists("Workspace", canonical)

	if has_old and has_new:
		frappe.delete_doc("Workspace", arabic_or_eg_name, force=True, ignore_permissions=True)
	elif has_old and not has_new:
		frappe.rename_doc("Workspace", arabic_or_eg_name, canonical, force=True, merge=False)

	if not frappe.db.exists("Workspace", canonical):
		return

	doc = frappe.get_doc("Workspace", canonical)
	changed = False
	if doc.label != canonical:
		doc.label = canonical
		changed = True
	if doc.title != canonical:
		doc.title = canonical
		changed = True
	if changed:
		doc.save(ignore_permissions=True)
