# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Set country_code=EG and tax_provider=einvoice_eta on all existing branches."""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.table_exists("tabBranch"):
		return
	meta = frappe.get_meta("Branch")
	if not meta.has_field("country_code"):
		return

	for name in frappe.get_all("Branch", pluck="name"):
		updates = {}
		code = (frappe.db.get_value("Branch", name, "country_code") or "").strip().upper()
		if not code:
			updates["country_code"] = "EG"
			code = "EG"
		if meta.has_field("tax_provider"):
			provider = (frappe.db.get_value("Branch", name, "tax_provider") or "").strip()
			if not provider:
				updates["tax_provider"] = "einvoice_eta" if code == "EG" else "einvoice_zatca"
		if updates:
			frappe.db.set_value("Branch", name, updates, update_modified=False)
