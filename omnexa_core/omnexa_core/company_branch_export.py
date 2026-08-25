# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import json
import os

import frappe
from frappe.utils import get_bench_path


@frappe.whitelist()
def export_company_branch_snapshot() -> dict:
	frappe.only_for("System Manager")
	companies = frappe.get_all(
		"Company",
		fields=["name", "company_name", "abbr", "default_currency"],
		order_by="name asc",
	)
	branches = frappe.get_all(
		"Branch",
		fields=["name", "branch_name", "branch_code", "company", "is_head_office"],
		order_by="company asc, is_head_office desc, branch_name asc",
	)
	payload = {"exported_at": str(frappe.utils.now()), "companies": companies, "branches": branches}
	path = os.path.join(
		get_bench_path(),
		"Docs",
		"2026-08-06_OMNEXA_ISOLATION_AND_HR",
		"company_branch_snapshot.json",
	)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(payload, fh, indent=2, ensure_ascii=False)
	return {"path": path, "companies": len(companies), "branches": len(branches)}
