"""Force-sync Company DocType so Demo data tab appears after Additional."""

from __future__ import annotations

import frappe
from frappe.modules.import_file import import_file_by_path


def execute() -> None:
	if not frappe.db.exists("DocType", "Company"):
		return

	path = frappe.get_app_path("omnexa_core", "omnexa_core", "doctype", "company", "company.json")
	import_file_by_path(path, force=True, ignore_version=True)

	if not frappe.db.exists("DocField", {"parent": "Company", "fieldname": "tab_break_demo_data"}):
		frappe.throw("Company Demo data tab missing after sync — check omnexa_core/company.json")

	frappe.clear_cache(doctype="Company")
