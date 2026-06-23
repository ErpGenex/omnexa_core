# Copyright (c) 2026, Omnexa and contributors
"""Ensure Branch education demo fields exist on Demo data tab."""

from __future__ import annotations

import frappe
from frappe.modules.import_file import import_file_by_path


def execute() -> None:
	if not frappe.db.exists("DocType", "Branch"):
		return

	path = frappe.get_app_path("omnexa_core", "omnexa_core", "doctype", "branch", "branch.json")
	import_file_by_path(path, force=True, ignore_version=True)

	for fieldname in (
		"branch_demo_group_education_label",
		"branch_demo_education_institution_type",
		"branch_demo_btn_education",
	):
		if not frappe.db.exists("DocField", {"parent": "Branch", "fieldname": fieldname}):
			frappe.throw(f"Branch education demo field missing: {fieldname}")

	frappe.clear_cache(doctype="Branch")
