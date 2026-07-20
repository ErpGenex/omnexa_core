"""Force-sync Branch DocType so Demo data tab appears after Financial."""

from __future__ import annotations

import frappe
from frappe.modules.import_file import import_file_by_path


def execute() -> None:
	if not frappe.db.exists("DocType", "Branch"):
		return

	path = frappe.get_app_path("omnexa_core", "omnexa_core", "doctype", "branch", "branch.json")
	import_file_by_path(path, force=True, ignore_version=True)

	if not frappe.db.exists("DocField", {"parent": "Branch", "fieldname": "tab_break_branch_demo_data"
	}):
		frappe.throw("Branch Demo data tab missing after sync — check omnexa_core/branch.json")

	if not frappe.db.exists("DocField", {"parent": "Branch", "fieldname": "branch_demo_btn_seed_masters"
	}):
		frappe.throw("Branch demo masters button missing after sync — check omnexa_core/branch.json")

	frappe.clear_cache(doctype="Branch")
