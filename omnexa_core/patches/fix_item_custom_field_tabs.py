# Copyright (c) 2026, ErpGenex — fix Item custom field chain after first migrate

from __future__ import annotations

import frappe


def execute():
	for old in ("inventory_enterprise_section", "attachments_section"):
		name = frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": old})
		if name:
			frappe.delete_doc("Custom Field", name, force=1, ignore_permissions=True)

	updates = {
		"supporting_attachment": "qr_code",
	}
	for fieldname, insert_after in updates.items():
		if frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": fieldname}):
			frappe.db.set_value("Custom Field", {"dt": "Item", "fieldname": fieldname}, "insert_after", insert_after)

	frappe.db.commit()
	frappe.clear_cache(doctype="Item")
