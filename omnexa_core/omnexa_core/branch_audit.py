# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Scan DocTypes for company/branch isolation coverage."""

from __future__ import annotations

import frappe
from frappe.utils import get_bench_path
import os


_SKIP_DOCTYPES = frozenset(
	{
		"DocType",
		"Custom Field",
		"Property Setter",
		"Patch Log",
		"Version",
		"Error Log",
		"File",
		"Module Def",
		"Singles",
	}
)

_SKIP_FIELDTYPES = frozenset({"Section Break", "Column Break", "Tab Break", "Table", "Table MultiSelect"})


def _app_for_module(module: str | None) -> str | None:
	if not module:
		return None
	return frappe.db.get_value("Module Def", module, "app_name")


@frappe.whitelist()
def scan_branch_coverage(app: str | None = None) -> list[dict]:
	"""Return isolation status for custom DocTypes (optionally filtered by app)."""
	filters: dict = {"istable": 0, "issingle": 0, "custom": 0}
	if app:
		modules = frappe.get_all("Module Def", filters={"app_name": app}, pluck="name")
		if modules:
			filters["module"] = ["in", modules]

	rows: list[dict] = []
	for dt in frappe.get_all("DocType", filters=filters, pluck="name", order_by="name asc"):
		if dt in _SKIP_DOCTYPES:
			continue
		meta = frappe.get_meta(dt)
		if meta.issingle or meta.istable:
			continue

		has_company = meta.has_field("company")
		has_branch = meta.has_field("branch")
		mod = meta.module
		app_name = _app_for_module(mod) or ""

		if has_company and has_branch:
			status = "OK"
		elif has_company:
			status = "MISSING_BRANCH"
		elif meta.is_submittable or _looks_transactional(meta):
			status = "MISSING_BOTH"
		else:
			status = "MASTER_OR_CONFIG"

		rows.append(
			{
				"doctype": dt,
				"app": app_name,
				"module": mod,
				"has_company": int(has_company),
				"has_branch": int(has_branch),
				"is_submittable": int(meta.is_submittable),
				"status": status,
			}
		)
	return rows


def _looks_transactional(meta) -> bool:
	"""Heuristic: DocTypes with employee/customer/party links are likely transactional."""
	for df in meta.fields:
		if df.fieldtype in _SKIP_FIELDTYPES:
			continue
		if df.fieldtype == "Link" and df.options in ("Employee", "Customer", "Supplier", "Sales Invoice"):
			return True
	return False


@frappe.whitelist()
def export_branch_coverage_csv(app: str | None = None) -> dict:
	rows = scan_branch_coverage(app)
	import csv
	import io

	buf = io.StringIO()
	writer = csv.DictWriter(
		buf,
		fieldnames=["doctype", "app", "module", "has_company", "has_branch", "is_submittable", "status"],
	)
	writer.writeheader()
	writer.writerows(rows)

	path = os.path.join(get_bench_path(), "Docs", "2026-08-06_OMNEXA_ISOLATION_AND_HR", "audit_doctypes.csv")
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		fh.write(buf.getvalue())

	summary = {}
	for row in rows:
		summary[row["status"]] = summary.get(row["status"], 0) + 1

	return {"path": path, "total": len(rows), "summary": summary}


def get_missing_branch_doctypes(app: str | None = None, limit: int = 200) -> list[str]:
	rows = scan_branch_coverage(app)
	return [r["doctype"] for r in rows if r["status"] == "MISSING_BRANCH"][:limit]
