"""Force-sync Company DocType so Activity websites demo tab and seed button exist."""

from __future__ import annotations

import frappe
from frappe.modules.import_file import import_file_by_path


def execute() -> None:
	if not frappe.db.exists("DocType", "Company"):
		return

	path = frappe.get_app_path("omnexa_core", "omnexa_core", "doctype", "company", "company.json")
	import_file_by_path(path, force=True, ignore_version=True)

	required = (
		"tab_break_activity_website",
		"demo_activity_website_help",
		"demo_btn_seed_activity_website",
	)
	for fieldname in required:
		if not frappe.db.exists("DocField", {"parent": "Company", "fieldname": fieldname}):
			frappe.throw(
				f"Company Activity websites field '{fieldname}' missing after sync — check company.json"
			)

	frappe.clear_cache(doctype="Company")
