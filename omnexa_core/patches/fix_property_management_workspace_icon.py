# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""`building` is not a timeless desk icon — sidebar showed blank for Property Management."""

from __future__ import annotations

import frappe


def execute() -> None:
	for name in ("Property Management", "EG Property Management", "إدارة العقارات"):
		if frappe.db.exists("Workspace", name):
			frappe.db.set_value("Workspace", name, "icon", "organization", update_modified=False)
	frappe.clear_cache()
